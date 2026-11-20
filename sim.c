/* sim.c — simulation engine for Master Planner.
 *
 * Implements the frozen sim.h interface. Tick order is the CONTRACT.md order:
 *   power flood-fill -> pollution diffusion -> crime -> land value ->
 *   zone growth/decay -> scorecard.
 *
 * The five scorecard metrics follow docs/scorecard.md verbatim (integer only,
 * Chebyshev radii 4/5, clamp 0..100). Everything is deterministic: no RNG, no
 * floating point, no signed-overflow-prone arithmetic. All derived state lives
 * in Tile fields; no heap allocation, no pointers between tiles.
 *
 * Owned by T2 (sim engineer).
 */
#include <string.h>
#include "sim.h"
#include "world.h"

int sim_paused = 0;
static int day = 0;
static Scorecard cached;

/* ---------- small integer helpers ---------- */

static int clampi(int v, int lo, int hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

static int clamp100(int v)
{
    return clampi(v, 0, 100);
}

static int cheb(int ax, int ay, int bx, int by)
{
    int dx = ax - bx, dy = ay - by;
    if (dx < 0) dx = -dx;
    if (dy < 0) dy = -dy;
    return dx > dy ? dx : dy;
}

static int pct(int n, int d)
{
    return d > 0 ? (100 * n) / d : 0;
}

static int is_zone(int t)
{
    return t == T_RES || t == T_COM || t == T_IND;
}

/* CONTRACT addendum v1.2: pickleball courts are recreational open space —
 * park-equivalent in every metric, no pollution/crime source, never develop
 * (not a zone), need no power or road. */
static int is_park(int t)
{
    return t == T_PARK || t == T_PICKLEBALL;
}

/* ---------- 1. power flood-fill ---------- */

/* Conductors are power plants, power lines and zone tiles. A plant is the
 * source; the fill crosses the 8-neighbourhood (the CONTRACT "adjacent" rule —
 * a plant placed diagonally from a line still feeds it). Zones participate in
 * the fill as endpoints: a zone adjacent to a live line/zone becomes powered
 * and may pass power to the next zone, so a zoned block develops inward from
 * its serviced frontage. Roads do not conduct. */
static void power_flood(void)
{
    int q[GRID_W * GRID_H];
    int head = 0, tail = 0;

    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            Tile *t = &world[y][x];
            t->powered = 0;
            if (t->type == T_POWERPLANT) {
                t->powered = 1;
                q[tail++] = y * GRID_W + x;
            }
        }
    }

    while (head < tail) {
        int idx = q[head++];
        int x = idx % GRID_W, y = idx / GRID_W;
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                if (dx == 0 && dy == 0) continue;
                int ax = x + dx, ay = y + dy;
                if (ax < 0 || ax >= GRID_W || ay < 0 || ay >= GRID_H) continue;
                Tile *t = &world[ay][ax];
                if (!t->powered &&
                    (t->type == T_POWERLINE || t->type == T_POWERPLANT || is_zone(t->type))) {
                    t->powered = 1;
                    q[tail++] = ay * GRID_W + ax;
                }
            }
        }
    }

    /* Every zone in the 8-neighbourhood of a live conductor is powered. */
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            Tile *t = &world[y][x];
            if (!t->powered ||
                (t->type != T_POWERPLANT && t->type != T_POWERLINE))
                continue;
            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    int ax = x + dx, ay = y + dy;
                    if (ax < 0 || ax >= GRID_W || ay < 0 || ay >= GRID_H) continue;
                    if (is_zone(world[ay][ax].type)) world[ay][ax].powered = 1;
                }
            }
        }
    }
}

/* ---------- 2. pollution diffusion ---------- */

/* Each source spreads strength >> chebyshev_distance across a clipped square
 * window. The source tile keeps full strength; a tile one step away gets half,
 * two steps a quarter, and so on. Contributions sum, then the field is
 * normalised by 8 — an approximation of the 4x4 block averaging described in
 * research.md §2 item 5. Without it a solid 12-tile industrial block would
 * pile up ~176 raw pollution and pin all nearby land value at zero through the
 * crime/land-value feedback; normalised, one industry still raises a
 * neighbour's pollution (40>>1 / 8 = 2) while a dense block stays recoverable.
 * Final values clamp to 0..255. */
static void diffuse_pollution(void)
{
    static int acc[GRID_H][GRID_W];
    memset(acc, 0, sizeof acc);

    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            int strength = 0, radius = 0;
            switch (world[y][x].type) {
            case T_IND:        strength = 40; radius = 4; break;
            case T_ROAD:       strength =  6; radius = 2; break;
            case T_POWERPLANT: strength = 80; radius = 5; break;
            default: break;
            }
            if (strength == 0) continue;
            for (int yy = y - radius; yy <= y + radius; yy++) {
                if (yy < 0 || yy >= GRID_H) continue;
                for (int xx = x - radius; xx <= x + radius; xx++) {
                    if (xx < 0 || xx >= GRID_W) continue;
                    acc[yy][xx] += strength >> cheb(x, y, xx, yy);
                }
            }
        }
    }

    for (int y = 0; y < GRID_H; y++)
        for (int x = 0; x < GRID_W; x++)
            world[y][x].pollution = (uint8_t)clampi(acc[y][x] / 8, 0, 255);
}

/* ---------- 3. crime ---------- */

/* Crime feeds off LAST tick's land value (land value is recomputed after this
 * step in the CONTRACT tick order). Low land value raises crime; proximity to
 * a police station suppresses it. */
static void compute_crime(void)
{
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            int pot = clampi(140 - (int)world[y][x].landValue, 0, 160);
            int reduction = 0;
            for (int yy = y - 5; yy <= y + 5; yy++) {
                if (yy < 0 || yy >= GRID_H) continue;
                for (int xx = x - 5; xx <= x + 5; xx++) {
                    if (xx < 0 || xx >= GRID_W) continue;
                    if (world[yy][xx].type != T_POLICE) continue;
                    int cover = 100 - 15 * cheb(x, y, xx, yy);
                    if (cover > reduction) reduction = cover;
                }
            }
            world[y][x].crime = (uint8_t)clampi(pot - reduction, 0, 255);
        }
    }
}

/* ---------- 4. land value ---------- */

/* Base value, a downtown bonus fading from the map centre, green adjacency
 * (parks/courts/water/trees), minus half the pollution and half the crime. */
static void compute_landvalue(void)
{
    const int cx = GRID_W / 2, cy = GRID_H / 2;

    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            int downtown = 24 - cheb(x, y, cx, cy) / 2;
            if (downtown < 0) downtown = 0;

            int green = 0;
            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    if (dx == 0 && dy == 0) continue;
                    int ax = x + dx, ay = y + dy;
                    if (ax < 0 || ax >= GRID_W || ay < 0 || ay >= GRID_H) continue;
                    int t = world[ay][ax].type;
                    if (is_park(t)) green += 6;
                    else if (t == T_WATER) green += 4;
                    else if (t == T_EMPTY && world_trees[ay][ax]) green += 3;
                }
            }
            if (green > 30) green = 30;

            int lv = 110 + downtown + green
                   - (int)world[y][x].pollution / 2
                   - (int)world[y][x].crime / 2;
            world[y][x].landValue = (uint8_t)clampi(lv, 0, 255);
        }
    }
}

/* ---------- 5. zone growth / decay ---------- */

/* A zone with no road access or no power decays. A serviced zone grows when
 * land value is high enough, decays in a truly blighted spot, and otherwise
 * holds its level. Levels are clamped to 0..3. */
static void grow_decay(void)
{
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            Tile *t = &world[y][x];
            if (!is_zone(t->type)) continue;

            int road = 0;
            for (int dy = -1; dy <= 1 && !road; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    int ax = x + dx, ay = y + dy;
                    if (ax < 0 || ax >= GRID_W || ay < 0 || ay >= GRID_H) continue;
                    if (world[ay][ax].type == T_ROAD) { road = 1; break; }
                }
            }

            int lvl = t->level;
            if (!road || !t->powered) {
                if (lvl > 0) lvl--;
            } else if (t->landValue >= 80) {
                if (lvl < 3) lvl++;
            } else if (t->landValue < 25) {
                if (lvl > 0) lvl--;
            }
            t->level = (uint8_t)lvl;
        }
    }
}

/* ---------- 6. scorecard (docs/scorecard.md, normative) ---------- */

static int near_type(int x, int y, int r, int type)
{
    for (int yy = y - r; yy <= y + r; yy++) {
        if (yy < 0 || yy >= GRID_H) continue;
        for (int xx = x - r; xx <= x + r; xx++) {
            if (xx < 0 || xx >= GRID_W) continue;
            if (world[yy][xx].type == type) return 1;
        }
    }
    return 0;
}

/* Park-equivalent radius scan (addendum v1.2): parks AND pickleball courts. */
static int near_park(int x, int y, int r)
{
    for (int yy = y - r; yy <= y + r; yy++) {
        if (yy < 0 || yy >= GRID_H) continue;
        for (int xx = x - r; xx <= x + r; xx++) {
            if (xx < 0 || xx >= GRID_W) continue;
            if (is_park(world[yy][xx].type)) return 1;
        }
    }
    return 0;
}

static void compute_scorecard(void)
{
    int n = 0, w = 0, a = 0;       /* developed residents, walkers, amenity-served */
    int poll_sum = 0, L = 0, Z = 0; /* resident pollution, zone level-sum, zone count */
    int G = 0;                     /* green tiles */

    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            Tile *t = &world[y][x];
            if (is_park(t->type) || t->type == T_WATER ||
                (t->type == T_EMPTY && world_trees[y][x]))
                G++;
            if (is_zone(t->type)) {
                Z++;
                L += t->level;
            }
            if (t->type == T_RES && t->level >= 1) {
                n++;
                poll_sum += t->pollution;
                if (near_type(x, y, 4, T_COM) ||
                    near_park(x, y, 4) ||
                    near_type(x, y, 4, T_SCHOOL))
                    w++;
                if (near_type(x, y, 5, T_SCHOOL) &&
                    near_type(x, y, 5, T_COM))
                    a++;
            }
        }
    }

    cached.walkability = clamp100(pct(w, n));
    cached.green       = clamp100(pct(G, GRID_W * GRID_H));
    cached.amenities   = clamp100(pct(a, n));
    cached.yield       = clamp100(Z > 0 ? (100 * L) / (3 * Z) : 0);

    int base = (cached.walkability + cached.green + cached.amenities + cached.yield) / 4;
    int penalty = n > 0 ? poll_sum / (2 * n) : 0;
    cached.livability  = clamp100(base - penalty);
}

/* ---------- public interface ---------- */

void sim_init(void)
{
    day = 0;
    sim_paused = 0;
    /* Reset derived state only: world type/level (including loaded plans) stay. */
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            Tile *t = &world[y][x];
            t->powered = 0;
            t->landValue = 0;
            t->pollution = 0;
            t->crime = 0;
        }
    }
    memset(&cached, 0, sizeof cached);
    compute_scorecard(); /* sane scorecard even before the first tick */
}

void sim_tick(void)
{
    day++;
    power_flood();
    diffuse_pollution();
    compute_crime();
    compute_landvalue();
    grow_decay();
    compute_scorecard();
}

Scorecard sim_scorecard(void)
{
    Scorecard sc = cached;
    sc.population = world_population();
    sc.jobs = world_jobs();
    sc.day = day;
    return sc;
}
