#!/usr/bin/env python3
"""ONE DAY ON EARTH - iteration 6 builder (make.fun news-image-20261119).

OFFLINE ONLY - built in lane-final-v6/ while submissions are paused
(account 429). Nothing here submits, calls the API, or touches the repo.

Fork of the iteration-5 builder (lane-final-v5/build_final_v5.py): same
page, same identity, same layout engine, same zero-ellipsis assertion,
and every iteration-5 fix kept (EU loan + Jeffries in the
cutting-room-floor box, Voyager briefing frame, Gaza peace-board lead,
Florida dispatch, Van Gogh as-is). Iteration 6 is the BREADTH push plus
the evening facts from addendum 2 (lane-stories/ADDENDUM-2.md):
  * Akvan: the lead stat moves from the stale 46,701 to the evening
    figure - more than 80,000 moved (Revenue dept official via The
    Hindu BusinessLine); the 204,070 stat keeps its "identified for
    evacuation" caption, so moved vs identified stay distinct.
  * APEC: the Shenzhen Declaration is STILL NOT ISSUED - our restraint
    stands. Today's concrete output, Xi's plenary announcements ($20m,
    a Shenzhen research centre, new cooperation bodies), gets its own
    brief ahead of the CEO Summit Initiative brief; the trilateral
    (held, no agreements) gets a one-line outcome brief.
  * Berlin brief upgraded to the addendum-2 story (30-plus leaders
    locking in Ukraine funding, Reuters) - the EC loan itself stays
    boxed as Wednesday's proposal.
  * Breadth: five new one-line briefs, each a complete fact - Dhaka
    lockdown deaths (Reuters), the Xi plenary, the trilateral outcome,
    the Berlin spying charge, the $12bn Venezuela revenue report.
  * Kerch / COP31 / Gaza addendum-2 framings reviewed and NOT adopted
    (calls recorded in ITERATION-6.md).
Geometry: the type floors are untouched (date >= 72, stat numerals
>= 34, dispatch and brief type at iteration-5 sizes, brief pitch
12.8). The added rows are bought with layout only - the ladder now
extends past iteration 5's last rung (gap, map height, hero art,
footer padding), in cheapest-first order.
Dispatch 8 stays the ICJ verdict slot (banner above DISPATCHES) for a
minutes-fast swap after the ~16:00 WIB reading - still no outcome
stated anywhere on the page.

Iteration 3 implemented ITERATION-3-SPEC.md:
  3.1 ZERO ELLIPSES - every headline/summary/brief is hand-composed to
      its character budget in the COMPOSED tables below (clause cuts,
      never character cuts; every qualifier and source preserved). The
      builder asserts zero "..."/"..." in every rendered string and
      fails loudly otherwise. No trim function touches story copy.
  3.2 The logbook is now one-clause BRIEFS: PLACE - clause. (Source),
      numbered on from the dispatches, in three sun legs.
  3.3 Dispatch set rebalanced: Van Gogh demoted to a brief (its number
      lives in the stat band); Libya seizure promoted (crime, Africa's
      first dispatch); Florida floods lead the Dusk briefs (weather).
      Shenzhen Declaration carried as its own brief.
  3.4 Standard art bands >= 48px (heroes 56-64px), funded by the map
      and by the headline space composed copy frees.
  3.5 Breadth stated at masthead level: per-region counts in the
      eyebrow idiom, computed from the stories actually on the page.
  3.6 Stat band back to 6 stats; GTA caption names its measure.
  3.7 Map pins relaxed with a separation pass; numerals never touch.

ICJ note (iteration 4): the judgment still had NOT been delivered when
this draft was built (reading set for ~16:00 WIB, 19 Nov). Dispatch 8
is framed as judgment day - no outcome is stated. The verdict swap is
documented step-by-step in FINAL-PASS.md.

Layout is cursor-stacked and measured; a declared fallback ladder
(gaps -> brief pitch -> map height -> weakest brief -> date size ->
hero art) is applied in order until the footer fits <= 1022px. Every
applied fallback is reported. Deterministic: seeded RNG, no clock,
no network. Output: JPEG bytes in a .png name, 1024x1024, <= 1 MiB,
target <= 380 KB.
"""
import io
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STORIES_V2 = os.path.join(ROOT, "lane-stories", "stories-v2.json")
ADDENDUM = os.path.join(ROOT, "lane-stories", "stories-addendum.json")
ADDENDUM2 = os.path.join(ROOT, "lane-stories", "stories-addendum-2.json")
LAND_PATH = os.path.join(ROOT, "lane-map", "land.json")
ART_DIR = os.path.join(ROOT, "lane-art-v4")
OUT_PATH = os.path.join(HERE, "entry-iteration6.png")
THUMB_PATH = os.path.join(HERE, "entry-iteration6-300.png")

W = 1024
MX = 34
CW = W - 2 * MX  # 956

# ---- palette (ours: midnight observatory) ----
BG_TOP = (9, 16, 32)
BG_BOT = (13, 25, 48)
MAP_FILL = (10, 21, 43)
MAP_EDGE = (38, 58, 96)
LAND = (133, 158, 205)
LAND_EDGE = (199, 213, 240)
LAND_GLOW = (70, 102, 168)
AMBER = (242, 169, 59)
AMBER_DEEP = (198, 128, 32)
STAR = (237, 239, 245)
MUTED = (168, 181, 204)
FAINT = (126, 142, 170)
TEAL = (94, 200, 180)
CARD_BG = (17, 28, 50)
CARD_EDGE = (44, 62, 98)
PIN_DOT = (148, 170, 212)
BODY = (203, 212, 230)

NOTO = "/usr/share/fonts/truetype/noto"
F_SERIF_BLACK = f"{NOTO}/NotoSerif-Black.ttf"
F_SERIF_BOLD = f"{NOTO}/NotoSerif-Bold.ttf"
F_SERIF_IT = f"{NOTO}/NotoSerif-Italic.ttf"
F_SANS_BOLD = f"{NOTO}/NotoSans-Bold.ttf"
F_COND = f"{NOTO}/NotoSans-Condensed.ttf"
F_COND_BOLD = f"{NOTO}/NotoSans-CondensedBold.ttf"

REPORT = {"notes": [], "fallbacks": []}
TEXTS = []  # registry of every composed string rendered (acceptance A1)


def reg(text):
    TEXTS.append(text)
    return text


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def draw_tracked(draw, xy, text, fnt, fill, tracking=2):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += tw(draw, ch, fnt) + tracking
    return x - tracking - xy[0]


def tracked_width(draw, text, fnt, tracking=2):
    return sum(tw(draw, ch, fnt) for ch in text) + tracking * (len(text) - 1)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if tw(draw, trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- data
def _norm(s):
    return {
        "place": s["place"], "headline": s["headline"],
        "summary": s.get("summary") or s.get("detail") or "",
        "fact": s.get("fact") or "",
        "source": s["source"], "lat": s["lat"], "lon": s["lon"],
        "region": s.get("region", ""),
        "contested": bool(s.get("contested")),
        "cut": bool(s.get("cut_candidate")),
    }


# Iteration 4 data merge (see ADDENDUM.md): the addendum's CONFIRMED
# updates supersede their v2 twins - same story, later facts, new
# source - so the footer source list and the map pins follow the copy
# actually printed. Matched by a distinctive headline substring on
# each side; every pair is asserted so a data drift fails loudly.
ADDENDUM_REPLACEMENTS = [
    # (v2 headline substring, addendum headline substring)
    ("Odisha readies evacuation", "46,701 people to shelters"),   # Akvan
    ("Crimean Bridge attacked again", "railway section"),        # Kerch
    ("ground operation beyond", "peace board warns"),            # Gaza
    ("COP31 heads into final hours", "COP31 ministers take over"),  # COP31
]


def load_data():
    with open(STORIES_V2) as f:
        d = json.load(f)
    stories = [_norm(s) for s in d["stories"]]
    with open(ADDENDUM) as f:
        addendum = [_norm(s) for s in json.load(f)]
    for v2_key, add_key in ADDENDUM_REPLACEMENTS:
        vi = next((i for i, s in enumerate(stories)
                   if v2_key.lower() in s["headline"].lower()), None)
        ai = next((i for i, s in enumerate(addendum)
                   if add_key.lower() in s["headline"].lower()), None)
        assert vi is not None, f"addendum replacement: v2 story '{v2_key}' not found"
        assert ai is not None, f"addendum replacement: addendum story '{add_key}' not found"
        assert addendum[ai]["region"] == stories[vi]["region"], \
            f"addendum replacement {v2_key}: region changed, census counts would shift"
        stories[vi] = addendum[ai]
    # The rest of the addendum joins the lookup pool (the Shenzhen
    # Initiative brief finds its story here). Pending entries (ICJ
    # verdict, Shenzhen Declaration, Anthropic first trade) are in the
    # pool for completeness but no composed copy points at them - the
    # ICJ dispatch keeps its v2 story and judgment-day framing.
    known = {s["headline"] for s in stories}
    stories.extend(s for s in addendum if s["headline"] not in known)
    # Iteration 6: addendum 2 (evening developments). Two CONFIRMED
    # updates supersede their current twins in place - the Akvan
    # evacuation total (80,000-plus moved, superseding 46,701) and the
    # Berlin coalition summit (30-plus leaders, superseding the v2
    # envoys brief) - matched by distinctive substrings, asserted like
    # the round-1 merge. The rest of addendum 2 joins the lookup pool
    # (the Dhaka, Xi-plenary and trilateral briefs find their stories
    # here); appended AFTER the existing pool, so every find() key
    # that matched an earlier story still resolves to it first.
    with open(ADDENDUM2) as f:
        addendum2 = [_norm(s) for s in json.load(f)]
    for cur_key, add_key in ADDENDUM2_REPLACEMENTS:
        ci = next((i for i, s in enumerate(stories)
                   if cur_key.lower() in s["headline"].lower()), None)
        ai = next((i for i, s in enumerate(addendum2)
                   if add_key.lower() in s["headline"].lower()), None)
        assert ci is not None, f"addendum2 replacement: current story '{cur_key}' not found"
        assert ai is not None, f"addendum2 replacement: addendum story '{add_key}' not found"
        assert addendum2[ai]["region"] == stories[ci]["region"], \
            f"addendum2 replacement {cur_key}: region changed, census counts would shift"
        stories[ci] = addendum2[ai]
    known = {s["headline"] for s in stories}
    stories.extend(s for s in addendum2 if s["headline"] not in known)
    return stories, d.get("stats", [])


# Iteration 6 data merge (see ADDENDUM-2.md): the evening's confirmed
# updates supersede their earlier twins - same story, later facts.
ADDENDUM2_REPLACEMENTS = [
    # (current headline substring, addendum-2 headline substring)
    ("46,701 people to shelters", "Odisha evacuation passes 80,000"),  # Akvan
    ("allies meet in Berlin", "Coalition of the Willing meets in Berlin"),  # Berlin
]


def find(stories, *keys):
    for s in stories:
        if all(k.lower() in s["headline"].lower() for k in keys):
            return s
    return None


# ------------------------------------------------- composed copy (3.1)
# Every string below was hand-composed from stories-v2.json fields by
# cutting clauses, never characters. Qualifiers ("proposes", "believed",
# "officials say") and every source survive whole. Budgets: dispatch
# headline <= 52 chars; hero summary <= ~96 (2 lines at 311px); standard
# summary <= ~72 (2 lines at 232px); brief = one clause, ~1 line.
# Spec worked rewrites used verbatim where they fit (Akvan headline,
# Kerch headline); where the spec's own rewrite broke its budget
# (Anthropic headline 55 chars, summaries 99-104 chars = 3 lines at our
# widths), a tighter clause-cut of the same rewrite is used - each is
# logged in ITERATION-3.md.
# =====================================================================
# ICJ VERDICT SLOT - dispatch 8 (hero, THE HAGUE). READ THIS FIRST.
# ---------------------------------------------------------------------
# The ICJ judgment in The Gambia v. Myanmar was due at 10:00 The Hague
# time (16:00 WIB) on Thu 19 Nov 2026, read by President Iwasawa; wire
# copy of the finding should exist by ~17:30 WIB. Until the verdict is
# reported by a named outlet, dispatch 8 carries the judgment-day
# framing in the two constants below - NO outcome is stated anywhere
# on the page.
#
# THE SWAP (minutes, once the verdict is out - full steps in
# FINAL-PASS.md): replace ICJ_HEADLINE and ICJ_SUMMARY ONLY, keeping
# the same budgets (headline <= ~48 chars, summary <= ~96 chars, ends
# " - <outlet that reported the verdict>"), then re-run this builder.
# The zero-ellipsis and 2-line assertions re-check the new copy
# automatically. Structural shapes, to adapt to the actual wire copy:
#   finding:    "World Court finds Myanmar committed genocide"
#               "First genocide ruling against a state; orders ... — Reuters"
#   no finding: "World Court clears Myanmar of genocide charge"
#               "Judges reject The Gambia's case over the 2017 crackdown. — Reuters"
# Do NOT ship either shape verbatim - compose from the real report.
ICJ_HEADLINE = "World Court delivers Rohingya judgment today"
ICJ_SUMMARY = "A genocide finding in The Gambia's case would be a first against a state. — Reuters"
# =====================================================================

DISPATCHES = [
    # keys, panel (None = procedural), hero, place line, headline, summary
    (("shake hands",), "panel-summit.png", True, "SHENZHEN · CHINA",
     "Trump, Xi and Putin shake hands in Shenzhen",
     "Trade, security and Ukraine topped the APEC summit agenda in Shenzhen. — The New York Times"),
    # Akvan: iteration-6 update (addendum 2) - the morning's 46,701
    # moved figure is STALE: a Revenue and Disaster Management
    # Department official now puts more than 80,000 people shifted to
    # safety (The Hindu BusinessLine), so 80,000-plus leads. The
    # 204,070 figure stays in the stat band with its "identified for
    # evacuation" caption - moved vs identified stay distinct, and
    # the two numbers cannot be read as contradicting each other.
    # Landfall guidance is UNCHANGED (IMD: between Narsapur and Puri,
    # near Gopalpur, by noon 20 Nov). Ganjam's 36,398 sheltered and
    # the 74 rescue teams stay in the data; the summary budget carries
    # the lead figure only.
    (("Cyclone Akvan",), "panel-cyclone.png", True, "PURI · ODISHA, INDIA",
     "Odisha moves 80,000-plus to shelters as Akvan nears",
     "80,000-plus moved to shelters; landfall due near Gopalpur by noon 20 Nov. — The Hindu BusinessLine"),
    # Kerch: iteration-4 update (addendum #6) - the third strike hit the
    # RAILWAY section; the 227m road-span collapse is BBC Verify-verified
    # (carried in FINAL-PASS.md; the summary budget carries the rail fact).
    (("Crimean Bridge",), "panel-crimean-bridge.png", False, "KERCH BRIDGE · CRIMEA",
     "Crimean Bridge hit for the third time this week",
     "Railway section struck; road and rail halted. — The Guardian"),
    # Gaza: iteration-5 re-lead - the peace board's UNSC report and
    # warning are TODAY's development (addendum #5, Dawn, read in
    # full), so the board leads the headline; the three killed in
    # strikes (medics, via Dawn) ride as the report's context instead
    # of leading as if they were today's event.
    (("killed in Gaza strikes",), "panel-gaza-tanks.png", False, "GAZA CITY · GAZA",
     "Peace board warns Gaza ceasefire cannot last",
     "Blames both sides in UNSC report; three killed in strikes. — Dawn"),
    # COP31: iteration-4 update (addendum #7) - ministers hold the final
    # draft; its figures ($120bn adaptation, fossil-fuel exit) replace
    # the v2 "21 issues unresolved" framing.
    (("COP31",), "panel-cop31.png", False, "ANTALYA · TÜRKİYE",
     "COP31 deadlocked over fossil fuels in final hours",
     "Draft demands fossil-fuel exit, $120bn adaptation. — The Business Standard"),
    (("Cocaine and millions",), None, False, "BENGHAZI · LIBYA",
     "Cocaine, millions of pills seized in eastern Libya",
     "Cocaine and millions of pills seized, officials say. — Jagran Josh"),
    # Iteration 5: the EU EUR45bn Ukraine loan dispatch is GONE from
    # the body - the field's top 3 date-check the proposal as an
    # 18 Nov story, so it now sits in the cutting-room-floor box
    # (footer) as an excluded Wednesday item, in our own words.
    # Dispatch 8 = the ICJ verdict slot (see the banner above): copy
    # comes from ICJ_HEADLINE / ICJ_SUMMARY so the verdict swap touches
    # exactly two strings.
    (("World Court",), "panel-icj.png", True, "THE HAGUE · NETHERLANDS",
     ICJ_HEADLINE,
     ICJ_SUMMARY),
    (("Anthropic",), "panel-anthropic.png", False, "NEW YORK · USA",
     "Anthropic debuts in the largest IPO on record",
     "Priced at $83, the debut values Anthropic near $1.5tn. — Reuters"),
    (("Grand Theft Auto",), "panel-gta.png", False, "NEW YORK · USA",
     "GTA VI begins its global rollout after 13 years",
     "Gamers enter Vice City as GTA VI ends a 13-year wait. — BBC News"),
    # Florida floods: promoted from the Dusk briefs (iteration 5
    # backfill for the EU loan slot). Today's conditions - flood
    # watches through Thursday evening, river in major flood now.
    # Procedural river art (no generated panel exists).
    (("St. Johns River",), "proc:floods", False, "COCOA · FLORIDA, USA",
     "Florida's east coast floods as river hits major stage",
     "St. Johns River in major flood at 17.2 ft, near Cocoa. — The Watchers"),
    # Voyager: iteration-5 re-anchor. The crossing itself is NOT
    # today's news - NASA timed it Wed 18 Nov, 10:16 UTC, and the
    # summary now says so. Today's verifiable event is JPL's public
    # briefing on both probes, held Thu 19 Nov (the today-anchor in
    # the story's own contested_note), so the briefing carries the
    # headline and the milestone rides as its subject.
    (("Voyager",), "panel-voyager.png", False, "PASADENA · CALIFORNIA, USA",
     "JPL briefs on Voyager 1, a light-day out",
     "NASA timed the crossing to Wed; craft 25.9bn km out. — Jagran Josh"),
]

# Briefs: (data keys, leg index, composed text). Format per spec 3.2:
# PLACE - one complete factual clause. (Source)
BRIEFS = [
    # Iteration 6: the APEC block is reframed around today's concrete
    # output. The Shenzhen Declaration is STILL NOT ISSUED (addendum 2,
    # Asia Today read in full) - we do not state it adopted, whatever
    # REF1/REF2 print. What leaders actually produced today is Xi's
    # plenary programme ($20m for APEC cooperation, a Center for
    # Asia-Pacific Community Studies in Shenzhen, new bodies on digital
    # tech, cross-border data, clean energy and SMEs), so that brief
    # leads the leg; the CEO Summit's Shenzhen Initiative (addendum 1,
    # Xinhua - a confirmed outcome, the summit's first in 30 years)
    # stays as its own brief, and the trilateral's outcome - held,
    # no agreements - closes the Shenzhen set.
    (("pledges $20 million",), 0,
     "SHENZHEN — Xi pledges $20m and a Shenzhen research centre at APEC. (Asia Today)"),
    # Iteration 4: the Shenzhen Initiative (addendum #9, Xinhua) takes
    # the Shenzhen brief slot - it is a CONFIRMED outcome (the CEO
    # Summit's first outcome document in 30 years) where the v2 brief
    # carried the still-pending leaders' Declaration draft. Census
    # stays 34; the Declaration remains a pending item in FINAL-PASS.md.
    (("Shenzhen Initiative",), 0,
     "SHENZHEN — CEO Summit issues the Shenzhen Initiative, a first in 30 years. (Xinhua)"),
    # Iteration 6: the first Xi-Trump-Putin trilateral was HELD today
    # (WSJ); the honest outcome line is that no agreements were
    # announced. The ~40-minute Trump-Putin bilateral rides in the
    # data; the brief budget carries the outcome only. Distinct from
    # dispatch 1, which carries the summit's agenda, not its result.
    (("no agreements announced",), 0,
     "SHENZHEN — Trilateral ends with no agreements announced. (The Wall Street Journal)"),
    (("2+2 defence",), 0,
     "TOKYO — India and Japan hold 2+2 defence talks. (The Times of India)"),
    (("loan package of over",), 0,
     "MANILA — US pursues a $2bn-plus military loan package. (AppiSToS)"),
    (("Indonesia trade pact",), 0,
     "JAKARTA — EU approves a tariff-cutting trade pact. (News Media House)"),
    (("Port of Darwin",), 0,
     "DARWIN — Landbridge refuses to rule out tribunal action over the lease. (Kalgoorlie Miner)"),
    # Iteration 6: the afternoon's strongest new story (addendum 2,
    # Reuters read in full) - the Awami League lockdown shut parts of
    # Bangladesh on Thursday; police said two ruling-party members
    # were killed and 97 Border Guard platoons deployed. The brief
    # carries the deaths; the platoons stay in the data (one line,
    # one complete fact). The Chattogram arson was Wednesday Nov 18
    # and is NOT in the brief - if it is ever mentioned, it is dated.
    (("lockdown turns violent",), 0,
     "DHAKA — Awami League lockdown turns violent; two party members killed. (Reuters)"),
    # Iteration 6: the Berlin brief moves to the addendum-2 story -
    # the Coalition of the Willing summit itself (30-plus leaders,
    # Thursday, Berlin) with its purpose as the fact. The EC's EUR45bn
    # loan proposal is Wednesday's and stays in the cutting-room box;
    # it is not re-imported here as the summit's news.
    (("Coalition of the Willing",), 1,
     "BERLIN — 30-plus European leaders meet to lock in Ukraine funding. (Reuters)"),
    # Iteration 6: a second Berlin story, from the unused v2 pool -
    # federal prosecutors charged a Ukrainian-German entrepreneur as
    # an alleged Russian informant (The Munich Eye). "Entrepreneur"
    # is cut by clause budget, not by character trim; the charge and
    # the allegation both survive.
    (("entrepreneur charged with spying",), 1,
     "BERLIN — Ukrainian-German charged as alleged Russian informant. (The Munich Eye)"),
    (("fourth weekend of protests",), 1,
     "PARIS — Fourth weekend of cost-of-living protests. (The Paris Eye)"),
    (("Four nations urge",), 1,
     "GAZA — Four nations urge aid access to flooded Gaza. (The Paris Eye)"),
    (("Eisenkot",), 1,
     "JERUSALEM — Herzog asks Eisenkot to form a government. (The Paris Eye)"),
    (("danger has passed",), 1,
     "RIYADH — Houthis claim strikes; danger passed, Riyadh says. (AppiSToS)"),
    (("Tanker struck",), 1,
     "KHASAB — Tanker hit near Hormuz; all crew safe. (UKMTO)"),
    (("sanctions three entities",), 1,
     "BEIRUT — US sanctions three entities over Hezbollah. (AppiSToS)"),
    (("pull back from Bab",), 1,
     "ADEN — Forces fall back to defend Aden. (Molitics Global)"),
    (("exchange drone attacks",), 1,
     "KYIV — Drone attacks damage infrastructure amid talks. (The Munich Eye)"),
    (("restore direct flights",), 1,
     "CAIRO — Egypt-Syria flights resume after 14 years. (Egyptian Streets)"),
    (("dialogue with terrorists",), 1,
     "ILORIN — Army admits dialogue with terrorists. (Premium Times)"),
    (("17,300 herders",), 1,
     "MOGADISHU — $11.5m aids 17,300 drought-hit herders. (Puntland Times)"),
    (("reserves judgment",), 1,
     "HARARE — Court reserves judgment on term challenges. (Nehanda Radio)"),
    # Iteration 5: the Cocoa brief is promoted to a dispatch (above),
    # and the Jeffries brief is OUT of the body - the 251-11 caucus
    # vote is date-checked by the field's top 3 as an 18 Nov item, so
    # it now sits in the cutting-room-floor box as an excluded
    # Wednesday item. Two clean Washington briefs backfill the leg:
    # both are statements made in today's cycle, both composed to
    # exactly one line (the swap is height-neutral by design).
    (("Van Gogh sells",), 2,
     "NEW YORK — Van Gogh sells for a record $190.4m. (BBC News)"),
    (("AI-enabled cyber threats",), 2,
     "WASHINGTON — Senators warn AI cyber threats outpace defences. (Reuters)"),
    (("technology outages",), 2,
     "WASHINGTON — Lawmakers demand outage briefings. (Washington Examiner)"),
    (("re-establish military ties",), 2,
     "CARACAS — US and Venezuela restore military ties. (CNN)"),
    # Iteration 6: from the unused v2 pool - the State Department's
    # 53-page report on how over $12bn in Venezuelan oil and mineral
    # revenue was handled (The Paris Eye). The brief carries the
    # report and its headline figure; "mineral" is cut by clause
    # budget, the $12bn survives.
    (("$12bn in Venezuelan oil",), 2,
     "CARACAS — US report details $12bn in Venezuelan oil revenue. (The Paris Eye)"),
    (("fishermen sue",), 2,
     "GUAYAQUIL — Fishermen sue over alleged drone strike. (Kalgoorlie Miner)"),
    (("second arrest",), 2,
     "PANAMA — Second arrest over journalist home attack. (AppiSToS)"),
]

LEGS = [
    ("LEG ONE", "FIRST LIGHT", "ASIA & THE PACIFIC"),
    ("LEG TWO", "MIDDAY", "EUROPE · AFRICA · THE MIDDLE EAST"),
    ("LEG THREE", "DUSK", "THE AMERICAS"),
]

# Stat captions: clean substrings of the data labels (never trimmed).
CAPTIONS = {
    "$81.3bn": "Anthropic's record IPO",
    # "identified" is the load-bearing word (vs the 46,701 already
    # MOVED in the Akvan dispatch); the place rides on the dispatch's
    # own place line. The longer "...in Odisha" form wraps to a second
    # caption line and pushes the whole page ~13px past the fit cap.
    "204,070": "identified for evacuation",
    "15.9m": "GTA VI pre-orders (Sensor Tower)",
    "$190.4m": "record price for a Van Gogh",
    "25.9bn km": "Voyager 1's distance from Earth",
    "730,000": "Rohingya who fled in 2017",
}

# Vertical focus (0=top, 1=bottom) for cropping panels into wide bands.
PANEL_FOCUS = {
    "panel-summit.png": 0.48, "panel-cyclone.png": 0.45,
    "panel-crimean-bridge.png": 0.38, "panel-gaza-tanks.png": 0.55,
    "panel-cop31.png": 0.40, "panel-eu-loan.png": 0.42,
    "panel-icj.png": 0.38, "panel-anthropic.png": 0.30,
    "panel-gta.png": 0.50, "panel-voyager.png": 0.45,
}


# ---------------------------------------------------------------- background
def make_background():
    grad = Image.new("RGB", (1, W))
    for y in range(W):
        t = y / (W - 1)
        grad.putpixel((0, y), tuple(int(BG_TOP[c] + (BG_BOT[c] - BG_TOP[c]) * t) for c in range(3)))
    img = grad.resize((W, W))
    rng = random.Random(20261119)
    stars = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(300):
        x, y = rng.uniform(0, W), rng.uniform(0, W)
        r = rng.choice([0.6, 0.8, 1.0, 1.3])
        a = rng.randint(22, 80)
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(220, 230, 250, a))
    for _ in range(14):
        x, y = rng.uniform(20, W - 20), rng.uniform(10, 700)
        sd.line([(x - 4, y), (x + 4, y)], fill=(230, 238, 255, 60), width=1)
        sd.line([(x, y - 4), (x, y + 4)], fill=(230, 238, 255, 60), width=1)
    img.paste(Image.alpha_composite(img.convert("RGBA"), stars).convert("RGB"), (0, 0))
    return img


# ---------------------------------------------------------------- masthead
def draw_masthead(img, total, region_groups, date_max=80):
    d = ImageDraw.Draw(img)
    f_eye = font(F_COND_BOLD, 13)
    d.polygon([(MX + 4, 18), (MX + 9, 24), (MX + 4, 30), (MX - 1, 24)], fill=AMBER)
    left = reg("ONE DAY ON EARTH — FOLLOW THE SUN · ONE ROTATION OF THE PLANET")
    draw_tracked(d, (MX + 16, 17), left, f_eye, AMBER, 2)
    right = reg(f"THURSDAY · {total} STORIES · ONE PAGE")
    rw = tracked_width(d, right, f_eye, 2)
    draw_tracked(d, (W - MX - rw, 17), right, f_eye, MUTED, 2)

    # THE DATE - largest type on the page, autofit, hard floor 72 (v2 spec)
    date_text = reg("19 NOVEMBER 2026")
    size = date_max
    while size > 72 and tw(d, date_text, font(F_SERIF_BLACK, size)) > CW:
        size -= 2
    d.text((MX - 2, 32), date_text, font=font(F_SERIF_BLACK, size), fill=AMBER)

    # Standfirst and breadth proof share one line (spec 3.5): the spread
    # is stated at masthead level, in our own voice, computed from the
    # stories actually on the page.
    f_stand = font(F_SERIF_IT, 13)
    counts = " · ".join(f"{name} {n}" for name, n in region_groups)
    # Iteration 6: two-digit region counts (ASIA-PACIFIC 12, AMERICAS
    # 12) pushed this line 2px past one line; the tail clause is cut
    # ("the way the day travelled" -> "as the day travelled") - the
    # counts themselves are computed and never trimmed.
    stand = reg(f"{total} stories from a single turn of the planet — {counts} "
                f"— read westward, as the day travelled.")
    assert len(wrap(d, stand, f_stand, CW)) == 1, "masthead line must be one line"
    d.text((MX, 38 + size), stand, font=f_stand, fill=(205, 214, 232))
    rule_y = 38 + size + 20
    d.line([(MX, rule_y), (W - MX, rule_y)], fill=AMBER_DEEP, width=1)
    d.line([(MX, rule_y + 3), (W - MX, rule_y + 3)], fill=(60, 74, 104), width=1)
    return {"date_size": size, "masthead_bottom": rule_y + 5}


# ---------------------------------------------------------------- stats
def draw_stats(img, stats, y0):
    d = ImageDraw.Draw(img)
    assert len(stats) == 6, "stat band must carry all 6 stats (spec 3.6)"
    # Unequal columns, matched to the data order: the wide Voyager
    # numeral ("25.9bn km" = 182px at 34px) gets a wide column so every
    # numeral keeps the >=34px floor.
    col_ws = {"$81.3bn": 151, "204,070": 140, "15.9m": 165,
              "$190.4m": 153, "25.9bn km": 205, "730,000": 142}
    assert sum(col_ws.values()) == CW
    f_cap = font(F_COND, 12)
    # label rides on the rule (no separate header row)
    f_head = font(F_COND_BOLD, 12)
    label = reg("THE DAY IN NUMBERS")
    lw = tracked_width(d, label, f_head, 2)
    d.line([(MX, y0 + 5), (MX + lw + 12, y0 + 5)], fill=BG_BOT, width=3)
    draw_tracked(d, (MX, y0), label, f_head, TEAL, 2)
    d.line([(MX + lw + 16, y0 + 5), (W - MX, y0 + 5)], fill=(70, 88, 128), width=1)
    used = []
    cap_lines_max = 0
    cx = MX
    for i, it in enumerate(stats):
        col_w = col_ws[it["value"]]
        d.ellipse([cx + 2, y0 + 2, cx + 8, y0 + 8], fill=AMBER)
        size = 36
        while size > 34 and tw(d, it["value"], font(F_SERIF_BLACK, size)) > col_w - 8:
            size -= 1
        assert tw(d, it["value"], font(F_SERIF_BLACK, size)) <= col_w - 8, \
            f"stat numeral {it['value']} breaks the 34px floor"
        d.text((cx + 2, y0 + 8), reg(it["value"]), font=font(F_SERIF_BLACK, size), fill=AMBER)
        cap = reg(CAPTIONS[it["value"]])
        lines = wrap(d, cap, f_cap, col_w - 8)
        assert len(lines) <= 2, f"stat caption {it['value']} wraps past 2 lines"
        cap_lines_max = max(cap_lines_max, len(lines))
        for li, ln in enumerate(lines):
            d.text((cx + 2, y0 + 8 + size + 3 + li * 13), ln, font=f_cap, fill=MUTED)
        used.append(it["value"])
        cx += col_w
    bottom = y0 + 8 + 36 + 3 + cap_lines_max * 13
    return {"stats_used": used, "stats_bottom": bottom}


# ---------------------------------------------------------------- map
LAT_TOP, LAT_BOT = 62.0, -45.0


def project(lat, lon, box):
    x0, y0, x1, y1 = box
    sy = (y1 - y0) / (LAT_TOP - LAT_BOT)
    sx = sy * 1.45
    ox = x0 + ((x1 - x0) - 360.0 * sx) / 2.0
    oy = y0 + ((y1 - y0) - (LAT_TOP - LAT_BOT) * sy) / 2.0
    return (ox + (lon + 180.0) * sx, oy + (LAT_TOP - lat) * sy)


def draw_map(img, dispatches, brief_stories, y0, height):
    box = (MX, y0, W - MX, y0 + height)
    x0, y0b, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0b
    lbox = (0, 0, bw, bh)
    layer = Image.new("RGB", (bw, bh), MAP_FILL)
    with open(LAND_PATH) as f:
        polys = json.load(f)["polygons"]

    def pts(ring):
        return [project(lat, lon, lbox) for lon, lat in ring]

    glow = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for poly in polys:
        outer = pts(poly[0])
        if len(outer) >= 3:
            gd.polygon(outer, fill=LAND_GLOW + (110,))
    glow = glow.filter(ImageFilter.GaussianBlur(7))
    layer = Image.alpha_composite(layer.convert("RGBA"), glow).convert("RGB")
    ld = ImageDraw.Draw(layer)
    for poly in polys:
        outer = pts(poly[0])
        if len(outer) >= 3:
            ld.polygon(outer, fill=LAND, outline=LAND_EDGE, width=1)
        for hole in poly[1:]:
            hp = pts(hole)
            if len(hp) >= 3:
                ld.polygon(hp, fill=MAP_FILL)
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=12, fill=255)
    img.paste(layer, (x0, y0b), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=12, outline=MAP_EDGE, width=1)

    for s in brief_stories:
        x, y = project(s["lat"], s["lon"], box)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=PIN_DOT)

    pins = []
    for i, ds in enumerate(dispatches):
        s = ds["story"]
        x, y = project(s["lat"], s["lon"], box)
        pins.append({"x": x, "y": y, "r": 12, "n": i + 1})
    for _ in range(300):
        moved = False
        for i in range(len(pins)):
            for j in range(i + 1, len(pins)):
                a, b = pins[i], pins[j]
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                dist = math.hypot(dx, dy)
                need = a["r"] + b["r"] + 2
                if dist < need:
                    if dist < 0.01:
                        ang = (i * 37 + j * 91) % 360 * math.pi / 180.0
                        dx, dy, dist = math.cos(ang), math.sin(ang), 1.0
                    push = (need - dist) / 2.0
                    ux, uy = dx / dist, dy / dist
                    a["x"] -= ux * push; a["y"] -= uy * push
                    b["x"] += ux * push; b["y"] += uy * push
                    moved = True
        for p in pins:
            p["x"] = min(max(p["x"], x0 + p["r"] + 2), x1 - p["r"] - 2)
            p["y"] = min(max(p["y"], y0b + p["r"] + 2), y1 - p["r"] - 2)
        if not moved:
            break
    max_disp = 0.0
    min_gap = 1e9
    for p, ds in zip(pins, dispatches):
        tx, ty = project(ds["story"]["lat"], ds["story"]["lon"], box)
        max_disp = max(max_disp, math.hypot(p["x"] - tx, p["y"] - ty))
    for i in range(len(pins)):
        for j in range(i + 1, len(pins)):
            min_gap = min(min_gap, math.hypot(pins[j]["x"] - pins[i]["x"],
                                              pins[j]["y"] - pins[i]["y"]) - 24)

    start = (pins[0]["x"], pins[0]["y"])
    end = (pins[-1]["x"], pins[-1]["y"])
    mid = ((start[0] + end[0]) / 2.0, min(start[1], end[1]) - 40)

    def bez(t):
        return ((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * mid[0] + t * t * end[0],
                (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * mid[1] + t * t * end[1])

    arc = [bez(k / 140.0) for k in range(141)]
    layer2 = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ld2 = ImageDraw.Draw(layer2)
    for width, alpha in [(11, 36), (7, 62), (3, 110), (2, 185)]:
        ld2.line(arc, fill=AMBER + (alpha,), width=width, joint="curve")
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer2).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    t_ang = math.atan2(arc[-1][1] - arc[-6][1], arc[-1][0] - arc[-6][0])
    ex, ey = arc[-1]
    ah = 9
    d.polygon([(ex, ey),
               (ex - ah * math.cos(t_ang - 0.42), ey - ah * math.sin(t_ang - 0.42)),
               (ex - ah * math.cos(t_ang + 0.42), ey - ah * math.sin(t_ang + 0.42))], fill=AMBER)
    sx, sy = start[0] + 3, start[1] - 12
    glow2 = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(glow2).ellipse([sx - 20, sy - 20, sx + 20, sy + 20], fill=AMBER + (70,))
    img.paste(Image.alpha_composite(img.convert("RGBA"),
                                     glow2.filter(ImageFilter.GaussianBlur(7))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        d.line([(sx + 12 * math.cos(a), sy + 12 * math.sin(a)),
                (sx + 16 * math.cos(a), sy + 16 * math.sin(a))], fill=AMBER, width=2)
    d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=AMBER, outline=(255, 214, 130), width=2)
    f_num = font(F_SANS_BOLD, 11)
    for p in pins:
        x, y, r = p["x"], p["y"], p["r"]
        d.ellipse([x - r, y - r, x + r, y + r], fill=AMBER, outline=STAR, width=2)
        label = str(p["n"])
        bb = d.textbbox((0, 0), label, font=f_num)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]),
               label, font=f_num, fill=(20, 14, 4))
    # Iteration 6: the arc labels are drawn AFTER the pins, and two
    # anchors moved. At the 116px map height the flatter arc pulls
    # the DUSK and MIDDAY chips into the pin row: pins drawn over
    # them clipped the words ("DU..", "MIDDA."), and chips drawn
    # over the pins at the old anchors covered pin 9's numeral.
    # MIDDAY 0.40 -> 0.34 and DUSK 0.88 -> 0.68 put both chips in
    # open water (the Mediterranean gap, the mid-Atlantic) - every
    # word and every pin numeral reads on the render.
    f_lab = font(F_COND_BOLD, 11)
    for t, label, dy in [(0.13, "DAWN", -24), (0.34, "MIDDAY", 30), (0.68, "DUSK", -24)]:
        reg(label)
        px, py = bez(t)
        wlab = tracked_width(d, label, f_lab, 3)
        cx, cy = px - wlab / 2, py + dy
        cy = min(max(cy, y0b + 3), y1 - 18)
        d.rounded_rectangle((cx - 5, cy - 2, cx + wlab + 5, cy + 14), radius=4, fill=(8, 15, 30))
        draw_tracked(d, (cx, cy), label, f_lab, AMBER, 3)
    f_cap = font(F_COND_BOLD, 11)
    cap = reg("EVERY PIN A STORY — NUMBERED PINS MARK THE DISPATCHES · "
              "DOTS MARK THE BRIEFS · POSITIONS APPROXIMATE")
    cw_ = tracked_width(d, cap, f_cap, 1)
    d.rounded_rectangle((x0 + 6, y1 - 22, x0 + 16 + cw_, y1 - 3), radius=4, fill=(8, 15, 30))
    draw_tracked(d, (x0 + 11, y1 - 18), cap, f_cap, (150, 168, 200), 1)
    return {"map_box": box, "max_pin_displacement_px": round(max_disp, 1),
            "min_pin_gap_px": round(min_gap, 1)}


# ---------------------------------------------------------------- art
def crop_art(panel, w, h):
    art = Image.open(os.path.join(ART_DIR, panel)).convert("RGB")
    focus = PANEL_FOCUS.get(panel, 0.5)
    target = w / h
    aw, ah = art.size
    if aw / ah > target:
        nw = int(ah * target)
        art = art.crop(((aw - nw) // 2, 0, (aw - nw) // 2 + nw, ah))
    else:
        nh = int(aw / target)
        y_off = int((ah - nh) * focus)
        art = art.crop((0, y_off, aw, y_off + nh))
    return art.resize((w, h))


def libya_art(w, h):
    """Procedural flat band for the Libya seizure (no generated panel
    exists): desert horizon, seized crates under a prohibition ring."""
    img = Image.new("RGB", (w, h), (16, 30, 54))
    d = ImageDraw.Draw(img)
    d.rectangle((0, h * 0.62, w, h), fill=(122, 90, 44))          # sand
    d.rectangle((0, h * 0.60, w, h * 0.64), fill=(168, 124, 58))  # horizon light
    d.ellipse((w * 0.80, h * 0.08, w * 0.80 + h * 0.34, h * 0.08 + h * 0.34), fill=AMBER)
    crate = (52, 44, 34)
    edge = (196, 160, 100)
    boxes = [(0.06, 0.30, 0.20, 0.34), (0.22, 0.30, 0.36, 0.34),
             (0.13, 0.06, 0.27, 0.26), (0.62, 0.34, 0.74, 0.30),
             (0.76, 0.34, 0.88, 0.30)]
    for bx, by, bw_, bh_ in boxes:
        x0, y0 = w * bx, h * (0.94 - by - bh_)
        x1, y1 = w * (bx + bw_), h * (0.94 - by)
        d.rectangle((x0, y0, x1, y1), fill=crate, outline=edge, width=2)
        d.line((x0, y0, x1, y1), fill=edge, width=1)
        d.line((x0, y1, x1, y0), fill=edge, width=1)
    cx, cy, r = w * 0.44, h * 0.52, h * 0.34
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(196, 74, 52), width=max(3, h // 12))
    d.line((cx - r * 0.7, cy + r * 0.7, cx + r * 0.7, cy - r * 0.7),
           fill=(196, 74, 52), width=max(3, h // 12))
    return img


def floods_art(w, h):
    """Procedural flat band for the Florida floods (no generated panel
    exists): a dark treeline over a flooded river plain, current
    streaks on the water, and a plain gauge post with tick marks
    (no numerals - the 17.2 ft figure lives in the summary text)."""
    img = Image.new("RGB", (w, h), (14, 26, 48))
    d = ImageDraw.Draw(img)
    # rain-grey sky band
    d.rectangle((0, 0, w, h * 0.30), fill=(52, 68, 96))
    # treeline silhouette
    d.rectangle((0, h * 0.26, w, h * 0.40), fill=(18, 34, 30))
    for fx in (0.08, 0.30, 0.55, 0.78, 0.93):
        tx = w * fx
        d.polygon([(tx - h * 0.10, h * 0.30), (tx + h * 0.10, h * 0.30),
                   (tx, h * 0.10)], fill=(18, 34, 30))
    # flooded plain: water with a lighter current sheen
    d.rectangle((0, h * 0.40, w, h), fill=(30, 62, 96))
    d.rectangle((0, h * 0.40, w, h * 0.44), fill=(120, 158, 196))
    for fy, fl in ((0.56, 0.55), (0.68, 0.38), (0.80, 0.62), (0.90, 0.30)):
        y = h * fy
        d.line((w * 0.05, y, w * (0.05 + fl), y), fill=(110, 148, 190),
               width=max(1, h // 24))
    # rooftops poking out of the water, right side
    for rx, ry in ((0.66, 0.60), (0.82, 0.66)):
        x0, y0 = w * rx, h * ry
        d.polygon([(x0, y0), (x0 + w * 0.07, y0 - h * 0.10),
                   (x0 + w * 0.14, y0)], fill=(122, 90, 44))
        d.rectangle((x0 + w * 0.015, y0, x0 + w * 0.125, y0 + h * 0.05),
                    fill=(84, 62, 36))
    # gauge post, left: post + tick marks, top tick in amber
    gx = w * 0.16
    d.rectangle((gx, h * 0.34, gx + max(2, w // 90), h * 0.96), fill=(196, 160, 100))
    for i, fy in enumerate((0.44, 0.56, 0.68, 0.80)):
        col = AMBER if i == 0 else (196, 160, 100)
        d.line((gx, h * fy, gx + w * 0.055, h * fy), fill=col, width=max(1, h // 24))
    return img


# ---------------------------------------------------------------- dispatches
def draw_dispatches(img, dispatches, y0, hero_art_h, std_art_h, gap):
    d = ImageDraw.Draw(img)
    f_head = font(F_COND_BOLD, 13)
    draw_tracked(d, (MX, y0), reg("DISPATCHES FROM THE DAY"), f_head, AMBER, 2)
    f_sub = font(F_SERIF_IT, 13)
    sub = reg("the day's biggest stories, told in full — numbered in sun order")
    d.text((W - MX - tw(d, sub, f_sub), y0 + 1), sub, font=f_sub, fill=MUTED)
    y = y0 + 16

    f_place_chip = font(F_COND_BOLD, 12)
    f_sum = font(F_COND, 14)
    heroes = [ds for ds in dispatches if ds["hero"]]
    standards = [ds for ds in dispatches if not ds["hero"]]
    info = {"hero_cards": [], "std_rows": []}

    def place_chip(cx, cy_top, art_h, ds):
        pl = reg(ds["place_line"])
        pw = tw(d, pl, f_place_chip)
        chip_y = cy_top + art_h - 15
        d.rounded_rectangle((cx + 5, chip_y - 2, cx + 9 + pw, chip_y + 14),
                            radius=3, fill=(8, 15, 30))
        d.text((cx + 7, chip_y), pl, font=f_place_chip, fill=AMBER)

    # ---- heroes: 3 across, ~311 wide, larger art band, place chip on art
    hw = (CW - 2 * 11) / 3
    cards = []
    for ds in heroes:
        f_hl = font(F_COND_BOLD, 24)
        hl_lines = wrap(d, ds["hl"], f_hl, hw - 18)
        sum_lines = wrap(d, ds["sum"], f_sum, hw - 18)
        assert len(hl_lines) <= 2, f"hero headline n={ds['n']} wraps past 2 lines"
        assert len(sum_lines) <= 2, f"hero summary n={ds['n']} wraps past 2 lines"
        h = hero_art_h + 3 + len(hl_lines) * 24 + 2 + len(sum_lines) * 14.5 + 6
        cards.append((ds, hl_lines, sum_lines, h))
    hero_h = max(c[3] for c in cards)
    for ci, (ds, hl_lines, sum_lines, _h) in enumerate(cards):
        cx = MX + ci * (hw + 11)
        d.rounded_rectangle((cx, y, cx + hw, y + hero_h), radius=8, fill=CARD_BG,
                            outline=CARD_EDGE, width=1)
        if ds["panel"]:
            img.paste(crop_art(ds["panel"], int(hw) - 4, hero_art_h), (int(cx) + 2, int(y) + 2))
            d = ImageDraw.Draw(img)
        d.rectangle((cx + 8, y + 5, cx + 27, y + 22), fill=AMBER)
        f_chip = font(F_SANS_BOLD, 11)
        bb = d.textbbox((0, 0), str(ds["n"]), font=f_chip)
        d.text((cx + 8 + (19 - (bb[2] - bb[0])) / 2 - bb[0],
                y + 5 + (17 - (bb[3] - bb[1])) / 2 - bb[1]),
               str(ds["n"]), font=f_chip, fill=(20, 14, 4))
        place_chip(cx, y + 2, hero_art_h, ds)
        cy = y + hero_art_h + 3
        f_hl = font(F_COND_BOLD, 24)
        for ln in hl_lines:
            d.text((cx + 9, cy), ln, font=f_hl, fill=STAR)
            cy += 24
        cy += 2
        for ln in sum_lines:
            d.text((cx + 9, cy), ln, font=f_sum, fill=BODY)
            cy += 14.5
        info["hero_cards"].append({"n": ds["n"], "hl_lines": len(hl_lines),
                                   "sum_lines": len(sum_lines)})
    y += hero_h + gap

    # ---- standards: 2 rows of 4, ~232 wide, place as a chip on the art
    sw = (CW - 3 * 9) / 4
    rows = [standards[:4], standards[4:]]
    for row in rows:
        rcards = []
        for ds in row:
            f_hl = font(F_COND_BOLD, 20)
            hl_lines = wrap(d, ds["hl"], f_hl, sw - 16)
            sum_lines = wrap(d, ds["sum"], f_sum, sw - 16)
            assert len(hl_lines) <= 2, f"standard headline n={ds['n']} wraps past 2 lines"
            assert len(sum_lines) <= 2, f"standard summary n={ds['n']} wraps past 2 lines"
            h = std_art_h + 3 + len(hl_lines) * 20 + 2 + len(sum_lines) * 14.5 + 5
            rcards.append((ds, hl_lines, sum_lines, h))
        row_h = max(c[3] for c in rcards)
        for ci, (ds, hl_lines, sum_lines, _h) in enumerate(rcards):
            cx = MX + ci * (sw + 9)
            d.rounded_rectangle((cx, y, cx + sw, y + row_h), radius=8, fill=CARD_BG,
                                outline=CARD_EDGE, width=1)
            if ds["panel"] and not ds["panel"].startswith("proc:"):
                img.paste(crop_art(ds["panel"], int(sw) - 4, std_art_h), (int(cx) + 2, int(y) + 2))
            elif ds["panel"] == "proc:floods":
                img.paste(floods_art(int(sw) - 4, std_art_h), (int(cx) + 2, int(y) + 2))
                REPORT["notes"].append("Florida dispatch: procedural flat art band "
                                       "(no generated panel exists for this story)")
            else:
                img.paste(libya_art(int(sw) - 4, std_art_h), (int(cx) + 2, int(y) + 2))
                REPORT["notes"].append("Libya dispatch: procedural flat art band "
                                       "(no generated panel exists for this story)")
            d = ImageDraw.Draw(img)
            d.rectangle((cx + 7, y + 4, cx + 24, y + 18), fill=AMBER)
            f_chip = font(F_SANS_BOLD, 9)
            bb = d.textbbox((0, 0), str(ds["n"]), font=f_chip)
            d.text((cx + 7 + (17 - (bb[2] - bb[0])) / 2 - bb[0],
                    y + 4 + (14 - (bb[3] - bb[1])) / 2 - bb[1]),
                   str(ds["n"]), font=f_chip, fill=(20, 14, 4))
            # place chip on the art band, bottom-left (dark backing)
            place_chip(cx, y + 2, std_art_h, ds)
            cy = y + std_art_h + 3
            f_hl = font(F_COND_BOLD, 20)
            for ln in hl_lines:
                d.text((cx + 8, cy), ln, font=f_hl, fill=STAR)
                cy += 20
            cy += 2
            for ln in sum_lines:
                d.text((cx + 8, cy), ln, font=f_sum, fill=BODY)
                cy += 14.5
            info["std_rows"].append({"n": ds["n"], "hl_lines": len(hl_lines),
                                     "sum_lines": len(sum_lines)})
        y += row_h + gap
    return {"dispatch_bottom": y - gap, "hero_h": hero_h, "cards": info}


# ---------------------------------------------------------------- logbook (briefs)
def draw_logbook(img, briefs, first_num, y0, pitch):
    """Briefs flow in two columns in sun order; a leg divider row marks
    each leg change. Numbering is assigned in flow order (down column 1,
    then column 2) with no gaps."""
    d = ImageDraw.Draw(img)
    f_head = font(F_COND_BOLD, 13)
    draw_tracked(d, (MX, y0), reg("THE LOGBOOK — BRIEFS FROM THE REST OF THE DAY"),
                 f_head, AMBER, 2)
    f_sub = font(F_SERIF_IT, 13)
    sub = reg("first light · midday · dusk — still in sun order")
    d.text((W - MX - tw(d, sub, f_sub), y0 + 1), sub, font=f_sub, fill=MUTED)
    top = y0 + 16

    f_entry = font(F_COND, 12.5)
    f_num = font(F_COND_BOLD, 12.5)
    f_div = font(F_COND_BOLD, 11)
    col_gap = 22
    col_w = (CW - col_gap) / 2
    text_w = col_w - 24
    DIV_H = 12

    # build the item sequence: divider pseudo-items at leg boundaries
    items = []  # ("div", leg) or ("brief", brief_dict, lines)
    cur_leg = None
    for b in briefs:
        reg(b["text"])  # acceptance A1 covers briefs too
        if b["leg"] != cur_leg:
            cur_leg = b["leg"]
            items.append(("div", cur_leg))
        lines = wrap(d, b["text"], f_entry, text_w)
        items.append(("brief", b, lines))

    def item_h(it):
        if it[0] == "div":
            return DIV_H
        return pitch * len(it[2]) + 0.5

    prefix = [0]
    for it in items:
        prefix.append(prefix[-1] + item_h(it))
    best = None
    for a in range(1, len(items)):
        hs = (prefix[a], prefix[-1] - prefix[a])
        key = (max(hs), max(hs) - min(hs))
        if best is None or key < best[0]:
            best = (key, a, hs)
    _key, split, col_heights = best
    cols = [items[:split], items[split:]]

    # numbering in flow order
    n = first_num
    for col in cols:
        for it in col:
            if it[0] == "brief":
                it[1]["_num"] = n
                n += 1

    for ci, col in enumerate(cols):
        x = MX + ci * (col_w + col_gap)
        y = top
        for it in col:
            if it[0] == "div":
                leg = LEGS[it[1]]
                lab = reg(f"{leg[0]} · {leg[1]} — {leg[2]}")
                # Rule low in the slot and the label knocked out with a
                # background stroke: no opaque patch, so the previous
                # brief's descenders are never painted over.
                d.line([(x, y + 5), (x + col_w, y + 5)], fill=(44, 60, 92), width=1)
                cx2 = x + 2
                for ch in lab:
                    d.text((cx2, y), ch, font=f_div, fill=TEAL,
                           stroke_width=2, stroke_fill=BG_BOT)
                    cx2 += tw(d, ch, f_div) + 1
                y += DIV_H
            else:
                b, lines = it[1], it[2]
                d.text((x, y), str(b["_num"]), font=f_num, fill=AMBER)
                for li, ln in enumerate(lines):
                    d.text((x + 24, y + li * pitch), ln, font=f_entry, fill=BODY)
                y += item_h(it)
    if col_heights[0] > 0:
        rx = MX + col_w + col_gap / 2
        d.line([(rx, top + 2), (rx, top + max(col_heights) - 2)], fill=(44, 60, 92), width=1)
    return {"logbook_bottom": top + max(col_heights),
            "col_heights": list(col_heights),
            "brief_lines": {b["text"][:24]: len(wrap(d, b["text"], f_entry, text_w))
                            for b in briefs}}


# ---------------------------------------------------------------- footer
def draw_footer(img, used_stories, y0, box_h=34):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((MX, y0, W - MX, y0 + box_h), radius=8, outline=AMBER_DEEP, width=1)
    f_box = font(F_COND, 12.5)
    f_lead = font(F_COND_BOLD, 12.5)
    lead = reg("LEFT ON THE CUTTING-ROOM FLOOR — ")
    # Iteration 5: the box now also carries the two items the local
    # harness caught us featuring as today's news - the EU loan
    # proposal and the Jeffries vote, both Wednesday items - in our
    # own compressed wording. The older items are tightened by a few
    # characters each so the box still wraps to exactly 2 lines.
    items_txt = reg("held back on date discipline: the EU's €45bn Ukraine loan "
                    "(proposed Wed 18 Nov) · the 251–11 Jeffries vote (Wed 18 Nov) · "
                    "a Prague media protest (Sun 15 Nov) · a Spanish strike "
                    "(Wed 18 Nov) · a North Korean missile launch (day unclear) · "
                    "an actor's obituary (dateline unverified).")
    lines = wrap(d, lead + items_txt, f_box, CW - 24)
    assert len(lines) <= 2, "date-check box text wraps past 2 lines"
    ly = y0 + 4
    for ln in lines:
        if ln.startswith("LEFT ON"):
            d.text((MX + 12, ly), lead, font=f_lead, fill=AMBER)
            d.text((MX + 12 + tw(d, lead, f_lead), ly), ln[len(lead):], font=f_box, fill=MUTED)
        else:
            d.text((MX + 12, ly), ln, font=f_box, fill=MUTED)
        ly += 13.5
    f_claim = font(F_COND, 13)
    claim = reg("Every story here happened, or was first reported, on Thursday "
                "19 November 2026. Disputed claims are attributed, not stated as fact.")
    cy = y0 + box_h + 3
    cl = wrap(d, claim, f_claim, CW)
    assert len(cl) == 1, "claim line must be one line"
    d.text((MX, cy), cl[0], font=f_claim, fill=(190, 200, 220))
    cy += 14
    seen = []
    for s in used_stories:
        if s["source"] not in seen:
            seen.append(s["source"])
    f_src = font(F_COND, 12)
    head = seen[:9]
    src = "Sources: " + " · ".join(head)
    if len(seen) > len(head):
        src += f" · + {len(seen) - len(head)} more outlets"
    src = reg(src)
    assert len(wrap(d, src, f_src, CW)) == 1, "sources line must be one line"
    d.text((MX, cy + 1), src, font=f_src, fill=FAINT)
    return {"footer_bottom": cy + 13, "sources_count": len(seen)}


# ---------------------------------------------------------------- assembly
def build_sets(stories, drop_weakest_brief=False):
    dispatches = []
    used = set()
    for keys, panel, hero, place_line, hl, summ in DISPATCHES:
        s = find(stories, *keys)
        assert s is not None, f"dispatch {keys} not found in data"
        dispatches.append({"story": s, "panel": panel, "hero": hero,
                           "place_line": place_line, "hl": hl, "sum": summ,
                           "n": len(dispatches) + 1})
        used.add(id(s))
    briefs = []
    for keys, leg, text in BRIEFS:
        s = find(stories, *keys)
        assert s is not None, f"brief {keys} not found in data"
        assert s["source"] in text, f"brief {keys}: source not in composed text"
        assert id(s) not in used, f"brief {keys} duplicates a dispatch"
        briefs.append({"story": s, "leg": leg, "text": text})
        used.add(id(s))
    if drop_weakest_brief:
        briefs = [b for b in briefs if "reserves judgment" not in b["story"]["headline"]]
        REPORT["notes"].append("fallback: Harare brief dropped (weakest brief - "
                               "a court reserving judgment is a non-outcome)")
    groups = {}
    for ds in dispatches:
        groups[ds["story"]["region"]] = groups.get(ds["story"]["region"], 0) + 1
    for b in briefs:
        r = b["story"]["region"]
        groups[r] = groups.get(r, 0) + 1
    region_groups = [
        ("ASIA-PACIFIC", groups.get("asia", 0) + groups.get("oceania", 0)),
        ("EUROPE", groups.get("europe", 0)),
        ("MIDEAST", groups.get("middle-east", 0)),
        ("AFRICA", groups.get("africa", 0)),
        ("AMERICAS", groups.get("north-america", 0) + groups.get("south-america", 0)),
    ]
    return dispatches, briefs, region_groups


LADDER = [
    # gap, brief pitch, map height, hero art, drop weakest brief,
    # date max, footer box height
    (5, 13.5, 148, 56, False, 80, 34),
    (4, 13.0, 148, 56, False, 80, 34),
    (4, 12.8, 145, 56, False, 78, 34),
    (4, 12.8, 142, 52, False, 78, 34),
    (4, 12.8, 140, 52, True, 76, 34),
    (3, 12.8, 140, 52, True, 76, 34),
    # Iteration 6 extension: five added briefs cost ~33px of logbook
    # column; the rungs below buy it back with layout only, cheapest
    # first (gaps and footer padding, then hero art, then the date
    # toward its 72px floor, then map height). Type sizes and the
    # 12.8 brief pitch never move.
    (2, 12.8, 136, 50, True, 74, 32),
    (2, 12.8, 130, 48, True, 72, 32),
    (2, 12.8, 124, 48, True, 72, 32),
    (2, 12.8, 120, 48, True, 72, 32),
    # The logbook split is granular (13.3px briefs), so the deepest
    # rung buys the last 4px from the map alone. Probed before
    # adoption: at 116px the pins hold exactly as at 140 (min gap
    # 2.0px, max displacement 14.8px vs iteration 5's 15.8) - the
    # relaxation pass, not the band height, is what separates them.
    (2, 12.8, 116, 48, True, 72, 32),
]


def render(params):
    global REPORT, TEXTS
    REPORT = {"notes": [], "fallbacks": []}
    TEXTS = []
    gap, pitch, map_h, hero_art, drop_brief, date_max, footer_box_h = params
    stories, stats = load_data()
    dispatches, briefs, region_groups = build_sets(stories, drop_brief)
    total = len(dispatches) + len(briefs)

    img = make_background()
    mh = draw_masthead(img, total, region_groups, date_max)
    st = draw_stats(img, stats, mh["masthead_bottom"])
    mp = draw_map(img, dispatches, [b["story"] for b in briefs],
                  st["stats_bottom"] + 2, map_h)
    disp = draw_dispatches(img, dispatches, mp["map_box"][3] + 4, hero_art, 48, gap)
    lb = draw_logbook(img, briefs, len(dispatches) + 1,
                      disp["dispatch_bottom"] + gap, pitch)
    used_stories = [ds["story"] for ds in dispatches] + [b["story"] for b in briefs]
    ft = draw_footer(img, used_stories, lb["logbook_bottom"] + gap, footer_box_h)

    # ---- acceptance A1: zero ellipses in ANY rendered string
    bad = [t for t in TEXTS if "…" in t or "..." in t]
    assert not bad, f"ELLIPSIS FOUND in rendered text: {bad}"

    buf = io.BytesIO()
    q = 88
    img.save(buf, format="JPEG", quality=q)
    data = buf.getvalue()
    while len(data) > 380_000 and q > 70:
        q -= 2
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q)
        data = buf.getvalue()
    REPORT.update({
        "zones": {"masthead": mh["masthead_bottom"], "stats": st["stats_bottom"],
                  "map": mp["map_box"][3], "dispatches": disp["dispatch_bottom"],
                  "logbook": lb["logbook_bottom"], "footer": ft["footer_bottom"]},
        "params": {"gap": gap, "brief_pitch": pitch, "map_h": map_h,
                   "hero_art_h": hero_art, "std_art_h": 48,
                   "drop_weakest_brief": drop_brief, "date_max": date_max,
                   "footer_box_h": footer_box_h},
        "total_stories": total,
        "dispatches": len(dispatches),
        "briefs": len(briefs),
        "date_size_px": mh["date_size"],
        "stats": st, "map": mp, "dispatches_layout": disp,
        "logbook_layout": {k: v for k, v in lb.items() if k != "kept"},
        "footer": ft, "bytes": len(data), "jpeg_quality": q,
        "jpeg_magic": data[:2] == b"\xff\xd8",
        "rendered_strings_checked": len(TEXTS),
        "ellipsis_found": 0,
    })
    return data, REPORT, img


def main():
    chosen = None
    for li, params in enumerate(LADDER):
        data, report, img = render(params)
        if report["footer"]["footer_bottom"] <= 1022:
            chosen = (li, data, report, img)
            break
        print(f"ladder L{li}: footer_bottom={report['footer']['footer_bottom']} > 1022, escalating")
    assert chosen is not None, "no ladder level fits the page"
    li, data, report, img = chosen
    report["ladder_level"] = li
    if li > 0:
        report["fallbacks"].append(f"layout fallback ladder level L{li} applied: {LADDER[li]}")
    data2, _r2, _i2 = render(LADDER[li])
    report["deterministic"] = data == data2
    assert report["deterministic"], "two renders differ"
    # census / mix acceptance (iteration 6: the breadth push - five
    # added briefs over iteration 5's list of 24; the weakest-brief
    # fallback may still drop one)
    assert report["dispatches"] == 11
    assert 27 <= report["briefs"] <= 29
    assert 38 <= report["total_stories"] <= 40
    with open(OUT_PATH, "wb") as f:
        f.write(data)
    print(json.dumps(report, indent=2, default=str))
    print("wrote", OUT_PATH, len(data), "bytes")
    thumb = Image.open(io.BytesIO(data)).resize((300, 300))
    thumb.save(THUMB_PATH)
    print("wrote", THUMB_PATH)


if __name__ == "__main__":
    main()
