/* render.h — SDL2 drawing interface. FROZEN per docs/CONTRACT.md.
 * Layout constants added by T1 scaffold for T3 (window/map/sidebar geometry). */
#ifndef RENDER_H
#define RENDER_H

#include <SDL.h>
#include "sim.h"
#include "world.h"

#define WIN_W     920
#define WIN_H     680
#define MAP_X     0
#define MAP_Y     40   /* top bar occupies y=0..39; map is 640x640 */
#define SIDEBAR_X 656  /* sidebar x=656..919: palette, scorecard, legend */

int  render_init(SDL_Renderer *r);   /* loads font, returns 0 ok */
void render_frame(SDL_Renderer *r, int hover_x, int hover_y,
                  TileType tool, int overlay, Scorecard sc, int day, int paused);
void render_quit(void);
/* overlay: 0=none 1=landValue 2=pollution 3=power 4=crime */

#endif /* RENDER_H */