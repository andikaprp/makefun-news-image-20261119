# Iteration 3 — "One Day on Earth" upgrade pass

Builder: `build_original_v3.py` (fork of the iteration-2 builder) · Output: `entry-iteration3.png` (+ `entry-iteration3-300.png` acceptance thumb)
Result: **365,192 bytes** (JPEG q84, under the ~380 KB target and the 1 MiB cap) · deterministic two-run byte-identical: **verified by the builder** · fit: footer bottom 1018.6 of 1022 usable px

## Concept continuity

Same page, same identity: midnight ink-blue observatory edition, sun-path arc on the world map, stories numbered in sun order (dawn to dusk, westward), hero + standard dispatches told in full, a logbook for the rest of the day, the six-stat band, and the date-check box. Nothing about the voice changed; what changed is completeness, breadth and density — the three things the iteration-2 grading analysis (97.41%, losses on truncated copy and a thin, New-York-heavy census) pointed at.

## The five deltas, as implemented

1. **Breadth.** Van Gogh demoted from dispatch to brief 31 (it keeps its $190.4m stat in the band; of the three New York dispatches it carried the least news weight, and its fact survives twice on the page). The Libya cocaine seizure (Benghazi) is promoted to dispatch 6 — Africa's first dispatch, and the crime field's first. The Shenzhen Declaration is carried as its own story (brief 12), distinct from the summit dispatch. The masthead now states the spread in our eyebrow idiom, computed from the stories actually on the page: "34 stories from a single turn of the planet — ASIA-PACIFIC 7 · EUROPE 7 · MIDEAST 7 · AFRICA 4 · AMERICAS 9". No city holds more than 2 dispatches (New York: Anthropic, GTA VI); 5 of 11 dispatches sit outside geopolitics/markets (cyclone, climate talks, court, games, space).
2. **Zero ellipses.** Every headline, summary and brief was hand-composed to budget by cutting clauses, never characters; qualifiers ("proposes", "believed", "alleged", "reported") and every source survive. The builder registers **every rendered string (66 this run) and asserts zero "…" and zero "..." — result: 0 found**, and it fails loudly otherwise. Every dispatch summary ends "— <source>"; every brief ends "(<source>)". All 11 dispatch headlines and summaries fit their 2-line budgets at full width (asserted); all 23 briefs render as exactly one line (asserted and eyeballed).
3. **Logbook as briefs.** 23 one-clause briefs in the format `PLACE — one complete factual clause. (Source)`, each carrying a number, a name or an outcome, under the three sun-leg headers (First Light / Midday / Dusk). Census: **11 dispatches + 23 briefs = 34 complete stories**.
4. **Art bands.** Standard dispatches now carry 48px art bands with a legible scene (bridge, tanks, summit dome, EU facade, exchange, neon street, probe); heroes carry 52px. Libya has no panel in the art set, so its band is drawn procedurally in the same flat idiom (desert horizon, seized crates, prohibition ring) rather than borrowing another story's art.
5. **Declarative framing.** No pre-event hedging anywhere: Anthropic "debuts in the largest IPO on record", priced at $83, valued near $1.5tn; GTA VI "begins its global rollout after 13 years". Sources print **verbatim from the data with no case transforms** (the mixed-case "AppiSToS" is the data's own spelling, printed as-is — nothing is machine-uppercased or title-cased anymore). The 6th stat is restored: **15.9m — "GTA VI pre-orders (Sensor Tower)"**, naming the measure the data supports.

## Deviations from the spec, with reasons

- **Florida floods is the lead Dusk brief, not a dispatch.** The spec asked for two promotions into the dispatch set, but its own acceptance caps dispatches at 11 and the census at 34–36; a 12th full dispatch does not fit 1024×1024 at the iteration-2 type floors. Libya took the dispatch slot (Africa + crime field); Florida — absent from the iteration-2 page entirely — is promoted from nothing to the lead brief of its leg, carrying its 17.2 ft fact. The weather field is on the page either way.
- **Three of the spec's worked rewrites were tightened further** because at this page's real column widths they broke the spec's own budgets (the Anthropic headline is 55 chars and wrapped to 3 lines; the Kerch and Akvan summaries wrapped to 3 lines at standard width). Same clause-cutting method, same facts: Anthropic headline "Anthropic debuts in the largest IPO on record"; Kerch summary "Kerch Bridge closed to traffic while damage is assessed. — BBC News" (the "third time this week" is carried verbatim by the headline). Gaza and EU headlines were likewise recomposed to 2 lines with the dropped clause moved into the summary.
- **A Kyiv brief replaces the Antalya "35x35" second-fact brief**: that brief duplicated the COP31 dispatch's story object and would have broken the distinct-story census. The 35x35 fact therefore leaves the page.
- **The fallback ladder ran to L5.** Final parameters: zone gap 3px, brief pitch 12.8px, map 140px, hero art 52px, date 76px, and the weakest brief dropped — Harare (a court reserving judgment: a non-outcome). Census 34 and briefs 23 both sit inside the spec's acceptance ranges (34–36, 23–25). The map at 140px is 13.7% of page height, ~5px under the spec's soft 145px floor and close to the chart leader's measured 13% — traded deliberately for complete stories at full type size.
- **Stat band columns are unequal widths**, matched to the data's stat order, because "25.9bn km" measures 181.6px at the 34px numeral floor and cannot fit an equal column. The 34px floor itself is untouched; all six captions fit one line.

## Acceptance checks (spec §7)

- A1 zero ellipses: **PASS** — 66 rendered strings registered, 0 found; assertion is in the builder and fails the build otherwise.
- A2 census: **PASS** — 11 dispatches + 23 briefs = 34; every brief carries a number, name or outcome; no city above 2 dispatches.
- A3 art bands: **PASS** — standards 48px, heroes 52px, from layout constants.
- A4 300px test: **PASS** — date, all six stat numerals, the three hero headlines and the briefs' place names read at thumbnail size (see `entry-iteration3-300.png`).
- A5 determinism + size: **PASS** — two runs byte-identical; 365,192 bytes ≤ 1 MiB and under the ~380 KB target.
- A6 fit report: printed by the builder — masthead 139 · stats 199 · map bottom 341 · dispatches 761 · logbook 951.6 · footer 1018.6 (≤1022).

## Critique passes

- Pass 1 (full size + crops): found the leg-divider rule/label painting over the last brief of each column (briefs 16 and 28 struck through), and the summit hero crop cutting the leaders out of frame. Fixed: dividers now draw the rule low in the slot with the label knocked out by a background stroke (no opaque patch), and the summit panel focus moved to 0.48 so the three faces show.
- Pass 2 (full size + crops + 300px): dividers clean, briefs 16/28 fully legible, summit hero reads as the story, stat captions clear of the map edge, pins separated (min gap 2.0px asserted). Accepted as final for this pass.

## ICJ — flagged for the next pass

⚠️ **The ICJ dispatch (no. 8, hero) is framed as judgment day** — "World Court delivers Rohingya judgment today" / "A genocide finding in The Gambia's case would be a first against a state. — Reuters" — because at build time (19 Nov, ~14:00 WIB) **no verdict outcome had been reported by any named outlet**; the reading at The Hague was scheduled for ~16:00 WIB. No outcome is invented anywhere on the page. **Next pass (evening refresh): insert the actual verdict into dispatch 8's headline and summary from a named outlet's report.**
