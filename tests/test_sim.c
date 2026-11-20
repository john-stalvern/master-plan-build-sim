/* test_sim.c — headless tests for the simulation module (T2).
 * Self-contained: <assert.h> only, no test framework. Owned by T2 sim
 * engineer; the Makefile picks this file up automatically. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "world.h"
#include "sim.h"

/* ---------- helpers ---------- */

/* Chebyshev distance (authoritative metric distance in docs/scorecard.md §1). */
static int cheb(int ax, int ay, int bx, int by)
{
    int dx = ax - bx, dy = ay - by;
    if (dx < 0) dx = -dx;
    if (dy < 0) dy = -dy;
    return dx > dy ? dx : dy;
}

static int clamp100(int v)
{
    return v < 0 ? 0 : (v > 100 ? 100 : v);
}

/* Wipe the entire grid to bare T_EMPTY with no trees and no derived fields. */
static void clear_grid(void)
{
    for (int y = 0; y < GRID_H; y++)
        for (int x = 0; x < GRID_W; x++)
            world_bulldoze(x, y);
}

/* Reset to a known, tree-cleared canvas with a fresh sim state. */
static void control(void)
{
    world_init();
    sim_init();
    clear_grid();
}

static void check_ranges(Scorecard sc)
{
    assert(sc.walkability >= 0 && sc.walkability <= 100);
    assert(sc.green       >= 0 && sc.green       <= 100);
    assert(sc.amenities   >= 0 && sc.amenities   <= 100);
    assert(sc.yield       >= 0 && sc.yield       <= 100);
    assert(sc.livability  >= 0 && sc.livability  <= 100);
}

/* Controlled residential anchor at (10,10): developed, roaded, powered.
 * landValue is seeded high so the low-crime branch keeps it >= 80 across the
 * tick and growth can never zero the level. */
static void build_home(void)
{
    control();
    assert(world_place(10, 10, T_RES) == 0);
    world[10][10].level = 1;
    world[10][10].landValue = 200;
    assert(world_place(10, 11, T_ROAD) == 0);       /* 8-neighbour road */
    assert(world_place(11, 10, T_POWERLINE) == 0);  /* powered chain */
    assert(world_place(12, 10, T_POWERLINE) == 0);
    assert(world_place(13, 10, T_POWERLINE) == 0);
    assert(world_place(14, 10, T_POWERPLANT) == 0);
}

/* Fully serviced, powered residential block used by the growth tests. */
static void build_growth_plan(void)
{
    control();
    assert(world_place(5, 5, T_RES) == 0);
    assert(world_place(5, 6, T_ROAD) == 0);
    assert(world_place(9, 5, T_POWERPLANT) == 0);
    assert(world_place(8, 5, T_POWERLINE) == 0);
    assert(world_place(7, 5, T_POWERLINE) == 0);
    assert(world_place(6, 5, T_POWERLINE) == 0);
}

int main(void)
{
    /* 1. Fresh map: metric sanity, day 0, independent green + livability. */
    {
        world_init();
        sim_init();
        Scorecard sc = sim_scorecard();
        check_ranges(sc);
        assert(sc.day == 0);

        /* Recompute green from the doc formula (no -O2-specific hardcoding). */
        int green = 0;
        for (int y = 0; y < GRID_H; y++)
            for (int x = 0; x < GRID_W; x++) {
                Tile *t = &world[y][x];
                if (t->type == T_PARK || t->type == T_WATER ||
                    (t->type == T_EMPTY && world_trees[y][x]))
                    green++;
            }
        assert(sc.green == clamp100((100 * green) / (GRID_W * GRID_H)));

        /* Recompute livability with our own developed-RES pollution scan. */
        int n = 0, poll_sum = 0;
        for (int y = 0; y < GRID_H; y++)
            for (int x = 0; x < GRID_W; x++)
                if (world[y][x].type == T_RES && world[y][x].level >= 1) {
                    n++;
                    poll_sum += world[y][x].pollution;
                }
        int base = (sc.walkability + sc.green + sc.amenities + sc.yield) / 4;
        int penalty = n > 0 ? poll_sum / (2 * n) : 0;
        assert(sc.livability == clamp100(base - penalty));
    }

    /* 2. All five fields stay 0..100 across ticks on several grids. */
    {
        world_init();
        sim_init();
        for (int i = 0; i < 20; i++) {
            sim_tick();
            check_ranges(sim_scorecard());
        }

        build_growth_plan();
        assert(world_place(5, 4, T_COM) == 0);
        assert(world_place(7, 6, T_IND) == 0);
        assert(world_place(4, 4, T_PARK) == 0);
        assert(world_place(6, 4, T_SCHOOL) == 0);
        for (int i = 0; i < 20; i++) {
            sim_tick();
            check_ranges(sim_scorecard());
        }

        /* After bulldozing everything, still bounded. */
        clear_grid();
        for (int i = 0; i < 10; i++) {
            sim_tick();
            check_ranges(sim_scorecard());
        }
    }

    /* 3. Scorecard boundary anchors (docs/scorecard.md §4.3). */
    {
        /* COM at cheb exactly 4 -> walkability 100. */
        build_home();
        assert(world_place(10, 14, T_COM) == 0);  /* cheb((10,10),(10,14)) = 4 */
        sim_tick();
        assert(world[10][10].level >= 1);         /* home stayed developed */
        assert(sim_scorecard().walkability == 100);

        /* COM at cheb 5 -> walkability 0. */
        build_home();
        assert(world_place(10, 15, T_COM) == 0);  /* cheb = 5 */
        sim_tick();
        assert(sim_scorecard().walkability == 0);

        /* SCHOOL + COM both within cheb 5 -> amenities 100. */
        build_home();
        assert(world_place(10, 13, T_SCHOOL) == 0); /* cheb 3 */
        assert(world_place(10, 14, T_COM) == 0);    /* cheb 4 */
        sim_tick();
        assert(sim_scorecard().amenities == 100);

        /* SCHOOL only -> amenities 0 (needs COM too). */
        build_home();
        assert(world_place(10, 13, T_SCHOOL) == 0);
        sim_tick();
        assert(sim_scorecard().amenities == 0);
    }

    /* 4. Zones without a road never develop. */
    {
        control();
        assert(world_place(10, 10, T_RES) == 0);
        for (int i = 0; i < 30; i++)
            sim_tick();
        assert(world[10][10].level == 0);
    }

    /* 5. Powered + roaded zones grow and produce population. */
    {
        build_growth_plan();
        for (int i = 0; i < 30; i++)
            sim_tick();
        assert(world[5][5].level >= 2);
        assert(world_population() > 0);
    }

    /* 6. Park adjacency raises a home's land value. */
    {
        build_growth_plan();
        for (int i = 0; i < 10; i++)
            sim_tick();
        int before = world[5][5].landValue;
        assert(world_place(4, 4, T_PARK) == 0);   /* 8-neighbour of (5,5) */
        for (int i = 0; i < 10; i++)
            sim_tick();
        int after = world[5][5].landValue;
        assert(after > before);                    /* +6 green bonus, no pollution */
    }

    /* 7. Industry raises nearby pollution (+40 >> 1 at cheb 1). */
    {
        control();
        sim_tick();
        int before = world[10][10].pollution;
        assert(world_place(11, 10, T_IND) == 0);
        sim_tick();
        int after = world[10][10].pollution;
        assert(after > before);
    }

    /* 8. Empty-set: bulldoze all zones -> yield/walk/amenities 0. */
    {
        build_growth_plan();
        assert(world_place(5, 4, T_COM) == 0);
        assert(world_place(7, 6, T_IND) == 0);
        for (int i = 0; i < 15; i++)
            sim_tick();
        clear_grid();
        sim_tick();
        Scorecard sc = sim_scorecard();
        assert(sc.yield == 0);
        assert(sc.walkability == 0);
        assert(sc.amenities == 0);
    }

    /* 9. save/load round-trip through the world API. */
    {
        control();
        assert(world_place(5, 5, T_RES) == 0);
        assert(world_place(5, 4, T_COM) == 0);
        assert(world_place(6, 4, T_IND) == 0);
        world[5][5].level = 3;
        world[5][4].level = 2;
        world[6][4].level = 2;

        Tile snap[GRID_H][GRID_W];
        uint8_t tsnap[GRID_H][GRID_W];
        memcpy(snap, world, sizeof snap);
        memcpy(tsnap, world_trees, sizeof tsnap);
        int pop = world_population(), jobs = world_jobs();
        assert(pop > 0 && jobs > 0);

        const char *path = "test_sim_tmp.bin";
        assert(world_save(path) == 0);
        clear_grid();
        assert(world_population() == 0 && world_jobs() == 0);
        assert(world_load(path) == 0);
        assert(memcmp(snap, world, sizeof snap) == 0);
        assert(memcmp(tsnap, world_trees, sizeof tsnap) == 0);
        assert(world_population() == pop && world_jobs() == jobs);
        remove(path);
    }

    puts("test_sim: OK (fresh/ranges/anchors/zones/growth/park/pollution/empty/save-load)");
    return 0;
}
