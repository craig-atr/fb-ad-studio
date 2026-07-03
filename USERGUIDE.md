# fb-ad-studio — User Guide

A step-by-step guide to making Facebook / Instagram video ads with this project —
written for someone who has **never heard of "ICM"** and just wants to get an ad
made and make the workflow their own.

---

## 1. What this actually is

`fb-ad-studio` is an **assistant you talk to** that turns an idea into a finished
set of ad assets. You chat with **Claude Code** inside this folder and it walks a
fixed pipeline with you:

```
idea  →  script  →  storyboard  →  images  →  video clips  →  editor handoff
```

At each step it stops and asks for your approval before spending money or moving
on. The images and video are generated through **your fal.ai account**. The final
result is a folder of clips, stills, a shot list, and offer images that you (or an
editor) assemble into the finished ad.

You don't build a finished video here — you build **all the pieces plus a plan**,
then cut them together (or hand them to an editor). That's on purpose: the hard,
taste-driven last mile stays with a human.

---

## 2. "ICM" in plain English (you can skip the theory)

This project is built with the **Interpretable Context Methodology (ICM)**. Here's
all you need to know:

- Instead of an app with buttons, the "program" is a **folder of plain-English
  instruction files** (`reference/stages/001…006`), a few **small scripts**
  (`tools/`), and **human review gates**.
- You run it by **chatting with Claude Code** in this folder. Claude reads the
  instruction file for the current step, does the creative work, calls a tool when
  it needs to generate an image or video, and **stops to ask for your OK**.
- **Everything is a readable text file you can open and edit.** Nothing is hidden
  in code you can't see. If you want the ads to behave differently, you edit the
  instructions — in English.

That's the whole idea: **inspectable, editable, human-in-the-loop.** You do not
need to understand ICM beyond this to use (or change) the workflow.

---

## 3. Why fal.ai?

The workflow needs to generate images and video. [fal.ai](https://fal.ai) is the
backend it uses, for a few practical reasons:

- **One key, many models.** A single account gives you top image models
  (nano-banana) *and* the leading video models (Veo, Kling, Seedance, Hailuo). You
  can pick the best model **per shot** — cheap for volume, premium for hero shots,
  text-stable for tricky lettering.
- **Pay-per-use, no subscription.** You're billed per generation, and the built-in
  `tools/fal_cost.py` reports **how much each ad cost** and your remaining balance.
- **No GPU / no installs.** The models run on fal's servers; the tools just make
  HTTP calls.
- **You're not locked in.** The tools are thin, **model-agnostic** wrappers — you
  pass `--model`, so switching models (or, with small edits, providers) is easy.

If you'd rather use a different provider, the tools in `tools/` are short and only
use the Python standard library, so they're straightforward to point elsewhere —
but fal gives you the widest model menu with the least setup.

---

## 4. One-time setup

1. **Claude Code** — this workflow runs by chatting with it inside this folder.
2. **A fal.ai account + API key** ([fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)).
   Put the key in a file named **`.fal_key`** at the repo root (nothing else in
   the file). For cost/balance reporting, also create a **billing-scoped admin
   key** and save it to **`.fal_admin_key`**. Both files are gitignored.
3. **Python** — the tools run under [`uv`](https://docs.astral.sh/uv/) (no manual
   installs) or any system `python3`. They use only the standard library.
4. **ffmpeg** — needed for the rough cut, text overlays, and offer images. On
   Windows: `scoop install ffmpeg`.

Full details live in [`reference/fal-generation.md`](reference/fal-generation.md).

---

## 5. Make your first ad — step by step

**You don't run commands. You talk to Claude.** Start by telling it what you want,
**including the offer**:

> "Make a summer ad for Atomic Tattoo Removal — the offer is a free consultation
> plus $50 off the first package."

Claude then walks the pipeline, pausing at each **gate** (⏸ = it waits for you):

| # | Stage | What happens | ⏸ Your gate |
| --- | --- | --- | --- |
| 1 | **Ideas** | 3–5 distinct concepts | Pick one |
| 2 | **Script** | Ad copy + timed beat sheet | Approve copy/beats |
| 3 | **Storyboard** | Scene-by-scene plan | Approve — **nothing is generated before this** |
| 4 | **Images** | A still per AI scene (costs money) | Approve each / reroll |
| 5 | **Clips** | Animate approved stills | Approve each / reroll |
| 6 | **Handoff** | Shot list, offer images, optional rough cut | — |

Everything for a campaign lands in **`output/<campaign>/`**: `clips/`, `stills/`,
`offer-images/`, `shot-list.md`, `copy.md`, and a `rough-cut.mp4` preview. Then you
film any real footage, edit, and publish.

> **Tip:** if you forget to give an offer, Claude will ask — the offer is the
> single most important input, so it's never assumed.

---

## 6. Make it your own

### The #1 thing to change: your brand
The whole workflow reads a **brand profile**. To use it for *your* business:

1. Copy `brand/atomic-tattoo-removal.md` → **`brand/<your-brand>.md`**.
2. Fill in: business, default offer, audience, **voice**, CTA, aspect ratios, and
   asset paths.
3. Drop your **logo** at `brand/assets/logo.png` and reference photos in
   `brand/assets/reference/`.
4. Tell Claude: *"Use the `<your-brand>` profile."*

### The offer
The offer is a **per-ad input** — you type it when you start an ad (see step 5).
The brand profile holds a *default* Claude can suggest.

### Which AI model is used
Defaults: images = `nano-banana-pro`, video = `Veo 3.1`. You (or Claude) can
override **per shot** — see the model menu in
[`reference/fal-generation.md`](reference/fal-generation.md). The workflow is
built to **recommend the right model for each shot** (e.g. a text-stable model
when lettering must stay crisp).

### Ad sizes / placements
Default is 9:16 (1080×1920). To target other Meta placements (1:1 square, 4:5),
just ask — or edit [`reference/facebook-ad-specs.md`](reference/facebook-ad-specs.md).

### How the workflow itself behaves
The stage instructions are in `reference/stages/*.md` and the artifact templates
in `reference/templates/`. **Edit these in plain English** to change how Claude
works. Standing behavior lives in `rules.md` and `identity.md`.

---

## 7. Files you'll actually edit — cheat sheet

| To change… | Edit… |
| --- | --- |
| Your business identity, voice, default offer | `brand/<your-brand>.md` |
| Logo / reference photos | `brand/assets/` |
| The offer for a specific ad | (just type it when you start the ad) |
| Which AI model a shot uses | `--model` flag / model menu in `reference/fal-generation.md` |
| Ad sizes & safe zones | `reference/facebook-ad-specs.md` |
| How a pipeline step behaves | `reference/stages/001…006-*.md` |
| Standing rules / non-negotiables | `rules.md`, `identity.md` |
| The rough-cut timeline for a campaign | `work/<campaign>/roughcut-beats.txt` |
| Offer-image / overlay text | top of `tools/build_offer_image.sh` / `build_overlays.sh` |

You never need to touch the Python in `tools/` for normal use.

---

## 8. The tools (what each script is for)

Run under `uv run tools/<script> …` (Claude calls these for you):

| Tool | Purpose |
| --- | --- |
| `generate_image.py` | Make a still via fal (nano-banana etc.) |
| `generate_video.py` | Animate a still via fal (Veo / Kling / Seedance / Hailuo) — model-agnostic |
| `build_shot_list.py` | Copy approved assets to `output/` and validate sizes |
| `build_roughcut.sh` | Stitch clips + slates into a `rough-cut.mp4` preview |
| `build_overlays.sh` | Transparent text-overlay clips (PNG + ProRes) |
| `build_offer_image.sh` | Static offer images (square / 4:5 / 9:16) |
| `fal_cost.py` | Show fal.ai balance and per-ad spend |

---

## 9. Costs (rough guide)

Pay-per-use, tracked by `fal_cost.py`. Ballpark: a still ~$0.15, a Veo clip
~$1.25 / 4s, Seedance ~$0.45 / 5s, Kling ~$0.40 / 5s. A full ad typically runs
**~$3–13** depending on how many clips and which video model you use.

---

## 10. Good-to-know gotchas

- **A model rejects your prompt/image (content filter)?** Switch models — that's
  why the video tool is model-agnostic. (Veo's filter is strict on photoreal
  medical/treatment shots; Seedance/Kling are more permissive.)
- **Video warps small text** (a tattoo, a sign)? Use a **start/end-frame** model
  (Seedance) so the lettering can't wander.
- **Seedance defaults to 16:9** — always pass `--aspect-ratio 9:16` for vertical.
- **Real footage comes last** — the pipeline reserves a slot and never blocks on it.
- **Keep unrelated fal work out of the window** while an ad is in progress, so the
  per-ad cost figure stays accurate.

---

*New to the pipeline internals? Start with [`AGENTS.md`](AGENTS.md) (agent entry
point), then [`reference/workflow.md`](reference/workflow.md) and
[`reference/methodology.md`](reference/methodology.md).*
