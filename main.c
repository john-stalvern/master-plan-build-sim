/* main.c — CLI smoke harness (T1) + full input/HUD wiring (T3). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL.h>
#include "world.h"
#include "sim.h"
#include "render.h"

/* Scripted test plan for --smoke: road spine + zones + plant + park + school.
 * Placements that hit water/occupied tiles fail silently (world_place = -1). */
static void place_test_plan(void)
{
    for (int x = 2; x <= 37; x++) world_place(x, 20, T_ROAD);   /* spine */
    for (int x = 6; x <= 12; x++)
        for (int y = 17; y <= 19; y++) world_place(x, y, T_RES);
    for (int x = 6; x <= 12; x++)
        for (int y = 21; y <= 23; y++) world_place(x, y, T_RES);
    for (int x = 14; x <= 17; x++)
        for (int y = 17; y <= 19; y++) world_place(x, y, T_COM);
    for (int x = 14; x <= 17; x++)
        for (int y = 21; y <= 23; y++) world_place(x, y, T_IND);
    for (int x = 8; x <= 10; x++)
        for (int y = 25; y <= 26; y++) world_place(x, y, T_PARK);
    world_place(18, 17, T_SCHOOL);
    world_place(3, 17, T_POWERPLANT);
    for (int x = 4; x <= 13; x++) world_place(x, 16, T_POWERLINE);
}

static int run_smoke(int ticks)
{
    if (!getenv("WAYLAND_DISPLAY") && !getenv("DISPLAY"))
        setenv("SDL_VIDEODRIVER", "dummy", 1);
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    world_init();
    sim_init();
    place_test_plan();
    for (int i = 0; i < ticks; i++) sim_tick();
    Scorecard sc = sim_scorecard();
    printf("{\"walkability\":%d,\"green\":%d,\"amenities\":%d,\"yield\":%d,"
           "\"livability\":%d,\"population\":%d,\"jobs\":%d,\"day\":%d}\n",
           sc.walkability, sc.green, sc.amenities, sc.yield,
           sc.livability, sc.population, sc.jobs, sc.day);
    SDL_Quit();
    return 0;
}

/* The 11 tool slots, in palette order. Index 0 is the bulldoze sentinel.
 * Keys map in order: 1,2,3,4,5,6,7,8,9,0,-  ->  indices 0..10. */
static const TileType tool_type[11] = {
    (TileType)-1,   /* 0 / key '1' : bulldoze sentinel */
    T_ROAD,         /* 1 / key '2' : road (default)    */
    T_RES,          /* 2 / key '3' : residential       */
    T_COM,          /* 3 / key '4' : commercial        */
    T_IND,          /* 4 / key '5' : industrial        */
    T_PARK,         /* 5 / key '6' : park              */
    T_SCHOOL,       /* 6 / key '7' : school            */
    T_POLICE,       /* 7 / key '8' : police            */
    T_FIRE,         /* 8 / key '9' : fire              */
    T_POWERPLANT,   /* 9 / key '0' : power plant       */
    T_POWERLINE     /* 10 / key '-': power line        */
};

/* Palette button geometry — MUST match render.c.
 * first button top-left y=70, height=22, vertical step=24, 11 buttons. */
#define PALETTE_FIRST_Y 70
#define PALETTE_STEP_Y  24
#define PALETTE_COUNT   11

/* Convert a window-space mouse position to tile coordinates.
 * Writes (-1,-1) when the cursor is outside the 640x640 map. */
static void mouse_to_tile(int mx, int my, int *tx, int *ty)
{
    if (mx >= MAP_X && mx < MAP_X + GRID_W * TILE &&
        my >= MAP_Y && my < MAP_Y + GRID_H * TILE) {
        *tx = (mx - MAP_X) / TILE;
        *ty = (my - MAP_Y) / TILE;
    } else {
        *tx = -1;
        *ty = -1;
    }
}

/* Paint the selected tool (or bulldoze) at a window-space position. */
static void paint_at(int mx, int my, int tool_idx)
{
    int tx, ty;
    mouse_to_tile(mx, my, &tx, &ty);
    if (tx < 0 || ty < 0) return;
    if (tool_type[tool_idx] == (TileType)-1)
        world_bulldoze(tx, ty);
    else
        world_place(tx, ty, tool_type[tool_idx]);
}

int main(int argc, char **argv)
{
    int smoke = 0, ticks = 200;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--smoke") == 0) smoke = 1;
        else if (strcmp(argv[i], "--ticks") == 0 && i + 1 < argc) ticks = atoi(argv[++i]);
    }
    if (smoke) return run_smoke(ticks);

    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    SDL_Window *win = SDL_CreateWindow("Master Planner",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, WIN_W, WIN_H, 0);
    if (!win) { fprintf(stderr, "window: %s\n", SDL_GetError()); SDL_Quit(); return 1; }
    SDL_Renderer *r = SDL_CreateRenderer(win, -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!r) { fprintf(stderr, "renderer: %s\n", SDL_GetError()); SDL_DestroyWindow(win); SDL_Quit(); return 1; }
    if (render_init(r) != 0) {
        fprintf(stderr, "render_init failed\n");
        SDL_DestroyRenderer(r);
        SDL_DestroyWindow(win);
        SDL_Quit();
        return 1;
    }

    world_init();
    sim_init();

    int running = 1;
    int painting = 0;
    int tool_idx = 1;          /* default: T_ROAD */
    int overlay = 0;
    int hover_x = -1, hover_y = -1;
    Uint32 last = SDL_GetTicks(), acc = 0;
    while (running) {
        Uint32 frame_start = SDL_GetTicks();

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                running = 0;
            } else if (e.type == SDL_KEYDOWN) {
                switch (e.key.keysym.sym) {
                case SDLK_q:       running = 0; break;
                case SDLK_ESCAPE:  if (overlay) overlay = 0; else running = 0; break;
                case SDLK_SPACE:   sim_paused = !sim_paused; break;
                case SDLK_s:       world_save("plan.bin"); break;
                case SDLK_l:       world_load("plan.bin"); break;
                case SDLK_F1:      overlay = (overlay == 1) ? 0 : 1; break;
                case SDLK_F2:      overlay = (overlay == 2) ? 0 : 2; break;
                case SDLK_F3:      overlay = (overlay == 3) ? 0 : 3; break;
                case SDLK_F4:      overlay = (overlay == 4) ? 0 : 4; break;
                case SDLK_1:       tool_idx = 0;  break; /* bulldoze */
                case SDLK_2:       tool_idx = 1;  break; /* road */
                case SDLK_3:       tool_idx = 2;  break; /* res */
                case SDLK_4:       tool_idx = 3;  break; /* com */
                case SDLK_5:       tool_idx = 4;  break; /* ind */
                case SDLK_6:       tool_idx = 5;  break; /* park */
                case SDLK_7:       tool_idx = 6;  break; /* school */
                case SDLK_8:       tool_idx = 7;  break; /* police */
                case SDLK_9:       tool_idx = 8;  break; /* fire */
                case SDLK_0:       tool_idx = 9;  break; /* powerplant */
                case SDLK_MINUS:   tool_idx = 10; break; /* powerline */
                default: break;
                }
            } else if (e.type == SDL_MOUSEBUTTONDOWN) {
                if (e.button.button == SDL_BUTTON_LEFT) {
                    mouse_to_tile(e.button.x, e.button.y, &hover_x, &hover_y);
                    if (e.button.x >= SIDEBAR_X) {
                        int idx = (e.button.y - PALETTE_FIRST_Y) / PALETTE_STEP_Y;
                        if (idx >= 0 && idx < PALETTE_COUNT) tool_idx = idx;
                    } else {
                        painting = 1;
                        paint_at(e.button.x, e.button.y, tool_idx);
                    }
                }
            } else if (e.type == SDL_MOUSEBUTTONUP) {
                if (e.button.button == SDL_BUTTON_LEFT) painting = 0;
            } else if (e.type == SDL_MOUSEMOTION) {
                mouse_to_tile(e.motion.x, e.motion.y, &hover_x, &hover_y);
                if (painting) paint_at(e.motion.x, e.motion.y, tool_idx);
            }
        }

        Uint32 now = SDL_GetTicks();
        acc += now - last;
        last = now;
        while (acc >= 500) { if (!sim_paused) sim_tick(); acc -= 500; }

        Scorecard sc = sim_scorecard();
        render_frame(r, hover_x, hover_y, tool_type[tool_idx],
                     overlay, sc, sc.day, sim_paused);
        SDL_RenderPresent(r);

        /* ~60 fps: sleep out the remainder of the 16 ms frame budget. */
        Uint32 frame_time = SDL_GetTicks() - frame_start;
        if (frame_time < 16) SDL_Delay(16 - frame_time);
    }

    render_quit();
    SDL_DestroyRenderer(r);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}
