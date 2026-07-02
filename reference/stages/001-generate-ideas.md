# Stage 001 — Generate Ideas

## Objective

Turn a loose request ("a Mother's Day ad for Atomic") into a small set of
distinct, ready-to-build **ad concepts**, each anchored on an offer and an angle.
The user picks one to promote to a script.

Read `identity.md`, `rules.md`, the brand profile, and
`reference/methodology.md` first.

## 1. Establish the brief

Determine (infer from the brand profile and request; ask only what you can't):

- `CAMPAIGN`: filesystem-safe name, e.g. `atomic-mothers-day`
- `OCCASION / THEME`: e.g. Mother's Day, evergreen, summer
- `OFFER`: **required user input** — the specific promotion this ad runs. See
  step 2. Do not proceed without it.
- `OBJECTIVE`: default Leads / consultation bookings (from brand profile)
- `AUDIENCE`: default from brand profile; note any tightening (e.g. women first)
- `CONSTRAINTS`: anything the user requires (a specific line or footage)

Create `work/<campaign>/01-ideas/`.

## 2. Confirm the offer (required input)

The offer is the single most important input — **the offer beats the ad** — so it
is a required, user-supplied input for every campaign, not something to infer
silently.

- If the user **supplied an offer** (e.g. "Free consult + $50 off first package",
  "Buy $300 gift card, get $50", "20% off removal packages"), use it verbatim as
  `OFFER`.
- If the user **did not supply an offer, stop and ask what the offer is** before
  generating any concepts. Do not silently fall back to the brand-profile
  default. When you ask, present the brand-profile default offer and the framing
  menu below as quick suggestions the user can accept or override.

Framing menu (frame as **Gift + Confidence + Fresh Start**, not "discount"):

1. Free consultation + small bonus (default for a newer studio, low friction)
2. Gift-card promo (cash flow, feels like a gift)
3. Limited package offer (bigger jobs; pair with premium language)

Record the confirmed `OFFER` in the brief at the top of `ideas.md`. Every concept
in step 3 uses this offer (concepts differ on hook/angle, not on offer, per the
"test hooks, not ads" methodology) unless a concept deliberately proposes an
offer variant.

## 3. Generate 3–5 distinct concepts

Each concept is one idea card (use `reference/templates/idea.md`). Make them
**genuinely different angles**, not reworded twins. For each:

- **Hook line** — the arresting first-3-seconds line. Muted-friendly, ≤ ~6 words
  ideally. Clever, never insulting (respect brand voice).
- **Angle** — the emotional mechanism (humor / relatability / regret-relief /
  aspiration / social proof).
- **Offer** — which framing from step 2.
- **Audience note** — who this angle hits hardest.
- **Why it works** — one honest sentence.
- **Proof plan** — what real footage carries the trust (laser in action,
  before/after) so we know the real-footage slots early.

Include at least one playful/relatable angle and one straightforward
aspirational angle so the user has range.

## 4. Recommend and present

Write all cards to `work/<campaign>/01-ideas/ideas.md`. Give a short honest
recommendation of the strongest 1–2 for this brand and why.

## Review gate

Present the cards and ask the user to **pick one** (or request more / a remix).
Do not proceed to stage 002 until the user selects a concept.

Record the chosen concept clearly at the top of `ideas.md` before moving on.
