# Methodology

The ad-building method this project automates, distilled from the Van Clief
Facebook video-ad process (the worked Atomic Tattoo Removal example) and the
Interpretable Context Methodology (ICM) it is structured with.

## Core beliefs

- **The offer beats the ad.** Get the offer/angle right first (stage 001). For
  local service ads, frame as **Gift + Confidence + Fresh Start**, not "discount."
- **The hook is the ad.** The first 3 seconds decide whether anyone watches. Lead
  with the most arresting, emotionally relatable line.
- **Muted-first.** Most people watch with sound off. Big on-screen text carries
  the message; audio is a bonus, not the plan.
- **Authentic beats polished.** Real treatment room, real client examples, real
  sounds outperform overproduced stock-style content. "Authentic professional"
  wins.
- **Real footage sells; AI supports.** The winning combo is
  **AI hook + real proof + real results + strong CTA.** AI generates hooks,
  emotional beats, lifestyle, and brand frames. The money shot (the laser in
  action, real before/after) is real footage.
- **Fast cuts.** Movement or a cut every 2–3 seconds. No slow scenes.
- **Test hooks, not ads.** Ship 3 versions with the same offer and different
  hooks; the platform surprises you with the winner.

## Length and shape (15–20 s vertical)

Target ~18 seconds, 9:16. Three acts:

```text
0:00–0:03  HOOK      Most important. Arresting line + fast visual movement.
0:03–0:12  PROOF     Real treatment in action, before/after, close-ups.
0:12–0:20  OFFER+CTA Offer text overlay, then brand close. CTA: Book Now.
```

A scene-by-scene example (the Atomic Mother's Day ad) lives in the storyboard
stage. Typical scene breakdown for an 18–20 s ad is 5–6 scenes of 2–5 s each.

## The offer framing menu (stage 001)

Strong local-service offers, best to weakest for a newer studio:

1. **Free consultation + small bonus** (e.g. "Free Consultation + $50 Off First
   Package") — low friction, good for colder traffic and lead gen.
2. **Gift-card promo** (e.g. "Buy $300, Get $50 Bonus") — feels like a gift,
   improves upfront cash flow.
3. **Limited package offer** (e.g. "Up to 20% Off Removal Packages") — best for
   bigger jobs; risks cheapening perceived value, so pair with premium language.

Add urgency ("limited availability") without heavy discount language, which
weakens perceived value.

## Copy structure (stage 002)

- **Headline** — the hook line (~40 chars).
- **Subheadline** — the offer framing.
- **Primary text** — a short punchy version (often wins) and a longer version.
- **Description** — the urgency line.
- **CTA** — always **Book Now**.

Ad copy and the landing page must repeat the **same** hook line. Consistency
lifts conversion; a disconnect kills it.

## Scene source types (stage 003+)

Every storyboard scene is tagged:

- `AI_CLIP` — generated still → animated to a 5 s clip (fal image → Kling).
- `AI_IMAGE` — generated still used as a static hold (no motion needed).
- `REAL_FOOTAGE` — captured by the human (laser in action, real before/after,
  real clinic). The shot list gives capture instructions.

Do not fake `REAL_FOOTAGE` with AI. That footage is the trust builder.

## ICM structure (why this is a folder, not an app)

Each stage is a markdown instruction file; intermediate artifacts are plain
markdown/JSON; humans review between stages; generation is delegated to small
deterministic tools. This keeps every step inspectable and editable, and lets a
human intervene at any gate.
