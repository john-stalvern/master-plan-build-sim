/* world.c — tile grid: terrain, placement, save/load, population/jobs.
 * Owned by T1 (architect). Deterministic terrain, no RNG state. */
#include <stdio.h>
#include <string.h>
#include "world.h"

Tile world[GRID_H][GRID_W];
uint8_t world_trees[GRID_H][GRID_W];

/* Deterministic per-tile hash (fixed constants, no seed state). */
static uint32_t tile_hash(int x, int y)
{
    uint32_t h = (uint32_t)(x * 374761393 + y * 668265263) ^ 0x5bf03635u;
    h = (h ^ (h >> 13)) * 1274126177u;
    return h ^ (h >> 16);
}

void world_init(void)
{
    memset(world, 0, sizeof world);
    memset(world_trees, 0, sizeof world_trees);
    for (int y = 0; y < GRID_H; y++) {
        int river_x = 27 + (int)((y * y) / 13 % 5) - 2; /* meanders x=25..29 */
        for (int x = 0; x < GRID_W; x++) {
            int dx = x - 8, dy = y - 31;
            if (x >= river_x - 1 && x <= river_x + 1)
                world[y][x].type = T_WATER;            /* river, width 3 */
            else if (dx * dx + dy * dy <= 10)
                world[y][x].type = T_WATER;            /* small lake */
            else if (tile_hash(x, y) % 100 < 18)
                world_trees[y][x] = 1;                 /* ~18% forest cover */
        }
    }
}

int world_place(int x, int y, TileType t)
{
    if (x < 0 || x >= GRID_W || y < 0 || y >= GRID_H) return -1;
    if (t < 0 || t >= T_COUNT) return -1;
    if (world[y][x].type != T_EMPTY) return -1; /* occupied (incl. water) */
    Tile tile = {0};
    tile.type = (uint8_t)t;
    world[y][x] = tile;
    world_trees[y][x] = 0; /* building clears any tree */
    return 0;
}

void world_bulldoze(int x, int y)
{
    if (x < 0 || x >= GRID_W || y < 0 || y >= GRID_H) return;
    memset(&world[y][x], 0, sizeof(Tile));
    world_trees[y][x] = 0;
}

int world_save(const char *path)
{
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    int ok = fwrite("MPv1", 1, 4, f) == 4
          && fwrite(world, sizeof world, 1, f) == 1
          && fwrite(world_trees, sizeof world_trees, 1, f) == 1;
    fclose(f);
    return ok ? 0 : -1;
}

int world_load(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    char magic[4];
    Tile grid[GRID_H][GRID_W];
    uint8_t trees[GRID_H][GRID_W];
    int ok = fread(magic, 1, 4, f) == 4 && memcmp(magic, "MPv1", 4) == 0
          && fread(grid, sizeof grid, 1, f) == 1
          && fread(trees, sizeof trees, 1, f) == 1;
    fclose(f);
    if (!ok) return -1;
    for (int y = 0; y < GRID_H; y++)
        for (int x = 0; x < GRID_W; x++)
            if (grid[y][x].type >= T_COUNT) return -1;
    memcpy(world, grid, sizeof world);
    memcpy(world_trees, trees, sizeof world_trees);
    return 0;
}

int world_population(void)
{
    int pop = 0;
    for (int y = 0; y < GRID_H; y++)
        for (int x = 0; x < GRID_W; x++)
            if (world[y][x].type == T_RES) pop += world[y][x].level * 4;
    return pop;
}

int world_jobs(void)
{
    int jobs = 0;
    for (int y = 0; y < GRID_H; y++)
        for (int x = 0; x < GRID_W; x++)
            if (world[y][x].type == T_COM || world[y][x].type == T_IND)
                jobs += world[y][x].level * 3;
    return jobs;
}