# Stage 004 — Storyboard to Images

## Objective

Generate one correctly-sized 9:16 still for each `AI_CLIP` and `AI_IMAGE` scene
in the approved storyboard. Present each for approval; reroll rejects in place.
`REAL_FOOTAGE` scenes are skipped here (the human films them).

Read the approved `work/<campaign>/03-storyboard/storyboard.md`,
`reference/facebook-ad-specs.md`, and `reference/fal-generation.md`. Requires a
fal.ai key.

## 0. Cost baseline

Before the first generation, snapshot the fal.ai balance so we can report the
ad's cost later (needs a billing-scoped admin key — see
`reference/fal-generation.md`):

```bash
uv run tools/fal_cost.py snapshot --campaign <campaign> --label start
```

If it 403s (no admin key configured), skip it and note that cost tracking is
unavailable for this run — do not block generation on it.

## 1. Per AI scene, write an image prompt

Use `reference/templates/image-prompt.md`. Save to
`work/<campaign>/04-images/prompts/scene-<NN>.md`. A strong prompt states:

- **Format:** "Photorealistic vertical 9:16 advertising image, 1080×1920."
- **Subject & identity:** who, wardrobe, age range, expression — concrete.
- **Emotion / tone:** matched to the beat (e.g. wry regret for the hook, warm
  fresh-start confidence for the offer scene).
- **Composition:** where the subject sits so the storyboard's text overlay has a
  clear, safe-zone area (usually leave the vertical center clear for text).
- **Lighting & style:** bright soft advertising light, clean/premium, authentic
  not stocky — per brand voice.
- **Setting:** minimal or the real-room vibe; no fake clinical claims.
- **Negatives:** no watermark, no distorted hands/faces, no text unless the scene
  is explicitly "bake text," no fake before/after.

**Text policy:** by default do **not** ask the model to render the overlay text
(it renders unreliably). Generate a clean plate; the editor adds text. Only
include the overlay in the prompt if the storyboard marked the scene "bake text."

## 2. Generate

```bash
uv run tools/generate_image.py \
  --prompt-file work/<campaign>/04-images/prompts/scene-<NN>.md \
  --output work/<campaign>/04-images/scene-<NN>.png \
  --aspect-ratio 9:16 \
  --resolution 2K
```

- Add `--anchor brand/assets/logo.png` (or a room/style reference) when a scene
  must hold brand identity (e.g. the brand close).
- Start with one candidate. Use `--num-images 3` only after the look is dialed in.
- Default model `fal-ai/nano-banana-pro/edit` (see fal-generation for alternates).

## 3. Validate size

Confirm each saved PNG is 9:16 and close to 1080×1920. Editing models may not hit
exact pixels — if proportions are right but pixels differ, note it; the clip stage
and editor can normalize. If the aspect ratio is wrong, regenerate. Never promote
a wrong-aspect image.

## 4. Present each for approval

Show the user each still against its scene. On rejection, translate feedback into
precise prompt edits, regenerate, and **replace** the file (no versioned folders).

## Review gate

Every AI scene needs an approved still before stage 005. Copy approved stills for
`AI_IMAGE` scenes toward the deliverables; `AI_CLIP` stills feed stage 005.
