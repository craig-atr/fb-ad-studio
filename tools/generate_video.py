#!/usr/bin/env python3
"""Stage 005 image-to-video via fal.ai — model-agnostic.

Animates an approved still into a short clip. The workflow is free to pick the
best model for each shot (see reference/fal-generation.md for the menu); this
tool just sends `prompt` + `image_url` plus whatever OPTIONAL params you pass, so
it works with Veo, Kling, Seedance, Hailuo, etc. — pass `--model` + the params
that model accepts.

Video is slow, so this uses fal's QUEUE API (submit -> poll -> fetch -> download).

Auth: FAL_KEY env var, else a .fal_key file at the repo root.

Veo 3.1 (default, best all-rounder):
  uv run tools/generate_video.py --image still.png --prompt-file p.md \
    --output clip.mp4 --duration 4s --resolution 1080p --aspect-ratio 9:16 \
    --generate-audio false

Kling (cheaper motion):
  uv run tools/generate_video.py --model fal-ai/kling-video/v2.5-turbo/pro/image-to-video \
    --image still.png --prompt-file p.md --output clip.mp4 --duration 5 \
    --cfg-scale 0.5 --negative-prompt "blur, warp"

Start/end-frame (e.g. Seedance) to pin motion (great for text stability):
  ... --end-image end.png --end-image-field end_image_url
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "fal-ai/veo3.1/image-to-video"
QUEUE_BASE = "https://queue.fal.run"
KEY_FILE_NAME = ".fal_key"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_api_key() -> str:
    key = os.environ.get("FAL_KEY", "").strip()
    if key:
        return key
    key_path = repo_root() / KEY_FILE_NAME
    if key_path.is_file():
        key = key_path.read_text(encoding="utf-8-sig").strip()
        if key:
            return key
    raise SystemExit(
        "No fal.ai API key found. Set FAL_KEY or write the key to "
        f"{key_path}."
    )


def image_to_data_uri(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"Image not found: {path}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None:
        mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def http_json(url: str, api_key: str, data: bytes | None = None, timeout: int = 60) -> dict:
    request = urllib.request.Request(
        url, data=data, method="POST" if data is not None else "GET", headers=auth_headers(api_key)
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"fal.ai request failed ({exc.code}) at {url}: {detail[:1500]}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach fal.ai: {exc.reason}")


def status_and_result_urls(model: str, submit_response: dict) -> tuple[str, str]:
    status_url = submit_response.get("status_url")
    response_url = submit_response.get("response_url")
    if status_url and response_url:
        return status_url, response_url
    request_id = submit_response.get("request_id")
    if not request_id:
        raise SystemExit("fal queue submit returned no request_id:\n" + json.dumps(submit_response, indent=2)[:2000])
    base = f"{QUEUE_BASE}/{model.strip('/')}/requests/{request_id}"
    return f"{base}/status", base


def poll_until_done(status_url: str, api_key: str, poll_secs: int, max_wait: int) -> None:
    waited = 0
    while True:
        state = http_json(status_url, api_key).get("status")
        if state == "COMPLETED":
            return
        if state in ("FAILED", "ERROR", "CANCELLED"):
            raise SystemExit(f"fal video job failed (status {state}).")
        if waited >= max_wait:
            raise SystemExit(f"Timed out after {max_wait}s (status {state}).")
        print(f"  ...{state or 'IN_QUEUE'} ({waited}s)", file=sys.stderr)
        time.sleep(poll_secs)
        waited += poll_secs


def extract_video_url(result: dict) -> str:
    video = result.get("video")
    if isinstance(video, dict) and video.get("url"):
        return video["url"]
    videos = result.get("videos")
    if isinstance(videos, list) and videos and isinstance(videos[0], dict) and videos[0].get("url"):
        return videos[0]["url"]
    raise SystemExit("No video URL in fal response:\n" + json.dumps(result, indent=2)[:2000])


def download(url: str, dest: Path, timeout: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        dest.write_bytes(response.read())


def main() -> None:
    p = argparse.ArgumentParser(description="Animate a still into a clip via fal.ai (model-agnostic).")
    p.add_argument("--image", required=True, help="Start still (maps to image_url).")
    p.add_argument("--prompt")
    p.add_argument("--prompt-file")
    p.add_argument("--output", required=True)
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"fal model id (default {DEFAULT_MODEL}).")
    # Optional, model-specific — only sent if provided:
    p.add_argument("--duration", help='e.g. "4s" (Veo) or "5" (Kling).')
    p.add_argument("--resolution", help='e.g. 720p, 1080p, 4k (Veo/Seedance).')
    p.add_argument("--aspect-ratio", help='e.g. 9:16.')
    p.add_argument("--negative-prompt")
    p.add_argument("--cfg-scale", type=float, help="Kling guidance scale.")
    p.add_argument("--generate-audio", choices=["true", "false"], help="Veo audio (default we pass false).")
    p.add_argument("--seed", type=int)
    p.add_argument("--end-image", help="End/last frame still for start-end-frame models.")
    p.add_argument("--end-image-field", default="end_image_url",
                   help="Payload field for the end frame (Seedance: end_image_url; Kling: tail_image_url).")
    p.add_argument("--param", action="append", default=[], help="Extra field key=value (JSON when possible). Repeatable.")
    p.add_argument("--poll-secs", type=int, default=10)
    p.add_argument("--max-wait", type=int, default=900)
    p.add_argument("--timeout", type=int, default=300)
    args = p.parse_args()

    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit("Provide --prompt or --prompt-file.")

    payload: dict = {"prompt": prompt, "image_url": image_to_data_uri(Path(args.image))}
    if args.duration:
        payload["duration"] = args.duration
    if args.resolution:
        payload["resolution"] = args.resolution
    if args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio
    if args.negative_prompt:
        payload["negative_prompt"] = args.negative_prompt
    if args.cfg_scale is not None:
        payload["cfg_scale"] = args.cfg_scale
    if args.generate_audio is not None:
        payload["generate_audio"] = args.generate_audio == "true"
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.end_image:
        payload[args.end_image_field] = image_to_data_uri(Path(args.end_image))
    for raw in args.param:
        if "=" not in raw:
            raise SystemExit(f"--param must be key=value: {raw}")
        key, value = raw.split("=", 1)
        try:
            payload[key.strip()] = json.loads(value)
        except json.JSONDecodeError:
            payload[key.strip()] = value

    api_key = load_api_key()
    print(f"Submitting to {args.model} ...", file=sys.stderr)
    submit_response = http_json(f"{QUEUE_BASE}/{args.model.strip('/')}", api_key,
                                data=json.dumps(payload).encode("utf-8"))
    status_url, response_url = status_and_result_urls(args.model, submit_response)
    print("Queued. Polling (video takes a few minutes)...", file=sys.stderr)
    poll_until_done(status_url, api_key, args.poll_secs, args.max_wait)
    url = extract_video_url(http_json(response_url, api_key))
    download(url, Path(args.output), args.timeout)
    print(f"Saved {args.output}", file=sys.stderr)
    print(args.output)


if __name__ == "__main__":
    main()
