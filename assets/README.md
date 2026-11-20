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
