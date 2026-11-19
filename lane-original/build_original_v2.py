#!/usr/bin/env python3
"""ONE DAY ON EARTH - iteration 2 builder (make.fun news-image-20261119).

Same identity as v1 (midnight observatory, sun-path arc, sun-order
numbering, postcards grown into dispatches, three-leg logbook), rebuilt
around the UPGRADE-SPEC reading layer:
  - the DATE is the largest type on the page (>=72px, autofit)
  - 11 DISPATCHES with headline + a real summary sentence ending in the
    source (3 heroes ~311px wide, 8 standards ~232px)
  - THE DAY IN NUMBERS stat band (verified stats from the data file)
  - logbook entries carry a fact fragment after a dash
  - map demoted; numbered pins only for dispatches, dots for the logbook
  - contested stories framed as attributed claims (data contested flags)
  - date-check box with dated items + footer claim line

Geometry note (see ITERATION-2.md): the spec's simultaneous targets
(40 stories + 27% map + full dispatches at the type floors) exceed a
1024px page; this build prioritises completeness per story - the
spec's own central finding - over raw count.

Data: prefers lane-stories/stories-v2.json (enriched: summary + fact +
stats); falls back to stories.json (detail as summary) and says so.
Deterministic: seeded RNG only, no clock, no network. Output is JPEG
bytes in a .png name, 1024x1024, under 1 MiB.
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
STORIES_V1 = os.path.join(ROOT, "lane-stories", "stories.json")
LAND_PATH = os.path.join(ROOT, "lane-map", "land.json")
ART_DIR = os.path.join(ROOT, "lane-art-v4")
OUT_PATH = os.path.join(HERE, "entry-v2.png")
THUMB_PATH = os.path.join(HERE, "entry-v2-300.png")

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

NOTO = "/usr/share/fonts/truetype/noto"
F_SERIF_BLACK = f"{NOTO}/NotoSerif-Black.ttf"
F_SERIF_BOLD = f"{NOTO}/NotoSerif-Bold.ttf"
F_SERIF_IT = f"{NOTO}/NotoSerif-Italic.ttf"
F_SANS_BOLD = f"{NOTO}/NotoSans-Bold.ttf"
F_COND = f"{NOTO}/NotoSans-Condensed.ttf"
F_COND_BOLD = f"{NOTO}/NotoSans-CondensedBold.ttf"

REPORT = {"trims": [], "drops": [], "notes": []}


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


def trim_to_lines(draw, text, fnt, max_w, max_lines, tag):
    """Trim text (word boundary, ellipsis) until it wraps to <= max_lines."""
    if len(wrap(draw, text, fnt, max_w)) <= max_lines:
        return text
    orig = text
    words = text.split()
    while len(words) > 3:
        words = words[:-1]
        cand = " ".join(words).rstrip(",;:") + "…"
        if len(wrap(draw, cand, fnt, max_w)) <= max_lines:
            REPORT["trims"].append(f"{tag}: {len(orig)} -> {len(cand)} chars")
            return cand
    return text


def trim_clause(draw, text, fnt, max_w, max_lines, tag):
    """Prefer cutting a summary at a clause boundary before word-trimming."""
    if len(wrap(draw, text, fnt, max_w)) <= max_lines:
        return text
    for sep in ("; ", " — ", ", as ", ", while ", ", with ", ", after ", ", before "):
        idx = text.find(sep)
        if idx > 30:
            cand = text[:idx].rstrip(",;:") + "."
            if len(wrap(draw, cand, fnt, max_w)) <= max_lines:
                REPORT["trims"].append(f"{tag}: clause-cut {len(text)} -> {len(cand)} chars")
                return cand
    return trim_to_lines(draw, text, fnt, max_w, max_lines, tag)


# ---------------------------------------------------------------- data
def load_data():
    """Returns (stories, stats, enriched_bool)."""
    if os.path.exists(STORIES_V2):
        with open(STORIES_V2) as f:
            d = json.load(f)
        stories = []
        for s in d["stories"]:
            stories.append({
                "place": s["place"], "headline": s["headline"],
                "summary": s.get("summary") or s.get("detail") or "",
                "fact": s.get("fact") or "",
                "source": s["source"], "lat": s["lat"], "lon": s["lon"],
                "region": s.get("region", ""),
                "contested": bool(s.get("contested")),
                "contested_note": s.get("contested_note", ""),
                "cut": bool(s.get("cut_candidate")),
            })
        return stories, d.get("stats", []), True
    with open(STORIES_V1) as f:
        raw = json.load(f)
    stories = []
    for s in raw:
        stories.append({
            "place": s["place"], "headline": s["headline"],
            "summary": s.get("detail") or "", "fact": "",
            "source": s["source"], "lat": s["lat"], "lon": s["lon"],
            "region": s.get("region", ""), "contested": False,
            "contested_note": "", "cut": False,
        })
    stats = [
        {"value": "$190.4m", "label": "record auction price for a Van Gogh"},
        {"value": "47,000", "label": "people evacuated ahead of Cyclone Akvan"},
        {"value": "$1.4tn+", "label": "Anthropic's expected stock market valuation"},
        {"value": "1 light-day", "label": "Voyager 1's distance from Earth"},
        {"value": "€45bn", "label": "EU Ukraine loan proposed, tied to reparations"},
    ]
    REPORT["notes"].append("FALLBACK: stories-v2.json missing at render time; "
                           "used stories.json details as summaries, no fact fragments")
    return stories, stats, False


def find(stories, *keys):
    for s in stories:
        if all(k.lower() in s["headline"].lower() for k in keys):
            return s
    return None


# Dispatch definitions in SUN ORDER (westward, descending longitude):
# (headline keys, panel file, hero?)
DISPATCH_DEFS = [
    (("shake hands",), "panel-summit.png", True),            # Shenzhen summit
    (("Cyclone Akvan",), "panel-cyclone.png", True),         # Odisha evacuation
    (("Crimean Bridge",), "panel-crimean-bridge.png", False),
    (("ground operation beyond",), "panel-gaza-tanks.png", False),
    (("COP31",), "panel-cop31.png", False),
    (("Ukraine loan",), "panel-eu-loan.png", False),          # contested: proposal-framed
    (("World Court",), "panel-icj.png", True),               # ICJ Rohingya judgment
    (("Van Gogh",), "panel-vangogh.png", False),
    (("Anthropic",), "panel-anthropic.png", False),
    (("Grand Theft Auto",), "panel-gta.png", False),
    (("Voyager",), "panel-voyager.png", False),              # contested: JPL anchor appended
]

# Logbook drop priority (first = dropped first when space runs out)
DROP_KEYS = ["outages", "second arrest", "helicopter flew", "pull back from Bab",
             "sanctions three entities", "entrepreneur charged", "fourth weekend of protests",
             "senators warn", "reserves judgment", "Cocaine and millions",
             "targets Modi", "loan package of over"]


def leg_of(story):
    if story["region"] in ("asia", "oceania"):
        return 0
    if story["region"] in ("europe", "africa", "middle-east"):
        return 1
    return 2


LEGS = [
    ("LEG ONE", "FIRST LIGHT", "ASIA & THE PACIFIC"),
    ("LEG TWO", "MIDDAY", "EUROPE · AFRICA · THE MIDDLE EAST"),
    ("LEG THREE", "DUSK", "THE AMERICAS"),
]


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
def draw_masthead(img, total, n_regions):
    d = ImageDraw.Draw(img)
    f_eye = font(F_COND_BOLD, 13)
    d.polygon([(MX + 4, 22), (MX + 9, 28), (MX + 4, 34), (MX - 1, 28)], fill=AMBER)
    left = "ONE DAY ON EARTH — FOLLOW THE SUN · ONE ROTATION OF THE PLANET"
    draw_tracked(d, (MX + 16, 21), left, f_eye, AMBER, 2)
    right = f"THURSDAY · {total} STORIES · {n_regions} REGIONS · ONE PAGE"
    rw = tracked_width(d, right, f_eye, 2)
    if MX + 16 + tracked_width(d, left, f_eye, 2) + 20 > W - MX - rw:
        right = f"THURSDAY · {total} STORIES · ONE PAGE"
        rw = tracked_width(d, right, f_eye, 2)
    draw_tracked(d, (W - MX - rw, 21), right, f_eye, MUTED, 2)

    # THE DATE - largest type on the page, autofit with a hard floor of 72
    date_text = "19 NOVEMBER 2026"
    size = 92
    while size > 72 and tw(d, date_text, font(F_SERIF_BLACK, size)) > CW:
        size -= 2
    f_date = font(F_SERIF_BLACK, size)
    d.text((MX - 2, 36), date_text, font=f_date, fill=AMBER)

    f_stand = font(F_SERIF_IT, 14)
    stand = (f"{total} stories from a single turn of the planet — read westward, "
             f"the way the day travelled.")
    stand = trim_to_lines(d, stand, f_stand, CW, 1, "standfirst")
    d.text((MX, 42 + size), stand, font=f_stand, fill=(205, 214, 232))
    d.line([(MX, 156), (W - MX, 156)], fill=AMBER_DEEP, width=1)
    d.line([(MX, 159), (W - MX, 159)], fill=(60, 74, 104), width=1)
    return {"date_size": size, "masthead_bottom": 162}


# ---------------------------------------------------------------- stats
def draw_stats(img, stats):
    """THE DAY IN NUMBERS - amber numerals on midnight along a sun rule.
    Zone: header 168, rule 182, numerals 188, one-line captions below."""
    d = ImageDraw.Draw(img)
    f_head = font(F_COND_BOLD, 12)
    draw_tracked(d, (MX, 168), "THE DAY IN NUMBERS", f_head, TEAL, 2)
    stats = list(stats)

    def fits(items):
        col_w = CW / len(items)
        for it in items:
            size = 36
            while size > 34 and tw(d, it["value"], font(F_SERIF_BLACK, size)) > col_w - 10:
                size -= 1
            if tw(d, it["value"], font(F_SERIF_BLACK, size)) > col_w - 10:
                return False
        return True

    if len(stats) > 5 and not fits(stats):
        # prefer dropping the estimate-sourced GTA stat, then Voyager
        for drop_key in ("Grand Theft Auto", "Voyager"):
            trimmed = [s for s in stats if drop_key not in s.get("story_ref", "")]
            if len(trimmed) == len(stats) - 1:
                stats = trimmed
                REPORT["notes"].append(f"stat band: dropped the {drop_key} stat so every "
                                       "numeral fits its column at >=34px")
                break
    col_w = CW / len(stats)
    rule_y = 182
    d.line([(MX, rule_y), (W - MX, rule_y)], fill=(70, 88, 128), width=1)
    f_cap = font(F_COND, 12)
    # hand-picked substrings of the data labels (cleaner than blind trims)
    caption_overrides = {
        "$81.3bn": "in Anthropic's record-breaking IPO",
        "204,070": "identified for evacuation in Odisha",
        "$190.4m": "record auction price for a Van Gogh",
        "25.9bn km": "Voyager 1's distance from Earth",
        "730,000": "Rohingya at issue in the ICJ case",
    }
    used = []
    for i, it in enumerate(stats):
        cx = MX + i * col_w
        d.ellipse([cx + 2, rule_y - 3, cx + 8, rule_y + 3], fill=AMBER)
        size = 36
        while size > 34 and tw(d, it["value"], font(F_SERIF_BLACK, size)) > col_w - 10:
            size -= 1
        d.text((cx + 2, rule_y + 6), it["value"], font=font(F_SERIF_BLACK, size), fill=AMBER)
        cap = caption_overrides.get(it["value"], it["label"])
        if cap != it["label"]:
            REPORT["trims"].append(f"stat caption {it['value']}: override substring of data label")
        cap = trim_to_lines(d, cap, f_cap, col_w - 8, 1, f"stat caption {it['value']}")
        d.text((cx + 2, rule_y + 6 + size + 5), cap, font=f_cap, fill=MUTED)
        used.append(it["value"])
    return {"stats_used": used, "stats_bottom": 242}


# ---------------------------------------------------------------- map
LAT_TOP, LAT_BOT = 62.0, -45.0
MAP_Y0, MAP_Y1 = 244, 412  # 168 tall - demoted so the reading layer can breathe,
# but tall enough for the world to read as a world


def project(lat, lon, box):
    """Equirectangular with a mild horizontal stretch (1.45x) so the world
    fills the wide, short panel; positions are approximate (captioned so)."""
    x0, y0, x1, y1 = box
    sy = (y1 - y0) / (LAT_TOP - LAT_BOT)
    sx = sy * 1.45
    ox = x0 + ((x1 - x0) - 360.0 * sx) / 2.0
    oy = y0 + ((y1 - y0) - (LAT_TOP - LAT_BOT) * sy) / 2.0
    return (ox + (lon + 180.0) * sx, oy + (LAT_TOP - lat) * sy)


def draw_map(img, dispatches, logbook):
    box = (MX, MAP_Y0, W - MX, MAP_Y1)
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
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
    img.paste(layer, (x0, y0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=12, outline=MAP_EDGE, width=1)

    # logbook dots (raw projection - the texture of the day)
    for s in logbook:
        x, y = project(s["lat"], s["lon"], box)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=PIN_DOT)

    # numbered dispatch pins, relaxed among themselves
    pins = []
    for i, (s, _panel, _hero) in enumerate(dispatches):
        x, y = project(s["lat"], s["lon"], box)
        pins.append({"x": x, "y": y, "r": 13, "n": i + 1})
    for _ in range(120):
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
            p["y"] = min(max(p["y"], y0 + p["r"] + 2), y1 - p["r"] - 2)
        if not moved:
            break
    max_disp = 0.0
    for p, (s, _pn, _h) in zip(pins, dispatches):
        tx, ty = project(s["lat"], s["lon"], box)
        max_disp = max(max_disp, math.hypot(p["x"] - tx, p["y"] - ty))

    # sun path from pin 1 (Shenzhen) to the last dispatch pin (Pasadena)
    start = (pins[0]["x"], pins[0]["y"])
    end = (pins[-1]["x"], pins[-1]["y"])
    mid = ((start[0] + end[0]) / 2.0, min(start[1], end[1]) - 46)

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
    # stage labels on dark chips
    f_lab = font(F_COND_BOLD, 11)
    for t, label, dy in [(0.13, "DAWN", -26), (0.40, "MIDDAY", 34), (0.88, "DUSK", -26)]:
        px, py = bez(t)
        wlab = tracked_width(d, label, f_lab, 3)
        cx, cy = px - wlab / 2, py + dy
        d.rounded_rectangle((cx - 5, cy - 2, cx + wlab + 5, cy + 14), radius=4, fill=(8, 15, 30))
        draw_tracked(d, (cx, cy), label, f_lab, AMBER, 3)
    # pins on top of the arc
    f_num = font(F_SANS_BOLD, 11)
    for p in pins:
        x, y, r = p["x"], p["y"], p["r"]
        d.ellipse([x - r, y - r, x + r, y + r], fill=AMBER, outline=STAR, width=2)
        label = str(p["n"])
        bb = d.textbbox((0, 0), label, font=f_num)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]),
               label, font=f_num, fill=(20, 14, 4))
    # caption chip
    f_cap = font(F_COND_BOLD, 11)
    cap = "EVERY PIN A STORY — NUMBERED PINS MARK THE DISPATCHES · DOTS MARK THE LOGBOOK · POSITIONS APPROXIMATE"
    cw_ = tracked_width(d, cap, f_cap, 1)
    d.rounded_rectangle((x0 + 6, y1 - 22, x0 + 16 + cw_, y1 - 3), radius=4, fill=(8, 15, 30))
    draw_tracked(d, (x0 + 11, y1 - 18), cap, f_cap, (150, 168, 200), 1)
    return {"map_box": box, "max_pin_displacement_px": round(max_disp, 1)}


# ---------------------------------------------------------------- dispatches
def crop_art(panel, w, h):
    art = Image.open(os.path.join(ART_DIR, panel)).convert("RGB")
    target = w / h
    aw, ah = art.size
    if aw / ah > target:
        nw = int(ah * target)
        art = art.crop(((aw - nw) // 2, 0, (aw - nw) // 2 + nw, ah))
    else:
        nh = int(aw / target)
        art = art.crop((0, (ah - nh) // 2, aw, (ah - nh) // 2 + nh))
    return art.resize((w, h))


def place_caps(story, draw, fnt, max_w):
    parts = [p.strip() for p in story["place"].split(",")]
    txt = parts[0].upper()
    if len(parts) > 1:
        cand = f"{parts[0].upper()} · {parts[-1].upper()}"
        if tw(draw, cand, fnt) <= max_w:
            txt = cand
    while tw(draw, txt, fnt) > max_w and len(txt) > 4:
        txt = txt[:-1]
    return txt


def dispatch_summary(draw, story, fnt, max_w, max_lines, tag):
    """Summary sentence ending with the source. The source is NEVER trimmed;
    the body is shortened (clause first, then words) until the composed
    text fits max_lines."""
    body = story["summary"]
    if story["contested"] and "Voyager" in story["headline"]:
        # Contested-date hygiene (spec U9): the crossing was timed to 18 Nov,
        # so the dispatch may only run with the data's true today-anchor -
        # JPL's briefing held today. Composed from the data's summary + its
        # own contested_note, short enough that the anchor survives trimming.
        body = "First object one light-day out, 25.9bn km; JPL briefs today."
        REPORT["notes"].append("Voyager dispatch: summary composed from data summary + "
                               "contested_note today-anchor (JPL briefing, Thu 19 Nov)")
    suffix = f" — {story['source']}"
    if len(wrap(draw, body + suffix, fnt, max_w)) <= max_lines:
        return body + suffix
    orig_len = len(body)
    body = trim_clause(draw, body, fnt, max_w, max_lines, tag)
    words = body.rstrip(".…").split()
    while len(wrap(draw, body + suffix, fnt, max_w)) > max_lines and len(words) > 4:
        words = words[:-1]
        body = " ".join(words).rstrip(",;:") + "…"
    if len(body) != orig_len:
        REPORT["trims"].append(f"{tag}: body {orig_len} -> {len(body)} chars (source kept whole)")
    return body + suffix


def draw_dispatches(img, dispatches, y0):
    d = ImageDraw.Draw(img)
    f_head = font(F_COND_BOLD, 13)
    draw_tracked(d, (MX, y0), "DISPATCHES FROM THE DAY", f_head, AMBER, 2)
    f_sub = font(F_SERIF_IT, 13)
    sub = "the day's biggest stories, told in full — numbered in sun order"
    d.text((W - MX - tw(d, sub, f_sub), y0 + 1), sub, font=f_sub, fill=MUTED)
    y = y0 + 22

    f_place = font(F_COND_BOLD, 13)
    f_sum = font(F_COND, 14)
    heroes = [(i, s, p) for i, (s, p, h) in enumerate(dispatches) if h]
    standards = [(i, s, p) for i, (s, p, h) in enumerate(dispatches) if not h]

    # ---- heroes: 3 across, ~311 wide; headlines trimmed (logged) to <=2 lines
    hw = (CW - 2 * 11) / 3
    hero_cards = []
    for i, s, panel in heroes:
        f_hl = font(F_COND_BOLD, 26)
        hl = trim_to_lines(d, s["headline"], f_hl, hw - 18, 2, f"hero headline n={i+1}")
        hl_lines = wrap(d, hl, f_hl, hw - 18)
        sum_text = dispatch_summary(d, s, f_sum, hw - 18, 2, f"hero summary n={i+1}")
        sum_lines = wrap(d, sum_text, f_sum, hw - 18)
        h = 30 + 14 + len(hl_lines) * 26 + len(sum_lines) * 16 + 10
        hero_cards.append((i, s, panel, hl_lines, sum_lines, h))
    hero_h = max(c[5] for c in hero_cards)
    for ci, (i, s, panel, hl_lines, sum_lines, _h) in enumerate(hero_cards):
        cx = MX + ci * (hw + 11)
        d.rounded_rectangle((cx, y, cx + hw, y + hero_h), radius=8, fill=CARD_BG,
                            outline=CARD_EDGE, width=1)
        if panel and os.path.exists(os.path.join(ART_DIR, panel)):
            art = crop_art(panel, int(hw) - 4, 30)
            img.paste(art, (int(cx) + 2, y + 2))
            d = ImageDraw.Draw(img)
        else:
            REPORT["notes"].append(f"hero n={i+1}: panel {panel} missing, text-only card")
        d.rectangle((cx + 8, y + 5, cx + 27, y + 22), fill=AMBER)
        f_chip = font(F_SANS_BOLD, 11)
        bb = d.textbbox((0, 0), str(i + 1), font=f_chip)
        d.text((cx + 8 + (19 - (bb[2] - bb[0])) / 2 - bb[0], y + 5 + (17 - (bb[3] - bb[1])) / 2 - bb[1]),
               str(i + 1), font=f_chip, fill=(20, 14, 4))
        cy = y + 37
        d.text((cx + 9, cy), place_caps(s, d, f_place, hw - 18), font=f_place, fill=AMBER)
        cy += 14
        f_hl = font(F_COND_BOLD, 26)
        for ln in hl_lines:
            d.text((cx + 9, cy), ln, font=f_hl, fill=STAR)
            cy += 26
        cy += 1
        for ln in sum_lines:
            d.text((cx + 9, cy), ln, font=f_sum, fill=(203, 212, 230))
            cy += 16
    y += hero_h + 8

    # ---- standards: 2 rows of 4, ~232 wide; headlines trimmed (logged) to <=2 lines
    sw = (CW - 3 * 9) / 4
    rows = [standards[:4], standards[4:]]
    std_info = []
    for row in rows:
        cards = []
        for i, s, panel in row:
            f_hl = font(F_COND_BOLD, 20)
            hl = trim_to_lines(d, s["headline"], f_hl, sw - 16, 2, f"standard headline n={i+1}")
            hl_lines = wrap(d, hl, f_hl, sw - 16)
            sum_text = dispatch_summary(d, s, f_sum, sw - 16, 2, f"standard summary n={i+1}")
            sum_lines = wrap(d, sum_text, f_sum, sw - 16)
            h = 14 + 13 + len(hl_lines) * 20 + len(sum_lines) * 16 + 9
            cards.append((i, s, panel, hl_lines, sum_lines, h))
        std_info.append(cards)
    for row in std_info:
        row_h = max(c[5] for c in row)
        for ci, (i, s, panel, hl_lines, sum_lines, _h) in enumerate(row):
            cx = MX + ci * (sw + 9)
            d.rounded_rectangle((cx, y, cx + sw, y + row_h), radius=8, fill=CARD_BG,
                                outline=CARD_EDGE, width=1)
            if panel and os.path.exists(os.path.join(ART_DIR, panel)):
                art = crop_art(panel, int(sw) - 4, 14)
                img.paste(art, (int(cx) + 2, y + 2))
                d = ImageDraw.Draw(img)
            else:
                REPORT["notes"].append(f"standard n={i+1}: panel {panel} missing, text-only card")
            d.rectangle((cx + 7, y + 2, cx + 24, y + 16), fill=AMBER)
            f_chip = font(F_SANS_BOLD, 9)
            bb = d.textbbox((0, 0), str(i + 1), font=f_chip)
            d.text((cx + 7 + (17 - (bb[2] - bb[0])) / 2 - bb[0], y + 2 + (14 - (bb[3] - bb[1])) / 2 - bb[1]),
                   str(i + 1), font=f_chip, fill=(20, 14, 4))
            cy = y + 20
            d.text((cx + 8, cy), place_caps(s, d, f_place, sw - 16), font=f_place, fill=AMBER)
            cy += 13
            f_hl = font(F_COND_BOLD, 20)
            for ln in hl_lines:
                d.text((cx + 8, cy), ln, font=f_hl, fill=STAR)
                cy += 20
            cy += 1
            for ln in sum_lines:
                d.text((cx + 8, cy), ln, font=f_sum, fill=(203, 212, 230))
                cy += 16
        y += row_h + 8
    return {"dispatch_bottom": y - 8, "hero_h": hero_h,
            "std_rows": [[c[5] for c in row] for row in std_info]}


# ---------------------------------------------------------------- logbook
LB_ENTRY_LH = 16
LB_GAP = 3


def entry_text(draw, story, fnt, max_w):
    """Place - Headline - fact (Source). The headline is truncated (logged)
    first to a 1-line fit, then to 2 lines; the fact always survives whole."""
    place = story["place"].split(",")[0]
    fact = story["fact"]
    hl = story["headline"]

    def build(h):
        if fact:
            return f"{place} — {h} — {fact} ({story['source']})"
        return f"{place} — {h} ({story['source']})"

    text = build(hl)
    if len(wrap(draw, text, fnt, max_w)) <= 1:
        return text
    words = hl.split()
    while len(words) > 3:
        words = words[:-1]
        cand = build(" ".join(words).rstrip(",;:") + "…")
        if len(wrap(draw, cand, fnt, max_w)) <= 1:
            REPORT["trims"].append(f"logbook '{place}': headline trimmed to 1 line")
            return cand
    # fall back: allow 2 lines, trim only as much as needed for that
    words = hl.split()
    while len(words) > 3:
        words = words[:-1]
        cand = build(" ".join(words).rstrip(",;:") + "…")
        if len(wrap(draw, cand, fnt, max_w)) <= 2:
            REPORT["trims"].append(f"logbook '{place}': headline trimmed to 2 lines")
            return cand
    return text


def draw_logbook(img, candidates, first_num, y0, y_limit):
    """Two-column logbook in leg/sun order. The solver runs first (measure
    only), numbers are assigned to the KEPT set so the sequence has no gaps,
    then the section is drawn with the true per-leg counts in its sub-line."""
    d = ImageDraw.Draw(img)
    f_entry = font(F_COND, 13)
    f_num = font(F_COND_BOLD, 13)
    col_gap = 22
    col_w = (CW - col_gap) / 2
    text_w = col_w - 24
    top = y0 + 19
    avail = y_limit - top

    cand = list(candidates)
    dropped = []

    def measure(items_cand):
        items = []
        for s in items_cand:
            lines = wrap(d, entry_text(d, s, f_entry, text_w), f_entry, text_w)
            items.append((s, lines, LB_ENTRY_LH * len(lines) + LB_GAP))
        prefix = [0]
        for _s, _l, h in items:
            prefix.append(prefix[-1] + h)
        best = None
        for a in range(1, len(items)):
            hs = (prefix[a], prefix[-1] - prefix[a])
            key = (max(hs), max(hs) - min(hs))
            if best is None or key < best[0]:
                best = (key, a, hs)
        if best is None:
            return items, 0, (prefix[-1], 0)
        return items, best[1], best[2]

    while True:
        items, split, col_heights = measure(cand)
        if max(col_heights) <= avail or not cand:
            break
        # Drop the weakest entry, but protect regional breadth: editorial
        # drop-keys first (from the longest leg), then the longest leg's tail.
        leg_counts = {}
        for s in cand:
            leg_counts[s["_leg"]] = leg_counts.get(s["_leg"], 0) + 1
        longest = max(leg_counts, key=lambda l: leg_counts[l])
        drop_idx = None
        for key in DROP_KEYS:
            for ci, s in enumerate(cand):
                if s["_leg"] == longest and key.lower() in s["headline"].lower():
                    drop_idx = ci
                    break
            if drop_idx is not None:
                break
        if drop_idx is None:
            for key in DROP_KEYS:
                for ci, s in enumerate(cand):
                    if key.lower() in s["headline"].lower():
                        drop_idx = ci
                        break
                if drop_idx is not None:
                    break
        if drop_idx is None:
            for ci in range(len(cand) - 1, -1, -1):
                if cand[ci]["_leg"] == longest:
                    drop_idx = ci
                    break
        dropped.append(cand[drop_idx]["headline"])
        cand.pop(drop_idx)

    # contiguous numbering for the kept set
    for i, s in enumerate(cand):
        s["_num"] = first_num + i
    leg_counts = {}
    for s in cand:
        leg_counts[s["_leg"]] = leg_counts.get(s["_leg"], 0) + 1

    f_head = font(F_COND_BOLD, 13)
    draw_tracked(d, (MX, y0), "THE LOGBOOK", f_head, AMBER, 2)
    f_sub = font(F_SERIF_IT, 13)
    leg_bits = " · ".join(f"{LEGS[l][0].title()} {LEGS[l][1].title()} ({leg_counts.get(l, 0)})"
                           for l in range(3))
    sub = f"the day in sun order — {leg_bits} — logged on Thursday 19 November"
    sub = trim_to_lines(d, sub, f_sub, CW - 130, 1, "logbook sub-line")
    d.text((W - MX - tw(d, sub, f_sub), y0 + 1), sub, font=f_sub, fill=MUTED)

    items, split, col_heights = measure(cand)
    cols = [items[:split], items[split:]]
    for ci, col in enumerate(cols):
        x = MX + ci * (col_w + col_gap)
        y = top
        for s, lines, h in col:
            d.text((x, y), str(s["_num"]), font=f_num, fill=AMBER)
            for li, ln in enumerate(lines):
                d.text((x + 24, y + li * LB_ENTRY_LH), ln, font=f_entry, fill=(203, 212, 230))
            y += h
    if len(cols) == 2 and col_heights[0] > 0:
        rx = MX + col_w + col_gap / 2
        d.line([(rx, top + 2), (rx, top + max(col_heights) - 2)], fill=(44, 60, 92), width=1)
    return {"logbook_entries": len(cand), "dropped_for_space": dropped,
            "col_heights": list(col_heights), "avail": avail,
            "fits": max(col_heights) <= avail, "kept": cand}


# ---------------------------------------------------------------- footer
def draw_footer(img, used_stories, y0):
    d = ImageDraw.Draw(img)
    box_h = 36
    d.rounded_rectangle((MX, y0, W - MX, y0 + box_h), radius=8, outline=AMBER_DEEP, width=1)
    f_box = font(F_COND, 13)
    f_lead = font(F_COND_BOLD, 13)
    lead = "LEFT ON THE CUTTING-ROOM FLOOR — "
    items_txt = ("kept off this page on date discipline: Prague's media protest (held Sun 15 Nov) · "
                 "a Spanish general strike (dated Wed 18 Nov) · a North Korean missile launch "
                 "(reports conflict on the day) · an actor's obituary (no dateline we could trust).")
    lines = wrap(d, lead + items_txt, f_box, CW - 24)
    ly = y0 + 4
    for ln in lines[:2]:
        if ln.startswith("LEFT ON"):
            d.text((MX + 12, ly), lead, font=f_lead, fill=AMBER)
            d.text((MX + 12 + tw(d, lead, f_lead), ly), ln[len(lead):], font=f_box, fill=MUTED)
        else:
            d.text((MX + 12, ly), ln, font=f_box, fill=MUTED)
        ly += 15
    f_claim = font(F_COND, 13)
    claim = ("Every story here happened, or was first reported, on Thursday 19 November 2026. "
             "Disputed claims are attributed, not stated as fact.")
    cy = y0 + box_h + 6
    for ln in wrap(d, claim, f_claim, CW)[:2]:
        d.text((MX, cy), ln, font=f_claim, fill=(190, 200, 220))
        cy += 16
    seen = []
    for s in used_stories:
        if s["source"] not in seen:
            seen.append(s["source"])
    f_src = font(F_COND, 12)
    src = trim_to_lines(d, "Sources: " + ", ".join(seen), f_src, CW, 1, "sources line")
    d.text((MX, cy + 1), src, font=f_src, fill=FAINT)
    return {"footer_bottom": cy + 15, "sources_count": len(seen)}


# ---------------------------------------------------------------- main
def render():
    global REPORT
    REPORT = {"trims": [], "drops": [], "notes": []}
    stories, stats, enriched = load_data()
    REPORT["enriched_data"] = enriched

    dispatches = []
    used_ids = set()
    for keys, panel, hero in DISPATCH_DEFS:
        s = find(stories, *keys)
        if s is None:
            REPORT["notes"].append(f"dispatch {keys} NOT FOUND in data - skipped")
            continue
        dispatches.append((s, panel, hero))
        used_ids.add(id(s))

    cand = [s for s in stories if id(s) not in used_ids and not s["cut"]]
    cand.sort(key=lambda s: (leg_of(s), -s["lon"]))
    for s in cand:
        s["_leg"] = leg_of(s)
    n_regions = len({s["region"] for s in stories
                     if id(s) in used_ids or s in cand})

    # Planning pass on a scratch canvas (identical geometry): learn how many
    # logbook entries survive the space solver, so the masthead can print the
    # TRUE story count. Logging from this pass is discarded and regenerated
    # identically by the real pass.
    saved = (list(REPORT["trims"]), list(REPORT["drops"]), list(REPORT["notes"]))
    scratch = Image.new("RGB", (W, W))
    disp_plan = draw_dispatches(scratch, dispatches, MAP_Y1 + 8)
    lb_plan = draw_logbook(scratch, cand, len(dispatches) + 1,
                           disp_plan["dispatch_bottom"] + 8, W - 76)
    kept = lb_plan["kept"]
    REPORT["trims"], REPORT["drops"], REPORT["notes"] = saved
    total = len(dispatches) + len(kept)

    img = make_background()
    mh = draw_masthead(img, total, n_regions)
    st = draw_stats(img, stats)
    mp = draw_map(img, dispatches, kept)
    disp = draw_dispatches(img, dispatches, MAP_Y1 + 8)
    lb_y = disp["dispatch_bottom"] + 8
    lb = draw_logbook(img, cand, len(dispatches) + 1, lb_y, W - 76)
    kept = lb["kept"]
    used_stories = [s for (s, _p, _h) in dispatches] + kept
    ft = draw_footer(img, used_stories, W - 76)
    REPORT["drops"].extend(lb["dropped_for_space"])

    buf = io.BytesIO()
    q = 88
    img.save(buf, format="JPEG", quality=q)
    data = buf.getvalue()
    if len(data) > 450_000:  # tie-break favours smaller files; step quality down
        for q in (84, 80, 76):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=q)
            data = buf.getvalue()
            if len(data) <= 450_000:
                break
    REPORT.update({
        "total_stories": len(used_stories),
        "dispatches": len(dispatches),
        "logbook_kept": lb["logbook_entries"],
        "date_size_px": mh["date_size"],
        "stats": st,
        "map": mp,
        "dispatches_layout": disp,
        "logbook_layout": {k: v for k, v in lb.items() if k != "kept"},
        "footer": ft,
        "bytes": len(data),
        "jpeg_quality": q,
        "jpeg_magic": data[:2] == b"\xff\xd8",
    })
    return data, REPORT


def main():
    data, report = render()
    data2, _ = render()
    report["deterministic"] = data == data2
    for k in ("trims", "drops", "notes"):
        report[k] = list(dict.fromkeys(report[k]))
    with open(OUT_PATH, "wb") as f:
        f.write(data)
    print(json.dumps(report, indent=2, default=str))
    print("wrote", OUT_PATH, len(data), "bytes")
    thumb = Image.open(io.BytesIO(data)).resize((300, 300))
    thumb.save(THUMB_PATH)
    print("wrote", THUMB_PATH)


if __name__ == "__main__":
    main()
