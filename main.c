/* main.c — skeleton by T1: CLI smoke harness + 60 fps window loop.
 * T3 (GUI engineer) owns the input/HUD wiring marked TODO below. */
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
    if (render_init(r) != 0) { fprintf(stderr, "render_init failed\n"); return 1; }

    world_init();
    sim_init();

    int running = 1;
    Uint32 last = SDL_GetTicks(), acc = 0;
    while (running) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) running = 0;
            else if (e.type == SDL_KEYDOWN) {
                switch (e.key.keysym.sym) {
                case SDLK_q: case SDLK_ESCAPE: running = 0; break;
                case SDLK_SPACE: sim_paused = !sim_paused; break;
                case SDLK_s: world_save("plan.bin"); break;
                case SDLK_l: world_load("plan.bin"); break;
                /* TODO(T3): 1..9,0,- tool select; F1..F4 overlays; mouse paint. */
                default: break;
                }
            }
        }
        Uint32 now = SDL_GetTicks();
        acc += now - last;
        last = now;
        while (acc >= 500) { if (!sim_paused) sim_tick(); acc -= 500; }

        Scorecard sc = sim_scorecard();
        render_frame(r, -1, -1, T_ROAD, 0, sc, sc.day, sim_paused);
        SDL_RenderPresent(r);
        SDL_Delay(16); /* ~60 fps */
    }

    render_quit();
    SDL_DestroyRenderer(r);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}