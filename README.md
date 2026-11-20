# Master Planner

A SimCity-style **master planned community builder** — a fast, minimal native
prototype to inspire property developers. Paint a plan (zones, streets, parks,
amenities) on a 40×40 tile grid and watch a live scorecard tell you how good a
place it is to live and invest. No failure states, no bankruptcy — a sandbox
for spatial thinking, in the spirit of the original 1989 SimCity.

Built in C11 + SDL2. Flat top-down tile graphics (SVG-sourced sprite atlas with
a zero-asset fallback). One `make` to build, one binary to run.

> First-pass README. The release card (T6) will extend this with demo plans,
> screenshots, and the full architecture map.

## Requirements

- Linux (Wayland or X11), gcc, make, pkg-config
- SDL2 and SDL2_ttf development packages

Arch / Omarchy:

```sh
sudo pacman -S sdl2 sdl2_ttf
```

Debian / Ubuntu:

```sh
sudo apt install build-essential pkg-config libsdl2-dev libsdl2-ttf-dev
```

Fedora:

```sh
sudo dnf install gcc make pkgconf-pkg-config SDL2-devel SDL2_ttf-devel
```

Optional (only for regenerating art from SVG sources): `librsvg`
(`rsvg-convert`) and ImageMagick.

## Build & run

```sh
git clone https://github.com/john-stalvern/master-plan-build-sim.git
cd master-plan-build-sim
make
./masterplanner
```

Headless checks (no window needed):

```sh
make test                      # unit tests + 50-tick smoke run
./masterplanner --smoke        # scripted plan, 200 ticks, scorecard JSON
./masterplanner --smoke --ticks 400
```

Example smoke output:

```json
{"walkability":42,"green":20,"amenities":0,"yield":16,"livability":18,"population":84,"jobs":36,"day":200}
```

## Controls

| Input | Action |
|---|---|
| Left click / drag on map | Paint with the selected tool |
| Sidebar click | Select tool |
| `1`–`9`, `0`, `-` | Tools: bulldoze, road, residential, commercial, industrial, park, school, police, fire, power plant, power line |
| **Ctrl + click a park** | Convert it to a **pickleball court** 🏓 |
| `F1` / `F2` / `F3` / `F4` | Overlays: land value / pollution / power / crime |
| `Esc` | Clear overlay (or quit if none) |
| `Space` | Pause / resume simulation |
| `S` / `L` | Save / load plan (`plan.bin`) |
| `Q` | Quit |

## How it works

You **zone**; the simulation decides whether development happens. Each tick
(one simulated day, ~0.5 s):

1. Power floods from plants across power lines to adjacent zones.
2. Pollution diffuses from industry, roads and coal plants.
3. Crime rises where land value is low and police are far.
4. Land value = downtown bonus + park/water adjacency − pollution − crime.
5. Zones grow (level 0→3) only with road access + power + desirability;
   otherwise they decay.

The scorecard (0–100 each) reads the result:

- **Walkability** — developed homes near shops/parks/schools (radius 4)
- **Green** — share of park, water and forest tiles
- **Amenities** — homes within radius 5 of a school and of commerce
- **Yield** — developed density vs theoretical maximum
- **Livability** — blend of the four, minus pollution penalty

Pickleball courts count as recreational green space, exactly like parks.

Definitions: `docs/scorecard.md`. Pattern stamps (village centre, green spine,
transit node, …): `docs/patterns.md`. Full interface contract: `docs/CONTRACT.md`.

## Repository layout

```
main.c      window, input, timing, --smoke harness
world.c/h   tile grid, placement, save/load
sim.c/h     simulation tick + scorecard
render.c/h  tiles, sprites, palette, HUD, overlays
assets/     SVG sources + PNG atlases (optional; flat fallback without them)
tests/      headless unit tests
docs/       contract, research, scorecard, patterns, asset manifest
```

Sprites are optional: with `assets/` present the app renders the tile atlas and
UI icons; without it, everything falls back to flat colour rectangles.

## Project status

Prototype under active multi-agent development (Hermes kanban board
`master-planner`). Core loop, GUI, simulation, sprite art and the pickleball
feature are implemented; QA and release polish are in progress.

Research & design brief: `docs/research.md`.
