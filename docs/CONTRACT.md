# Master Planner — frozen interface contract (PM decision, v1)

All workers implement against this contract. Headers are FROZEN after the
scaffold card completes; changing a header requires a kanban comment to the PM
and approval. File ownership is strict — only touch files you own.

## Project
- Repo: /home/will/master-planner (git). Binary name: `masterplanner`.
- Language: C11. Libs: SDL2 + SDL2_ttf (both installed; pkg-config names `sdl2 SDL2_ttf`).
- Build: `make` (Makefile, gcc, -O2 -Wall -Wextra). `make test` builds+runs headless tests.
- Background research: docs/research.md. No failure states, no money pressure — sandbox.

## Layout & ownership
| File | Owner card |
|---|---|
| Makefile, world.h, world.c, sim.h, render.h, main.c (skeleton) | T1 architect |
| sim.c, tests/test_sim.c | T2 sim engineer (after T1) |
| render.c, main.c (input/HUD wiring) | T3 GUI engineer (after T1) |
| docs/scorecard.md, docs/patterns.md | T4 design (no code) |
T2 and T3 run in parallel: T2 must NOT edit main.c/render.c/Makefile; T3 must NOT
edit sim.c/world.c. Both `git add` ONLY their own files when committing.

## Constants
GRID_W=40, GRID_H=40, TILE=16. Window 920x680.
Map origin (0,40); map 640x640. Top bar y=0..39 (title + day/population).
Sidebar x=656..919: tool palette (11 buttons), scorecard, overlay legend.

## world.h (frozen shape)
```c
typedef enum { T_EMPTY, T_WATER, T_ROAD, T_POWERLINE, T_POWERPLANT,
               T_RES, T_COM, T_IND, T_PARK, T_SCHOOL, T_POLICE, T_FIRE,
               T_COUNT } TileType;
typedef struct { uint8_t type, level, powered, landValue, pollution, crime; } Tile;
extern Tile world[GRID_H][GRID_W];
void world_init(void);            /* empty land + a river/lake + some trees (T_EMPTY w/ level as decoration is NOT allowed; keep deterministic seed) */
int  world_place(int x, int y, TileType t);  /* 0 ok, -1 occupied/invalid; roads/powerlines may overwrite EMPTY only */
void world_bulldoze(int x, int y);
int  world_save(const char *path); /* fwrite whole grid + header magic "MPv1" */
int  world_load(const char *path);
int  world_population(void);       /* sum res level * 4 */
int  world_jobs(void);             /* sum (com+ind) level * 3 */
```

## sim.h (frozen shape)
```c
typedef struct { int walkability, green, amenities, yield, livability; /* 0..100 */
                 int population, jobs, day; } Scorecard;
void sim_init(void);
void sim_tick(void);              /* advances one day; recompute everything */
Scorecard sim_scorecard(void);
extern int sim_paused;            /* 0/1, set by main */
```
Tick order: power flood-fill from plants across POWERLINE+adjacent zones →
pollution diffusion (IND, ROAD, POWERPLANT sources, distance falloff) →
crime (low landValue + distance from POLICE) → landValue (downtown bonus +
park/water adjacency − pollution − crime) → zone growth/decay (needs road in
8-neighbourhood + powered + landValue threshold; level 0..3) → scorecard.
Metric definitions: docs/scorecard.md (T4). Defaults if absent: walkability =
% of developed RES with COM or PARK or SCHOOL within Chebyshev radius 4;
green = % of map tiles that are PARK/WATER/T_EMPTY-with-trees; amenities =
% of developed RES within radius 5 of SCHOOL and radius 5 of COM;
yield = developed level-sum / theoretical max * 100; livability = mean of the
four, minus pollution penalty. All clamp 0..100.

## render.h (frozen shape)
```c
int  render_init(SDL_Renderer *r);   /* loads font, returns 0 ok */
void render_frame(SDL_Renderer *r, int hover_x, int hover_y,
                  TileType tool, int overlay, Scorecard sc, int day, int paused);
void render_quit(void);
/* overlay: 0=none 1=landValue 2=pollution 3=power 4=crime */
```
Flat top-down colours: EMPTY dark green, WATER blue, ROAD grey, POWERLINE yellow,
POWERPLANT orange, RES green shades by level, COM blue shades, IND brown shades,
PARK bright green, SCHOOL purple, POLICE navy, FIRE red. Developed zones draw a
small inner rect per level. Palette buttons show colour swatch + label.

## main.c behaviour (skeleton by T1, input/HUD polish by T3)
- 60 fps loop; sim_tick every 500 ms when !sim_paused.
- Mouse: left click/drag paints selected tool on map; sidebar clicks select tool.
- Keys: 1..9,0,- select the 11 tools; F1..F4 toggle overlays (ESC clears);
  SPACE pause; S save plan.bin; L load plan.bin; Q/ESC-window quit.
- CLI: `--smoke [--ticks N]` runs headless (SDL_VIDEODRIVER=dummy set internally
  if no display), places a scripted test plan (road spine + zones + plant + park
  + school), runs N ticks (default 200), prints scorecard JSON to stdout, exits 0.
  This is the QA harness — it must work with zero user interaction.
- Font: TTF_OpenFont, try in order:
  /usr/share/fonts/TTF/DejaVuSans.ttf,
  /usr/share/fonts/dejavu/DejaVuSans.ttf,
  /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf,
  then glob fallback; if none found, render text via SDL's built-in debug font
  is NOT available — instead draw scorecard as labelled colour bars + numbers
  using a tiny embedded 5x7 bitmap font (implement in render.c).

## Acceptance style
Every code card: `make` clean (no warnings), `make test` green (where tests
exist), `./masterplanner --smoke` exits 0, git commit with own files only,
kanban_complete summary lists changed files + verification output.

## Addendum v1.2 — Pickleball court (PM-approved)

Extends the frozen v1 contract; everything not restated here is unchanged.

1. **world.h (append-only enum change).** `T_PICKLEBALL` is added immediately
   BEFORE `T_COUNT` in `TileType`; all existing enum values are unchanged:
   ```c
   typedef enum { T_EMPTY, T_WATER, T_ROAD, T_POWERLINE, T_POWERPLANT,
                  T_RES, T_COM, T_IND, T_PARK, T_SCHOOL, T_POLICE, T_FIRE,
                  T_PICKLEBALL, T_COUNT } TileType;   /* T_PICKLEBALL = 12, T_COUNT = 13 */
   ```
   No other world.h change; no conversion helper is added — the in-place
   conversion is a direct tile-type assignment consistent with the world API.
2. **Interaction.** Ctrl+left-click on an existing `T_PARK` tile converts it
   to `T_PICKLEBALL` in place, at no cost. Ctrl+click on any other tile is a
   no-op. Plain park placement is unchanged. Pickleball is NOT a palette tool.
   Input handling lives in main.c (mp-gui).
3. **Simulation.** `T_PICKLEBALL` is recreational open space: it counts as
   green/open space exactly like `T_PARK` in ALL scorecard metrics (green
   coverage and the park term of walkability; docs/scorecard.md §1, §2.1,
   §2.2 read `T_PARK` as park-equivalent = `T_PARK` or `T_PICKLEBALL`), raises
   neighbour landValue like a park (+6 adjacency), is not a pollution or crime
   source, never develops (level stays 0), and needs no power or road. sim.c
   treats it as park-equivalent everywhere `T_PARK` is handled.
4. **Rendering (mp-gui).** Flat court colour `#2E86AB` (court blue) with white
   boundary lines + centre net line; sprite variant in atlas cell index 21
   (atlas grows 21 -> 22 cells; assets/README.md atlas layout doc updated by
   mp-gui). Sidebar help hint: "CTRL+click park = pickleball".
5. **Persistence.** world_save/load format magic stays `"MPv1"`; the grid is
   raw bytes, so the new enum value round-trips unchanged (world_load's
   `type >= T_COUNT` validation accepts it). No world.c change.

Feature ownership: mp-architect owns the world.h enum addition, sim.c
treatment, tests (tests/test_sim.c additions) and this addendum; mp-gui owns
main.c input, render.c and the atlas/layout doc update. Neither edits the
other's files.

## Sprite atlas (v1.1, optional) — PM-approved GUI integration

Extends v1/v1.2; nothing above is changed. Owner: mp-gui (render.c, this
addendum and the vendored `third_party/stb_image.h` only). PNGs are decoded
with stb_image (public domain, v2.34); SDL2_image is NOT installed and the
frozen Makefile is NOT modified (HDR/linear stb paths are compiled out so no
`-lm` is needed).

1. **Tiles.** `render_init()` attempts to load `assets/tiles.png` if present.
   Layout is documented in `assets/README.md`: 112x48, 21 cells of 16x16 in a
   7-column x 3-row row-major grid (a 22-cell 112x64 extension adds
   `T_PICKLEBALL` at cell 21). Cell selection: non-zone types use their
   same-named sprite; `T_RES`/`T_COM`/`T_IND` use the base sprite at level 0
   and `T_<TYPE>_L1/_L2/_L3` at levels 1..3. When a usable atlas is loaded,
   sprites replace the flat `fill_rect` tiles in the no-overlay view and also
   supply tree/level detail; `T_PICKLEBALL` uses its flat court drawing when
   cell 21 is absent.
2. **Overlays keep the computed tint path.** The four overlays still recolour
   every tile with `overlay_color()` in the normal view. The A4 `heat.png`
   alpha cells are deliberately NOT substituted: they are five quantised
   60%-alpha swatches over the tile, not visually equivalent to the existing
   continuous per-tile interpolation, so computed tints remain authoritative.
3. **Batch A UI art (manifest A1-A6), all optional.** Layouts are in
   `assets/README.md` and `assets/layout_*.json`.
   - A1 `tools.png` (176x16, 11 cells): replaces the colour swatch on each of
     the 11 sidebar tool buttons, cell order = `pal_tool[]`.
   - A2 `metrics.png` (80x16, 5 cells): a 16x16 icon to the right of each
     scorecard bar (x=886), cells WALKABILITY/GREEN/AMENITIES/YIELD/LIVABILITY.
   - A3 ramp PNGs (180x10 each), `legend_glyphs.png` and `legend_tags.png`
     (64x16, 4 cells): the active ramp/glyph/F-tag sit beside the current
     legend bar; a four-row key (tag + glyph + stepped ramp per mode) replaces
     the keyboard hint lines when all individual PNGs are present. The
     composite `legend_keys.png` (212x64) is the fallback key sheet.
   - A5 `cursors.png` (64x16, HOVER/VALID/INVALID/BULLDOZE) replaces the
     white/dark double outline; the four `cursor_*.png` singles are the
     per-file fallback. Marker choice: BULLDOZE tool -> BULLDOZE, an active
     overlay -> neutral HOVER, otherwise VALID on `T_EMPTY` and INVALID on an
     occupied tile.
   - A6 `hud_topbar.png` (920x40) is drawn as the top-bar background; all
     live text (MASTER PLANNER / DAY / POP / PAUSED) is rendered on top in its
     safe zones exactly as before.
4. **Fallback rule.** A missing, unreadable or wrongly-sized PNG disables only
   that element: its previous flat-rect/text rendering is used, unchanged.
   Nothing is required for `render_init()` to succeed, and `--smoke` (which
   never creates a window) is unaffected. Rendering with the art removed is
   byte-for-byte the v1 appearance, apart from the v1.2 court colour.
