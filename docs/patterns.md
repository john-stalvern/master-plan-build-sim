# Master Planner — one-click neighbourhood pattern stamps (T4 design)

Five coherent mini-neighbourhoods a developer can drop onto the 40x40 grid in
one click. Each is an **exact tile layout** using the CONTRACT.md `TileType`
names, with a recommended anchor, a tile census, measured scorecard impact, and
a short "why this works for developers" note. These are the pattern stamps
research.md §3 calls "the single most inspiring feature for a design tool …
cheap to implement", and §6.5 rates high-value / low-cost.

Status: design spec. Stamping UI is NOT in the frozen v1 palette (CONTRACT
lists exactly 11 tools); this document defines the layouts so a stamp feature
(v2, or a GUI extension) can place them verbatim. Every layout below was
verified by compiling against `world.c` and asserting placement, road access,
power connectivity, and resulting metrics — see §6.

---

## 1. Encoding & placement rules (normative)

Each stamp is a rectangle of `w` columns x `h` rows. Row strings are written
top (north) to bottom (south); character position `c` in row `r` maps to grid
tile `(x = ax + c, y = ay + r)` where `(ax, ay)` is the stamp's top-left anchor.
One character = one tile, using this legend (letters are mnemonics, the right
column is the frozen `TileType`):

| Char | TileType     | Meaning                          |
|------|--------------|----------------------------------|
| `R`  | T_ROAD       | street                           |
| `L`  | T_POWERLINE  | power line                       |
| `P`  | T_POWERPLANT | power plant                      |
| `H`  | T_RES        | residential zone (H = housing)   |
| `C`  | T_COM        | commercial zone (shops)          |
| `I`  | T_IND        | industrial zone                  |
| `G`  | T_PARK       | park / green space               |
| `S`  | T_SCHOOL     | school                           |
| `O`  | T_POLICE     | police station                   |
| `F`  | T_FIRE       | fire station                     |
| `.`  | (no place)   | leave the existing tile untouched|

Placement algorithm (identical for every stamp):

    for r in 0..h-1:
      for c in 0..w-1:
        ch = rows[r][c]
        if ch == '.': continue                 # skip, keep existing tile
        world_place(ax + c, ay + r, tiletype(ch))

`world_place` returns 0 only when the target tile is `T_EMPTY` (it clears any
tree); it returns -1 on water or occupied tiles. **All five recommended anchors
were verified to place with zero failures on a fresh `world_init()` map, both
individually and all five together.** If a user re-anchors a stamp onto water or
existing buildings, the failing tiles are simply skipped (the -1 return) — the
stamp degrades gracefully rather than corrupting the map. A stamp never
bulldozes; it only fills empty land.

Power topology (why every stamp has a left-edge `L` column): the CONTRACT
flood-fills power from plants across `T_POWERLINE` + adjacent zones. To be
robust under the strictest reading (power travels only along connected
powerlines), each stamp carries a **contiguous powerline network**: a vertical
riser in column 0 links every horizontal line row back to the plant `P`, and
every zone tile is 4-adjacent to a lit line or the plant. Verified: every zone
in every stamp is powered under strict line-only conduction. Roads, parks and
schools do not conduct.

Road access: every zone tile has a `T_ROAD` in its 8-neighbourhood (Chebyshev
<= 1), satisfying the CONTRACT growth gate. Verified for all zones.

---

## 2. village-centre

A mixed-use main street: shops and homes flank a central green/school square,
with a second school-and-shops row serving the southern housing blocks, all on
a four-road grid. The classic "village centre" the brief names first.

- Anchor `(ax, ay) = (2, 2)`, size **13 x 13** (169 tiles).
- Census: 48 ROAD, 48 POWERLINE, 1 POWERPLANT, 41 RES, 18 COM, 7 PARK, 6 SCHOOL.

```
LRRRRRRRRRRRR
LCHHGGGGGHHCC
PLLLLLLLLLLLL
LCHHGSSSGHHCC
LRRRRRRRRRRRR
LHHHHHHHHHHHH
LLLLLLLLLLLLL
LHHHHHHHHHHHH
LRRRRRRRRRRRR
LCCCCSSSCCCCC
LLLLLLLLLLLLL
LCHHHHHHHHHCC
LRRRRRRRRRRRR
```

Measured (isolated, all zones developed to level 3): walkability **100**,
green 19, amenities **100**, yield **100**, livability **79**; 41 developed
homes. Every home is within a 4-tile walk of a shop/park/school AND within 5 of
both a school and shops.

**Why this works for developers:** it is the highest-confidence "good plan"
starting point — a walkable, mixed-use core where every home has daily needs
and a school nearby. Dropping it instantly shows a near-max scorecard, so a
developer sees what "good" looks like before customising. The central square
(park + school) is the community anchor; the shop rows front the streets.

---

## 3. green-spine

A two-row linear park corridor with housing on both flanks, corner shops and
three small schools dotted along the edges so every home has amenities within
reach. The "green spine" the brief names.

- Anchor `(ax, ay) = (2, 17)`, size **15 x 8** (120 tiles).
- Census: 28 ROAD, 35 POWERLINE, 1 POWERPLANT, 21 RES, 4 COM, 28 PARK, 3 SCHOOL.

```
LRRRRRRRRRRRRRR
LHHSCHHHCHSHHHC
PLLLLLLLLLLLLLL
LGGGGGGGGGGGGGG
LGGGGGGGGGGGGGG
LLLLLLLLLLLLLLL
LHHHHHHSHHHHHHC
LRRRRRRRRRRRRRR
```

Measured (isolated, developed): walkability **100**, green **21**, amenities
**100**, yield **100**, livability **80**; 21 developed homes. The 28 park
tiles are the largest green contribution of any stamp.

**Why this works for developers:** it demonstrates the green-coverage lever in
isolation — a park spine that raises the green metric and land value (park
adjacency) while keeping every home walkable. It is the template for
"open space as the organising element", a strong selling point for
family-oriented subdivisions. Pair it with a village-centre to see green +
mixed-use compose.

---

## 4. transit-node

A dense transfer hub: a school+shops node at top, a commercial spine through
the middle, housing rings above and below, stitched by a three-row road grid.
The "transit node" the brief names (transit is abstracted as a dense mixed-use
node — v1 has no rail tool).

- Anchor `(ax, ay) = (13, 27)`, size **11 x 9** (99 tiles).
- Census: 30 ROAD, 28 POWERLINE, 1 POWERPLANT, 17 RES, 20 COM, 3 SCHOOL.

```
LRRRRRRRRRR
LCCCSSSCCCC
LLLLLPLLLLL
LHHHCCCHHHH
LRRRRRRRRRR
LHHHHHHHHHH
LLLLLLLLLLL
LCCCCCCCCCC
LRRRRRRRRRR
```

Measured (isolated, developed): walkability **100**, green 20, amenities
**100**, yield **100**, livability **80**; 17 developed homes. Highest
commercial ratio of the five (20 COM) — a jobs/retail anchor.

**Why this works for developers:** it shows density around a node — the
"build up around the station" pattern. High commercial floor area means high
jobs (see HUD), and the tight road grid keeps everything walkable. It is the
template for a town centre or a transit-oriented development, and its compact
footprint leaves room for other stamps.

---

## 5. school-cluster

A family campus district: two school rows bracketing a park commons, housing
between, and police/fire stations anchoring the bottom corners. The "school
cluster" the brief names.

- Anchor `(ax, ay) = (31, 2)`, size **9 x 10** (88 tiles placed, 2 skipped).
- Census: 26 ROAD, 20 POWERLINE, 1 POWERPLANT, 19 RES, 5 COM, 9 PARK, 6 SCHOOL,
  1 POLICE, 1 FIRE. The two `.` cells (bottom row, positions 1 and 7) leave the
  underlying tile untouched.

```
RRRRRRRRR
CHHHHHHHC
PLLLLLLLL
LHHSSSHHC
LRRRRRRRR
LHHGGGHHG
LLLLLLLLL
CHHSSSHHC
RRRRRRRRR
O.GGGGG.F
```

Measured (isolated, developed): walkability **100**, green **22**, amenities
**100**, yield **100**, livability **80**; 19 developed homes. The only stamp
with police + fire, so it also demonstrates the safety services (which act
upstream on crime/land value, not as a direct scorecard term — see
scorecard.md §1).

**Why this works for developers:** it is the "family neighbourhood" archetype —
schools and a park commons at the heart, safety services at the edge. It shows
how amenity coverage (school + shops within 5) can be guaranteed for every home
by design, which is exactly what a developer marketing to families wants to
see. The police/fire corners illustrate service placement without cluttering
the core.

---

## 6. garden-works

A jobs district: an industry row buffered from the housing row by a two-tile
park greenbelt (plus line rows), with a shop row serving the homes at the south
edge. An original pattern showing industry done responsibly.

- Anchor `(ax, ay) = (31, 14)`, size **9 x 10** (90 tiles).
- Census: 16 ROAD, 33 POWERLINE, 1 POWERPLANT, 11 RES, 5 COM, 8 IND, 16 PARK.

```
LRRRRRRRR
LIIIIIIII
PLLLLLLLL
LGGGGGGGG
LGGGGGGGG
LLLLLLLLL
LHHHHHHHH
LRRRRRRRR
LCCHHHCCC
LLLLLLLLL
```

Measured (isolated, developed): walkability **100**, green **22**, amenities
**0**, yield **100**, livability **55**; 11 developed homes. Amenities is 0 by
design — this is an industrial district with no school; its homes are all
walkable (100) via the parks and shops. The 8 IND tiles generate jobs and
pollution; the 16-tile park greenbelt is the buffer.

**Why this works for developers:** it teaches the industry-buffering trade-off
visibly. Industry brings jobs (the developer's bottom line) but pollution;
separating it from homes by a park greenbelt is the standard mitigation, and
the scorecard/overlays show the effect (pollution overlay, livability penalty).
It is the honest counterpoint to the residential stamps — a complete plan needs
jobs, and this shows how to place them without poisoning the homes. Combine
with a school-bearing stamp to lift the combined amenities score.

---

## 7. Combining stamps & verification evidence

All five stamps placed together at their recommended anchors on one fresh map
(verified, zero placement failures, no overlap with each other or the river/lake):

| Metric       | Combined value |
|--------------|----------------|
| walkability  | 100            |
| green        | 20             |
| amenities    | 89             |
| yield        | 100            |
| livability   | 77             |

Combined census: 109 RES, 52 COM, 8 IND, 60 PARK, 18 SCHOOL, 148 ROAD,
164 POWERLINE, 5 POWERPLANT, 1 POLICE, 1 FIRE (157 WATER and 877 EMPTY remain).
At full development: **population 1308, jobs 540**. Combined amenities is 89
(not 100) precisely because garden-works' 11 homes have no school within 5 —
the metric is doing its job, and adding a school near garden-works would close
the gap. This is the "comparison of alternative layouts" behaviour the brief
wants [research.md §3].

Anchor map (top-left of each stamp on the 40x40 grid):

    village-centre  (2, 2)    green-spine   (2, 17)
    transit-node    (13, 27)  school-cluster(31, 2)
    garden-works    (31, 14)

Verification method (reproducible): a scratch C harness links the repo's
`world.c`, calls `world_init()`, applies each stamp via `world_place`, asserts
(a) zero placement failures, (b) every zone has a road in its 8-neighbourhood,
(c) every zone is powered under strict line-only BFS from the plant, then sets
all zones to level 3 and computes the scorecard.md formulas. Result on the
project's -O2 build: **ALL CHECKS PASSED, exit 0**, for each stamp isolated and
all five combined. The fresh-map baseline (green 21, livability 5) and the
radius-boundary / yield-truncation anchors in scorecard.md §4 also pass. Layouts
place cleanly under -O0 as well (only the fresh-map tree baseline differs, due
to the world.c terrain-hash UB noted in scorecard.md §2.2 — not a stamp issue).

Design notes for whoever implements stamping:
- Stamps only fill `T_EMPTY`; they never bulldoze. Re-anchoring onto water or
  buildings skips those tiles (world_place returns -1). Consider a ghost
  preview that greys out blocked cells before committing.
- The left-edge powerline riser is load-bearing for power connectivity; do not
  strip column 0 when adapting a layout.
- These five are a starting library. The encoding (rect + char rows + anchor)
  is trivially extensible — add more stamps as data, no new code paths.