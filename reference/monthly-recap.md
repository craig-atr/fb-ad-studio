# Monthly recap video

A standalone, repeatable workflow for the monthly "tattoos I worked on this
month" post: a fast-cut, vertical montage of this month's photos, **silent** so
you add the music track in Instagram / Facebook.

This is **not** the ad pipeline — no stages, no review gates, no fal.ai, no cost.
It reuses only the local tooling (`uv`, `ffmpeg`).

## Folder layout

One folder per month under `work/monthly-recap/`:

```
work/monthly-recap/2026-11/
  photos/        <- drop this month's photos here (jpg / png / webp)
  crops.json     <- written by the crop UI (per-photo crop + order)
  recap.mp4      <- the finished video
```

## Steps

**1. Drop the photos.** Put the month's photos in `photos/`. Any mix of portrait
and landscape is fine — you crop them next.

**2. Crop each photo.**

```bash
uv run tools/crop_ui.py work/monthly-recap/2026-11
```

Opens a local web page. For each photo, drag the aspect-locked box to frame the
tattoo, use **Prev/Next** (or ← →) to move through them, reorder with the ▲▼
buttons on a thumbnail, and **Exclude** any you don't want. Click **Save
crops.json** (or Ctrl+S) when done. Nothing leaves your machine — it's a local
server on `127.0.0.1`.

- `--aspect 1:1` for a square feed post (default is `9:16` for Reels/Stories).
- `--port 8800` if 8765 is busy.

**3. Build the video.**

```bash
uv run tools/build_recap.py work/monthly-recap/2026-11
```

Writes `recap.mp4` (1080×1920, silent). Knobs:

| Flag | Default | Effect |
| --- | --- | --- |
| `--seconds 0.4` | 0.4 | seconds each photo is on screen |
| `--target 15` | — | fit all photos into a 15s clip (overrides `--seconds`) |
| `--crossfade 0.1` | 0 (hard cuts) | brief dissolve between photos |
| `--aspect`/`--width`/`--height` | 9:16 / 1080×1920 | frame size |
| `--fps 30` | 30 | frame rate |

**4. Post.** Drop `recap.mp4` into Instagram/Facebook and add your music.

## Notes

- If you skip the crop UI, `build_recap.py` center-crops every photo to fill the
  frame, so it still works — the UI just gives you control over the framing.
- Crops are stored as fractions of each source image, so re-running the build at
  a different size (e.g. `1:1`) reuses the same framing.
