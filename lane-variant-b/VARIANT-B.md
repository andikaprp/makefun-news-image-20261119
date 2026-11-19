# Variant B — "One Day on Earth", maximum-dispatches bet

Built by `build_variant_b.py` in this lane. Entry: `entry-variant-b.png`
(1024×1024 JPEG, 359,810 bytes at quality 86, sha256
`981d224d272fa4bed9f1b03efed472ffc616a49421d7d4b47cffe931e808759f`).
Acceptance thumb: `entry-variant-b-300.png`.

## The bet

Iteration 3 (in `lane-original/`) allocates the page as ~11 complete
dispatches + 23–25 one-clause briefs (census ~35). Variant B bets the
opposite way inside the same identity (midnight palette, sun-path arc,
sun-order numbering): **the featured layer is everything**. All 14 panels in
`lane-art-v4` — including the round-2 spares — become full dispatches, each
with a headline plus a closed summary sentence carrying the day's fact and
its source. The logbook shrinks to whatever briefs still fit, and the Day in
Numbers band moves to the foot of the page to fund the featured layer.

## What is on the page (census 20)

- **14 dispatches, all complete, zero headline-only featured stories:**
  3 heroes (Shenzhen summit, Akvan, ICJ — the last a round-2 spare panel,
  promoted to hero), 8 standard cards (48px art bands, place chip on the
  art), 3 wide cards in the last row (Anthropic, GTA VI, Voyager — art at
  118×96, near native aspect, the most legible pictures on the page).
  The Fed round-2 spare panel carries the Paraguay central-bank dispatch.
- **6 logbook briefs** (2 per sun-order leg), each one complete factual
  clause with source: Xi/Shenzhen Declaration, Tokyo 2+2, Berlin allies,
  Gaza aid call, Florida floods, Caracas oil revenue.
- Date at 80px (largest type), per-region counts in the masthead
  (ASIA 4 · EUROPE 5 · MIDEAST 2 · AFRICA 1 · S. AMERICA 3 · N. AMERICA 5 —
  computed from the stories actually on the page), all 6 verified stats,
  date-check box, claim line. Contested items framed as proposals/attributed
  claims (EU loan "proposes", Voyager anchored to the JPL briefing).
- Map band 136px (13.3% of page height), dispatch pins only + brief dots.

**Dropped by the logbook solver (10 verified briefs that did not fit):**
Jakarta EU pact, Manila $2bn loan, Darwin lease, Khasab tanker, Benghazi
seizure, Kyiv drones, Mogadishu drought aid, Jeffries vote, Guayaquil
fishermen, AI cyber senators. A further set of data-file stories was never
selected at all.

## Checks (all asserted in the builder, not eyeballed)

- Deterministic: `build()` runs twice in-process; JPEG bytes asserted
  identical before anything is written.
- Zero ellipses: the builder never trims copy — every headline/summary was
  hand-composed to its wrap budget by clause-cutting, an assertion fails
  the build if any wrap exceeds 2 lines, and a separate assertion scans
  all composed copy for "…" / "...". Final count on the page: **0**.
- Type floors: date 80px, hero headlines 24px, standard headlines 20px,
  summaries 14px, briefs 13px, stat numerals 34px, stat captions 12px
  (each verified to fit on one line), date-check 13px.
- Size: 359,810 bytes ≤ ~380 KB target (1 MiB hard cap), first bytes `ffd8`.
- 300px test saved and eyeballed: date, all six stat numerals and the
  hero headlines are readable; standard headlines mostly readable;
  briefs become texture (expected — see weaknesses).
- Three critique passes were run (overflow collapse → overlap fixes →
  final), each from a fresh full-size render.

## The geometry finding (why census is 20, not ~30)

At the mandated type floors this is arithmetic, not taste. Fourteen
complete dispatches (art ≥48px + place + 2-line headline + 2-line summary)
plus date, map, stats and footer consume ~950 of the 1024 vertical pixels.
Each additional 2-line brief costs ~36px of column height, so a ~30-story
census would need ~190px of logbook that does not exist next to 14
dispatches. Iteration 3's ~35 census is bought precisely by having only 11
dispatches. The two variants sit on the same frontier; the A/B tests which
side of it the judge pays for.

## Honest weaknesses vs the iteration-3 approach

- **Breadth (judge criterion 2) is deliberately conceded.** Census 20 vs
  ~35; 16 verified stories never appear. If the judge's breadth margin is
  decided before completeness is even compared, B loses on that criterion.
- **NYC ×3 in the featured layer** (Van Gogh, Anthropic, GTA) — the field
  analysis flagged this and iteration 3 demotes one; B keeps all three
  because each is top-tier news with its own panel, but the featured
  layer's geographic spread is narrower than the census implies.
- **The Paraguay/Ueno dispatch is the weakest story on the page** (a
  `cut_candidate` in the data). It is complete and sourced, but it is in
  the featured layer only to use the spare Fed panel.
- **Hero art is a 36px strip** — thinner than the standards' 48px. Heroes
  win on width and 24px type, not on picture size.
- **Stats sit at the foot**, against the field pattern of an early Day in
  Numbers band. They still read at 300px, but later in the scan path.
- **Map at 13.3%** vs iteration 3's ~16% — a small, deliberate deviation
  to fund two extra briefs per leg.
- Brief layer (6) turns to texture at 300px; iteration 3's ~24 briefs
  remain a second readable layer for longer.

## What B does better than iteration 3

- 14 of 14 featured stories are told in full (headline + fact + source);
  iteration 3 tells 11 in full.
- Every panel is used, including all three round-2 spares; the wide row's
  near-native-aspect art is the clearest picture treatment on either page.
- No featured story anywhere is a headline alone, and no summary on the
  page is truncated — the v2 wound (11/11 headlines ending in "…") is
  structurally impossible here because the builder fails instead of
  trimming.
