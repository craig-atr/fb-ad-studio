#!/usr/bin/env python3
"""Stage 004 image generation via fal.ai.

Sends a prompt (plus optional reference/anchor images) to a fal.ai image model
and saves the returned still. Synchronous endpoint (https://fal.run).

Auth: FAL_KEY environment variable, else a .fal_key file at the repo root.

Run with uv (no system Python or pip install required):

  uv run tools/generate_image.py \
    --prompt-file work/atomic-mothers-day/04-images/prompts/scene-01.md \
    --output work/atomic-mothers-day/04-images/scene-01.png \
    --aspect-ratio 9:16 \
    --resolution 2K

Models (via --model): fal-ai/nano-banana-pro/edit (default),
fal-ai/bytedance/seedream/v4.5/edit, fal-ai/flux-pro/kontext.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "fal-ai/nano-banana-pro/edit"
FAL_SYNC_BASE = "https://fal.run"
KEY_FILE_NAME = ".fal_key"


def repo_root() -> Path:
    # tools/generate_image.py -> repo root is the parent of tools/.
    return Path(__file__).resolve().parent.parent


def load_api_key() -> str:
    import os

    key = os.environ.get("FAL_KEY", "").strip()
    if key:
        return key

    key_path = repo_root() / KEY_FILE_NAME
    if key_path.is_file():
        # utf-8-sig tolerates the BOM PowerShell adds by default.
        key = key_path.read_text(encoding="utf-8-sig").strip()
        if key:
            return key

    raise SystemExit(
        "No fal.ai API key found.\n"
        "Set the FAL_KEY environment variable, or write the key to "
        f"{key_path}\n"
        "Get a key at https://fal.ai/dashboard/keys"
    )


def image_to_data_uri(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"Anchor image not found: {path}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None:
        mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def parse_param(raw: str):
    if "=" not in raw:
        raise SystemExit(f"--param must be key=value, got: {raw}")
    key, value = raw.split("=", 1)
    key = key.strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    return key, parsed


def build_payload(args) -> dict:
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit("Provide --prompt or --prompt-file.")

    payload: dict = {
        "prompt": prompt,
        "num_images": args.num_images,
        "output_format": args.output_format,
    }
    # Editing models take image_urls; text-to-image with no anchor omits it.
    if args.anchor:
        payload["image_urls"] = [image_to_data_uri(Path(a)) for a in args.anchor]
    if args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio
    if args.resolution:
        payload["resolution"] = args.resolution
    if args.seed is not None:
        payload["seed"] = args.seed
    for raw in args.param:
        key, value = parse_param(raw)
        payload[key] = value
    return payload


def call_fal(model: str, payload: dict, api_key: str, timeout: int) -> dict:
    url = f"{FAL_SYNC_BASE}/{model.strip('/')}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"fal.ai request failed ({exc.code}): {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach fal.ai: {exc.reason}")
    return json.loads(body)


def extract_image_urls(result: dict) -> list[str]:
    images = result.get("images")
    if isinstance(images, list) and images:
        urls = [i.get("url") for i in images if isinstance(i, dict) and i.get("url")]
        if urls:
            return urls
    single = result.get("image")
    if isinstance(single, dict) and single.get("url"):
        return [single["url"]]
    raise SystemExit(
        "No image URL in fal.ai response. Raw response:\n"
        + json.dumps(result, indent=2)[:2000]
    )


def download(url: str, dest: Path, timeout: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("data:"):
        _, _, b64 = url.partition(",")
        dest.write_bytes(base64.b64decode(b64))
        return
    with urllib.request.urlopen(url, timeout=timeout) as response:
        dest.write_bytes(response.read())


def numbered_path(base: Path, index: int) -> Path:
    if index == 0:
        return base
    return base.with_name(f"{base.stem}-{index + 1:02d}{base.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an ad still via fal.ai (stage 004)."
    )
    parser.add_argument("--prompt", help="Inline generation prompt text.")
    parser.add_argument("--prompt-file", help="Path to a file holding the prompt.")
    parser.add_argument(
        "--anchor",
        action="append",
        default=[],
        help="Reference image path (e.g. logo, room). Repeatable. Optional.",
    )
    parser.add_argument("--output", required=True, help="Where to save the result.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"fal model id (default {DEFAULT_MODEL}).")
    parser.add_argument("--num-images", type=int, default=1, help="Candidates to request.")
    parser.add_argument("--output-format", default="png", choices=["png", "jpeg"])
    parser.add_argument("--aspect-ratio", default="9:16", help="Default 9:16 for Reels/Stories.")
    parser.add_argument("--resolution", help="e.g. 1K, 2K, 4K (model-dependent).")
    parser.add_argument("--seed", type=int, help="Seed for reproducibility.")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Extra payload field as key=value (JSON-parsed when possible).",
    )
    parser.add_argument("--timeout", type=int, default=300, help="Request timeout seconds.")
    args = parser.parse_args()

    api_key = load_api_key()
    payload = build_payload(args)

    print(f"Calling {args.model} (aspect {args.aspect_ratio})...", file=sys.stderr)
    result = call_fal(args.model, payload, api_key, args.timeout)
    urls = extract_image_urls(result)

    output_base = Path(args.output)
    saved = []
    for index, url in enumerate(urls):
        dest = numbered_path(output_base, index)
        download(url, dest, args.timeout)
        saved.append(dest)
        print(f"Saved {dest}", file=sys.stderr)

    if result.get("description"):
        print(f"Model note: {result['description']}", file=sys.stderr)

    for path in saved:
        print(path)


if __name__ == "__main__":
    main()
