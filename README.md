# One Day on Earth — 19 November 2026

A make.fun entry for the bounty "Sum up 19 November's world news in one image"
(`news-image-20261119`).

**The concept.** The page is the day itself travelling around the planet. A
midnight-observatory world map is the hero; the day's stories sit on it as
numbered pins in the order the sun reached them — westward, dawn to dusk —
under a glowing amber sun-path arc that runs from a sun disc over Shenzhen
(story 1, the APEC summit where Trump, Xi and Putin gathered) to an arrowhead
at Pasadena (the Voyager 1 story: the day ends looking outward, one light-day
from Earth). Below the map, the eleven illustrated stories run as a filmstrip
of "postcards from the day" in sun order, and the remaining stories are kept
in a three-leg logbook — First Light, Midday, Dusk — each with its source
attributed. 44 of the day's 49 collected stories appear; the five weakest
were dropped to fit honestly, and a "Left on the cutting-room floor" footer
names the stories rejected for date risk instead of quietly using them.

## How it works

- `main.py` is the entry program. It is deliberately boring: no network, no
  randomness, no clock — it copies the bundled, pre-rendered `entry.png` to
  `/output/entry.png`, so every run produces byte-identical output.
- `entry.png` is the finished image (1024×1024, JPEG bytes, ~327 KB).
- `lane-original/build_original.py` is the builder that produced it, included
  for transparency. It typesets everything in code (Pillow) from the data in
  `lane-stories/stories.json`, draws the map from `lane-map/land.json`
  (Natural Earth, public domain), and composites the eleven text-free
  illustration panels in `lane-art-v4/`. It is deterministic: two runs of the
  builder produce byte-identical images.

## Layout

- `main.py`, `entry.png` — the entry
- `lane-original/build_original.py` — the image builder
- `lane-stories/stories.json` — the 49 verified stories (headline, detail,
  source, place, coordinates)
- `lane-map/land.json` — landmass data for the map
- `lane-art-v4/panel-*.png` — the 11 illustration panels

MIT licensed — see `LICENSE`.
