#!/usr/bin/env python3
"""Monthly-recap montage builder — fast-cut video from a folder of photos.

This is NOT part of the ad pipeline. It is the second half of the monthly
"tattoos I worked on this month" recap:

  1. Drop the month's photos in  work/monthly-recap/<month>/photos/
  2. uv run tools/crop_ui.py  work/monthly-recap/<month>     # crop each photo
  3. uv run tools/build_recap.py  work/monthly-recap/<month> # build the video

It reads the per-photo crop rectangles from <folder>/crops.json (written by the
crop UI) and stitches a silent, vertical, quick-cut montage with ffmpeg. The
video is SILENT on purpose — you add the music track in Instagram / Facebook.

If crops.json is missing, every photo is center-cropped to fill the frame
(cover), so the tool still works without the UI.

  uv run tools/build_recap.py work/monthly-recap/2026-11
  uv run tools/build_recap.py work/monthly-recap/2026-11 --seconds 0.3
  uv run tools/build_recap.py work/monthly-recap/2026-11 --target 15      # fit a 15s clip
  uv run tools/build_recap.py work/monthly-recap/2026-11 --crossfade 0.12

Needs ffmpeg on PATH (check: ffmpeg -version).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def list_photos(photos_dir: Path) -> list[str]:
    names = [p.name for p in photos_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return sorted(names, key=str.lower)


def ordered_photos(folder: Path) -> list[dict]:
    """Return [{file, crop, include}] honoring crops.json order; fall back to disk."""
    photos_dir = folder / "photos"
    crops_path = folder / "crops.json"
    on_disk = list_photos(photos_dir)

    if crops_path.is_file():
        data = json.loads(crops_path.read_text(encoding="utf-8"))
        items = []
        seen = set()
        for item in data.get("photos", []):
            name = item.get("file")
            if name in on_disk and name not in seen:
                items.append({
                    "file": name,
                    "crop": item.get("crop"),
                    "include": item.get("include", True),
                })
                seen.add(name)
        # Any new photos not yet in crops.json get appended, center-cropped.
        for name in on_disk:
            if name not in seen:
                items.append({"file": name, "crop": None, "include": True})
        return items

    return [{"file": n, "crop": None, "include": True} for n in on_disk]


def crop_scale_filter(crop: dict | None, w: int, h: int) -> str:
    """ffmpeg filter for one image: apply manual crop (if any), then fill WxH."""
    if crop and all(k in crop for k in ("x", "y", "w", "h")):
        # Manual crop box in fractions of the source; already matches target aspect.
        x, y, cw, ch = crop["x"], crop["y"], crop["w"], crop["h"]
        return (
            f"crop=iw*{cw:.6f}:ih*{ch:.6f}:iw*{x:.6f}:ih*{y:.6f},"
            f"scale={w}:{h}:flags=lanczos,setsar=1"
        )
    # No crop: cover the frame (scale up to fill, then center-crop).
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={w}:{h},setsar=1"
    )


def build(folder: Path, seconds: float, w: int, h: int, fps: int,
          crossfade: float, output: Path) -> None:
    photos = [p for p in ordered_photos(folder) if p.get("include", True)]
    if not photos:
        raise SystemExit(f"No photos to build. Add images to {folder / 'photos'}.")

    photos_dir = folder / "photos"
    n = len(photos)

    # Inputs: each still looped for its on-screen duration. With crossfades the
    # clips must overlap, so each (except the first) is extended by the fade.
    args: list[str] = ["ffmpeg", "-y"]
    for i, p in enumerate(photos):
        # With crossfades, EVERY clip (the first included) needs fade headroom so
        # xfade has frames to dissolve into; otherwise the chain starves and the
        # output collapses. Each photo still gets ~`seconds` of unique screen time
        # because the xfade offsets advance by `seconds` (see below).
        dur = seconds + (crossfade if crossfade > 0 else 0)
        args += ["-loop", "1", "-t", f"{dur:.4f}", "-i", str(photos_dir / p["file"])]

    chains = []
    for i, p in enumerate(photos):
        chains.append(f"[{i}:v]{crop_scale_filter(p['crop'], w, h)},fps={fps},format=yuv420p[v{i}]")

    if crossfade > 0 and n > 1:
        # Chain xfade transitions. offset accumulates: each segment adds `seconds`.
        prev = "v0"
        offset = seconds
        for i in range(1, n):
            out = f"x{i}" if i < n - 1 else "outv"
            chains.append(
                f"[{prev}][v{i}]xfade=transition=fade:duration={crossfade:.4f}:"
                f"offset={offset:.4f}[{out}]"
            )
            prev = out
            offset += seconds
        filtergraph = ";".join(chains)
        vout = "[outv]"
    else:
        filtergraph = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[outv]"
        vout = "[outv]"

    args += [
        "-filter_complex", filtergraph,
        "-map", vout,
        "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart",
        str(output),
    ]

    total = seconds * n + (crossfade if crossfade > 0 else 0)
    print(f"Building recap: {n} photos x {seconds:.2f}s"
          + (f" with {crossfade:.2f}s crossfades" if crossfade > 0 else " (hard cuts)"))
    print(f"  size: {w}x{h} @ {fps}fps   ~{total:.1f}s   silent (add music in-app)")
    print(f"  output: {output}")

    result = subprocess.run(args, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr[-3000:])
        raise SystemExit(f"\nffmpeg failed (exit {result.returncode}).")
    print(f"Done -> {output}")


def main() -> None:
    p = argparse.ArgumentParser(description="Build the monthly recap montage from cropped photos.")
    p.add_argument("folder", help="Month folder, e.g. work/monthly-recap/2026-11.")
    p.add_argument("--seconds", type=float, default=0.4, help="Seconds each photo is on screen (default 0.4).")
    p.add_argument("--target", type=float, default=None,
                   help="Target total length in seconds; overrides --seconds to fit all photos.")
    p.add_argument("--width", type=int, default=1080, help="Output width (default 1080).")
    p.add_argument("--height", type=int, default=1920, help="Output height (default 1920).")
    p.add_argument("--fps", type=int, default=30, help="Frame rate (default 30).")
    p.add_argument("--crossfade", type=float, default=0.0,
                   help="Crossfade seconds between photos (default 0 = hard cuts). Try 0.1.")
    p.add_argument("--output", default=None, help="Output file (default <folder>/recap.mp4).")
    args = p.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not found on PATH. Install it or check `ffmpeg -version`.")

    folder = Path(args.folder).resolve()
    if not (folder / "photos").is_dir():
        raise SystemExit(f"No photos folder: {folder / 'photos'}")

    seconds = args.seconds
    if args.target is not None:
        n = len([p for p in ordered_photos(folder) if p.get("include", True)])
        if n == 0:
            raise SystemExit(f"No photos to build. Add images to {folder / 'photos'}.")
        seconds = args.target / n

    output = Path(args.output).resolve() if args.output else folder / "recap.mp4"
    build(folder, seconds, args.width, args.height, args.fps, args.crossfade, output)


if __name__ == "__main__":
    main()
