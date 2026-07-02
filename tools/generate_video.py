#!/usr/bin/env python3
"""Stage 005 image-to-video via fal.ai Kling.

Animates one approved still into a short 9:16 clip. The clip's aspect ratio is
inherited from the input image, so feed a 1080x1920 still to get a 9:16 clip.

Video generation is slow (minutes), so this uses fal's QUEUE API:
  submit -> poll status -> fetch result -> download the mp4.

Auth: FAL_KEY environment variable, else a .fal_key file at the repo root.

  uv run tools/generate_video.py \
    --image work/atomic-mothers-day/04-images/scene-01.png \
    --prompt-file work/atomic-mothers-day/05-clips/prompts/scene-01.md \
    --output work/atomic-mothers-day/05-clips/scene-01.mp4 \
    --duration 5
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
QUEUE_BASE = "https://queue.fal.run"
KEY_FILE_NAME = ".fal_key"
DEFAULT_NEGATIVE = (
    "blur, distortion, warping, morphing face, extra fingers, text, watermark, "
    "camera shake, rapid zoom, scene change"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_api_key() -> str:
    import os

    key = os.environ.get("FAL_KEY", "").strip()
    if key:
        return key
    key_path = repo_root() / KEY_FILE_NAME
    if key_path.is_file():
        key = key_path.read_text(encoding="utf-8-sig").strip()
        if key:
            return key
    raise SystemExit(
        "No fal.ai API key found.\n"
        "Set the FAL_KEY environment variable, or write the key to "
        f"{key_path}\nGet a key at https://fal.ai/dashboard/keys"
    )


def image_to_data_uri(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"Input image not found: {path}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None:
        mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def http_json(url: str, api_key: str, data: bytes | None = None, timeout: int = 60) -> dict:
    method = "POST" if data is not None else "GET"
    request = urllib.request.Request(url, data=data, method=method, headers=auth_headers(api_key))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"fal.ai request failed ({exc.code}) at {url}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach fal.ai: {exc.reason}")


def submit(model: str, payload: dict, api_key: str) -> dict:
    url = f"{QUEUE_BASE}/{model.strip('/')}"
    return http_json(url, api_key, data=json.dumps(payload).encode("utf-8"))


def status_and_result_urls(model: str, submit_response: dict) -> tuple[str, str]:
    # Prefer the URLs fal returns; fall back to constructing them.
    status_url = submit_response.get("status_url")
    response_url = submit_response.get("response_url")
    if status_url and response_url:
        return status_url, response_url
    request_id = submit_response.get("request_id")
    if not request_id:
        raise SystemExit(
            "fal queue submit returned no request_id/status_url:\n"
            + json.dumps(submit_response, indent=2)[:2000]
        )
    base = f"{QUEUE_BASE}/{model.strip('/')}/requests/{request_id}"
    return f"{base}/status", base


def poll_until_done(status_url: str, api_key: str, poll_secs: int, max_wait: int) -> None:
    waited = 0
    while True:
        status = http_json(status_url, api_key)
        state = status.get("status")
        if state == "COMPLETED":
            return
        if state in ("FAILED", "ERROR", "CANCELLED"):
            raise SystemExit("fal video job failed:\n" + json.dumps(status, indent=2)[:2000])
        if waited >= max_wait:
            raise SystemExit(f"Timed out after {max_wait}s waiting for the video (status {state}).")
        print(f"  ...{state or 'IN_QUEUE'} ({waited}s)", file=sys.stderr)
        time.sleep(poll_secs)
        waited += poll_secs


def extract_video_url(result: dict) -> str:
    video = result.get("video")
    if isinstance(video, dict) and video.get("url"):
        return video["url"]
    # Some variants return a list of videos.
    videos = result.get("videos")
    if isinstance(videos, list) and videos and isinstance(videos[0], dict) and videos[0].get("url"):
        return videos[0]["url"]
    raise SystemExit("No video URL in fal response:\n" + json.dumps(result, indent=2)[:2000])


def download(url: str, dest: Path, timeout: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("data:"):
        _, _, b64 = url.partition(",")
        dest.write_bytes(base64.b64decode(b64))
        return
    with urllib.request.urlopen(url, timeout=timeout) as response:
        dest.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate a still into a clip via fal Kling (stage 005).")
    parser.add_argument("--image", required=True, help="Approved still (9:16) to animate.")
    parser.add_argument("--prompt", help="Inline motion prompt.")
    parser.add_argument("--prompt-file", help="Path to a file holding the motion prompt.")
    parser.add_argument("--output", required=True, help="Where to save the mp4.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"fal model id (default {DEFAULT_MODEL}).")
    parser.add_argument("--duration", default="5", choices=["5", "10"], help="Clip length seconds.")
    parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE)
    parser.add_argument("--cfg-scale", type=float, default=0.5, help="Guidance scale (default 0.5).")
    parser.add_argument("--poll-secs", type=int, default=10, help="Status poll interval.")
    parser.add_argument("--max-wait", type=int, default=900, help="Max seconds to wait.")
    parser.add_argument("--timeout", type=int, default=300, help="Per-request/download timeout.")
    args = parser.parse_args()

    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit("Provide --prompt or --prompt-file.")

    api_key = load_api_key()
    payload = {
        "prompt": prompt,
        "image_url": image_to_data_uri(Path(args.image)),
        "duration": args.duration,
        "negative_prompt": args.negative_prompt,
        "cfg_scale": args.cfg_scale,
    }

    print(f"Submitting to {args.model} ({args.duration}s)...", file=sys.stderr)
    submit_response = submit(args.model, payload, api_key)
    status_url, response_url = status_and_result_urls(args.model, submit_response)

    print("Queued. Polling for completion (video takes a few minutes)...", file=sys.stderr)
    poll_until_done(status_url, api_key, args.poll_secs, args.max_wait)

    result = http_json(response_url, api_key)
    url = extract_video_url(result)

    dest = Path(args.output)
    download(url, dest, args.timeout)
    print(f"Saved {dest}", file=sys.stderr)
    print(dest)


if __name__ == "__main__":
    main()
