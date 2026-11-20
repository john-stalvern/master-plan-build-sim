/* world.h — tile grid model. FROZEN per docs/CONTRACT.md (T1 scaffold).
 * Additive note: trees live in a parallel world_trees array because the
 * contract forbids using Tile.level as decoration on T_EMPTY. */
#ifndef WORLD_H
#define WORLD_H

#include <stdint.h>

#define GRID_W 40
#define GRID_H 40
#define TILE   16

typedef enum { T_EMPTY, T_WATER, T_ROAD, T_POWERLINE, T_POWERPLANT,
               T_RES, T_COM, T_IND, T_PARK, T_SCHOOL, T_POLICE, T_FIRE,
               T_COUNT } TileType;

typedef struct { uint8_t type, level, powered, landValue, pollution, crime; } Tile;

extern Tile world[GRID_H][GRID_W];
extern uint8_t world_trees[GRID_H][GRID_W]; /* 1 = tree on a T_EMPTY tile */

void world_init(void);            /* empty land + a river/lake + some trees (deterministic) */
int  world_place(int x, int y, TileType t);  /* 0 ok, -1 occupied/invalid; only EMPTY is buildable */
void world_bulldoze(int x, int y);
int  world_save(const char *path); /* "MPv1" magic + whole grid + trees array */
int  world_load(const char *path);
int  world_population(void);       /* sum res level * 4 */
int  world_jobs(void);             /* sum (com+ind) level * 3 */

#endif /* WORLD_H */