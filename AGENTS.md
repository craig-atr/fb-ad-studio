# AGENTS.md

## Agent bootstrap

Before running any stage, read these in order:

1. `identity.md` — what this project is and its non-negotiables
2. `rules.md` — standing rules for every stage
3. `brand/<brand>.md` — the brand profile for this campaign (default
   `brand/atomic-tattoo-removal.md`)
4. `reference/facebook-ad-specs.md` — sizes, safe zones, copy limits
5. The applicable stage file under `reference/stages/`

`reference/methodology.md` is the distilled ad-building method; read it once so
the creative choices in every stage make sense.

## Stage routing

| Request | Start at |
| --- | --- |
| A full ad from scratch | `reference/stages/001-generate-ideas.md` |
| "I already have the angle, write the script" | `002-promote-idea-to-script.md` |
| "Turn this script into a storyboard" | `003-script-to-storyboard.md` |
| "Generate the images for the storyboard" | `004-storyboard-to-images.md` |
| "Turn the images into clips" | `005-images-to-video-clips.md` |
| "Give me the editor handoff" | `006-assemble-shot-list.md` |

For a complete ad request, start at `001` and continue through the pipeline in
`reference/workflow.md`. Do not treat each stage as an unrelated standalone task
unless the user explicitly asks for only that operation.

## Review gates

Stop and get explicit user approval at each gate defined in
`reference/workflow.md`. Never promote an artifact to the next stage without it.
Generation stages (`004`, `005`) cost money per call — never batch-generate a
whole storyboard without the storyboard being approved first.

## Local tooling

Generation stages call fal.ai through Python tools under `tools/`. They run under
`uv` (no system Python install required):

```bash
uv run tools/generate_image.py --help
uv run tools/generate_video.py --help
uv run tools/build_shot_list.py --help
```

Setup, API key, and models are in `reference/fal-generation.md`. Frame/preview
work (stage 006 optional rough-cut) needs `ffmpeg`; check with `ffmpeg -version`
and ask before installing.

If no generation path is available (no fal key), stop at the generation stage and
explain the missing capability rather than faking assets.

## Documentation changes

When you change the workflow contract, update every affected document so paths,
handoffs, review gates, and templates stay consistent.
