# Standing Rules

These apply to every stage. Stage files add specifics.

## Process

1. **Honor the review gates.** See `reference/workflow.md`. Stop and ask for
   explicit approval before promoting an artifact or spending generation budget.
2. **One campaign, one folder.** All working files live under
   `work/<campaign>/` in the numbered subfolder for the stage. Do not scatter
   files.
3. **Replace, don't fork.** When the user requests changes, edit the artifact in
   place and regenerate. Do not create `-v2`, `-final`, `-final2` folders.
4. **Infer from the brand profile and prior artifacts first.** Ask the user only
   for what genuinely cannot be inferred. Convert vague requests into concrete
   choices and show them, rather than interrogating.
5. **The offer is a required per-ad input.** When starting a new campaign, the
   user supplies the offer. If they don't, **ask what the offer is before
   generating concepts** — do not silently default to the brand profile. See
   `reference/stages/001-generate-ideas.md` step 2.

## Creative

6. **Follow the methodology.** `reference/methodology.md` is authoritative for
   hook timing, muted-first text, fast cuts, authentic-over-polished, and the
   AI-supports / real-footage-sells split.
7. **Match the brand voice.** Playful and clever, never insulting or
   cheap-discount. Pull voice and offer from the brand profile.
8. **Always CTA "Book Now."** Not "Learn More," unless the brand profile says
   otherwise.

## Sizing (never skip)

9. **Every asset matches the placement spec.** Default 9:16, 1080×1920. Generate
   at the exact aspect ratio; validate dimensions before handing off. See
   `reference/facebook-ad-specs.md`.
10. **Respect safe zones.** Keep text and key elements out of the top and bottom
   UI-occluded bands defined in the specs file. Design for muted viewing.

## Text overlays

11. **Prefer clean plates; add text in the editor.** Image and video models
    render text unreliably. Default: generate scenes *without* burned-in ad copy
    and record the intended overlay in the storyboard for the human editor. Only
    bake text into a generation prompt when the user explicitly asks, and treat
    any baked text as disposable/approximate.

## Compliance

12. **No fabricated medical claims or fake results.** Real before/after and real
    treatment footage only. AI scenes are hooks, lifestyle, and brand — never
    fake clinical proof. Avoid guarantees of outcome.

## Honesty

13. **Report what actually happened.** If a generation failed, a size is wrong,
    or a scene needs a reroll, say so plainly with the evidence.
