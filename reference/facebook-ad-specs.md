# Facebook / Instagram Ad Specs

Canonical sizes and limits every stage must honor. Default target for this
project is **9:16 vertical (Reels / Stories)**.

## Aspect ratios and pixel sizes

| Placement | Aspect | Pixel size | Use |
| --- | --- | --- | --- |
| **Reels / Stories (default)** | **9:16** | **1080 × 1920** | Full-screen mobile video. Primary target. |
| Feed video (square) | 1:1 | 1080 × 1080 | Feed fallback. Optional. |
| Feed video (vertical) | 4:5 | 1080 × 1350 | Highest feed real estate. Optional. |

This project generates **9:16 / 1080 × 1920** unless the user asks for another
placement. When generating with fal:

- Image tool: pass `--aspect-ratio 9:16` and `--resolution 2K` (nano-banana).
- Video tool (Kling): aspect ratio is inherited from the input image, so a
  1080 × 1920 still yields a 9:16 clip. Feed a correctly-sized image and the
  clip is correctly sized.

## Video encoding

| Field | Value |
| --- | --- |
| Container | MP4 or MOV |
| Video codec | H.264, high profile, progressive scan |
| Audio codec | AAC, 128 kbps+ |
| Frame rate | 30 fps (accepts up to 60) |
| Resolution | 1080 × 1920 (9:16) |
| Max file size | 4 GB |
| Ad length target | **15–20 s** (this method). Reels allow up to 90 s. |
| Per-clip AI length | 5 s (Kling default) |

The AI clips come out of Kling as MP4/H.264 already; the human editor exports the
final at the settings above.

## Safe zones (9:16) — design for muted, UI-occluded viewing

Meta overlays its own UI on Reels/Stories. Keep **text and critical elements**
inside the safe area:

```text
Canvas: 1080 × 1920

  ├─ Top 250 px .............. avoid (profile / sound icons)
  ├─ Middle ~1080 × 1420 ..... SAFE — put key text and subject here
  └─ Bottom 420 px (Stories) . avoid
     Bottom ~700 px (Reels) .. caption + CTA + profile row live here
```

Practical rule: **center important text vertically**, keep it within roughly the
middle 60% of the frame, and never place a headline in the bottom third. The
subject can fill the frame edge-to-edge; only text/logos need the safe band.

## Copy limits

| Element | Limit before truncation |
| --- | --- |
| Primary text | ~125 characters |
| Headline | ~40 characters |
| Description | ~30 characters |
| CTA button | Fixed choices — use **Book Now** |

Write copy to survive truncation: front-load the hook and offer.

## Text-on-screen (in the video itself)

- Assume **muted playback** — the on-screen text must carry the message.
- Keep text **big and high-contrast**; 2–6 words per beat.
- Change something on screen **every 2–3 seconds** (cut or motion).
- Keep burned-in text inside the safe zone above.

## Validation checklist (run before any handoff)

1. Aspect ratio is exactly 9:16 (or the requested placement).
2. Pixel dimensions are exactly 1080 × 1920 (or the requested size).
3. No critical text in the top 250 px or bottom third.
4. Video is H.264 MP4, ~30 fps.
5. Total assembled length lands 15–20 s.
