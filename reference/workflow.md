# Workflow Contract

## Pipeline

```text
001 generate ideas
    -> USER GATE: pick one idea (or request more)
002 promote idea to script (ad copy + beat sheet)
    -> USER GATE: approve the script
003 script to storyboard (scene-by-scene, source-tagged)
    -> USER GATE: approve the storyboard
004 storyboard to images (fal image, AI scenes only)
    -> USER GATE: approve each image (reroll rejects)
005 images to video clips (fal Kling i2v)
    -> USER GATE: approve each clip (reroll rejects)
006 assemble shot list (editor handoff + real-footage capture plan)
    -> deliver to output/<campaign>/
```

## Review gates (five hard stops)

1. **Offer confirmation** at the start of `001`. The offer is a required per-ad
   input; if the user didn't supply it, ask before generating concepts.
2. **Idea selection** after `001`. The user picks the angle to build.
3. **Script approval** after `002`. Copy + beat sheet locked before storyboarding.
4. **Storyboard approval** after `003`. Scene list, timings, and source tags
   locked before spending any generation budget.
5. **Asset approval** during `004` and `005`. Each image and each clip is
   reviewed; rejects are rerolled in place, not versioned into new folders.

Never spend fal generation budget (stages 004/005) before gate 4.

## Working files

```text
work/<campaign>/
├── 01-ideas/ideas.md
├── 02-script/script.md
├── 03-storyboard/storyboard.md
├── 04-images/
│   ├── prompts/scene-<NN>.md
│   └── scene-<NN>.png
├── 05-clips/
│   ├── prompts/scene-<NN>.md
│   └── scene-<NN>.mp4
└── 06-shot-list/shot-list.md
```

`<campaign>` is a filesystem-safe name like `atomic-mothers-day`.
`<NN>` is the zero-padded scene number from the storyboard.

## Deliverables

```text
output/<campaign>/
├── clips/scene-<NN>.mp4        approved AI clips, 1080×1920
├── stills/scene-<NN>.png       approved stills (for AI_IMAGE holds)
├── shot-list.md                editor handoff: order, timings, overlays,
│                               and real-footage capture instructions
└── copy.md                     final ad copy (headline, primary text, CTA)
```

The human editor assembles `output/<campaign>/` plus their real footage into the
final 9:16 MP4 and burns in the text overlays.

## Changing an approved artifact

Edit in place and re-run downstream only for what changed. If the storyboard
changes after images exist, regenerate only the affected scenes.
