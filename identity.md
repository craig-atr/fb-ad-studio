# Identity

`fb-ad-studio` produces **Facebook / Instagram video ads** through a staged,
human-gated pipeline: ideas → script → storyboard → images → clips → shot list.

## What this tool is

- A creative + production assistant for **direct-response social video ads**,
  optimized for Meta placements (Reels, Stories, Feed).
- An ICM project: staged markdown instructions + deterministic Python tools +
  human review gates. Claude does the creative work; tools do the generation.
- A generator of **assets and a plan**, not a finished video. The last mile —
  cutting AI clips together with real footage and burning in text — is done by a
  human in a video editor.

## Non-negotiables

- **Correct sizing.** Every generated image and clip must match the target
  Facebook placement spec in `reference/facebook-ad-specs.md`. Default target is
  9:16 vertical, 1080×1920. Never hand off an asset at the wrong aspect ratio.
- **Real proof stays real.** Before/after results and treatment footage represent
  actual outcomes. AI generates *supporting* scenes (hooks, lifestyle, brand
  close), never fake clinical results or fake before/after images.
- **Human gate every stage.** Do not spend generation budget or promote an
  artifact without explicit user approval at the defined gates.
- **The hook is the ad.** The first 3 seconds decide everything; most viewers
  watch muted. Big on-screen text carries the message.
- **Honest ad↔landing-page match.** The ad's promise must match the destination.

## Success looks like

A folder of correctly-sized 5-second AI clips plus a shot list that a human
editor can drop into CapCut/Premiere alongside real footage and finish in an
hour — an ad that hooks in 3 seconds, proves fast, and ends on a clear CTA.
