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

`tiles.png` is **112x48** px: 21 cells of 16x16 in a **7-column x 3-row** grid,
row-major, zero gaps, fully opaque. Cell `(x, y)` is the top-left pixel in the
atlas. The index is the sprite's position in row-major order.

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

Formula: `i` from the table, `x = (i % 7) * 16`, `y = (i // 7) * 16`.

### Sprite selection for the renderer

- Non-zone types (`T_EMPTY`, `T_WATER`, `T_ROAD`, `T_POWERLINE`,
  `T_POWERPLANT`, `T_PARK`, `T_SCHOOL`, `T_POLICE`, `T_FIRE`): use the same-named
  sprite; ignore `tile.level`.
- `T_RES`, `T_COM`, `T_IND`: `level == 0` uses the base sprite
  (`T_RES`/`T_COM`/`T_IND`, drawn as a surveyed empty lot); `level 1..3` uses
  `T_<TYPE>_L1` / `_L2` / `_L3`.

`preview.png` is **448x192**: `tiles.png` upscaled 4x with a nearest-neighbour
(point) filter, for human inspection without changing the source pixels.

## Rebuild and verify

```sh
cd assets
python3 verify_svgs.py   # XML, 16x16, exact base fill, integer rects, dark border
python3 build_atlas.py   # rsvg-convert each SVG, montage to tiles.png, 4x preview
```

Verification performed: 21/21 SVGs pass the style checks and rasterise to
16x16; atlas is 112x48 and preview 448x192; every one of the 21 atlas cells has
more than one colour; the pixel at each cell's `(1,1)` equals the exact palette
hex listed above (0 mismatches).

Source SVGs live in `assets/svg/` and are named exactly as in the table.
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
python3 assets/build_atlas.py     # base 21-tile atlas (unchanged)
python3 assets/verify_svgs.py     # base tile style checks
```

All builders are deterministic (re-running leaves every committed asset
byte-identical). `verify_ui.py` checks raw RGBA pixels: dimensions, cell
placement, exact swatch/accent/ramp hexes, 153/255 heat alpha, transparent
cursor interiors, individual-vs-atlas equality and flat HUD safe zones.
