# fal.ai Generation Setup

Two generation stages call fal.ai: images (stage 004) and video (stage 005).
Both tools live in `tools/` and reuse the same auth as the
`spritesheet-animation-tool` project.

## One-time setup

1. Get a fal.ai API key: https://fal.ai/dashboard/keys (add billing — image and
   video models are pay-per-call).
2. Provide the key one of two ways. Tools check `FAL_KEY` first, then a `.fal_key`
   file at the repo root:

   ```powershell
   $env:FAL_KEY = "your-key-here"        # PowerShell, per session
   ```

   ```text
   C:\fb-ad-studio\.fal_key              # or a local file (gitignored)
   ```

3. No system Python needed. Tools run under `uv`, which fetches a managed Python:

   ```bash
   uv run tools/generate_image.py --help
   uv run tools/generate_video.py --help
   ```

   Any Python 3.9+ also works (tools use only the standard library).

## Image generation (stage 004)

`tools/generate_image.py` posts a prompt plus optional reference/anchor images to
a fal image model and saves the result. Synchronous (`https://fal.run`).

```bash
uv run tools/generate_image.py \
  --prompt-file work/atomic-mothers-day/04-images/prompts/scene-01.md \
  --output work/atomic-mothers-day/04-images/scene-01.png \
  --aspect-ratio 9:16 \
  --resolution 2K
```

Optional `--anchor path.png` (repeatable) passes reference images — use the brand
logo or a real client photo to hold identity/branding. `--num-images N` returns
multiple candidates; `--seed N` for reproducibility.

**Two endpoints — pick by whether you have an anchor:**

- **No anchor (new person/scene from scratch):** use the text-to-image model
  `--model fal-ai/nano-banana-pro` (no `/edit`). Accepts `--aspect-ratio 9:16`
  and `--resolution 2K`; returns ~1536×2752.
- **With anchor(s) (hold identity/brand, or edit an existing still):** use the
  default `fal-ai/nano-banana-pro/edit`. This is how we reuse an approved hook
  still as the anchor for a later scene (same person), composite the real room +
  logo for the brand close, and make targeted edits (e.g. recolor logo text).

The edit model can over-copy the anchor's *pose*, not just identity. If a "same
person, new shot" scene clones the original pose, add an explicit instruction:
"use the reference ONLY for facial identity; do NOT copy the pose," and describe
the new pose concretely.

| Model id | Notes |
| --- | --- |
| `fal-ai/nano-banana-pro/edit` | **Default.** Best identity consistency across references. Supports `--aspect-ratio`, `--resolution`. |
| `fal-ai/bytedance/seedream/v4.5/edit` | Strong high-res + layout adherence. |
| `fal-ai/flux-pro/kontext` | Cheaper context editing for targeted iteration. |

Editing models don't always honor an exact pixel canvas — `--aspect-ratio 9:16`
gets the proportions; validate the saved file is 1080×1920 (or close and
crop/upscale) before handoff. See `reference/facebook-ad-specs.md`.

## Video generation (stage 005)

`tools/generate_video.py` animates one approved still into a short clip using
Kling image-to-video. Video is slow (minutes), so the tool uses fal's **queue
API** (submit → poll → fetch), not the sync endpoint.

```bash
uv run tools/generate_video.py \
  --image work/atomic-mothers-day/04-images/scene-01.png \
  --prompt-file work/atomic-mothers-day/05-clips/prompts/scene-01.md \
  --output work/atomic-mothers-day/05-clips/scene-01.mp4 \
  --duration 5
```

- **Aspect ratio is inherited from the input image.** Feed a 1080×1920 still and
  the clip is 9:16. This is why stage 004 sizing matters.
- `--duration` accepts `5` or `10` (Kling). Default `5`.
- `--negative-prompt` defaults to discouraging blur/distortion/warping; add
  scene-specific negatives (e.g. "no camera zoom, no text").
- `--cfg-scale` (default 0.5) trades prompt adherence vs natural motion.

| Model id | Notes |
| --- | --- |
| `fal-ai/kling-video/v2.5-turbo/pro/image-to-video` | **Default.** Fast, strong motion, holds the input image well. |
| `fal-ai/kling-video/v2.1/pro/image-to-video` | Alternate quality/price point. |

Kling clips come out as H.264 MP4 — already Meta-compatible. The human editor
trims and sequences them; each AI clip is a 5 s building block, not the final ad.
Observed output: ~1072×1928 (9:16), 24 fps, ~5 s. Close to but not exactly
1080×1920/30 fps — the editor scales to 1080×1920 and exports at 30 fps.

`ffmpeg`/`ffprobe` (used to spot-check clips and for the optional stage-006
rough-cut) are installed via scoop at `~/scoop/shims/`. Extract a late frame to
audit identity drift: `ffmpeg -ss 4 -i clip.mp4 -frames:v 1 frame.png`.

## Cost tracking + balance (`tools/fal_cost.py`)

Every campaign should report **how much the ad cost** and the **current fal.ai
balance**. fal doesn't return per-call cost, so cost is measured as the balance
drop across the campaign's generations.

**Setup (one-time):** the billing endpoint needs a **billing-scoped admin key**
(your normal generation key returns 403). Create one at
https://fal.ai/dashboard/keys and save it to `.fal_admin_key` at the repo root
(gitignored), or set `FAL_ADMIN_KEY`. The tool prefers the admin key and falls
back to `.fal_key`.

```bash
uv run tools/fal_cost.py balance                                  # current balance
uv run tools/fal_cost.py snapshot --campaign <c> --label start    # stage 004, pre-gen
uv run tools/fal_cost.py snapshot --campaign <c> --label end      # stage 006
uv run tools/fal_cost.py report   --campaign <c>                  # spend + balance
```

Snapshots are logged to `work/<campaign>/cost-log.jsonl`. Spend = first snapshot
balance − current balance, so keep unrelated fal work out of the window for an
exact per-ad figure. Without an admin key the tool 403s gracefully; report that
cost tracking is unavailable and point to the dashboard.

## Cost discipline

- Never generate a full storyboard before the storyboard is approved (gate 3).
- Generate one candidate first; only fan out `--num-images` after the look is
  dialed in.
- Reroll rejects in place; don't accumulate versioned folders.
