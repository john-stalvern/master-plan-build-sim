/* render.c — STUB by T1: flat tile colours only, so the window shows the map.
 * T3 (GUI engineer) replaces this with font/HUD/palette/overlays. */
#include "render.h"

static const Uint8 tile_rgb[T_COUNT][3] = {
    [T_EMPTY]      = { 24,  64,  24},  /* dark green */
    [T_WATER]      = { 32,  80, 180},  /* blue */
    [T_ROAD]       = {110, 110, 110},  /* grey */
    [T_POWERLINE]  = {220, 200,  40},  /* yellow */
    [T_POWERPLANT] = {230, 130,  30},  /* orange */
    [T_RES]        = { 60, 160,  60},  /* green */
    [T_COM]        = { 60, 100, 220},  /* blue */
    [T_IND]        = {150, 110,  50},  /* brown */
    [T_PARK]       = { 80, 220,  80},  /* bright green */
    [T_SCHOOL]     = {150,  70, 200},  /* purple */
    [T_POLICE]     = { 30,  50, 130},  /* navy */
    [T_FIRE]       = {210,  50,  40},  /* red */
};

int render_init(SDL_Renderer *r)
{
    (void)r; /* stub: font loading is T3's job */
    return 0;
}

void render_frame(SDL_Renderer *r, int hover_x, int hover_y,
                  TileType tool, int overlay, Scorecard sc, int day, int paused)
{
    (void)hover_x; (void)hover_y; (void)tool; (void)overlay;
    (void)sc; (void)day; (void)paused; /* HUD is T3's job */

    SDL_SetRenderDrawColor(r, 16, 16, 20, 255);
    SDL_RenderClear(r);
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            const Tile *t = &world[y][x];
            const Uint8 *c = tile_rgb[t->type < T_COUNT ? t->type : T_EMPTY];
            SDL_Rect rect = { MAP_X + x * TILE, MAP_Y + y * TILE, TILE, TILE };
            SDL_SetRenderDrawColor(r, c[0], c[1], c[2], 255);
            SDL_RenderFillRect(r, &rect);
            if (t->type == T_EMPTY && world_trees[y][x]) {
                SDL_Rect tree = { rect.x + 5, rect.y + 4, 6, 8 };
                SDL_SetRenderDrawColor(r, 12, 44, 16, 255);
                SDL_RenderFillRect(r, &tree);
            }
        }
    }
}

void render_quit(void)
{
    /* stub: nothing allocated yet */
}