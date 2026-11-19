# -*- coding: utf-8 -*-
"""
Variant B builder for make.fun news-image-20261119 - "One Day on Earth".

THE BET (different from iteration 3): completeness of the FEATURED layer wins.
14 illustrated dispatches - every panel in lane-art-v4, incl. the round-2 spares -
each carrying a headline plus a CLOSED summary sentence with the day's fact and
its source. The logbook shrinks to whatever briefs still fit at >=13px, and the
Day in Numbers band moves to the foot of the page to fund the featured layer.
Same identity as v2: midnight palette, sun-path arc, sun-order numbering,
date as the largest type, slim map band (~14%).

Layout is MEASURED, not estimated: a probe pass wraps every string with the
real fonts, zone heights are computed from those wraps, the logbook solver
then takes whatever vertical space remains. The builder never trims copy;
an over-budget wrap fails the build instead.

Hard rules honoured:
- 1024x1024, JPEG bytes targeted <= ~380 KB (1 MiB hard cap)
- deterministic: build() run twice in __main__, byte-identical asserted
- zero ellipses anywhere (asserted over all composed copy)
- type floors: date >= 80px, headlines >= 20px, summaries >= 13.5px (14 used),
  briefs >= 13px, stat numerals >= 34px, stat captions >= 12px,
  date-check >= 12.5px (13 used)
- contested stories framed as proposals / attributed claims, never as fact
"""
import hashlib
import io
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # news-image/
ART = os.path.join(ROOT, "lane-art-v4")
LAND = json.load(open(os.path.join(ROOT, "lane-map", "land.json")))["polygons"]
STORIES = json.load(open(os.path.join(ROOT, "lane-stories", "stories-v2.json")))["stories"]

W = H = 1024
MX = 34                      # side margin
CW = W - 2 * MX              # 956 content width

# ---------------------------------------------------------------- palette/fonts
INK = (226, 232, 245)
PAPER = (244, 238, 226)
MUTED = (158, 170, 196)
FAINT = (104, 116, 144)
AMBER = (242, 169, 59)
CARD = (17, 28, 52)
CARD_LINE = (52, 68, 104)
CHIP_BG = (10, 18, 36)

NF = "/usr/share/fonts/truetype/noto/"
SERIF_BLACK = "NotoSerif-Black.ttf"
SERIF_BOLD = "NotoSerif-Bold.ttf"
SERIF_IT = "NotoSerif-Italic.ttf"
COND = "NotoSans-Condensed.ttf"
COND_B = "NotoSans-CondensedBold.ttf"
DV_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- composed copy
# Hand-composed from stories-v2.json facts (clause-cutting only - no fact
# invented). Budgets are enforced by wrap assertions in the card functions.
# fields: keys (substring match into stories-v2 for traceability), panel,
#         hero flag, wide flag (last-row horizontal card), headline, summary
DISPATCHES = [
    dict(keys="shake hands", panel="panel-summit.png", hero=True,
         headline="Trump, Xi and Putin shake hands in Shenzhen",
         summary="Trade, security and the Ukraine war topped the APEC summit agenda."),
    dict(keys="204,070", panel="panel-cyclone.png", hero=True,
         headline="Odisha readies 204,070 evacuations for Akvan",
         summary="Akvan heads for the Andhra coast, landfall expected around noon on 20 Nov."),
    dict(keys="Crimean Bridge", panel="panel-crimean-bridge.png",
         headline="Crimean Bridge hit a third time this week",
         summary="Closed to traffic while damage is assessed."),
    dict(keys="Yellow Line", panel="panel-gaza-tanks.png",
         headline="Israeli tanks cross Gaza's Yellow Line",
         summary="A rare ground incursion across the cease-fire line."),
    dict(keys="14 years", panel="panel-egypt-flights.png",
         headline="Egypt-Syria flights resume after 14 years",
         summary="Direct flights resume after a 14-year gap."),
    dict(keys="deadlocked", panel="panel-cop31.png",
         headline="COP31 deadlocked in its final hours",
         summary="21 issues unresolved; fossil-fuel wording still split."),
    dict(keys="45bn", panel="panel-eu-loan.png",
         headline="EU proposes \u20ac45bn Ukraine loan",
         summary="It is repayable only after Russia pays reparations."),
    dict(keys="World Court", panel="panel-icj.png", hero=True,
         headline="World Court rules in Rohingya genocide case",
         summary="A genocide finding in The Gambia's case would be the first ever against a state."),
    dict(keys="Ueno Bank", panel="panel-fed.png",
         headline="Paraguay extends Ueno Bank guarantee review",
         summary="Review extended 15 days, to December 2."),
    dict(keys="re-establish military ties", panel="panel-venezuela-deal.png",
         headline="US and Venezuela restore military ties",
         summary="The pact covers training, equipment and intelligence sharing."),
    dict(keys="Van Gogh", panel="panel-vangogh.png",
         headline="Van Gogh sells for a record $190.4m",
         summary="A record for the artist, after an eleventh-hour deal."),
    dict(keys="81.3bn", panel="panel-anthropic.png", wide=True,
         headline="Anthropic's $81.3bn IPO record",
         summary="Priced at $83 a share, valued near $1.5tn."),
    dict(keys="GTA VI", panel="panel-gta.png", wide=True,
         headline="GTA VI begins its global rollout",
         summary="Vice City opens after a 13-year wait."),
    dict(keys="light-day", panel="panel-voyager.png", wide=True,
         headline="Voyager 1 reaches one light-day out",
         summary="One light-day out; JPL briefs today."),
]

# Briefs: one complete factual clause each, source in brackets. Column flow,
# legs in sun order. The solver drops the LAST brief of the tallest leg first.
BRIEFS = [
    ["SHENZHEN \u2014 Xi pledges $20m and four pillars toward a Shenzhen Declaration. (Aju Business Daily)",
     "TOKYO \u2014 India and Japan's ministers call defence ties key in 2+2 talks. (The Times of India)",
     "JAKARTA \u2014 EU governments approve a tariff-cutting trade pact with Indonesia. (News Media House)",
     "MANILA \u2014 White House pursues a $2bn-plus military loan package for the Philippines. (AppiSToS)",
     "DARWIN \u2014 Landbridge refuses to rule out tribunal action over the port lease. (Kalgoorlie Miner)"],
    ["BERLIN \u2014 Ukraine's allies meet US envoys Witkoff and Kushner on guarantees. (Reuters)",
     "GAZA \u2014 Four nations demand immediate, unrestricted aid access to flooded Gaza. (The Paris Eye)",
     "KHASAB \u2014 Tanker hit in the engine room near Hormuz; all crew safe. (UKMTO)",
     "BENGHAZI \u2014 Cocaine and millions of pills seized in eastern Libya. (Jagran Josh)",
     "KYIV \u2014 Drone attacks damage infrastructure despite Abu Dhabi talks. (The Munich Eye)",
     "MOGADISHU \u2014 $11.5m reaches 17,300 herders to save livestock in drought. (Puntland Times)"],
    ["COCOA \u2014 St. Johns River in major flood at 17.2 ft; 400 homes damaged. (The Watchers)",
     "CARACAS \u2014 State Department details $12bn in Venezuelan oil revenue in 53 pages. (The Paris Eye)",
     "WASHINGTON \u2014 Democrats nominate Jeffries 251-11, in line to be first Black Speaker. (The New York Times)",
     "GUAYAQUIL \u2014 Ecuadorian fishermen sue the US, alleging a drone struck their boat. (Kalgoorlie Miner)",
     "WASHINGTON \u2014 Senators warn AI cyber threats are outpacing US defences. (Reuters)"],
]
BRIEF_KEYS = [
    ["four-pillar", "2+2", "trade pact", "over $2bn", "Darwin lease"],
    ["Witkoff", "unrestricted aid", "engine room", "millions of pills", "Abu Dhabi", "17,300"],
    ["St. Johns River", "oil and mineral revenue", "251-11", "drone struck", "cyber threats"],
]

# (numeral, caption) - captions are faithful compressions of the data labels.
STATS = [
    ("$81.3bn", "Anthropic's record IPO raise"),
    ("204,070", "on Odisha's evacuation list"),
    ("15.9m", "GTA VI pre-orders (Sensor Tower est.)"),
    ("$190.4m", "record price for a Van Gogh"),
    ("25.9bn km", "Voyager 1's distance out"),
    ("730,000", "Rohingya fled in 2017"),
]

DATECHECK = ("KEPT OFF THIS PAGE ON DATE DISCIPLINE:  Prague protest (15 Nov) \u00b7 "
             "Spain strike (18 Nov) \u00b7 N. Korea launch (day disputed)")
CLAIM = ("Every story here happened, or was first reported, on Thursday 19 November 2026. "
         "Disputed claims are attributed, not stated as fact.")

CROP_FOCUS = {
    "panel-summit.png": 0.30, "panel-cyclone.png": 0.42, "panel-icj.png": 0.30,
    "panel-gaza-tanks.png": 0.45, "panel-crimean-bridge.png": 0.45,
    "panel-voyager.png": 0.40, "panel-fed.png": 0.40,
}


# ---------------------------------------------------------------- data binding
def find_story(keys):
    for s in STORIES:
        blob = s["headline"] + " " + s.get("summary", "") + " " + s.get("fact", "") + " " + s.get("detail", "")
        if keys in blob:
            return s
    raise KeyError("story not found for keys %r" % keys)


for d in DISPATCHES:
    st = find_story(d["keys"])
    d["story"] = st
    d["place"] = st["place"].replace(", ", " \u00b7 ").upper()
    d["full_summary"] = d["summary"] + " \u2014 " + st["source"]
    d.setdefault("hero", False)
    d.setdefault("wide", False)
BRIEF_STORIES = [[find_story(k) for k in leg] for leg in BRIEF_KEYS]

REGION_LABEL = {
    "asia": "ASIA", "oceania": "OCEANIA", "europe": "EUROPE",
    "middle-east": "MIDEAST", "africa": "AFRICA",
    "south-america": "S. AMERICA", "north-america": "N. AMERICA",
}
REGION_ORDER = ["asia", "oceania", "europe", "middle-east", "africa",
                "south-america", "north-america"]


def region_line(stories):
    counts = {}
    for s in stories:
        counts[s["region"]] = counts.get(s["region"], 0) + 1
    return " \u00b7 ".join("%s %d" % (REGION_LABEL[r], counts[r])
                           for r in REGION_ORDER if r in counts)


# ---------------------------------------------------------------- draw helpers
def tw(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(d, t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def tracked(d, xy, s, f, fill, tracking=2):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += tw(d, ch, f) + tracking
    return x - tracking


def tracked_w(d, s, f, tracking=2):
    return sum(tw(d, ch, f) for ch in s) + tracking * (len(s) - 1)


def crop_art(panel, w, h):
    im = Image.open(os.path.join(ART, panel)).convert("RGB")
    scale = max(w / im.width, h / im.height)
    nw, nh = max(w, round(im.width * scale)), max(h, round(im.height * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    focus = CROP_FOCUS.get(panel, 0.5)
    x0 = (nw - w) // 2
    y0 = max(0, min(nh - h, int((nh - h) * focus)))
    return im.crop((x0, y0, x0 + w, y0 + h))


def background():
    top, bot = (9, 16, 32), (13, 25, 48)
    strip = Image.new("RGB", (1, H))
    sp = strip.load()
    for yy in range(H):
        t = yy / H
        sp[0, yy] = tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    img = strip.resize((W, H))
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(20261119)
    for _ in range(210):
        x, y = rng.uniform(0, W), rng.uniform(0, 560)
        r = rng.uniform(0.6, 1.7)
        a = int(rng.uniform(28, 110) * (1 - y / 700))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 214, 245, max(0, a)))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.62, -H * 0.34, W * 1.24, H * 0.30], fill=(26, 17, 4))
    glow = glow.filter(ImageFilter.GaussianBlur(150))
    return Image.blend(img, Image.blend(img, glow, 0.55), 0.35)


PROBE = ImageDraw.Draw(Image.new("RGB", (8, 8)))

# ---------------------------------------------------------------- type system
F_EB = font(NF + COND_B, 13)        # masthead eyebrow
F_DATE = font(NF + SERIF_BLACK, 80)  # the date - largest type on the page
F_SF = font(NF + SERIF_IT, 15)      # standfirst
F_RC = font(NF + COND_B, 12)        # region counts
F_PLACE = font(NF + COND_B, 13)
F_HERO_HL = font(NF + COND_B, 24)
F_STD_HL = font(NF + COND_B, 20)
F_SUM = font(NF + COND, 14)         # summaries (>= 13.5 floor)
F_CHIP = font(DV_B, 11)             # number chips
F_CHIP_PLACE = font(NF + COND_B, 12)  # place chip on standard art
F_SEC = font(NF + COND_B, 13)       # section labels
F_SEC_IT = font(NF + SERIF_IT, 13)
F_BRIEF = font(NF + COND, 13)       # logbook briefs (>= 13 floor)
F_NUM = font(NF + SERIF_BOLD, 34)   # stat numerals (>= 34 floor)
F_CAP = font(NF + COND, 12)         # stat captions (>= 12 floor)
F_DC = font(NF + COND_B, 13)        # date-check (>= 12.5 floor)
F_CLAIM = font(NF + COND_B, 13)

HERO_W = (CW - 2 * 11) // 3         # 311
STD_W = (CW - 3 * 9) // 4           # 232
WIDE_W = HERO_W
HERO_ART, STD_ART = 36, 48
WIDE_ART_W = 118
MAP_H = 136
BRIEF_LEAD, BRIEF_GAP = 16, 6
COL_W = (CW - 2 * 16) // 3          # 308


def hero_card_h(dp):
    hl = wrap(PROBE, dp["headline"], F_HERO_HL, HERO_W - 18)
    sm = wrap(PROBE, dp["full_summary"], F_SUM, HERO_W - 18)
    assert len(hl) <= 2, ("hero headline", dp["keys"], hl)
    assert len(sm) <= 2, ("hero summary", dp["keys"], sm)
    # place rides on the art as a chip (bottom-left), like the standards -
    # the hero's distinction is its width and 24px headline
    return 2 + HERO_ART + 2 + len(hl) * 24 + 2 + len(sm) * 16 + 5, hl, sm


def std_card_h(dp):
    hl = wrap(PROBE, dp["headline"], F_STD_HL, STD_W - 18)
    sm = wrap(PROBE, dp["full_summary"], F_SUM, STD_W - 18)
    assert len(hl) <= 2, ("std headline", dp["keys"], hl)
    assert len(sm) <= 2, ("std summary", dp["keys"], sm)
    return 2 + STD_ART + 2 + len(hl) * 20 + 1 + len(sm) * 14 + 4, hl, sm


def wide_card_h(dp):
    tw_ = WIDE_W - WIDE_ART_W - 16
    hl = wrap(PROBE, dp["headline"], F_STD_HL, tw_)
    sm = wrap(PROBE, dp["full_summary"], F_SUM, tw_)
    assert len(hl) <= 2, ("wide headline", dp["keys"], hl)
    assert len(sm) <= 2, ("wide summary", dp["keys"], sm)
    text_h = 8 + 15 + 1 + len(hl) * 20 + 1 + len(sm) * 15 + 5
    return max(94, text_h), hl, sm


# ---------------------------------------------------------------- sections
def masthead(img, census, rline):
    d = ImageDraw.Draw(img, "RGBA")
    y = 12
    tracked(d, (MX, y), "\u25c6 ONE DAY ON EARTH \u2014 THE DAY, TOLD IN SUN ORDER", F_EB, AMBER, 2)
    right = "THURSDAY \u00b7 %d STORIES \u00b7 ONE PAGE" % census
    d.text((W - MX - tw(d, right, F_EB), y), right, font=F_EB, fill=MUTED)
    y += 18
    d.text((MX - 2, y), "19 NOVEMBER 2026", font=F_DATE, fill=PAPER)
    asc, desc = F_DATE.getmetrics()
    y += asc + desc - 14
    d.text((MX, y), "The world on Thursday, followed westward from dawn to dusk.",
           font=F_SF, fill=(196, 205, 226))
    rw = tracked_w(d, rline, F_RC, 1)
    tracked(d, (W - MX - rw, y + 2), rline, F_RC, AMBER, 1)
    return y + 20


def draw_map(img, y0, brief_stories):
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1 = MX, W - MX
    y1 = y0 + MAP_H
    d.rounded_rectangle([x0, y0, x1, y1], 10, fill=(11, 20, 40), outline=CARD_LINE, width=1)
    lat_t, lat_b = 62, -45
    sy = MAP_H / (lat_t - lat_b)
    sx = sy * 1.45
    ox = x0 + (CW - 360 * sx) / 2
    oy = y0

    def proj(lat, lon):
        return (ox + (lon + 180) * sx, oy + (lat_t - lat) * sy)

    clip = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(clip)
    cd.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], 9, fill=255)
    land_img = Image.new("RGB", (W, H), (11, 20, 40))
    ld = ImageDraw.Draw(land_img)
    for poly in LAND:
        for ring in poly:
            pts = [proj(p[1], p[0]) for p in ring]
            if len(pts) >= 3:
                ld.polygon(pts, fill=(122, 143, 188))
    img.paste(Image.blend(img, land_img, 0.85), (0, 0), clip)
    d = ImageDraw.Draw(img, "RGBA")

    pts = [proj(dp["story"]["lat"], dp["story"]["lon"]) for dp in DISPATCHES]
    (ax, ay), (bx, by) = pts[0], pts[-1]
    mxp, myp = (ax + bx) / 2, min(ay, by) - 28
    curve = []
    for i in range(81):
        t = i / 80
        curve.append(((1 - t) ** 2 * ax + 2 * (1 - t) * t * mxp + t ** 2 * bx,
                      (1 - t) ** 2 * ay + 2 * (1 - t) * t * myp + t ** 2 * by))
    d.line(curve, fill=(242, 169, 59, 70), width=5)
    d.line(curve, fill=AMBER, width=2)
    d.ellipse([ax - 7, ay - 7, ax + 7, ay + 7], fill=AMBER, outline=(255, 226, 160), width=2)
    for leg in brief_stories:
        for s in leg:
            px_, py_ = proj(s["lat"], s["lon"])
            d.ellipse([px_ - 2.5, py_ - 2.5, px_ + 2.5, py_ + 2.5], fill=(150, 168, 205, 200))
    disp = [[x, y] for x, y in pts]
    for _ in range(300):
        moved = False
        for i in range(len(disp)):
            for j in range(i + 1, len(disp)):
                dx, dy = disp[j][0] - disp[i][0], disp[j][1] - disp[i][1]
                dist = math.hypot(dx, dy)
                if dist < 25:
                    push = (25 - dist) / 2 + 0.6
                    ux, uy = (dx / dist, dy / dist) if dist else (1.0, 0.0)
                    disp[i][0] -= ux * push
                    disp[i][1] -= uy * push
                    disp[j][0] += ux * push
                    disp[j][1] += uy * push
                    moved = True
        if not moved:
            break
    f_stage = font(NF + COND_B, 11)
    for t, name in ((0.10, "DAWN"), (0.42, "MIDDAY"), (0.86, "DUSK")):
        cxp = (1 - t) ** 2 * ax + 2 * (1 - t) * t * mxp + t ** 2 * bx
        cyp = (1 - t) ** 2 * ay + 2 * (1 - t) * t * myp + t ** 2 * by
        wch = tracked_w(d, name, f_stage, 2) + 14
        chx, chy = cxp - wch / 2, max(y0 + 5, cyp - 26)
        d.rounded_rectangle([chx, chy, chx + wch, chy + 17], 8, fill=(10, 18, 36, 215),
                            outline=(90, 106, 142), width=1)
        tracked(d, (chx + 7, chy + 3), name, f_stage, (210, 220, 240), 2)
    f_pin = font(DV_B, 10)
    for i, (px_, py_) in enumerate(disp):
        px_ = max(x0 + 13, min(x1 - 13, px_))
        py_ = max(y0 + 13, min(y1 - 13, py_))
        d.ellipse([px_ - 11, py_ - 11, px_ + 11, py_ + 11], fill=CHIP_BG, outline=AMBER, width=2)
        label = str(i + 1)
        d.text((px_ - tw(d, label, f_pin) / 2, py_ - 6), label, font=f_pin, fill=(255, 214, 130))
    cap = "THE SUN'S PATH TODAY \u00b7 NUMBERED PINS ARE THE 14 DISPATCHES \u00b7 DOTS ARE THE BRIEFS"
    f_cap = font(NF + COND_B, 10)
    cw_ = tracked_w(d, cap, f_cap, 1) + 16
    d.rounded_rectangle([x0 + 8, y1 - 24, x0 + 8 + cw_, y1 - 6], 6, fill=(8, 14, 28, 200))
    tracked(d, (x0 + 16, y1 - 21), cap, f_cap, (196, 206, 228), 1)
    return y1


def num_chip(d, x, y, num, big=False):
    label = str(num)
    f = font(DV_B, 12 if big else 11)
    chw = tw(d, label, f) + 13
    d.rounded_rectangle([x, y, x + chw, y + 19], 6, fill=(8, 14, 28, 225), outline=AMBER, width=1)
    d.text((x + (chw - tw(d, label, f)) / 2, y + 4), label, font=f, fill=(255, 214, 130))


def draw_hero(img, x, y, dp, num):
    h, hl, sm = hero_card_h(dp)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x, y, x + HERO_W, y + h], 8, fill=CARD, outline=CARD_LINE, width=1)
    img.paste(crop_art(dp["panel"], HERO_W - 4, HERO_ART), (x + 2, y + 2))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x, y, x + HERO_W, y + h], 8, outline=CARD_LINE, width=1)
    num_chip(d, x + 8, y + 7, num, big=True)
    # place chip on the art, bottom-left
    pw = tracked_w(d, dp["place"], F_PLACE, 1) + 12
    pcy = y + 2 + HERO_ART - 21
    d.rounded_rectangle([x + 8, pcy, x + 8 + pw, pcy + 19], 6, fill=(8, 14, 28, 225))
    tracked(d, (x + 14, pcy + 3), dp["place"], F_PLACE, AMBER, 1)
    cy = y + 2 + HERO_ART + 2
    for ln in hl:
        d.text((x + 9, cy), ln, font=F_HERO_HL, fill=(238, 242, 250))
        cy += 24
    cy += 0
    for ln in sm:
        d.text((x + 9, cy), ln, font=F_SUM, fill=(198, 207, 226))
        cy += 16
    return h


def draw_std(img, x, y, dp, num):
    h, hl, sm = std_card_h(dp)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x, y, x + STD_W, y + h], 8, fill=CARD, outline=CARD_LINE, width=1)
    img.paste(crop_art(dp["panel"], STD_W - 4, STD_ART), (x + 2, y + 2))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x, y, x + STD_W, y + h], 8, outline=CARD_LINE, width=1)
    num_chip(d, x + 7, y + 7, num)
    # place chip on the art, top-right
    pw = tracked_w(d, dp["place"], F_CHIP_PLACE, 1) + 12
    d.rounded_rectangle([x + STD_W - 7 - pw, y + 7, x + STD_W - 7, y + 24], 6,
                        fill=(8, 14, 28, 225))
    tracked(d, (x + STD_W - 7 - pw + 6, y + 10), dp["place"], F_CHIP_PLACE, AMBER, 1)
    cy = y + 2 + STD_ART + 2
    for ln in hl:
        d.text((x + 9, cy), ln, font=F_STD_HL, fill=(238, 242, 250))
        cy += 20
    cy += 1
    for ln in sm:
        d.text((x + 9, cy), ln, font=F_SUM, fill=(198, 207, 226))
        cy += 14
    return h


def draw_wide(img, x, y, dp, num):
    h, hl, sm = wide_card_h(dp)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x, y, x + WIDE_W, y + h], 8, fill=CARD, outline=CARD_LINE, width=1)
    img.paste(crop_art(dp["panel"], WIDE_ART_W, h - 4), (x + 2, y + 2))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x, y, x + WIDE_W, y + h], 8, outline=CARD_LINE, width=1)
    num_chip(d, x + 7, y + 7, num)
    tx = x + WIDE_ART_W + 12
    cy = y + 8
    tracked(d, (tx, cy), dp["place"], F_PLACE, AMBER, 1)
    cy += 16
    for ln in hl:
        d.text((tx, cy), ln, font=F_STD_HL, fill=(238, 242, 250))
        cy += 20
    cy += 1
    for ln in sm:
        d.text((tx, cy), ln, font=F_SUM, fill=(198, 207, 226))
        cy += 15
    return h


# ---------------------------------------------------------------- logbook
def brief_lines(text):
    return wrap(PROBE, text, F_BRIEF, COL_W)


def solve_briefs(avail_h):
    kept = [list(leg) for leg in BRIEFS]
    dropped = []
    while True:
        heights = []
        for leg in kept:
            hh = sum(len(brief_lines(b)) * BRIEF_LEAD + BRIEF_GAP for b in leg)
            heights.append(hh - BRIEF_GAP if leg else 0)
        if max(heights) <= avail_h or sum(len(l) for l in kept) == 0:
            return kept, dropped, heights
        tallest = heights.index(max(heights))
        dropped.append(kept[tallest].pop())


def draw_logbook(img, y, kept):
    d = ImageDraw.Draw(img, "RGBA")
    leg_names = ["FIRST LIGHT \u2014 ASIA-PACIFIC", "MIDDAY \u2014 EUROPE, AFRICA, MIDEAST",
                 "DUSK \u2014 THE AMERICAS"]
    for ci, leg in enumerate(kept):
        cx = MX + ci * (COL_W + 16)
        tracked(d, (cx, y), leg_names[ci], F_SEC, AMBER, 1)
        cy = y + 20
        d.line([(cx, cy - 4), (cx + COL_W, cy - 4)], fill=CARD_LINE, width=1)
        for b in leg:
            for ln in brief_lines(b):
                d.text((cx, cy), ln, font=F_BRIEF, fill=(186, 196, 218))
                cy += BRIEF_LEAD
            cy += BRIEF_GAP


# ---------------------------------------------------------------- bottom zone
def stat_widths():
    """Column widths proportional to measured numeral/caption widths."""
    raw = []
    for num, cap in STATS:
        raw.append(max(tw(PROBE, num, F_NUM), tw(PROBE, cap, F_CAP)) + 16)
    scale = CW / sum(raw)
    return [r * scale for r in raw]


def bottom_zone_h():
    claim_lines = len(wrap(PROBE, CLAIM, F_CLAIM, CW))
    return 64 + 25 + claim_lines * 16   # stats + datecheck + claim


def draw_bottom(img, y):
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(MX, y), (MX + 150, y)], fill=AMBER, width=2)
    d.line([(MX + 150, y), (W - MX, y)], fill=CARD_LINE, width=1)
    tracked(d, (MX + 162, y - 6), "THE DAY IN NUMBERS", F_SEC, MUTED, 2)
    widths = stat_widths()
    cx = float(MX)
    for i, ((num, cap), wdt) in enumerate(zip(STATS, widths)):
        d.text((cx, y + 6), num, font=F_NUM, fill=AMBER)
        lines = wrap(d, cap, F_CAP, wdt - 10)
        assert len(lines) == 1, ("stat caption wraps", cap, lines)
        d.text((cx, y + 45), cap, font=F_CAP, fill=MUTED)
        if i:
            d.line([(cx - 9, y + 10), (cx - 9, y + 42)], fill=CARD_LINE, width=1)
        cx += wdt
    y += 64
    d.rounded_rectangle([MX, y, W - MX, y + 22], 6, fill=(13, 22, 42),
                        outline=(70, 60, 30), width=1)
    wch = tracked_w(d, DATECHECK, F_DC, 0)
    tracked(d, (MX + (CW - wch) / 2, y + 4), DATECHECK, F_DC, (226, 190, 110), 0)
    y += 25
    for ln in wrap(d, CLAIM, F_CLAIM, CW):
        d.text((MX + (CW - tw(d, ln, F_CLAIM)) / 2, y), ln, font=F_CLAIM, fill=(214, 221, 236))
        y += 16
    return y


# ---------------------------------------------------------------- build
def build():
    heroes = [dp for dp in DISPATCHES if dp["hero"]]
    stds = [dp for dp in DISPATCHES if not dp["hero"] and not dp["wide"]]
    wides = [dp for dp in DISPATCHES if dp["wide"]]
    hero_h = max(hero_card_h(dp)[0] for dp in heroes)
    row1_h = max(std_card_h(dp)[0] for dp in stds[:4])
    row2_h = max(std_card_h(dp)[0] for dp in stds[4:])
    wide_h = max(wide_card_h(dp)[0] for dp in wides)
    GAP = 5
    disp_h = hero_h + GAP + row1_h + GAP + row2_h + GAP + wide_h
    bot_h = bottom_zone_h()

    # census <-> logbook space are mutually dependent; iterate to a fixed point
    census = len(DISPATCHES) + sum(len(l) for l in BRIEFS)
    for _ in range(3):
        kept_probe, dropped_probe, heights = solve_briefs(10 ** 6)  # placeholder
        # measure top zone with the current census guess
        probe_img = background()
        y_top = masthead(probe_img, census, region_line(
            [dp["story"] for dp in DISPATCHES] +
            [s for leg in BRIEF_STORIES for s in leg]))
        y_top += 6
        map_top = y_top
        y_after_map = map_top + MAP_H + 8
        lb_top = y_after_map + disp_h + 6
        bot_top = H - 10 - bot_h
        # logbook stack above the briefs: section header offset 20 + leg
        # header/rule offset 20, then the briefs themselves, 3px safety
        avail = bot_top - lb_top - 40 - 3
        kept, dropped, heights = solve_briefs(avail)
        kept_stories = []
        for ci, leg in enumerate(kept):
            kept_stories += BRIEF_STORIES[ci][:len(leg)]
        new_census = len(DISPATCHES) + sum(len(l) for l in kept)
        if new_census == census:
            break
        census = new_census
    else:
        raise RuntimeError("census did not converge")

    rline = region_line([dp["story"] for dp in DISPATCHES] + kept_stories)
    img = background()
    y = masthead(img, census, rline)
    y += 6
    draw_map(img, y, [BRIEF_STORIES[ci][:len(kept[ci])] for ci in range(3)])
    y += MAP_H + 8
    num = {id(dp): i + 1 for i, dp in enumerate(DISPATCHES)}
    for i, dp in enumerate(heroes):
        draw_hero(img, MX + i * (HERO_W + 11), y, dp, num[id(dp)])
    y += hero_h + GAP
    for i, dp in enumerate(stds[:4]):
        draw_std(img, MX + i * (STD_W + 9), y, dp, num[id(dp)])
    y += row1_h + GAP
    for i, dp in enumerate(stds[4:]):
        draw_std(img, MX + i * (STD_W + 9), y, dp, num[id(dp)])
    y += row2_h + GAP
    for i, dp in enumerate(wides):
        draw_wide(img, MX + i * (WIDE_W + 11), y, dp, num[id(dp)])
    y += wide_h + 6
    d = ImageDraw.Draw(img, "RGBA")
    tracked(d, (MX, y), "ALSO TODAY \u2014 THE LOGBOOK", F_SEC, (210, 219, 238), 2)
    note = "one complete clause each, sources in brackets"
    d.text((W - MX - tw(d, note, F_SEC_IT), y), note, font=F_SEC_IT, fill=FAINT)
    draw_logbook(img, y + 20, kept)
    bot_end = draw_bottom(img, H - 10 - bot_h)
    report = dict(census=census, briefs_kept=sum(len(l) for l in kept),
                  briefs_dropped=[b.split(" \u2014 ")[0] for b in dropped],
                  logbook_heights=heights, logbook_avail=avail,
                  hero_h=hero_h, row1_h=row1_h, row2_h=row2_h, wide_h=wide_h,
                  logbook_top=lb_top, bottom_top=H - 10 - bot_h, bottom_end=bot_end)
    return img, report


def encode(img):
    data, q = None, None
    for q in (88, 86, 84, 82, 80):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, subsampling=1)
        data = buf.getvalue()
        if len(data) <= 382_000:
            break
    return data, q


def main():
    all_copy = ([dp["headline"] + dp["full_summary"] for dp in DISPATCHES] +
                [b for leg in BRIEFS for b in leg] + [DATECHECK, CLAIM] +
                [n + c for n, c in STATS])
    for s in all_copy:
        assert "\u2026" not in s and "..." not in s, "ellipsis in copy: %r" % s
    img1, report = build()
    img2, _ = build()
    d1, q = encode(img1)
    d2, _ = encode(img2)
    assert d1 == d2, "non-deterministic build"
    with open(os.path.join(HERE, "entry-variant-b.png"), "wb") as fh:
        fh.write(d1)
    img1.resize((300, 300), Image.LANCZOS).save(os.path.join(HERE, "entry-variant-b-300.png"))
    img1.crop((0, 330, W, 1024)).save(os.path.join(HERE, "crop-cards.png"))
    img1.crop((0, 0, W, 470)).save(os.path.join(HERE, "crop-top.png"))
    report.update(bytes=len(d1), jpeg_quality=q,
                  sha256=hashlib.sha256(d1).hexdigest(), first_bytes=d1[:2].hex())
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
