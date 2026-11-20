# Master Planner — Scorecard metric definitions (T4 design)

Status: authoritative for the five `Scorecard` metrics. CONTRACT.md is frozen;
this document refines its defaults ("Defaults if absent", sim.h section) with
exact formulas, planning rationale, and edge cases. Where this document and the
CONTRACT defaults agree, they are the same rule stated more precisely. Where a
CONTRACT phrase was ambiguous, the resolution is marked **Decision** and keeps
the default's intent. T2 (sim engineer) implements this file verbatim; T3 (GUI)
renders the five ints 0..100 as labelled bars.

Research references [R2]..[R7] point at the numbered reference list in
docs/research.md §2; [R§3] is research.md §3 (the developer-audience brief).

---

## 1. Conventions (apply to every metric)

- Grid: `world[GRID_H][GRID_W]`, GRID_W = GRID_H = 40. Coordinates (x, y):
  x = column 0..39, y = row 0..39. Tile access `world[y][x]`.
- **Developed residential tile**: `type == T_RES && level >= 1`.
  Level 0 means "zoned but undeveloped" (research.md §5 data model) and counts
  for nothing except the yield denominator question — it does not; yield uses
  achieved levels only.
- **Zone tile**: type in {T_RES, T_COM, T_IND}. Level range 0..3 (CONTRACT).
- **Green tile**: `type == T_PARK || type == T_WATER ||
  (type == T_EMPTY && world_trees[y][x] == 1)`. Trees live in the parallel
  `world_trees` array (world.h additive note); `Tile.level` on T_EMPTY is NOT
  decoration and must not be read as such.
- **Amenity tile**: type in {T_COM, T_PARK, T_SCHOOL, T_POLICE, T_FIRE}.
  Services count at any level — a placed school serves the neighbourhood the
  day it is built, which matches the sandbox's "instantly visible consequences"
  goal [R§3].
- **Distance**: Chebyshev. `cheb(a, b) = max(abs(ax-bx), abs(ay-by))`.
  "Within radius r" means `cheb <= r`, inclusive. Rationale: on a square tile
  grid with no diagonal streets modelled, the Chebyshev ball is the honest
  walking catchment; SimCity's own service radii are circular areas on the same
  square grid [R2, mechanics 6], and radius-4/5 balls are our 5-minute and
  ~6-minute walk proxies (see §2.1).
- **Arithmetic**: all sums in `int` (worst case 1600 tiles x 3 = 4800, safe).
  Every percentage is computed as `pct(n, d) = d > 0 ? (100 * n) / d : 0`
  — integer division, truncation toward zero, no floating point anywhere.
- **Clamping**: every metric ends with `clamp(v) = v < 0 ? 0 : (v > 100 ? 100 : v)`.
- **Empty-set conventions**: a metric whose denominator is 0 scores **0**
  (nothing built yet = nothing achieved). Exception: the pollution penalty in
  livability is 0 when there are no residents (§2.5). These conventions make
  every field well-defined on a fresh map, so `--smoke` JSON is always sane.
- Metrics are recomputed at the end of every `sim_tick()`, after growth/decay
  (CONTRACT tick order), and reflect the grid state at that instant.
  `sim_scorecard()` returns the latest values plus population/jobs/day from
  the world API. Metrics never mutate the world.

---

## 2. The five metrics

### 2.1 walkability — homes within a short walk of daily needs

**Formula**

    N = number of developed RES tiles
    W = number of developed RES tiles with at least one tile of type
        T_COM, T_PARK, or T_SCHOOL at Chebyshev distance <= 4
    walkability = N > 0 ? clamp(100 * W / N) : 0

Radius 4 (a 9x9 catchment, 81 tiles) is the CONTRACT default. Planning
rationale: at ~80 m per tile this is a ~320 m / 5-minute walk — the standard
"daily needs within a short walk" catchment used in walkable-neighbourhood
design, and the metric research.md §3 asks for first ("homes within walking
distance of shops + amenities"). It deliberately accepts ANY of shop/park/
school, not all three: mixed-use proximity is the walkability signal; requiring
all three is the stricter amenity metric (§2.3). This mirrors SimCity's
desirability model where nearby commerce and parks raise residential value
[R2, mechanics 4; R3 growth gates].

Implementation note: one pass over developed RES tiles, scanning the 9x9
window clipped to the grid; early-exit on first match. O(N * 81) worst case,
trivial at 40x40.

Edge cases: undeveloped RES (level 0) excluded; a RES tile does not satisfy
itself; COM/PARK/SCHOOL count regardless of their level or powered state.

### 2.2 green — share of the plan that is green/open space

**Formula**

    G = number of green tiles (definition in §1) over the whole grid
    green = clamp(100 * G / (GRID_W * GRID_H))      /* denominator always 1600 */

CONTRACT default, unchanged. Rationale: developers and planners read green
coverage as a site-wide ratio (open-space standards are expressed as % of site
area); SimCity's land-value model rewards parks and water terrain [R2,
mechanics 4], and research.md §3 lists "Green & open space coverage (% of
tiles)" verbatim. Existing trees count: clearing forest for a subdivision
visibly costs green score, which is exactly the trade-off the tool should
surface [R§3 comparison of alternative layouts].

Baseline (regression anchor): on a fresh `world_init()` map the deterministic
terrain yields green = **21** (verified by compiling world.c and counting:
157 water tiles + 190 forest tiles = 347 green of 1600; 100*347/1600 = 21).
Any implementation reporting a different fresh-map green value has a bug in
terrain generation or in this metric.

Edge cases: T_EMPTY without trees is NOT green (it is developable land);
T_ROAD/T_POWERLINE etc. are never green even if a tree flag were stale —
the type check comes first. `world_place` clears trees, `world_bulldoze`
clears trees, so the flag is only meaningful on T_EMPTY anyway.

### 2.3 amenities — homes near BOTH a school and shops

**Formula**

    N = number of developed RES tiles
    A = number of developed RES tiles that have
        (at least one T_SCHOOL at cheb <= 5) AND
        (at least one T_COM   at cheb <= 5)
    amenities = N > 0 ? clamp(100 * A / N) : 0

Radius 5 and the school+shops pairing are the CONTRACT default.
**Decision (ambiguity resolution):** the default's phrase "within radius 5 of
SCHOOL and radius 5 of COM" is read as a per-home AND (each counted home needs
both), not as two independent percentages averaged. Rationale: the metric is
"amenity coverage" for residents — a home with a school but no shops is not
covered. This is the family-neighbourhood test from research.md §3 ("schools,
parks, retail, services within a radius"): school + daily retail is the minimum
credible pair. Parks/police/fire already enter walkability (§2.1) and land
value (CONTRACT tick order), so they are not double-counted here.

Implementation note: same 11x11 window scan as walkability (121 tiles), track
two booleans (saw_school, saw_com), early-exit when both true.

Edge cases: one school may satisfy many homes (no capacity model in v1 —
research.md §4 keeps the sim local/neighbour-based); services count at any
level; COM must be type T_COM (a zoned-but-undeveloped COM still counts as a
future shop location — **Decision:** type-based, level-independent, consistent
with §1 amenity rule and with walkability).

### 2.4 yield — how much of the plan's development potential is built

**Formula**

    L = sum of level over ALL zone tiles (T_RES + T_COM + T_IND)
    Z = number of zone tiles (any level, including 0)
    yield = Z > 0 ? clamp(100 * L / (3 * Z)) : 0

**Decision (ambiguity resolution):** CONTRACT says "developed level-sum /
theoretical max * 100". The theoretical maximum is defined as **3 per zoned
tile** (max level is 3 per CONTRACT growth rules), i.e. denominator 3*Z over
all zoned tiles. Rationale: this is the developer's absorption question —
"of what I zoned, how much actually got built?" Zoning land that never develops
(low land value, no road, no power) lowers yield, which makes the metric a
honest signal about plan quality rather than a reward for hoarding empty
zones. It is the density/yield metric of research.md §3 ("developable floor
area hint — the developer's bottom line") and echoes the manual's
balance rule of thumb R ≈ C + I [R2 manual; R§3]: a plan that zones only
housing with no jobs floor area still shows its imbalance through jobs vs
population in the HUD.

Equivalent integer form: `yield = clamp((100 * L) / (3 * Z))`. Do NOT compute
per-tile percentages and average — truncation must happen once, at the end.

Edge cases: no zones at all → 0. Level-0 zones count in Z but contribute 0 to
L. Non-zone buildings (schools, plants, parks...) do not enter yield.

### 2.5 livability — the blended index, minus pollution burden

**Formula**

    base     = (walkability + green + amenities + yield) / 4   /* integer mean */
    P        = sum of Tile.pollution over developed RES tiles
    N        = number of developed RES tiles
    penalty  = N > 0 ? P / (2 * N) : 0        /* mean pollution / 2, truncated */
    livability = clamp(base - penalty)

CONTRACT default: "mean of the four, minus pollution penalty".
**Decision (penalty definition):** penalty = floor(mean pollution of developed
residents / 2). Rationale:

- Pollution is the one externality the four positive metrics do not capture;
  SimCity's desirability subtracts pollution from land value [R2, mechanics 4,
  5; R4 engine findings], and research.md §3's liveability candidate is
  "land value − pollution − crime blended". Crime already suppresses growth
  and land value upstream (CONTRACT tick order), so subtracting it again here
  would double-count; pollution reaches residents directly and is not otherwise
  penalised in the scorecard.
- Scaling by 1/2 keeps livability usable: `Tile.pollution` is uint8 (0..255);
  a heavily polluted home (pollution ≈ 100) costs 50 points, which is severe
  but recoverable by moving industry downwind / adding park buffers — the
  comparison behaviour the tool exists for [R§3]. An unscaled mean would pin
  livability at 0 for any plan with industry, hiding all other signal.
- Mean over developed RES only: pollution on empty land or industry tiles
  harms nobody yet; the index measures lived experience.

Order of operations (normative): compute the four metrics first, integer-mean
them, then subtract the integer penalty, then clamp. Do not clamp base before
subtracting (base is already 0..100 by construction).

Edge cases: N = 0 → penalty 0, livability = base (a greenfield plan with nice
parks scores on its merits; there are no residents to poison yet).

---

## 3. Reference implementation (normative pseudocode)

T2 may structure the code differently but must produce identical integers.

    static int clamp100(int v){ return v < 0 ? 0 : (v > 100 ? 100 : v); }
    static int pct(int n, int d){ return d > 0 ? (100 * n) / d : 0; }
    static int cheb(int ax,int ay,int bx,int by){
        int dx = ax-bx; if (dx < 0) dx = -dx;
        int dy = ay-by; if (dy < 0) dy = -dy;
        return dx > dy ? dx : dy;
    }
    /* window scan helper: does any tile of type t exist within radius r
       of (x,y), clipped to grid? */
    static int near_type(int x,int y,int r,TileType t){
        for (int yy = y-r; yy <= y+r; yy++)
            for (int xx = x-r; xx <= x+r; xx++)
                if (xx>=0 && xx<GRID_W && yy>=0 && yy<GRID_H
                    && world[yy][xx].type == t) return 1;
        return 0;
    }

    int n = 0, w = 0, a = 0, poll_sum = 0, L = 0, Z = 0, G = 0;
    for (y,x over grid) {
        Tile *t = &world[y][x];
        if (t->type==T_PARK || t->type==T_WATER ||
            (t->type==T_EMPTY && world_trees[y][x])) G++;
        if (t->type==T_RES || t->type==T_COM || t->type==T_IND) {
            Z++; L += t->level;
        }
        if (t->type==T_RES && t->level >= 1) {
            n++; poll_sum += t->pollution;
            if (near_type(x,y,4,T_COM) || near_type(x,y,4,T_PARK)
                || near_type(x,y,4,T_SCHOOL)) w++;
            if (near_type(x,y,5,T_SCHOOL) && near_type(x,y,5,T_COM)) a++;
        }
    }
    sc.walkability = clamp100(pct(w, n));
    sc.green       = clamp100(pct(G, GRID_W*GRID_H));
    sc.amenities   = clamp100(pct(a, n));
    sc.yield       = clamp100(Z > 0 ? (100*L)/(3*Z) : 0);
    int base = (sc.walkability + sc.green + sc.amenities + sc.yield) / 4;
    int penalty = n > 0 ? poll_sum / (2*n) : 0;
    sc.livability  = clamp100(base - penalty);

Complexity: O(1600 * 121) worst case per tick ≈ 194k tile reads — fine at one
tick per 500 ms. No allocation, no floats, deterministic.

## 4. Sanity anchors for tests (T2) and QA

1. Fresh `world_init()` map, zero placements: walkability 0, amenities 0,
   yield 0, green **21**, livability **5** (= (0+21+0+0)/4, no residents).
2. All five fields in 0..100 after every tick, on any grid (QA invariant).
3. One developed RES with a COM at cheb exactly 4 → walkability 100; at
   cheb 5 → walkability 0 (boundary inclusive). Same pattern for amenities
   with radius 5 (needs school AND com).
4. Adding a park on a formerly empty tile raises green by 0 or 1 point
   (100/1600 truncates to 0 per tile; 16 parks = +1). Green never decreases
   when a T_EMPTY-with-tree becomes T_PARK (both count).
5. Bulldozing all zones → yield 0, walkability 0, amenities 0 (empty-set rule).
6. Monotonicity: raising any developed RES tile's pollution field cannot
   raise livability; removing all pollution cannot lower it.

## 5. What this document deliberately does NOT define

Power flood-fill, pollution diffusion kernel, crime model, land-value formula,
growth/decay thresholds: those are T2's simulation design under the CONTRACT
tick order, not scorecard definitions. The scorecard only READS their outputs
(`Tile.pollution`, `Tile.level`). Balance (R ≈ C + I) and connectivity from
research.md §3 are v2 candidates; v1 ships exactly the five frozen fields.