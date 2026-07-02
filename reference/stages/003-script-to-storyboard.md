# Stage 003 — Script to Storyboard

## Objective

Expand the approved script's beat sheet into a concrete **scene-by-scene
storyboard**. Each scene is a fully specified shot: timing, visual, on-screen
text, source type, and (for AI scenes) enough detail to write a generation prompt
in stage 004.

Read `work/<campaign>/02-script/script.md`, the brand profile, and
`reference/facebook-ad-specs.md`. Use `reference/templates/storyboard.md`.

## 1. Break the beat sheet into scenes

Typical 18–20 s ad = 5–6 scenes of 2–5 s each. For each scene assign a
zero-padded id (`01`, `02`, …) in play order and define:

- `id` and `time` range (must chain with no gaps and total 15–20 s)
- `source`: `AI_CLIP` | `AI_IMAGE` | `REAL_FOOTAGE`
- `visual`: concrete description of the shot (subject, framing, expression,
  setting). Prefer physical description over vague adjectives.
- `text_overlay`: the exact on-screen words (or `none`). Keep muted-friendly and
  inside the safe zone.
- `motion`: for `AI_CLIP`, what should move in the 5 s (subtle — see stage 005);
  for `AI_IMAGE`, `static hold`; for `REAL_FOOTAGE`, what the human should shoot.
- `audio`: music/beat note.

## 2. Respect the source split

- `REAL_FOOTAGE` for the trust core: **laser in action, real before/after, real
  clinic**. Never convert these to AI. Write clear **capture instructions** so the
  human knows exactly what to film.
- `AI_CLIP` / `AI_IMAGE` for hook, emotional beat, lifestyle/fresh-start, brand
  close.
- Confirm every scene's aspect target is 9:16 / 1080×1920.

## 3. Design each AI scene to be generatable

For every `AI_CLIP` / `AI_IMAGE`, make sure the visual description is specific
enough to become a strong image prompt (subject identity, wardrobe, expression,
lighting, setting, mood). Note any brand asset to use as an anchor (logo, room
reference).

## 4. Text-overlay policy

Default: **do not** bake text into the generated images (models render text
badly). Record `text_overlay` in the storyboard for the human editor to burn in.
Only mark a scene "bake text" if the user explicitly wants it.

## 5. Write and present

Save to `work/<campaign>/03-storyboard/storyboard.md`. Present the scene list as a
compact table (id, time, source, visual, overlay) plus the real-footage capture
list.

## Review gate

This is the **budget gate**. Get explicit storyboard approval before stage 004 —
no fal generation happens until the storyboard (scenes, timings, source tags) is
locked. Revise in place on feedback.
