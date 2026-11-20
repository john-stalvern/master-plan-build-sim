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
