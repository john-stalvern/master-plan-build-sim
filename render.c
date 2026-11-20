/* render.c — SDL2 drawing: flat top-down tiles, hover cursor, 11-tool palette,
 * scorecard HUD and four recolouring overlays.  T3 (GUI engineer).
 *
 * Text uses SDL2_ttf when a TTF font can be found, otherwise a tiny embedded
 * 5x7 bitmap font (see CONTRACT.md's font fallback rule). */
#include <ctype.h>
#include <glob.h>
#include <stdio.h>
#include <string.h>
#include <SDL.h>
#include <SDL_ttf.h>
#include "render.h"

/* ---- layout (MUST match the palette constants in main.c) ---------------- */
#define PAL_X        664
#define PAL_FIRST_Y  70
#define PAL_BTN_H    22
#define PAL_STEP_Y   24
#define PAL_COUNT    11
#define SIDEBAR_W    (WIN_W - SIDEBAR_X)

static TTF_Font *g_font = NULL; /* NULL => use the embedded bitmap font */

/* ---- base tile colours -------------------------------------------------- */
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

/* The 11 palette slots, in the same order as main.c's key mapping. */
static const TileType pal_tool[PAL_COUNT] = {
    (TileType)-1,   /* bulldoze */
    T_ROAD, T_RES, T_COM, T_IND, T_PARK,
    T_SCHOOL, T_POLICE, T_FIRE, T_POWERPLANT, T_POWERLINE
};
static const char *pal_label[PAL_COUNT] = {
    "BULLDOZE", "ROAD", "RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL",
    "PARK", "SCHOOL", "POLICE", "FIRE", "POWER PLANT", "POWER LINE"
};

static const char *overlay_name[5] = {
    "NONE", "LAND VALUE", "POLLUTION", "POWER", "CRIME"
};

/* ---- embedded 5x7 bitmap font -------------------------------------------
 * Each glyph is five columns; bit 0 is the top row, bit 6 the bottom row.
 * Lowercase input is upper-cased by draw_text(). */
typedef struct { char c; unsigned char col[5]; } glyph;
static const glyph font5x7[] = {
    {' ', {0x00,0x00,0x00,0x00,0x00}},
    {'0', {0x3E,0x51,0x49,0x45,0x3E}},
    {'1', {0x00,0x42,0x7F,0x40,0x00}},
    {'2', {0x42,0x61,0x51,0x49,0x46}},
    {'3', {0x21,0x41,0x45,0x4B,0x31}},
    {'4', {0x18,0x14,0x12,0x7F,0x10}},
    {'5', {0x27,0x45,0x45,0x45,0x39}},
    {'6', {0x3C,0x4A,0x49,0x49,0x30}},
    {'7', {0x01,0x71,0x09,0x05,0x03}},
    {'8', {0x36,0x49,0x49,0x49,0x36}},
    {'9', {0x06,0x49,0x49,0x29,0x1E}},
    {'A', {0x7E,0x11,0x11,0x11,0x7E}},
    {'B', {0x7F,0x49,0x49,0x49,0x36}},
    {'C', {0x3E,0x41,0x41,0x41,0x22}},
    {'D', {0x7F,0x41,0x41,0x22,0x1C}},
    {'E', {0x7F,0x49,0x49,0x49,0x41}},
    {'F', {0x7F,0x09,0x09,0x09,0x01}},
    {'G', {0x3E,0x41,0x49,0x49,0x7A}},
    {'H', {0x7F,0x08,0x08,0x08,0x7F}},
    {'I', {0x00,0x41,0x7F,0x41,0x00}},
    {'J', {0x20,0x40,0x41,0x3F,0x01}},
    {'K', {0x7F,0x08,0x14,0x22,0x41}},
    {'L', {0x7F,0x40,0x40,0x40,0x40}},
    {'M', {0x7F,0x02,0x0C,0x02,0x7F}},
    {'N', {0x7F,0x04,0x08,0x10,0x7F}},
    {'O', {0x3E,0x41,0x41,0x41,0x3E}},
    {'P', {0x7F,0x09,0x09,0x09,0x06}},
    {'Q', {0x3E,0x41,0x51,0x21,0x5E}},
    {'R', {0x7F,0x09,0x19,0x29,0x46}},
    {'S', {0x46,0x49,0x49,0x49,0x31}},
    {'T', {0x01,0x01,0x7F,0x01,0x01}},
    {'U', {0x3F,0x40,0x40,0x40,0x3F}},
    {'V', {0x1F,0x20,0x40,0x20,0x1F}},
    {'W', {0x3F,0x40,0x38,0x40,0x3F}},
    {'X', {0x63,0x14,0x08,0x14,0x63}},
    {'Y', {0x07,0x08,0x70,0x08,0x07}},
    {'Z', {0x61,0x51,0x49,0x45,0x43}},
    {':', {0x00,0x00,0x12,0x00,0x00}},
    {'.', {0x00,0x00,0x00,0x00,0x40}},
    {',', {0x00,0x00,0x00,0x20,0x10}},
    {'-', {0x08,0x08,0x08,0x08,0x08}},
    {'/', {0x01,0x02,0x04,0x08,0x10}},
    {'%', {0x23,0x13,0x08,0x64,0x62}},
    {'(', {0x02,0x04,0x08,0x04,0x02}},
    {')', {0x08,0x04,0x02,0x04,0x08}},
    {'=', {0x00,0x1F,0x00,0x1F,0x00}},
    {'+', {0x08,0x08,0x3E,0x08,0x08}},
};

static const glyph *find_glyph(unsigned char c)
{
    for (size_t i = 0; i < sizeof(font5x7) / sizeof(font5x7[0]); i++)
        if ((unsigned char)font5x7[i].c == c) return &font5x7[i];
    return NULL;
}

/* ---- small drawing helpers ---------------------------------------------- */
static void fill_rect(SDL_Renderer *r, int x, int y, int w, int h,
                      Uint8 cr, Uint8 cg, Uint8 cb)
{
    SDL_Rect q = { x, y, w, h };
    SDL_SetRenderDrawColor(r, cr, cg, cb, 255);
    SDL_RenderFillRect(r, &q);
}

static void draw_text(SDL_Renderer *r, int x, int y, const char *s,
                      Uint8 cr, Uint8 cg, Uint8 cb, int scale)
{
    if (!s || !*s) return;
    if (g_font) {
        SDL_Color col = { cr, cg, cb, 255 };
        SDL_Surface *surf = TTF_RenderText_Solid(g_font, s, col);
        if (surf) {
            SDL_Texture *tex = SDL_CreateTextureFromSurface(r, surf);
            if (tex) {
                SDL_Rect dst = { x, y, surf->w, surf->h };
                SDL_RenderCopy(r, tex, NULL, &dst);
                SDL_DestroyTexture(tex);
            }
            SDL_FreeSurface(surf);
        }
        return;
    }
    SDL_SetRenderDrawColor(r, cr, cg, cb, 255);
    for (const char *p = s; *p; ++p) {
        unsigned char ch = (unsigned char)*p;
        if (ch >= 'a' && ch <= 'z') ch = (unsigned char)(ch - 'a' + 'A');
        const glyph *g = find_glyph(ch);
        if (g) {
            for (int col = 0; col < 5; col++) {
                unsigned char bits = g->col[col];
                for (int row = 0; row < 7; row++) {
                    if (bits & (1u << row))
                        fill_rect(r, x + col * scale, y + row * scale,
                                  scale, scale, cr, cg, cb);
                }
            }
        }
        x += 6 * scale;
    }
}

static void lerp_color(const Uint8 a[3], const Uint8 b[3], int v, Uint8 out[3])
{
    if (v < 0) v = 0;
    if (v > 255) v = 255;
    for (int i = 0; i < 3; i++) {
        int t = a[i] + (b[i] - a[i]) * v / 255;
        out[i] = (Uint8)(t < 0 ? 0 : (t > 255 ? 255 : t));
    }
}

/* Low/high endpoints of each overlay's heatmap scale. */
static void overlay_scale(int overlay, Uint8 lo[3], Uint8 hi[3])
{
    switch (overlay) {
    case 1: lo[0]=150; lo[1]= 40; lo[2]= 40;  hi[0]= 60; hi[1]=220; hi[2]= 90; break; /* land value */
    case 2: lo[0]= 50; lo[1]=170; lo[2]= 70;  hi[0]=220; hi[1]= 50; hi[2]= 40; break; /* pollution */
    case 4: lo[0]= 50; lo[1]=170; lo[2]= 70;  hi[0]=220; hi[1]= 60; hi[2]= 50; break; /* crime */
    default: lo[0]= 80; lo[1]= 55; lo[2]= 40; hi[0]= 70; hi[1]=140; hi[2]=255; break;
    }
}

static void overlay_color(int overlay, const Tile *t, Uint8 out[3])
{
    Uint8 lo[3], hi[3];
    if (overlay == 3) { /* power: binary coverage */
        if (t->powered) { out[0]=70; out[1]=140; out[2]=255; }
        else            { out[0]=80; out[1]= 55; out[2]= 40; }
        return;
    }
    overlay_scale(overlay, lo, hi);
    int v = (overlay == 1) ? t->landValue :
            (overlay == 2) ? t->pollution : t->crime;
    lerp_color(lo, hi, v, out);
}

static void gradient_bar(SDL_Renderer *r, int x, int y, int w, int h,
                         const Uint8 lo[3], const Uint8 hi[3])
{
    int denom = w > 1 ? w - 1 : 1;
    for (int i = 0; i < w; i++) {
        Uint8 c[3];
        lerp_color(lo, hi, i * 255 / denom, c);
        fill_rect(r, x + i, y, 1, h, c[0], c[1], c[2]);
    }
}

static void tool_color(TileType tool, Uint8 out[3])
{
    if (tool == (TileType)-1) { out[0]=200; out[1]= 70; out[2]= 70; return; }
    int i = (int)tool;
    if (i >= 0 && i < T_COUNT) {
        out[0]=tile_rgb[i][0]; out[1]=tile_rgb[i][1]; out[2]=tile_rgb[i][2];
    } else {
        out[0]=180; out[1]=180; out[2]=180;
    }
}

/* ---- font discovery ----------------------------------------------------- */
static TTF_Font *open_font(void)
{
    static const char *paths[] = {
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    };
    for (size_t i = 0; i < sizeof(paths) / sizeof(paths[0]); i++) {
        TTF_Font *f = TTF_OpenFont(paths[i], 13);
        if (f) return f;
    }
    /* Glob fallback when the canonical DejaVu paths are absent. */
    static const char *pats[] = {
        "/usr/share/fonts/*/*.ttf",
        "/usr/share/fonts/*/*/*.ttf",
        "/usr/share/fonts/*.ttf"
    };
    for (size_t p = 0; p < sizeof(pats) / sizeof(pats[0]); p++) {
        glob_t g;
        memset(&g, 0, sizeof g);
        if (glob(pats[p], 0, NULL, &g) == 0) {
            TTF_Font *found = NULL;
            for (size_t i = 0; i < g.gl_pathc; i++) {
                TTF_Font *f = TTF_OpenFont(g.gl_pathv[i], 13);
                if (f) { found = f; break; }
            }
            globfree(&g);
            if (found) return found;
        }
    }
    return NULL; /* bitmap-font fallback */
}

int render_init(SDL_Renderer *r)
{
    (void)r; /* font loading needs no renderer; textures are made per draw */
    if (TTF_Init() == 0) g_font = open_font();
    return 0; /* success either way: the 5x7 bitmap font is always available */
}

void render_quit(void)
{
    if (g_font) { TTF_CloseFont(g_font); g_font = NULL; }
    TTF_Quit();
}

/* ---- map --------------------------------------------------------------- */
static void draw_map(SDL_Renderer *r, int overlay)
{
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            const Tile *t = &world[y][x];
            int px = MAP_X + x * TILE;
            int py = MAP_Y + y * TILE;
            Uint8 rgb[3];
            if (overlay != 0) {
                /* heatmap: recolour every tile by the selected metric */
                overlay_color(overlay, t, rgb);
            } else {
                int type = t->type < T_COUNT ? (int)t->type : T_EMPTY;
                rgb[0] = tile_rgb[type][0];
                rgb[1] = tile_rgb[type][1];
                rgb[2] = tile_rgb[type][2];
                /* level shading: brighter with each development level */
                if ((t->type == T_RES || t->type == T_COM || t->type == T_IND)
                    && t->level > 0) {
                    int boost = (int)t->level * 16;
                    for (int k = 0; k < 3; k++) {
                        int v = rgb[k] + boost;
                        rgb[k] = (Uint8)(v > 255 ? 255 : v);
                    }
                }
            }
            fill_rect(r, px, py, TILE, TILE, rgb[0], rgb[1], rgb[2]);

            if (overlay == 0) {
                /* trees are decoration on empty land */
                if (t->type == T_EMPTY && world_trees[y][x])
                    fill_rect(r, px + 5, py + 4, 6, 8, 12, 44, 16);
                /* one small inner pip per development level */
                if ((t->type == T_RES || t->type == T_COM || t->type == T_IND)
                    && t->level > 0) {
                    for (unsigned k = 0; k < t->level && k < 3; k++)
                        fill_rect(r, px + TILE - 4 - (int)k * 5, py + TILE - 4,
                                  3, 3, 240, 240, 210);
                }
            }
        }
    }
}

static void draw_hover(SDL_Renderer *r, int hover_x, int hover_y)
{
    if (hover_x < 0 || hover_y < 0 || hover_x >= GRID_W || hover_y >= GRID_H)
        return;
    int hx = MAP_X + hover_x * TILE;
    int hy = MAP_Y + hover_y * TILE;
    SDL_Rect a = { hx, hy, TILE, TILE };
    SDL_Rect b = { hx + 1, hy + 1, TILE - 2, TILE - 2 };
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    SDL_RenderDrawRect(r, &a);
    SDL_SetRenderDrawColor(r, 20, 20, 20, 255);
    SDL_RenderDrawRect(r, &b);
}

/* ---- top bar ----------------------------------------------------------- */
static void draw_topbar(SDL_Renderer *r, int day, int population, int paused)
{
    char buf[64];
    fill_rect(r, 0, 0, WIN_W, MAP_Y, 18, 20, 28);
    draw_text(r, 8, 10, "MASTER PLANNER", 235, 235, 245, 2);
    snprintf(buf, sizeof buf, "DAY %d", day);
    draw_text(r, 420, 10, buf, 220, 225, 235, 2);
    snprintf(buf, sizeof buf, "POP %d", population);
    draw_text(r, 540, 10, buf, 220, 225, 235, 2);
    if (paused)
        draw_text(r, 700, 10, "PAUSED", 255, 200, 80, 2);
}

/* ---- sidebar: palette --------------------------------------------------- */
static void draw_palette(SDL_Renderer *r, TileType tool)
{
    draw_text(r, PAL_X, 50, "TOOLS", 205, 215, 235, 2);
    for (int i = 0; i < PAL_COUNT; i++) {
        int by = PAL_FIRST_Y + i * PAL_STEP_Y;
        int selected = (pal_tool[i] == tool);
        if (selected) {
            fill_rect(r, PAL_X, by, 248, PAL_BTN_H, 70, 92, 136);
            SDL_Rect edge = { PAL_X, by, 248, PAL_BTN_H };
            SDL_SetRenderDrawColor(r, 180, 210, 255, 255);
            SDL_RenderDrawRect(r, &edge);
        } else {
            fill_rect(r, PAL_X, by, 248, PAL_BTN_H, 40, 44, 56);
        }
        Uint8 sw[3];
        tool_color(pal_tool[i], sw);
        fill_rect(r, PAL_X + 4, by + 4, 14, 14, sw[0], sw[1], sw[2]);
        if (pal_tool[i] == (TileType)-1) { /* draw an X on the bulldoze swatch */
            SDL_SetRenderDrawColor(r, 20, 20, 20, 255);
            SDL_RenderDrawLine(r, PAL_X + 5, by + 5, PAL_X + 17, by + 17);
            SDL_RenderDrawLine(r, PAL_X + 17, by + 5, PAL_X + 5, by + 17);
        }
        draw_text(r, PAL_X + 24, by + 4, pal_label[i],
                  selected ? 255 : 205, selected ? 255 : 212,
                  selected ? 255 : 225, 2);
    }
}

/* ---- sidebar: scorecard ------------------------------------------------- */
static void draw_scorecard(SDL_Renderer *r, Scorecard sc)
{
    static const char *names[5] = {
        "WALKABILITY", "GREEN", "AMENITIES", "YIELD", "LIVABILITY"
    };
    int vals[5] = {
        sc.walkability, sc.green, sc.amenities, sc.yield, sc.livability
    };
    char buf[32];
    draw_text(r, PAL_X, 346, "SCORECARD", 205, 215, 235, 2);
    for (int i = 0; i < 5; i++) {
        int ry = 364 + i * 26;
        int v = vals[i];
        if (v < 0) v = 0;
        if (v > 100) v = 100;
        draw_text(r, PAL_X, ry, names[i], 190, 200, 215, 1);
        fill_rect(r, PAL_X, ry + 10, 180, 8, 30, 32, 42);
        int w = v * 180 / 100;
        /* interpolate bar colour from red (low) to green (high) */
        Uint8 lo[3] = { 200, 60, 50 }, hi[3] = { 70, 210, 90 }, c[3];
        lerp_color(lo, hi, v * 255 / 100, c);
        fill_rect(r, PAL_X, ry + 10, w, 8, c[0], c[1], c[2]);
        snprintf(buf, sizeof buf, "%d", v);
        draw_text(r, 852, ry, buf, 230, 235, 245, 1);
    }
    snprintf(buf, sizeof buf, "POP %d JOBS %d DAY %d",
             sc.population, sc.jobs, sc.day);
    draw_text(r, PAL_X, 494, buf, 225, 230, 240, 1);
}

/* ---- sidebar: overlay legend ------------------------------------------- */
static void draw_legend(SDL_Renderer *r, int overlay)
{
    char buf[64];
    int o = overlay >= 0 && overlay <= 4 ? overlay : 0;
    draw_text(r, PAL_X, 522, "OVERLAY", 205, 215, 235, 2);
    snprintf(buf, sizeof buf, "%s", overlay_name[o]);
    draw_text(r, PAL_X, 542, buf, 235, 235, 170, 1);

    if (o == 0) {
        fill_rect(r, PAL_X, 556, 180, 10, 40, 42, 52);
        draw_text(r, 852, 556, "OFF", 200, 200, 210, 1);
    } else if (o == 3) {
        fill_rect(r, PAL_X, 556, 88, 10, 80, 55, 40);
        fill_rect(r, PAL_X + 88, 556, 88, 10, 70, 140, 255);
        draw_text(r, PAL_X, 570, "OFF", 200, 200, 210, 1);
        draw_text(r, PAL_X + 92, 570, "ON", 200, 200, 210, 1);
    } else {
        Uint8 lo[3], hi[3];
        overlay_scale(o, lo, hi);
        gradient_bar(r, PAL_X, 556, 180, 10, lo, hi);
        draw_text(r, PAL_X, 570, "LOW", 200, 200, 210, 1);
        draw_text(r, PAL_X + 150, 570, "HIGH", 200, 200, 210, 1);
    }

    draw_text(r, PAL_X, 596, "1-9,0,-: TOOLS  F1-F4: OVERLAY", 175, 185, 205, 1);
    draw_text(r, PAL_X, 612, "SPACE: PAUSE  S/L: SAVE/LOAD",   175, 185, 205, 1);
    draw_text(r, PAL_X, 628, "ESC: CLEAR OVERLAY  Q: QUIT",    175, 185, 205, 1);
}

/* ---- public frame ------------------------------------------------------- */
void render_frame(SDL_Renderer *r, int hover_x, int hover_y,
                  TileType tool, int overlay, Scorecard sc, int day, int paused)
{
    /* background + map */
    fill_rect(r, 0, 0, WIN_W, WIN_H, 12, 12, 16);
    draw_map(r, overlay);
    draw_hover(r, hover_x, hover_y);

    /* chrome */
    draw_topbar(r, day, sc.population, paused);
    fill_rect(r, SIDEBAR_X, MAP_Y, SIDEBAR_W, WIN_H - MAP_Y, 24, 26, 34);
    draw_palette(r, tool);
    draw_scorecard(r, sc);
    draw_legend(r, overlay);
}
