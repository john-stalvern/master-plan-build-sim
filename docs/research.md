# Master Planner — research & brainstorm (phase 0)

Goal: an extremely quick, minimal-code, minimal-graphics **native** prototype of a
SimCity-style "master planned community builder", used to inspire property
developers. This document is the research and design brief before writing code.

---

## 1. What this machine can actually run (verified, not assumed)

Measured on this box (Omarchy / Arch, kernel 7.2.15, x86_64, 8 cores, 30 GB RAM,
Wayland session with X11 also available):

| Capability | Status | Notes |
|---|---|---|
| gcc / g++ / clang | present | C is fully viable |
| Rust / Go | absent | would need install |
| SDL2 2.32.74 | **installed & working** | compiled, linked and initialised OK |
| SDL2 Wayland + X11 drivers | **both work** | native window is guaranteed |
| SDL2_ttf 2.24.0 | installed | text labels possible |
| SDL2_image / SDL2_gfx | absent | not needed for primitive graphics |
| raylib 6.2-1 | available in pacman | not installed; `pacman -S raylib` is ~2.4 MB |
| Python 3.14 tkinter | **broken** | `libtk8.6.so` missing — Python GUI is not a shortcut here |
| pygame / numpy / PIL | absent | would need venv + pip installs |
| Node / npm | present | web route possible, but not "native app" |

Conclusion: **C + SDL2** is the lowest-friction native path. It needs zero installs,
one `gcc` line to build, and produces a real window on this desktop. raylib is the
"even fewer lines" alternative if you accept one `pacman -S`.

---

## 2. What the original SimCity actually did (the parts worth stealing)

SimCity 1989 (Will Wright, written in C) is a **cellular automaton on a tile grid**.
Source was later released as Micropolis under GPLv3, which is useful as a reference.

Core loop, distilled:

1. **Grid of tiles.** Each tile is one of: empty/forest/water, road/rail, power
   line, one of three zones (residential, commercial, industrial), or a service
   building. Original maps were roughly 40x40 tiles.
2. **You zone, the Sims decide.** Placing a zone does not create a building. It
   creates *permission* for development, which grows or decays over time.
3. **Growth gates.** A zone develops only if it has road access, power, and
   sufficient desirability. Original zones check their 12 surrounding tiles for a
   road/rail; no road = decline. Commercial zones additionally need "deliveries"
   (a traffic simulation) and get a downtown bonus that fades to a penalty at the
   map edge.
4. **Land value is the central currency.** Computed from: terrain (water/trees/parks
   raise it), accessibility (roads/transit), crime (higher crime lowers value, lower
   value raises crime — a feedback loop), pollution, and distance to downtown.
5. **Pollution & crime diffuse outward** from sources (industry, coal plants, roads)
   and are averaged in 4x4 blocks, then blended with neighbours.
6. **Services have radius.** Police/fire/stadium/airport/power affect a circular
   area; underfunding shrinks effective coverage.
7. **Economy & feedback.** Taxes fund services; budget allocation and tax rate feed
   back into desirability and growth. Disasters (fire, tornado, meltdown) reset areas.
8. **Overlay views** are a huge part of the experience: power, crime, pollution,
   land value, traffic, police/fire coverage. They make the invisible model legible.
9. **Score/evaluation screen** at the end rates the city.

Key design lesson: the game is fun because **one placement causes visible ripple
effects through several coupled systems**, and the overlays let you *see* them.
That — not the graphics — is what a prototype must preserve.

Useful primary references:
- Manual scan with mechanics & "good city form" discussion: https://users.ox.ac.uk/~uzdm0006/scans/sim/manual.html
- Analysis of the algorithm by a planner: https://www.njurbanthinker.org/blog/the-programming-language-and-algorithms-of-simcity-and-how-land-use-planners-can-learn-from-it
- Reverse-engineered diagrams: https://smalltalkzoo.computerhistory.org/users/Dan/uploads/SimCityReverseDiagrams.pdf
- Detailed engine findings (growth gates, downtown bonus, 4x4 pollution, land-value wrap bug): https://www.jeffquast.com/post/a-perfect-simcity/
- Reference implementations: https://github.com/SimHacker/micropolis (original-style C), https://github.com/SimHacker/MicropolisCore (C++), https://github.com/zeikar/cimulity (modern open-source city builder, TypeScript)

---

## 3. The twist: "master planned community builder"

This is **not** really a game about budgets and disasters. The audience is property
developers, and the purpose is *inspiration*: "show me what a good plan looks like
and how my choices change it." That changes the feature priorities:

| SimCity emphasises | This tool should emphasise |
|---|---|
| Money, taxes, bankruptcy | Spatial quality indicators (no failure state) |
| Organic growth over decades | Instantly visible consequences of a plan |
| Survival & disasters | Comparison of alternative layouts |
| City-wide simulation | Human-scale, walkable neighbourhood design |
| "Did my city survive?" | "Is this a good place to live / invest?" |

So the prototype's heart should be:
- Fast painting of a **plan** (zones, streets, green space, amenities).
- A live **scorecard** with the metrics developers care about.
- **Heatmap overlays** that explain *why* a score is what it is.
- Optional **pattern stamps** (e.g. "village centre", ".transit node", "green spine")
  that drop a coherent mini-neighbourhood in one click — this is the single most
  inspiring feature for a design tool and is cheap to implement.

Candidate scorecard metrics (pick a small subset for v1):
- Walkability / mixed-use: homes within walking distance of shops + amenities.
- Green & open space coverage (% of tiles).
- Amenity coverage: schools, parks, retail, services within a radius.
- Balance: residential vs commercial vs industrial ratio (like the manual's rule
  of thumb: R ≈ C + I).
- Density / yield: developable floor area hint (the developer's bottom line).
- Liveability index: land value − pollution − crime, blended into one number.
- Connectivity: % of zones with road access.

---

## 4. Recommended v1 scope ("first SimCity" proof of concept)

Keep it to roughly **400–800 lines of C in 3–5 files**, no engine, no assets.
Everything drawn as filled rectangles with a few letters/symbols.

Must have:
- 40x40 tile grid, ~16 px tiles, window ~900x700, fixed timestep loop.
- Tool palette: bulldoze, road, residential, commercial, industrial, park, school,
  police, fire, power plant, power line. Click + drag to paint.
- One simulation tick every ~500 ms: recompute power flood-fill, desirability and
  development level per tile; grow/decay zones.
- Text HUD: money, population, day/year, and 4–6 scorecard numbers.
- Overlay toggles: land value, pollution, crime, power coverage.
- Pause / speed control.
- Save & load plan to a plain binary file (a single `fwrite` of the grid).

Explicitly out of v1:
- Disasters, taxes/budget sliders, traffic pathfinding, UI tooling, sprite art,
  sound, multiplayer, terrain elevation, water simulation, isometric view.
  (These are v2 candidates, not prerequisites for the concept.)

Why this scope: it is small enough to finish in one sitting, but contains the full
feedback loop — *zone → infrastructure → desirability → growth → metric → overlay*
— which is the thing being proven.

---

## 5. Minimal architecture

```
main.c        initialisation, event loop, timing, input dispatch
world.c/h     tile grid, tile enum, place/bulldoze, save/load
sim.c/h       one tick: power flood-fill, land value, pollution, crime, growth
render.c/h    SDL2 drawing: tiles, hover cursor, HUD, overlays, palette
```

Data model — keep it a flat array of small structs, no pointers between tiles:

```c
typedef enum { T_EMPTY, T_WATER, T_ROAD, T_POWERLINE, T_POWERPLANT,
               T_RES, T_COM, T_IND, T_PARK, T_SCHOOL, T_POLICE, T_FIRE,
               T_COUNT } TileType;

typedef struct {
    uint8_t type;       /* TileType */
    uint8_t level;      /* 0 = zoned but undeveloped, 1..3 = density */
    uint8_t powered;
    uint8_t landValue;  /* 0..255 */
    uint8_t pollution;
    uint8_t crime;
} Tile;

Tile world[40][40];
```

Simulation tick (deliberately simple, all local/neighbour-based):
1. Flood power from each plant across power lines and adjacent tiles.
2. For each tile: pollution = weighted sum of nearby industry/roads/plants,
   decayed with distance. Crime = f(low land value, distance to police).
3. Land value = base + downtown bonus + green/water bonus − pollution − crime.
4. For each zoned tile: desirability = land value + road adjacency + power +
   demand for that zone type. If desirability > threshold, level++; if < lower
   threshold, level--. Population/jobs derived from residential/commercial levels.
5. Recompute scorecard metrics.

Rendering: one `SDL_Rect` per tile; colour by type, brightness by `level`;
overlay modes recolour by the selected metric. Use SDL2_ttf for the HUD, or draw
a tiny built-in bitmap font if you want to avoid even that dependency.

Build command:
```
gcc -O2 -Wall -o masterplanner main.c world.c sim.c render.c $(pkg-config --cflags --libs sdl2 SDL2_ttf)
```

---

## 6. Risks & decisions to settle before coding

1. **Sandbox vs game.** If it must "inspire developers", a no-failure sandbox with
   a scorecard is more honest than a budget-survival game. Recommended: sandbox.
2. **What defines a "good" plan.** Need to agree on the 4–6 scorecard metrics —
   this defines the product more than any other choice.
3. **Stack.** SDL2/C (zero installs, verified here) vs raylib (fewer lines, one
   install) vs web/HTML (easy to share, but not a native app).
4. **Visual style.** Flat top-down colour blocks are the authentic "first SimCity"
   look; isometric is much more work and not needed for the concept.
5. **Scope creep.** The template/preset pattern stamps are high-value and cheap;
   traffic simulation and disasters are high-cost and can wait.

---

## 7. Decisions settled (confirmed with user)

- **Stack:** SDL2 + C. Zero installs, verified working on this machine.
- **Framing:** no-failure sandbox + spatial scorecard. No bankruptcy, no disasters.
- **Scorecard:** all four metrics — walkability/mixed-use, green & open-space
  coverage, amenity coverage, density/yield potential (plus a blended liveability
  index derived from them).
- **Visuals:** flat top-down colour tiles, authentic first-SimCity look.

These replace the open questions in section 6 as the chosen direction.

---

## 8. Suggested roadmap after this research

- **Phase 0 — this doc.** Research + agreed decisions.
- **Phase 1 — walking skeleton:** window, grid, paint road + three zones, HUD.
  Testable in an afternoon.
- **Phase 2 — feedback loop:** power, land value, pollution, growth/decay.
- **Phase 3 — planner value:** scorecard + overlay views + pattern stamps.
- **Phase 4 — polish:** save/load, presets, speed control, a "before/after"
  comparison view, export image/text report for developer presentations.
