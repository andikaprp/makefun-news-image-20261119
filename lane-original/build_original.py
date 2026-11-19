#!/usr/bin/env python3
"""ONE DAY ON EARTH - original design for the make.fun news-image entry.

Concept: "One day, around the sun." A midnight-blue page: a luminous
world map carries every story as a numbered pin, ordered westward the
way the day itself travelled. A glowing amber sun-path arc sweeps from
Shenzhen (dawn) to Pasadena (dusk). Below, the 11 illustrated stories
run as a filmstrip of postcards, and the rest fill a three-leg logbook
(First Light / Midday / Dusk) in the order the sun reached them.

Deterministic: seeded RNG only, no clock, no network. Same inputs ->
same bytes. Output is JPEG bytes in a .png name (bounty allows either,
detected by magic bytes), 1024x1024, under 1 MiB.
"""
import io
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STORIES_PATH = os.path.join(ROOT, "lane-stories", "stories.json")
LAND_PATH = os.path.join(ROOT, "lane-map", "land.json")
ART_DIR = os.path.join(ROOT, "lane-art-v4")
OUT_PATH = os.path.join(HERE, "entry-original-draft.png")

W = 1024
MX = 34
CW = W - 2 * MX  # 956

# ---- palette (ours: midnight observatory) ----
BG_TOP = (9, 16, 32)
BG_BOT = (13, 25, 48)
INK = (14, 22, 38)
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
PIN_FILL = (36, 56, 96)
PIN_RING = (140, 166, 217)
PIN_TEXT = (216, 227, 248)
CREAM = (237, 239, 245)

NOTO = "/usr/share/fonts/truetype/noto"
F_SERIF_BLACK = f"{NOTO}/NotoSerif-Black.ttf"
F_SERIF_BOLD = f"{NOTO}/NotoSerif-Bold.ttf"
F_SERIF_IT = f"{NOTO}/NotoSerif-Italic.ttf"
F_SANS_BOLD = f"{NOTO}/NotoSans-Bold.ttf"
F_SANS = f"{NOTO}/NotoSans-Regular.ttf"
F_COND = f"{NOTO}/NotoSans-Condensed.ttf"
F_COND_BOLD = f"{NOTO}/NotoSans-CondensedBold.ttf"
F_COND_MED = f"{NOTO}/NotoSans-CondensedMedium.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def draw_tracked(draw, xy, text, fnt, fill, tracking=2):
    """Draw letter-spaced text; returns total width."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += tw(draw, ch, fnt) + tracking
    return x - tracking - xy[0]


def tracked_width(draw, text, fnt, tracking=2):
    return sum(tw(draw, ch, fnt) for ch in text) + tracking * (len(text) - 1)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap by pixel width. Returns list of lines."""
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
def load_stories():
    with open(STORIES_PATH) as f:
        return json.load(f)


# Featured (postcard) stories: story index in stories.json -> panel file.
# Ordered westward by longitude: the order the sun met them.
FEATURED = [
    (0, "panel-summit.png"),          # Shenzhen, China - APEC summit (HERO)
    (2, "panel-cyclone.png"),         # Odisha, India - Cyclone Akvan
    (8, "panel-crimean-bridge.png"),  # Kerch Bridge, Crimea
    (16, "panel-gaza-tanks.png"),     # Gaza City, Gaza
    (42, "panel-egypt-flights.png"),  # Cairo, Egypt
    (10, "panel-eu-loan.png"),        # Brussels, Belgium
    (31, "panel-venezuela-deal.png"), # Caracas, Venezuela
    (27, "panel-vangogh.png"),        # New York, USA
    (26, "panel-anthropic.png"),      # New York, USA
    (28, "panel-gta.png"),            # New York, USA
    (30, "panel-voyager.png"),        # Pasadena, USA - Voyager 1
]
DROP = {4, 15, 25, 34, 37}  # Jharkhand accident, ESA opinion, vague US outages,
# Paraguay bank-deadline notice, Olkaria plant announcement (weakest five)

LEGS = [
    ("LEG ONE", "FIRST LIGHT", "ASIA & THE PACIFIC", [1, 3, 5, 6, 7, 45, 46, 47, 48]),
    ("LEG TWO", "MIDDAY", "EUROPE · AFRICA · THE MIDDLE EAST",
     [9, 11, 12, 13, 14, 17, 18, 19, 20, 21, 22, 36, 38, 39, 40, 41, 43, 44]),
    ("LEG THREE", "DUSK", "THE AMERICAS", [23, 24, 29, 32, 33, 35]),
]

NUM_WORDS = {44: "Forty-four", 45: "Forty-five", 46: "Forty-six", 47: "Forty-seven",
             48: "Forty-eight", 49: "Forty-nine"}


def build_numbering(stories):
    """Assign display numbers: featured 1-11 (sun order), logbook 12+ (leg order)."""
    num = {}
    for i, (idx, _panel) in enumerate(FEATURED):
        num[idx] = i + 1
    n = len(FEATURED)
    for _leg, _name, _sub, idxs in LEGS:
        for idx in idxs:
            n += 1
            num[idx] = n
    used = [i for i in range(len(stories)) if i not in DROP]
    assert sorted(num.keys()) == sorted(used), "numbering must cover exactly the used stories"
    return num


# ---------------------------------------------------------------- background
def make_background():
    grad = Image.new("RGB", (1, W))
    for y in range(W):
        t = y / (W - 1)
        grad.putpixel((0, y), tuple(int(BG_TOP[c] + (BG_BOT[c] - BG_TOP[c]) * t) for c in range(3)))
    img = grad.resize((W, W))
    # deterministic starfield
    rng = random.Random(20261119)
    stars = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(300):
        x, y = rng.uniform(0, W), rng.uniform(0, W)
        r = rng.choice([0.6, 0.8, 1.0, 1.3])
        a = rng.randint(22, 80)
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(220, 230, 250, a))
    # a few brighter stars with a cross sparkle
    for _ in range(14):
        x, y = rng.uniform(20, W - 20), rng.uniform(10, 700)
        sd.line([(x - 4, y), (x + 4, y)], fill=(230, 238, 255, 60), width=1)
        sd.line([(x, y - 4), (x, y + 4)], fill=(230, 238, 255, 60), width=1)
    img.paste(Image.alpha_composite(img.convert("RGBA"), stars).convert("RGB"), (0, 0))
    return img


# ---------------------------------------------------------------- map
LAT_TOP, LAT_BOT = 62.0, -45.0
MAP_BOX = (MX, 152, W - MX, 398)


def project(lat, lon, box=MAP_BOX):
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / 360.0, (y1 - y0) / (LAT_TOP - LAT_BOT))
    ox = x0 + ((x1 - x0) - 360.0 * scale) / 2.0
    oy = y0 + ((y1 - y0) - (LAT_TOP - LAT_BOT) * scale) / 2.0
    return (ox + (lon + 180.0) * scale, oy + (LAT_TOP - lat) * scale)


def draw_map(img, stories, num):
    x0, y0, x1, y1 = MAP_BOX
    bw, bh = x1 - x0, y1 - y0
    box = (0, 0, bw, bh)
    layer = Image.new("RGB", (bw, bh), MAP_FILL)
    with open(LAND_PATH) as f:
        polys = json.load(f)["polygons"]

    def pts(ring):
        return [project(lat, lon, box) for lon, lat in ring]

    # luminous glow under the landmasses (clipped to the layer)
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
    # paste through a rounded mask so nothing spills into the masthead
    mask = Image.new("L", (bw, bh), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, bw, bh), radius=14, fill=255)
    img.paste(layer, (x0, y0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(MAP_BOX, radius=14, outline=MAP_EDGE, width=1)
    return d


def bezier(p0, p1, p2, t):
    mt = 1 - t
    return (mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
            mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1])


def draw_sun_path(img, start, end):
    """Glowing amber arc from dawn (start) to dusk (end), arrow at the end."""
    mid = ((start[0] + end[0]) / 2.0, min(start[1], end[1]) - 92)
    pts = [bezier(start, mid, end, t / 140.0) for t in range(141)]
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for width, alpha in [(15, 30), (9, 52), (4, 100), (2, 180)]:
        ld.line(pts, fill=AMBER + (alpha,), width=width, joint="curve")
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    # arrowhead at the dusk end, along the tangent
    t_ang = math.atan2(pts[-1][1] - pts[-6][1], pts[-1][0] - pts[-6][0])
    ex, ey = pts[-1]
    ah = 11
    left = (ex - ah * math.cos(t_ang - 0.42), ey - ah * math.sin(t_ang - 0.42))
    right = (ex - ah * math.cos(t_ang + 0.42), ey - ah * math.sin(t_ang + 0.42))
    d.polygon([(ex, ey), left, right], fill=AMBER)
    # sun disc at dawn end, with rays
    sx, sy = start[0] + 4, start[1] - 16
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([sx - 26, sy - 26, sx + 26, sy + 26], fill=AMBER + (70,))
    img.paste(Image.alpha_composite(img.convert("RGBA"),
                                     glow.filter(ImageFilter.GaussianBlur(8))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        d.line([(sx + 15 * math.cos(a), sy + 15 * math.sin(a)),
                (sx + 20 * math.cos(a), sy + 20 * math.sin(a))], fill=AMBER, width=2)
    d.ellipse([sx - 11, sy - 11, sx + 11, sy + 11], fill=AMBER, outline=(255, 214, 130), width=2)
    # arc stage labels (MIDDAY sits under the arc so it clears the panel edge)
    f_lab = font(F_COND_BOLD, 12)
    for t, label, dy in [(0.16, "DAWN", -26), (0.45, "MIDDAY", 15), (0.86, "DUSK", -26)]:
        px, py = bezier(start, mid, end, t)
        wlab = tracked_width(d, label, f_lab, 3)
        draw_tracked(d, (px - wlab / 2, py + dy), label, f_lab, AMBER, 3)
    return d


def relax_pins(pins, box=MAP_BOX):
    """Deterministic de-overlap: pins = list of dicts with x, y, r."""
    x0, y0, x1, y1 = box
    for _ in range(90):
        moved = False
        for i in range(len(pins)):
            for j in range(i + 1, len(pins)):
                a, b = pins[i], pins[j]
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                dist = math.hypot(dx, dy)
                need = a["r"] + b["r"] + 1.5
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
            p["y"] = min(max(p["y"], y0 + p["r"] + 2), y1 - p["r"] - 2)
        if not moved:
            break
    return pins


def draw_pins(img, stories, num):
    d = ImageDraw.Draw(img)
    pins = []
    for idx, story in enumerate(stories):
        if idx in DROP:
            continue
        x, y = project(story["lat"], story["lon"])
        featured = num[idx] <= len(FEATURED)
        pins.append({"idx": idx, "x": x, "y": y, "r": 11 if featured else 8,
                     "n": num[idx], "featured": featured})
    relax_pins(pins)
    # logbook pins first, featured on top
    for p in sorted(pins, key=lambda p: p["featured"]):
        x, y, r = p["x"], p["y"], p["r"]
        if p["featured"]:
            d.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], fill=AMBER + (0,) if False else (24, 32, 52))
            d.ellipse([x - r, y - r, x + r, y + r], fill=AMBER, outline=STAR, width=2)
            fnt = font(F_SANS_BOLD, 11 if p["n"] < 10 else 10)
            fill = (20, 14, 4)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=PIN_FILL, outline=PIN_RING, width=1)
            fnt = font(F_SANS_BOLD, 8)
            fill = PIN_TEXT
        label = str(p["n"])
        bb = d.textbbox((0, 0), label, font=fnt)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]),
               label, font=fnt, fill=fill)
    return {p["idx"]: (p["x"], p["y"]) for p in pins}


# ---------------------------------------------------------------- masthead
def draw_masthead(img, total):
    d = ImageDraw.Draw(img)
    f_eye = font(F_COND_BOLD, 13)
    # small amber diamond bullet (drawn, not a glyph)
    d.polygon([(MX + 4, 24), (MX + 9, 30), (MX + 4, 36), (MX - 1, 30)], fill=AMBER)
    left = "FOLLOW THE SUN — ONE ROTATION OF THE PLANET"
    draw_tracked(d, (MX + 16, 24), left, f_eye, AMBER, 2)
    right = f"{total} STORIES PINNED TO THE MAP"
    rw = tracked_width(d, right, f_eye, 2)
    draw_tracked(d, (W - MX - rw, 24), right, f_eye, MUTED, 2)

    f_title = font(F_SERIF_BLACK, 46)
    d.text((MX - 2, 44), "ONE DAY ON EARTH", font=f_title, fill=STAR)

    # standfirst sits beside the title, clear of the date line
    f_stand = font(F_SERIF_IT, 15)
    stand = (f"{NUM_WORDS[total]} stories from a single turn of the Earth — read westward, "
             "the way the day itself travelled, from a summit in Shenzhen to a "
             "probe one light-day from home.")
    lines = wrap(d, stand, f_stand, 336)
    for i, ln in enumerate(lines[:4]):
        d.text((654, 47 + i * 20), ln, font=f_stand, fill=(205, 214, 232))

    f_date = font(F_SERIF_BLACK, 37)
    draw_tracked(d, (MX, 102), "19 NOVEMBER 2026", f_date, AMBER, 1)
    f_day = font(F_COND_BOLD, 14)
    dw = tracked_width(d, "19 NOVEMBER 2026", f_date, 1)
    draw_tracked(d, (MX + dw + 14, 122), "· THURSDAY", f_day, MUTED, 2)

    d.line([(MX, 144), (W - MX, 144)], fill=AMBER_DEEP, width=1)
    d.line([(MX, 147), (W - MX, 147)], fill=(60, 74, 104), width=1)
    return d


# ---------------------------------------------------------------- postcards
PC_Y0, PC_Y1 = 434, 580
PC_HEAD_Y = 412


def draw_postcards(img, stories, num):
    d = ImageDraw.Draw(img)
    f_head = font(F_COND_BOLD, 13)
    draw_tracked(d, (MX, PC_HEAD_Y), "POSTCARDS FROM THE DAY", f_head, AMBER, 2)
    f_sub = font(F_SERIF_IT, 13)
    sub = "eleven frames, in the order the sun met them"
    d.text((W - MX - tw(d, sub, f_sub), PC_HEAD_Y + 1), sub, font=f_sub, fill=MUTED)

    # film band
    d.rounded_rectangle((MX, PC_Y0, W - MX, PC_Y1), radius=10, fill=(7, 13, 26),
                        outline=(40, 58, 94), width=1)
    # sprocket holes
    for sx in range(MX + 14, W - MX - 10, 26):
        for sy in (PC_Y0 + 6, PC_Y1 - 13):
            d.rounded_rectangle((sx, sy, sx + 12, sy + 7), radius=2, fill=(30, 46, 78))

    fw = 82
    gap = (CW - 11 * fw) / 10.0
    fy = PC_Y0 + 22
    fh_img = 48
    report = []
    for i, (idx, panel) in enumerate(FEATURED):
        story = stories[idx]
        fx = MX + i * (fw + gap)
        # shadow + cream photo border
        d.rounded_rectangle((fx + 2, fy + 3, fx + fw + 2, fy + fh_img + 4), radius=3, fill=(3, 6, 12))
        d.rectangle((fx - 2, fy - 2, fx + fw + 2, fy + fh_img + 2), fill=CREAM)
        art = Image.open(os.path.join(ART_DIR, panel)).convert("RGB")
        # centre-crop to fw x fh_img aspect
        target = fw / fh_img
        aw, ah = art.size
        if aw / ah > target:
            nw = int(ah * target)
            art = art.crop(((aw - nw) // 2, 0, (aw - nw) // 2 + nw, ah))
        else:
            nh = int(aw / target)
            art = art.crop((0, (ah - nh) // 2, aw, (ah - nh) // 2 + nh))
        art = art.resize((fw, fh_img))
        img.paste(art, (int(fx), fy))
        d = ImageDraw.Draw(img)
        # number chip
        n = num[idx]
        d.rectangle((fx - 2, fy - 2, fx + 15, fy + 13), fill=AMBER)
        f_chip = font(F_SANS_BOLD, 10)
        bb = d.textbbox((0, 0), str(n), font=f_chip)
        d.text((fx - 2 + (17 - (bb[2] - bb[0])) / 2 - bb[0], fy - 2 + (15 - (bb[3] - bb[1])) / 2 - bb[1]),
               str(n), font=f_chip, fill=(20, 14, 4))
        # caption: place, then headline
        place = story["place"].split(",")[0].upper()
        f_pl = font(F_COND_BOLD, 11)
        while tw(d, place, f_pl) > fw + 2 and len(place) > 4:
            place = place[:-1]
        f_hl = font(F_COND_MED, 11)
        lines = wrap(d, story["headline"], f_hl, fw + 6)
        report.append((n, len(lines)))
        # a 5-line caption (Voyager) starts a touch higher so it clears the band edge
        cap_dy = -5 if len(lines) > 4 else 0
        d.text((fx, fy + fh_img + 7 + cap_dy), place, font=f_pl, fill=AMBER)
        for li, ln in enumerate(lines[:5]):
            d.text((fx, fy + fh_img + 22 + cap_dy + li * 11.5), ln, font=f_hl, fill=(214, 221, 236))
    return report


# ---------------------------------------------------------------- logbook
LB_HEAD_Y = 590
LB_Y0 = 612
LB_Y1 = 966
ENTRY_LH = 13.5
ENTRY_GAP = 2
LEG_H = 22


def entry_lines(d, story, max_w, with_place=True):
    f = font(F_COND, 12)
    place = story["place"].split(",")[0]
    if with_place:
        text = f"{place} — {story['headline']} ({story['source']})"
    else:
        text = f"{story['headline']} ({story['source']})"
    return wrap(d, text, f, max_w), f


def draw_logbook(img, stories, num):
    d = ImageDraw.Draw(img)
    f_head = font(F_COND_BOLD, 13)
    draw_tracked(d, (MX, LB_HEAD_Y), "THE LOGBOOK", f_head, AMBER, 2)
    f_sub = font(F_SERIF_IT, 13)
    sub = "everything else the day brought, logged in sun order"
    d.text((W - MX - tw(d, sub, f_sub), LB_HEAD_Y + 1), sub, font=f_sub, fill=MUTED)

    ncols = 3
    col_gap = 20
    col_w = (CW - (ncols - 1) * col_gap) / ncols
    text_w = col_w - 26
    f_entry = font(F_COND, 12)
    f_num = font(F_COND_BOLD, 12)
    f_leg = font(F_COND_BOLD, 11)

    # build item list: ("leg", leg_tuple, LEG_H) or ("entry", idx, lines, h)
    items = []
    overflow = []
    for leg in LEGS:
        items.append(("leg", leg, LEG_H))
        for idx in leg[3]:
            lines, _ = entry_lines(d, stories[idx], text_w)
            if len(lines) > 2:
                lines, _ = entry_lines(d, stories[idx], text_w, with_place=False)
            if len(lines) > 2:
                overflow.append(num[idx])
                lines = lines[:2]
            items.append(("entry", idx, lines, ENTRY_LH * len(lines) + ENTRY_GAP))

    def item_h(it):
        return it[2] if it[0] == "leg" else it[3]

    # choose two split points minimising the tallest column;
    # a split may not land immediately after a leg header
    prefix = [0]
    for it in items:
        prefix.append(prefix[-1] + item_h(it))
    total_h = prefix[-1]
    best = None
    for s1 in range(1, len(items) - 1):
        if items[s1 - 1][0] == "leg":
            continue
        for s2 in range(s1 + 1, len(items)):
            if items[s2 - 1][0] == "leg":
                continue
            hs = (prefix[s1], prefix[s2] - prefix[s1], total_h - prefix[s2])
            key = (max(hs), max(hs) - min(hs))
            if best is None or key < best[0]:
                best = (key, s1, s2, hs)
    _key, s1, s2, col_heights = best
    cols = [items[:s1], items[s1:s2], items[s2:]]

    for ci, col in enumerate(cols):
        x = MX + ci * (col_w + col_gap)
        y = LB_Y0
        for it in col:
            if it[0] == "leg":
                _tag, (roman, name, sub, _idxs) = it[0], it[1]
                label = f"{roman} · {name} — {sub}"
                # shrink tracking if the long leg-two label overflows the column
                tr = 1
                if tracked_width(d, label, f_leg, tr) > col_w:
                    tr = 0
                draw_tracked(d, (x, y + 2), label, f_leg, TEAL, tr)
                d.line([(x, y + 17), (x + col_w, y + 17)], fill=(52, 68, 102), width=1)
                y += LEG_H
            else:
                _tag, idx, lines, h = it
                n = num[idx]
                d.text((x, y), str(n), font=f_num, fill=AMBER)
                for li, ln in enumerate(lines):
                    d.text((x + 26, y + li * ENTRY_LH), ln, font=f_entry, fill=(203, 212, 230))
                y += h
    # rules between columns
    for ci in (1, 2):
        rx = MX + ci * col_w + (ci - 1) * col_gap + col_gap / 2
        d.line([(rx, LB_Y0 + 2), (rx, LB_Y1 - 4)], fill=(44, 60, 92), width=1)
    return {"splits": [s1, s2], "col_heights": list(col_heights),
            "overflow_entries": overflow, "total_items_h": total_h,
            "fits": LB_Y0 + max(col_heights) <= LB_Y1}


# ---------------------------------------------------------------- footer
def draw_footer(img):
    d = ImageDraw.Draw(img)
    d.line([(MX, 972), (W - MX, 972)], fill=(60, 74, 104), width=1)
    f = font(F_COND, 11.5) if False else font(F_COND, 12)
    note = ("LEFT ON THE CUTTING-ROOM FLOOR — reports we could not pin to 19 November: a North Korean "
            "missile launch (the day was disputed), Prague's media protest (held 15 Nov), a Spanish general "
            "strike dated Wednesday, and an obituary with no dateline we could trust.")
    lines = wrap(d, note, f, CW - 4)
    for i, ln in enumerate(lines[:2]):
        d.text((MX, 980 + i * 14), ln, font=f, fill=FAINT)
    return len(lines)


def draw_map_captions(img):
    d = ImageDraw.Draw(img)
    f = font(F_COND_BOLD, 11)
    cap = "EVERY PIN A STORY — NUMBERED IN THE ORDER THE SUN REACHED THEM"
    cap_w = tracked_width(d, cap, f, 1)
    # dark chips keep the captions legible where they cross land
    d.rounded_rectangle((MAP_BOX[0] + 6, MAP_BOX[3] - 24, MAP_BOX[0] + 18 + cap_w, MAP_BOX[3] - 2),
                        radius=4, fill=(8, 15, 30))
    draw_tracked(d, (MAP_BOX[0] + 12, MAP_BOX[3] - 20), cap, f, (150, 168, 200), 1)
    credit = "WORLD OUTLINE: NATURAL EARTH"
    cw_ = tracked_width(d, credit, f, 1)
    d.rounded_rectangle((MAP_BOX[2] - 18 - cw_, MAP_BOX[3] - 24, MAP_BOX[2] - 6, MAP_BOX[3] - 2),
                        radius=4, fill=(8, 15, 30))
    draw_tracked(d, (MAP_BOX[2] - 12 - cw_, MAP_BOX[3] - 20), credit, f, (110, 128, 162), 1)


# ---------------------------------------------------------------- main
def render():
    stories = load_stories()
    num = build_numbering(stories)
    total = len(num)
    img = make_background()
    draw_masthead(img, total)
    draw_map(img, stories, num)
    # sun path between hero pin (Shenzhen) and last pin (Pasadena), pre-relaxation coords
    start = project(stories[0]["lat"], stories[0]["lon"])
    end = project(stories[30]["lat"], stories[30]["lon"])
    draw_sun_path(img, start, end)
    pin_xy = draw_pins(img, stories, num)
    draw_map_captions(img)
    pc_report = draw_postcards(img, stories, num)
    lb_report = draw_logbook(img, stories, num)
    foot_lines = draw_footer(img)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    data = buf.getvalue()
    return data, {
        "stories_used": total,
        "postcard_headline_lines": pc_report,
        "logbook": lb_report,
        "footer_lines": foot_lines,
        "bytes": len(data),
        "jpeg_magic": data[:2] == b"\xff\xd8",
    }


def main():
    data, report = render()
    data2, _ = render()
    report["deterministic"] = data == data2
    with open(OUT_PATH, "wb") as f:
        f.write(data)
    print(json.dumps(report, indent=2))
    print("wrote", OUT_PATH, len(data), "bytes")
    # thumbnail for the 256px readability test
    thumb = Image.open(io.BytesIO(data)).resize((256, 256))
    thumb.save(os.path.join(HERE, "entry-original-thumb256.png"))


if __name__ == "__main__":
    main()
