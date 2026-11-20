/* sim.c — STUB by T1 so the scaffold links. T2 (sim engineer) replaces this
 * with the full tick model from docs/CONTRACT.md. Do not build on this. */
#include "sim.h"
#include "world.h"

int sim_paused = 0;
static int day = 0;

void sim_init(void)
{
    day = 0;
    sim_paused = 0;
}

void sim_tick(void)
{
    day++; /* stub: no power/pollution/crime/growth yet */
}

Scorecard sim_scorecard(void)
{
    Scorecard sc = {0};
    sc.population = world_population();
    sc.jobs = world_jobs();
    sc.day = day;
    return sc; /* metric fields stay 0 until T2 lands */
}