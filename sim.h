/* sim.h — simulation interface. FROZEN per docs/CONTRACT.md. */
#ifndef SIM_H
#define SIM_H

typedef struct { int walkability, green, amenities, yield, livability; /* 0..100 */
                 int population, jobs, day; } Scorecard;

void sim_init(void);
void sim_tick(void);              /* advances one day; recompute everything */
Scorecard sim_scorecard(void);
extern int sim_paused;            /* 0/1, set by main */

#endif /* SIM_H */