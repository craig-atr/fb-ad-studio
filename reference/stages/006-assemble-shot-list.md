# Stage 006 — Assemble Shot List (Editor Handoff)

## Objective

Package everything a human editor needs to cut the final ad: the ordered
timeline, every asset (AI clips + AI stills), the exact real-footage the human
must film, the on-screen text overlays with timings, and the final ad copy.

This stage produces the **deliverable**. It does not (by default) render a final
video — the human assembles it.

Read the approved storyboard, the approved clips/stills, the script copy, and
`reference/facebook-ad-specs.md`. Use `reference/templates/shot-list.md`.

## 1. Build the timeline

List every scene in play order with:

- `id`, `in`–`out` time, running total
- `source`: `AI_CLIP` (file path) / `AI_IMAGE` (file path, hold duration) /
  `REAL_FOOTAGE` (capture instruction)
- `text_overlay`: exact words + on/off timing + safe-zone placement note
- `audio`: music/beat cue

Confirm the timeline totals 15–20 s and something changes every 2–3 s.

## 2. Write the real-footage capture list

For each `REAL_FOOTAGE` scene, give the human a concrete shot to film:

- what to shoot (e.g. "close-up laser pass across a forearm tattoo, visible
  frosting response")
- framing: **vertical 9:16**, film full-frame so it drops into the timeline
- rough length needed (film 2–3× the beat length for trim room)
- any must-avoid (client faces if no release, harsh reflections, etc.)

## 3. Assemble the deliverable folder

```text
output/<campaign>/
├── clips/scene-<NN>.mp4     approved AI clips
├── stills/scene-<NN>.png    approved AI_IMAGE stills
├── overlays/<id>.png/.mov   transparent text-overlay assets (optional, below)
├── shot-list.md             this handoff (timeline + capture list + overlays)
└── copy.md                  final headline / primary text / description / CTA
```

### Text-overlay assets (recommended)

Build the on-screen text as **transparent-background** assets the editor can drop
over the footage (keep them if they work, or swap in their own):

```bash
bash tools/build_overlays.sh <campaign>   # -> output/<campaign>/overlays/
```

Edit the `OVERLAYS` list at the top of the script to match the shot-list copy.
Each overlay is produced as a transparent **PNG** (RGBA, universal / CapCut) and
a **ProRes 4444 `.mov`** with alpha + fade (Premiere / Resolve / FCP). Needs
`ffmpeg`. White text, shadow + outline, centered in the 9:16 safe zone.

### Static offer images (companion creatives)

Facebook's feed wants static image creatives too — notably a **1:1 square**.
Build offer cards (hero photo + off-white offer panel with logo + text) in Meta's
key sizes:

```bash
bash tools/build_offer_image.sh <campaign> [background.png]   # -> offer-images/
```

Produces **square 1080×1080** (Feed, primary), **1080×1350** (4:5 Feed), and
**1080×1920** (9:16). Default hero is `stills/scene-05.png`; pass another still to
override. Edit `HOOK/OFFER/URGENCY` at the top for the copy. Text is ffmpeg-
rendered (reliable), logo auto-centered so it never overlaps the text.

Copy approved assets from `work/<campaign>/` into `output/<campaign>/`. Write
`copy.md` from the approved script. Export overlay text and timings in the shot
list so the editor can burn them in inside the safe zone.

## 4. Editor notes

State the export target explicitly for the human: **9:16, 1080×1920, H.264 MP4,
~30 fps, 15–20 s, muted-friendly big text**, CTA handled by Meta's Book Now
button (don't duplicate it as a hard end-card unless desired). Remind them the
landing page must repeat the headline hook.

## Optional: rough-cut assembly

Only if the user asks. `tools/build_roughcut.sh <campaign>` stitches the approved
AI clips + stills into a 1080×1920/30fps timeline with labeled dark slates where
REAL_FOOTAGE will go:

```bash
bash tools/build_roughcut.sh atomic-mothers-day   # -> output/<campaign>/rough-cut.mp4
```

Edit the `BEATS` list at the top of the script to match the campaign's shot-list
(order, per-beat durations, clip/still/slate). Needs `ffmpeg` (scoop:
`scoop install ffmpeg`); check `ffmpeg -version` first and ask before installing.
This is a scratch timing preview — no baked overlays, no audio — never the final
deliverable.

## 5. Cost report

Snapshot the balance again and report the ad's spend + remaining balance:

```bash
uv run tools/fal_cost.py snapshot --campaign <campaign> --label end
uv run tools/fal_cost.py report   --campaign <campaign>
```

Include the two figures — **cost to create this ad** and **current fal.ai
balance** — in the handoff summary. If no admin key is configured (403), state
that cost tracking wasn't available and point to the fal dashboard.

## Done

Report the deliverable path, the timeline length, the list of real shots the human
still needs to film, any size caveats, and the **cost of the ad + fal.ai
balance**.
