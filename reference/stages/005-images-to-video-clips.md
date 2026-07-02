# Stage 005 — Images to Video Clips

## Objective

Animate each approved `AI_CLIP` still into a short (5 s) 9:16 clip using Kling
image-to-video. Present each clip for approval; reroll rejects in place.
`AI_IMAGE` scenes stay static (no clip). `REAL_FOOTAGE` scenes are the human's.

Read the approved storyboard and stills, `reference/fal-generation.md`, and
`reference/facebook-ad-specs.md`. Requires a fal.ai key.

## 1. Per AI_CLIP scene, write a motion prompt

Use `reference/templates/kling-prompt.md`. Save to
`work/<campaign>/05-clips/prompts/scene-<NN>.md`. Describe **motion only** — the
still already fixes identity, composition, and style. Good motion prompts:

- Name the **specific movement** for the 5 s (e.g. "she slowly glances down at
  the tattoo, faint wry smile forms; subtle breathing").
- Keep the **camera controlled**: "fixed camera" or "slow subtle push-in" — avoid
  wild moves that break framing or the safe zone.
- Keep it **subtle and believable**. Big motion over 5 s drifts identity.
- Preserve framing and scale so the clip stays 9:16 with the subject where the
  overlay expects it.

### Negatives (default)

Start `--negative-prompt` from: `blur, distortion, warping, morphing face,
extra fingers, text, watermark, camera shake, rapid zoom`. Add scene-specific
prohibitions.

## 2. Generate

Aspect ratio is inherited from the input image, so a 1080×1920 still yields a 9:16
clip. Video is slow — the tool submits to fal's queue and polls until done.

```bash
uv run tools/generate_video.py \
  --image work/<campaign>/04-images/scene-<NN>.png \
  --prompt-file work/<campaign>/05-clips/prompts/scene-<NN>.md \
  --output work/<campaign>/05-clips/scene-<NN>.mp4 \
  --duration 5
```

Default model `fal-ai/kling-video/v2.5-turbo/pro/image-to-video`. Use `--duration
10` only if a beat genuinely needs it (most beats are 2–5 s; the editor trims).

## 3. Acceptance gate per clip

Reject and reroll a clip if:

- identity drifts badly from the approved still
- the face/hands warp or morph
- the camera lurches, zooms hard, or breaks framing
- the subject leaves the safe composition
- unwanted text, artifacts, or scene changes appear

First try a better motion prompt or a new seed before regenerating the still.

## 4. Validate and present

Confirm each clip is 9:16 MP4. Show each to the user against its scene. Replace
rejects in place.

## Review gate

Every `AI_CLIP` scene needs an approved clip before stage 006.
