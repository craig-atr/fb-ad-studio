#!/usr/bin/env python3
"""Stage 006 packaging helper.

Deterministic, no dependencies. Copies a campaign's approved AI clips and stills
from work/<campaign>/ into output/<campaign>/, and validates every PNG still
against the target Facebook aspect ratio by reading the PNG header directly
(standard library only -- no Pillow, no ffprobe).

  uv run tools/build_shot_list.py --campaign atomic-mothers-day
  uv run tools/build_shot_list.py --campaign atomic-mothers-day --aspect 9:16

It does NOT write the shot-list.md prose (the agent authors that from the
template). It stages the asset folder and reports size caveats to fold in.
"""

from __future__ import annotations

import argparse
import shutil
import struct
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def png_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) from a PNG's IHDR, or None if not a PNG."""
    try:
        with path.open("rb") as fh:
            signature = fh.read(8)
            if signature != b"\x89PNG\r\n\x1a\n":
                return None
            fh.read(4)  # IHDR length
            if fh.read(4) != b"IHDR":
                return None
            width, height = struct.unpack(">II", fh.read(8))
            return width, height
    except OSError:
        return None


def aspect_ok(width: int, height: int, target: tuple[int, int], tol: float = 0.02) -> bool:
    want = target[0] / target[1]
    have = width / height
    return abs(have - want) / want <= tol


def copy_tree(src_files: list[Path], dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in src_files:
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        copied.append(dest)
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage a campaign's deliverables and validate sizes.")
    parser.add_argument("--campaign", required=True, help="Campaign name, e.g. atomic-mothers-day.")
    parser.add_argument("--aspect", default="9:16", help="Target aspect ratio (default 9:16).")
    args = parser.parse_args()

    root = repo_root()
    work = root / "work" / args.campaign
    out = root / "output" / args.campaign
    if not work.is_dir():
        raise SystemExit(f"No working folder: {work}")

    w, h = (int(x) for x in args.aspect.split(":"))
    target = (w, h)

    clips = sorted((work / "05-clips").glob("scene-*.mp4"))
    stills = sorted((work / "04-images").glob("scene-*.png"))

    copied_clips = copy_tree(clips, out / "clips")
    copied_stills = copy_tree(stills, out / "stills")

    print(f"Campaign: {args.campaign}")
    print(f"Output:   {out}")
    print(f"Clips copied:  {len(copied_clips)}")
    print(f"Stills copied: {len(copied_stills)}")
    print()

    caveats = []
    print(f"PNG size check (target {args.aspect}):")
    for still in copied_stills:
        size = png_size(still)
        if size is None:
            print(f"  {still.name}: not a readable PNG")
            caveats.append(f"{still.name}: unreadable PNG")
            continue
        pw, ph = size
        ideal = pw == 1080 and ph == 1920 and args.aspect == "9:16"
        ok = aspect_ok(pw, ph, target)
        flag = "OK" if ok else "WRONG ASPECT"
        exact = " (exact 1080x1920)" if ideal else ""
        print(f"  {still.name}: {pw}x{ph} -> {flag}{exact}")
        if not ok:
            caveats.append(f"{still.name}: {pw}x{ph} is not {args.aspect} -- regenerate")
        elif not ideal and args.aspect == "9:16":
            caveats.append(f"{still.name}: {pw}x{ph} (right aspect, not exactly 1080x1920 -- editor can scale)")

    print()
    if caveats:
        print("Caveats to note in shot-list.md:")
        for c in caveats:
            print(f"  - {c}")
    else:
        print("No size caveats. All stills match the target aspect.")

    print()
    print("Next: author output/<campaign>/shot-list.md and copy.md from the templates.")


if __name__ == "__main__":
    main()
