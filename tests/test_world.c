/* test_world.c — headless tests for the world module (T1 scaffold).
 * T2 adds tests/test_sim.c; the Makefile picks it up automatically. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "world.h"

int main(void)
{
    /* init: terrain present and deterministic */
    world_init();
    int water = 0, trees = 0;
    for (int y = 0; y < GRID_H; y++)
        for (int x = 0; x < GRID_W; x++) {
            water += world[y][x].type == T_WATER;
            trees += world_trees[y][x];
            assert(world[y][x].type == T_EMPTY || world[y][x].type == T_WATER);
            assert(world[y][x].level == 0); /* no level-as-decoration */
        }
    assert(water > 0 && trees > 0);
    Tile snap[GRID_H][GRID_W];
    uint8_t tsnap[GRID_H][GRID_W];
    memcpy(snap, world, sizeof snap);
    memcpy(tsnap, world_trees, sizeof tsnap);
    world_init();
    assert(memcmp(snap, world, sizeof snap) == 0);
    assert(memcmp(tsnap, world_trees, sizeof tsnap) == 0);

    /* find a buildable land tile and a water tile */
    int lx = -1, ly = -1, wx = -1, wy = -1;
    for (int y = 0; y < GRID_H && lx < 0; y++)
        for (int x = 0; x < GRID_W && lx < 0; x++)
            if (world[y][x].type == T_EMPTY) { lx = x; ly = y; }
    for (int y = 0; y < GRID_H && wx < 0; y++)
        for (int x = 0; x < GRID_W && wx < 0; x++)
            if (world[y][x].type == T_WATER) { wx = x; wy = y; }
    assert(lx >= 0 && wx >= 0);

    /* place / occupy / invalid */
    assert(world_place(lx, ly, T_RES) == 0);
    assert(world_place(lx, ly, T_ROAD) == -1);      /* occupied */
    assert(world_place(wx, wy, T_ROAD) == -1);      /* water */
    assert(world_place(-1, 0, T_ROAD) == -1);       /* out of bounds */
    assert(world_place(0, GRID_H, T_ROAD) == -1);
    assert(world_place(lx + 1, ly, T_COUNT) == -1); /* invalid type */
    assert(world_trees[ly][lx] == 0);               /* build clears tree */

    /* population / jobs arithmetic */
    world[ly][lx].level = 3;
    assert(world_population() == 12);
    assert(world_place(lx + 1, ly, T_COM) == 0);
    world[ly][lx + 1].level = 2;
    assert(world_place(lx + 2, ly, T_IND) == 0);
    world[ly][lx + 2].level = 1;
    assert(world_jobs() == 9);

    /* save / load round-trip */
    memcpy(snap, world, sizeof snap);
    memcpy(tsnap, world_trees, sizeof tsnap);
    assert(world_save("test_plan_tmp.bin") == 0);
    world_bulldoze(lx, ly);
    assert(world[ly][lx].type == T_EMPTY && world_population() == 0);
    world_bulldoze(-1, -1); /* must not crash */
    assert(world_load("test_plan_tmp.bin") == 0);
    assert(memcmp(snap, world, sizeof snap) == 0);
    assert(memcmp(tsnap, world_trees, sizeof tsnap) == 0);
    assert(world_population() == 12 && world_jobs() == 9);
    assert(world_load("no_such_file.bin") == -1);
    remove("test_plan_tmp.bin");

    puts("test_world: OK (init/place/bulldoze/save/load/population/jobs)");
    return 0;
}