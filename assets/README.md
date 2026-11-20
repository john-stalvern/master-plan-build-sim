# Master Planner tile art

Flat 16x16 top-down sprites in the style of the original *SimCity*. SVG is the
source of truth; `tiles.png` and `preview.png` are generated from it.

## Palette (exact, from `render.c:tile_rgb`)

| Tile | Hex | Tile | Hex |
|---|---|---|---|
| T_EMPTY | `#184018` | T_RES | `#3CA03C` |
| T_WATER | `#2050B4` | T_COM | `#3C64DC` |
| T_ROAD | `#6E6E6E` | T_IND | `#966E32` |
| T_POWERLINE | `#DCC828` | T_PARK | `#50DC50` |
| T_POWERPLANT | `#E6821E` | T_SCHOOL | `#9646C8` |
| T_POLICE | `#1E3282` | T_FIRE | `#D23228` |
| T_PICKLEBALL | `#2E86AB` | | |

`T_PICKLEBALL` is court blue `#2E86AB` with white `#FFFFFF` boundary/net and
tiny service-box lines painted on top, plus the standard 1px `#141414` edge
outline on all four sides.

Development levels use the game's own `base + 16*level` brightness rule
(saturated at 255):

| Level | RES | COM | IND |
|---|---|---|---|
| L1 | `#4CB04C` | `#4C74EC` | `#A67E42` |
| L2 | `#5CC05C` | `#5C84FC` | `#B68E52` |
| L3 | `#6CD06C` | `#6C94FF` | `#C69E62` |

Style rules: every sprite has a full-bleed base fill in the exact colour above,
integer-coordinate rects only, `shape-rendering="crispEdges"`, no gradients,
filters or text, and a 1px `#141414` outline on all four tile edges. Because the
outline is per-tile, two adjacent rendered tiles show a 2px dark seam.

## Atlas layout

`tiles.png` is **112x64** px: 22 cells of 16x16 in a **7-column x 4-row** grid,
row-major, zero gaps. Cells 0..21 are fully opaque. Cell `(x, y)` is the
top-left pixel in the atlas. The index is the sprite's position in row-major
order.

| # | Sprite | x | y | # | Sprite | x | y |
|---:|---|---:|---:|---:|---|---:|---:|
| 0 | T_EMPTY | 0 | 0 | 11 | T_FIRE | 64 | 16 |
| 1 | T_WATER | 16 | 0 | 12 | T_RES_L1 | 80 | 16 |
| 2 | T_ROAD | 32 | 0 | 13 | T_RES_L2 | 96 | 16 |
| 3 | T_POWERLINE | 48 | 0 | 14 | T_RES_L3 | 0 | 32 |
| 4 | T_POWERPLANT | 64 | 0 | 15 | T_COM_L1 | 16 | 32 |
| 5 | T_RES | 80 | 0 | 16 | T_COM_L2 | 32 | 32 |
| 6 | T_COM | 96 | 0 | 17 | T_COM_L3 | 48 | 32 |
| 7 | T_IND | 0 | 16 | 18 | T_IND_L1 | 64 | 32 |
| 8 | T_PARK | 16 | 16 | 19 | T_IND_L2 | 80 | 32 |
| 9 | T_SCHOOL | 32 | 16 | 20 | T_IND_L3 | 96 | 32 |
| 10 | T_POLICE | 48 | 16 | | | | |
| | | | | 21 | T_PICKLEBALL | 0 | 48 |

Formula: `i` from the table, `x = (i % 7) * 16`, `y = (i // 7) * 16`.

Cells 22..27 are transparent padding: `montage` fills a full 7x4 canvas, and
the renderer reads only cells 0..21. The original 21 cells are regenerated
byte-identically from their unchanged SVGs.

### Sprite selection for the renderer

- Non-zone types (`T_EMPTY`, `T_WATER`, `T_ROAD`, `T_POWERLINE`,
  `T_POWERPLANT`, `T_PARK`, `T_SCHOOL`, `T_POLICE`, `T_FIRE`): use the same-named
  sprite; ignore `tile.level`.
- `T_RES`, `T_COM`, `T_IND`: `level == 0` uses the base sprite
  (`T_RES`/`T_COM`/`T_IND`, drawn as a surveyed empty lot); `level 1..3` uses
  `T_<TYPE>_L1` / `_L2` / `_L3`.
- `T_PICKLEBALL` uses cell 21 and is present only in the 22-cell atlas; with
  the 21-cell atlas it falls back to the flat court rectangle.

`preview.png` is **448x256**: `tiles.png` upscaled 4x with a nearest-neighbour
(point) filter, for human inspection without changing the source pixels.

## Rebuild and verify

```sh
cd assets
python3 verify_svgs.py   # XML, 16x16, exact base fill, integer rects, dark border
python3 build_atlas.py   # rsvg-convert each SVG, montage to tiles.png, 4x preview
# 22nd sprite: assets/svg/tile_pickleball.svg (NOT T_PICKLEBALL.svg)
```

Verification: after rebuilding, run both commands and confirm that all 22 SVGs
(22/22), including `assets/svg/tile_pickleball.svg`, pass the style checks and
rasterise to 16x16; that the atlas is 112x64 and the preview 448x256; and that
every used cell (0..21) contains more than one colour and its `(1,1)` pixel
matches the palette hex above. Exact counts will be finalised after the build.

Source SVGs live in `assets/svg/` and are named exactly as in the table, except
`T_PICKLEBALL`, whose source is `tile_pickleball.svg`.
Generated files: `tiles.png`, `preview.png`.

## Batch A UI assets (manifest A1-A6)

All UI assets follow the same flat first-SimCity rules: exact `render.c`
hexes, integer-coordinate SVG rects, `shape-rendering="crispEdges"`, a 1px
`#141414` outline (except the cursor markers, whose outline is the signal
colour per manifest A5), no gradients except the five hard-edged legend
steps. `layout_*.json` files are machine-readable copies of every table
below.

### A1 — tool palette: `tools.png` 176x16

11 cells of 16x16, one row, order = `render.c:pal_tool[]` (also the key order
1,2,3,4,5,6,7,8,9,0,-). Cell `i` is at `x = i*16, y = 0`.

| i | Tool | x | Swatch | SVG | i | Tool | x | Swatch |
|---:|---|---:|---|---|---:|---|---:|---|
| 0 | BULLDOZE | 0 | `#C84646` | tool_BULLDOZE.svg | 6 | SCHOOL | 96 | `#9646C8` |
| 1 | ROAD | 16 | `#6E6E6E` | tool_ROAD.svg | 7 | POLICE | 112 | `#1E3282` |
| 2 | RES | 32 | `#3CA03C` | tool_RES.svg | 8 | FIRE | 128 | `#D23228` |
| 3 | COM | 48 | `#3C64DC` | tool_COM.svg | 9 | POWERPLANT | 144 | `#E6821E` |
| 4 | IND | 64 | `#966E32` | tool_IND.svg | 10 | POWERLINE | 160 | `#DCC828` |
| 5 | PARK | 80 | `#50DC50` | tool_PARK.svg | | | | |

### A2 — scorecard metrics: `metrics.png` 80x16

5 cells of 16x16, one row, cell `i` at `x = i*16, y = 0`; `#E8E8E8` line art
plus one contract accent each.

| i | Metric | x | Accent | SVG |
|---:|---|---:|---|---|
| 0 | WALKABILITY | 0 | `#6E6E6E` | metric_WALKABILITY.svg |
| 1 | GREEN | 16 | `#50DC50` | metric_GREEN.svg |
| 2 | AMENITIES | 32 | `#9646C8` | metric_AMENITIES.svg |
| 3 | YIELD | 48 | `#DCC828` | metric_YIELD.svg |
| 4 | LIVABILITY | 64 | `#D23228` | metric_LIVABILITY.svg |

### A3 — overlay legend keys

Ramp bars `legend_landvalue.png`, `legend_pollution.png`, `legend_power.png`,
`legend_crime.png`: each **180x10**, five 36x10 steps at `x = i*36, y = 0..9`.
Step `i` uses `v = i*255/4` in `render.c:lerp_color()` (integer truncation),
with endpoints taken verbatim from `overlay_scale()`.

| Mode | F key | Step 0 | Step 1 | Step 2 | Step 3 | Step 4 |
|---|---|---|---|---|---|---|
| LANDVALUE | F1 | `#962828` | `#805434` | `#6A8140` | `#53AE4D` | `#3CDC5A` |
| POLLUTION | F2 | `#32AA46` | `#5C8D3F` | `#866F38` | `#B15130` | `#DC3228` |
| CRIME | F4 | `#32AA46` | `#5C8F42` | `#86743D` | `#B15838` | `#DC3C32` |
| POWER | F3 | `#503728` | `#503728` | `#468CFF` | `#468CFF` | `#468CFF` |

POWER is binary in `render.c`: its five steps are OFF, OFF, a half-OFF /
half-ON middle step, ON, ON — no blended colour is introduced.

- `legend_glyphs.png` **64x16**, 4 cells of 16x16 at `x = 0,16,32,48`:
  LANDVALUE, POLLUTION, POWER, CRIME (SVG `legend_glyph_<MODE>.svg`).
- `legend_tags.png` **64x16**, 4 cells of 16x16 at `x = 0,16,32,48`:
  F1, F2, F3, F4 as 5x7 pixel-font rects (SVG `legend_tag_F<n>.svg`).
- `legend_keys.png` **212x64** reference composite, four 16px rows in the
  same mode order; within row `r`: tag at `x=0`, glyph at `x=16`, ramp at
  `x=32`, `y = r*16+3`. The individual PNGs remain authoritative.

### A4 — overlay heat atlas: `heat.png` 80x64

5 columns x 4 rows of 16x16 cells, zero gaps, no transparent margins.
`x = step*16`, `y = (overlay-1)*16` where `overlay` is the `render_frame`
overlay index (1 landValue, 2 pollution, 3 power, 4 crime). Column order is
low → high step, matching the A3 ramp of the same row.

| y \ x | 0 (S0) | 16 (S1) | 32 (S2) | 48 (S3) | 64 (S4) |
|---:|---|---|---|---|---|
| 0 LANDVALUE | `#962828` | `#805434` | `#6A8140` | `#53AE4D` | `#3CDC5A` |
| 16 POLLUTION | `#32AA46` | `#5C8D3F` | `#866F38` | `#B15130` | `#DC3228` |
| 32 POWER | `#503728` | `#503728` | `#468CFF` | `#468CFF` | `#468CFF` |
| 48 CRIME | `#32AA46` | `#5C8F42` | `#86743D` | `#B15838` | `#DC3C32` |

Every pixel (fill and 1px border) has alpha **153 = 60%**, the manifest
maximum; SVG sources use `fill-opacity="0.6"` with the exact hex above.
`rsvg-convert` premultiplies alpha, so a few rasterised channels can land
one LSB below the source hex after unpremultiply — the SVG source is exact
and the difference is invisible at 60% alpha over a tile.

### A5 — cursor/placement markers: `cursors.png` 64x16

4 cells of 16x16 in one row: HOVER `x=0` (`#E8E8E8`), VALID `x=16`
(`#50DC50`), INVALID `x=32` (`#D23228`), BULLDOZE `x=48` (`#6E6E6E`).
Interiors are fully transparent; the coloured 1px outline is the marker.
The same rasters are also shipped individually as `cursor_HOVER.png`,
`cursor_VALID.png`, `cursor_INVALID.png`, `cursor_BULLDOZE.png`.

### A6 — top-bar HUD: `hud_topbar.png` 920x40

Flat `#141414` background; all text is drawn live by the GUI on top of it.
These zones are completely quiet (flat #141414, no rule/emblem/decoration):

| Zone | x | y | w | h | Live text drawn by render.c |
|---|---:|---:|---:|---:|---|
| TITLE | 8 | 8 | 192 | 24 | "MASTER PLANNER" at (8,10) |
| DAY | 416 | 8 | 120 | 24 | "DAY n" at (420,10) |
| POP | 536 | 8 | 124 | 24 | "POP n" at (540,10) |
| PAUSE | 696 | 8 | 88 | 24 | "PAUSED" at (700,10) |

Decoration lives only outside them: 1px rules at `y=0` (`#6E6E6E`) and
`y=39` (`#3C64DC`), separators at `x=408,532,688,808`, a 16x16 plan emblem
at (876,12) and a 16x16 pause slot at (812,12).

### Rebuild and verify batch A

```sh
cd /home/will/master-planner
python3 assets/build_icons.py     # A1+A2 SVGs -> tools.png, metrics.png
python3 assets/build_legends.py   # A3+A4 ramps/glyphs/tags/heat + JSON
python3 assets/build_cursors.py   # A5 markers + atlas + JSON
python3 assets/build_hud.py       # A6 HUD + JSON
python3 assets/verify_ui.py       # 387 independent pixel/layout assertions
python3 assets/build_atlas.py     # 22-cell atlas (pickleball extension)
python3 assets/verify_svgs.py     # base tile style checks
```

All builders are deterministic (re-running leaves every committed asset
byte-identical). `verify_ui.py` checks raw RGBA pixels: dimensions, cell
placement, exact swatch/accent/ramp hexes, 153/255 heat alpha, transparent
cursor interiors, individual-vs-atlas equality and flat HUD safe zones.

## Batch B UI assets (manifest B1-B8)

Same flat first-SimCity rules as batch A. The five PNG strips/atlases below are
all generated deterministically from their SVG sources by
`python3 assets/build_batch_b.py`; each cell is row-major with zero gaps.

### B1 — power badges: `power_badges.png` 16x8

Two 8x8 cells on `#141414`: cell `i` at `x = i*8`.

| i | Meaning | SVG | Bolt |
|---:|---|---|---|
| 0 | powered | `B1_POWERED.svg` | `#DCC828` |
| 1 | unpowered | `B1_UNPOWERED.svg` | `#6E6E6E` |

### B2 — development pips: `level_pips.png` 21x7

Three 7x7 cells at `x = i*7`: `B2_PIP_1.svg` (one `#F0F0D2` pip),
`B2_PIP_2.svg` (two), `B2_PIP_3.svg` (three), each on a `#141414` field with a
1px dark outline. Renderer mapping: `tile.level` 0 = no pips, 1/2/3 = cells
0/1/2.

### B3 — HUD status icons: `hud_status.png` 64x16

Four 16x16 cells at `x = i*16`, one contract accent each:

| i | Icon | SVG | Accent |
|---:|---|---|---|
| 0 | day / sun | `B3_DAY.svg` | `#DCC828` |
| 1 | population | `B3_POPULATION.svg` | `#3CA03C` |
| 2 | jobs | `B3_JOBS.svg` | `#3C64DC` |
| 3 | pause / play | `B3_PAUSE_PLAY.svg` | `#E8E8E8` / `#50DC50` |

### B4 — pattern stamps: `pattern_thumbnails.png` 480x96

Five 96x96 cells at `x = i*96`. Each SVG draws the **exact** tile rows from
`docs/patterns.md`; tile colours are the base atlas palette with a 1px
`#141414` seam. Transparent SVG margins are flattened onto `#141414`, and the
caption strip is `#E8E8E8` text. Cell size is chosen per stamp to fit its
bounding box.

| i | Stamp | SVG | Tile px | Tiles | Anchor |
|---:|---|---|---:|---:|---|
| 0 | village-centre | `PATTERN_VILLAGE_CENTRE.svg` | 6 | 169 | (2,2) |
| 1 | green-spine | `PATTERN_GREEN_SPINE.svg` | 6 | 120 | (2,17) |
| 2 | transit-node | `PATTERN_TRANSIT_NODE.svg` | 8 | 99 | (13,27) |
| 3 | school-cluster | `PATTERN_SCHOOL_CLUSTER.svg` | 7 | 88 | (31,2) |
| 4 | garden-works | `PATTERN_GARDEN_WORKS.svg` | 7 | 90 | (31,14) |

The two `.` cells of school-cluster are intentionally left blank (88 placed).

### B5 — app / window icon

`APP_ICON.svg` is the 64x64 master: orange `#E6821E` power-plant glyph on
`#184018` dark green with a 2px `#141414` frame and `#50DC50` foliage.
Rasters: `app_icon_32.png` (32x32), `app_icon_64.png` (64x64).

### B6 — architecture + tick-order diagram

`ARCHITECTURE_TICK_ORDER.svg` is 1000x600 (vector only; no committed PNG).
It shows main / sim / world / render and the tick chain
power → pollution → crime → landValue → growth → scorecard, with labels
`GRID 40x40`, `TILE 16`, `TICK 500 ms`.

### B7 — README hero banner

`HERO_BANNER.svg` (1280x400) + `hero_banner.png`: a 40x40 plan slice and a
sidebar mock (tools, scorecard, overlay legend), contract palette only.
Suggested embed: `![Master Planner](assets/hero_banner.png)`.

### B8 — keycap badge sheet: `keycaps.png` 240x12

Twenty 12x12 cells at `x = i*12`, in the exact order below (also the order of
`assets/svg/B8_KEY_<NAME>.svg`; `-` uses `B8_KEY_MINUS.svg`). Keycaps are the
one batch-B exception allowing `<text>`; all other fills use the contract
palette.

| i | Label | SVG name | i | Label | SVG name |
|---:|---|---|---:|---|---|
| 0 | 1 | `B8_KEY_1` | 10 | - | `B8_KEY_MINUS` |
| 1 | 2 | `B8_KEY_2` | 11 | F1 | `B8_KEY_F1` |
| 2 | 3 | `B8_KEY_3` | 12 | F2 | `B8_KEY_F2` |
| 3 | 4 | `B8_KEY_4` | 13 | F3 | `B8_KEY_F3` |
| 4 | 5 | `B8_KEY_5` | 14 | F4 | `B8_KEY_F4` |
| 5 | 6 | `B8_KEY_6` | 15 | ESC | `B8_KEY_ESC` |
| 6 | 7 | `B8_KEY_7` | 16 | SPACE | `B8_KEY_SPACE` |
| 7 | 8 | `B8_KEY_8` | 17 | S | `B8_KEY_S` |
| 8 | 9 | `B8_KEY_9` | 18 | L | `B8_KEY_L` |
| 9 | 0 | `B8_KEY_0` | 19 | Q | `B8_KEY_Q` |

Tool keys use `#DCC828`, F-keys `#3C64DC`, ESC `#D23228`, SPACE `#50DC50`,
S/L/Q `#E8E8E8`; every badge has a `#141414` field and `#F0F0D2` rim.

### Rebuild and verify batch B

```sh
cd /home/will/master-planner
python3 assets/build_batch_b.py          # regenerate all eight PNGs from SVG
python3 assets/build_batch_b.py --check  # XML, palette, census, labels, pixel+byte equality
```

Verification performed: 37/37 batch-B SVGs parse and use only contract palette
hexes; 5/5 pattern censuses match `docs/patterns.md` exactly (169/120/99/88/90
tiles); 13/13 diagram labels present; all eight PNGs have the documented
dimensions and regenerate byte-identically from their SVGs. `tiles.png` and
`build_atlas.py` have since been extended from 21 to 22 cells by the pickleball
card (cell 21, `assets/svg/tile_pickleball.svg`); that follow-up is now done.
