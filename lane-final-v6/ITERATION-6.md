# Iteration 6 — breadth push + evening facts ("One Day on Earth")

Builder: `build_final_v6.py` (fork of iteration 5's `build_final_v5.py`) · Output: `entry-iteration6.png` (sha256 `8c609949…`, **373,938 bytes**, JPEG q84, 1024×1024) + `entry-iteration6-300.png`
Result: census **39 (11 dispatches + 28 briefs)**, zero-ellipsis assertion passes (71 rendered strings, 0 found), deterministic two-run byte-identical **verified by the builder**, footer lands at 1019.2 of 1022. 300px test passes by the harness standard: date, all six stat numerals and the hero headlines read.

**Status: OFFLINE BUILD ONLY.** Nothing submitted, no make.fun endpoint called, repo root `entry.png` and git untouched. This is the new local #1, staged behind the same submission pause as iterations 4–5.

## Census arithmetic — how 34 became 39, and why 40 was the honest ceiling

Iteration 5 rendered 23 briefs (24 listed, Harare dropped by the fallback) at ladder L5, footer 1018.6 — **3.4px of slack**. Every brief on the page is already one line; each added one-line brief costs 13.3px of logbook column sum, ≈6.65px on the taller column after the split rebalances. Five added briefs therefore cost ≈33px of footer, against 3.4px of slack — **≈30px had to be bought back with layout**, and the ladder was extended past L5 to do it, cheapest first:

| Lever | Iteration 5 | Iteration 6 | Bought |
|---|---|---|---|
| Zone gaps | 3 | 2 | 2px |
| Footer box height | 34 | 32 | 2px |
| Hero art band | 52 | 48 | 4px |
| Date size | 76 | 72 (the documented floor) | 4px |
| Map height | 140 | 116 | 24px |
| **Total bought** | | | **36px** |

The landing rung is the new L10; L9 (map 120) missed by 1.2px. Two honest costs, stated plainly:

- **The split is granular.** With 28 briefs + 3 dividers the best column split is 210.2 / 198.2 — a 12px imbalance no rung can remove, because the split point can only land between 13.3px items. That granularity, not any single zone, is what makes the last brief the most expensive.
- **The map is thinner** (116px vs 140). Probed before adoption: the pins hold exactly as at 140 — min pin gap 2.0px, max displacement 14.8px vs iteration 5's 15.8 (the relaxation pass, not the band height, separates them). The one real regression was cosmetic and is fixed: at the flatter arc the DAWN/MIDDAY/DUSK chips fell into the pin row and clipped ("DU..", "MIDDA."); the chips now draw after the pins with MIDDAY re-anchored 0.40 → 0.34 and DUSK 0.88 → 0.68 into open water. Every word and every pin numeral reads on the final render.

**Why not 40:** a sixth added brief costs another ≈6.65px; the only remaining levers were the brief pitch (12.8 — a type metric, held), the standard art band (48px — the spec 3.4 floor), or a map below ~110px where the band stops reading as a map. The five strongest candidates were taken; the next three are documented under "cut on geometry" below. Census 39 sits inside the 38–40 target with every floor intact.

**Type floors held, explicitly:** date 72px (floor), stat numerals ≥34px, dispatch headlines 24/20px, summaries 14px, briefs 12.5px at 12.8 pitch — all identical to iteration 5. Region counts recomputed from the page: ASIA-PACIFIC 7→10 · EUROPE 6→7 · MIDEAST 7 · AFRICA 4 · AMERICAS 10→11 (total 39). The masthead standfirst's tail clause was cut ("the way the day travelled" → "as the day travelled") after the two-digit counts pushed it 2px past one line; the counts themselves are computed and were not trimmed.

## Fact changes (each verified against addendum 2's sources before use)

| Slot | Iteration 5 | Iteration 6 | Source |
|---|---|---|---|
| **Dispatch 2 — Akvan** | "Odisha moves 46,701 to shelters" / "46,701 moved to shelters… — News Ei Samay" | "Odisha moves 80,000-plus to shelters as Akvan nears" / "80,000-plus moved to shelters; landfall due near Gopalpur by noon 20 Nov. — The Hindu BusinessLine" | Addendum 2 #6: Revenue and Disaster Management Dept official via The Hindu BusinessLine (read in full) — more than 80,000 shifted, superseding 46,701; landfall guidance unchanged |
| **Stat band — 204,070** | caption "identified for evacuation" | **Unchanged, deliberately.** With the dispatch now at 80,000-plus *moved*, the caption's "identified" is what keeps the two numbers distinct: 204,070 identified for evacuation, 80,000-plus of them moved so far. No contradiction is printable from this page | Addendum 2 #6 (the 2 lakh / 204,070 target is stated in the same report) |
| **Brief 12 — APEC plenary** *(new)* | — | "SHENZHEN — Xi pledges $20m and a Shenzhen research centre at APEC. (Asia Today)" | Addendum 2 #1: Xi's Thursday plenary — $20m for APEC cooperation, Center for Asia-Pacific Community Studies in Shenzhen, new bodies on digital tech, cross-border data, clean energy, SMEs (Asia Today, read in full) |
| **Brief 14 — trilateral** *(new)* | — | "SHENZHEN — Trilateral ends with no agreements announced. (The Wall Street Journal)" | Addendum 2 #3: first Xi-Trump-Putin trilateral held Thursday; ~40-min Trump-Putin bilateral on Ukraine per the Kremlin; no agreements, no joint statement (WSJ). Framed as met-without-agreement; distinct from dispatch 1, which carries the summit's agenda, not its outcome |
| **Brief 19 — Dhaka** *(new)* | — | "DHAKA — Awami League lockdown turns violent; two party members killed. (Reuters)" | Addendum 2 #10: Thursday lockdown, two ruling-party members killed, 97 Border Guard platoons, 37 Grameen Bank branches hit (Reuters, read in full). The brief carries the deaths; the platoons stay in the data. The Chattogram arson was **Wednesday Nov 18** and is not on the page |
| **Brief 20 — Berlin** | "Allies meet US envoys Witkoff and Kushner. (Reuters)" (v2 story) | "30-plus European leaders meet to lock in Ukraine funding. (Reuters)" (addendum-2 story) | Addendum 2 #4: Coalition of the Willing summit, Berlin, Thursday, Witkoff and Kushner attending (Reuters). The EC's €45bn loan is the summit's money context but is Wednesday's proposal — it stays in the cutting-room box and is **not** re-imported here |
| **Brief 21 — Berlin spying** *(new)* | — | "BERLIN — Ukrainian-German charged as alleged Russian informant. (The Munich Eye)" | Unused v2 pool #13: federal prosecutors charged Ilona W. as an alleged Russian intelligence informant. The source's "alleged" survives; "entrepreneur" was cut by clause budget |
| **Brief 36 — Venezuela report** *(new)* | — | "CARACAS — US report details $12bn in Venezuelan oil revenue. (The Paris Eye)" | Unused v2 pool #32: State Department 53-page report on $12bn-plus in Venezuelan oil and mineral revenue. "Mineral" cut by clause budget; the $12bn survives |

**The Shenzhen Declaration is still not on this page.** Addendum 2 (Asia Today, 12:23 WIB, read in full): no text issued by ~15:45 WIB; adoption expected before the close, Putin backing the draft. Our restraint from iteration 5 stands — REF1 and REF2 both run a featured card stating it adopted; that is their exposure, not a lead to follow. If a named outlet confirms adoption before the final pass, this becomes a brief candidate (and two local-grade matches reopen — see the caveat below).

## Borderline calls

- **Kerch — NOT updated.** Addendum 2 adds the transport ministry's characterisation (nighttime drone attack, rail suspended, no injuries; HeadlinesXtra). Judged not a net sharpening: it trades The Guardian's account (railway section struck, road and rail halted) for a weaker roundup source and an official claim that would need attribution the summary budget cannot carry. The dispatch stands as iteration 5 has it.
- **COP31 — NOT updated.** Addendum 2's framing (Divan talks, IEA's "huge shock" line, 21 stocktake issues open) is process colour; the dispatch's existing facts (draft fossil-fuel exit, $120bn adaptation — The Business Standard) remain the sharpest verified specifics on the story. No new risk taken, none needed.
- **Gaza — NOT updated.** Addendum 2's new framing (the CENTCOM chief's visit coinciding with the tank incursion) hangs on the incursion, which **began Wednesday Nov 18** — carrying it would re-import a Wednesday event under a Thursday visit. The peace-board lead from iteration 5 stands.
- **Van Gogh — unchanged**, as instructed: still stat + brief, still the flagged exposure REF3 alone presses (REF1 features it as a brief, REF2 omits it). Addendum 2 offers no new dating evidence.
- **Fiji drought disaster — NOT used.** Reuters-reported Thursday, but Rabuka announced it **Wednesday Nov 18**; featuring it, even self-dated, spends criterion-1 capital this page just earned back. Recorded here as the first reserve if a slot ever frees.
- **Cut on geometry (in strength order):** New Delhi Congress white-paper brief (The Hindu, probed at 353px, one line) and the Miami NTSB brief (News Media House, 423px, one line) both fit as text; neither fits the page after the five above. The Iran/Gulf addendum-1 leftover was **not** used on date discipline: its own detail dates Tehran's self-defence statement to late Wednesday.
- **Anthropic pre-open framing — NOT used.** Analyst targets ($105 / $92 vs the $83 price) are pre-open colour; the dispatch already carries the debut, and the first print (Nasdaq opened 21:30 WIB) remains a separate pending swap, like the ICJ verdict.
- **ICJ — untouched.** Dispatch 7 still carries the judgment-day framing via `ICJ_HEADLINE` / `ICJ_SUMMARY`; no verdict is stated or invented. The swap steps in `lane-final/FINAL-PASS.md` apply verbatim to `build_final_v6.py`.

## Local re-grade (same harness, same rubric, same top-3 references)

Judged fresh, image-only, criteria in order. Full records appended to `local-grade/matches.json` (matches 17–20); ITER6's 300px thumb saved as `local-grade/iter6-300.png`. A summary also sits in `local-grade/LOCAL-GRADE.md`.

| # | Match | Winner | Criterion | Margin | Reason (one line) |
|---|---|---|---|---|---|
| 17 | ITER6 vs REF1 | **ITER6** | 1 | 2 | REF1 states the Declaration adopted and prints 200,000 as evacuated; ITER6 carries the verified evening facts on both — and now leads the census 39–36 |
| 18 | ITER6 vs REF2 | **ITER6** | 1 | 1 | Same C1 pattern; REF2's breadth edge narrowed 9 → 4 stories, short of the escape clause |
| 19 | ITER6 vs REF3 | REF3 | 1 | 1 | Van Gogh + Riyadh, unchanged, still decide against us vs the strictest box — margin narrows 2 → 1 on the fresher Akvan and the doubled breadth gap (39 vs 19) |
| 20 | ITER6 vs ITER5 | **ITER6** | 1 | 2 | Evening Akvan figure + today's actual APEC output vs ITER5's morning state; C2 reinforces (39 vs 34) |

**Local leaderboard (candidates): ITER6 > ITER5 > ITER4 > ITER3 > VARB.** ITER6 is the first of our candidates to beat any reference (2/3).

### Does breadth still decide against REF1/REF2?

**No.** Against REF1 the census itself flipped (39 vs 36), so breadth cannot decide that match at all. Against REF2 the gap narrowed from 9 stories to 4 (43 vs 39), and both matches now turn on **criterion 1** — the references' Declaration-adopted card and 200,000-as-evacuated Akvan against our verified evening facts. Breadth survives only as the reason match 18 is margin 1 rather than 2: REF2's remaining +4 is the counterweight that keeps it close. The frontier after this build is no longer breadth — it is the Van Gogh/Riyadh exposure (REF3 only) and the two pending swaps (ICJ verdict, Anthropic first print).

**Caveat that travels with matches 17–18:** both verdicts rest on addendum 2's ~15:45 WIB verification that the Declaration was still unissued. If it was adopted late Thursday, REF1's card becomes accurate, match 17 flips to REF1 on selection, and match 18 widens for REF2. The harness's standing limits apply unchanged: one judge, not the site's glm-5.3-flash; the house set is unseen; margins are this judge's calibration.

## Still pending (unchanged)

- **ICJ verdict** — the reading began ~16:00 WIB today; dispatch 7 awaits the swap (two constants in `build_final_v6.py`).
- **Anthropic first-day close** (Nasdaq opened 21:30 WIB) and any **Shenzhen Declaration** confirmation — same watch items as iterations 4–5.
- **Submission** — still paused on the account 429; when a slot opens, this candidate (with the ICJ swap applied) is the one to send.
