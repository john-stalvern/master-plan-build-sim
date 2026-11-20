# Master Planner — T1 scaffold. gcc + SDL2/SDL2_ttf via pkg-config.
CC      := gcc
CFLAGS  := -O2 -Wall -Wextra -std=c11 $(shell pkg-config --cflags sdl2 SDL2_ttf)
LDLIBS  := $(shell pkg-config --libs sdl2 SDL2_ttf)

OBJS := main.o world.o sim.o render.o

all: masterplanner

masterplanner: $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDLIBS)

main.o:   main.c world.h sim.h render.h
world.o:  world.c world.h
sim.o:    sim.c sim.h world.h
render.o: render.c render.h world.h sim.h

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Headless tests. tests/test_sim.c is owned by T2; it is picked up
# automatically once that file exists (T2 must not edit this Makefile).
TESTS := tests/test_world

tests/test_world: tests/test_world.c world.o world.h
	$(CC) $(CFLAGS) -I. -o $@ tests/test_world.c world.o

ifneq ($(wildcard tests/test_sim.c),)
TESTS += tests/test_sim
tests/test_sim: tests/test_sim.c sim.o world.o sim.h world.h
	$(CC) $(CFLAGS) -I. -o $@ tests/test_sim.c sim.o world.o
endif

test: masterplanner $(TESTS)
	./tests/test_world
	@if [ -x tests/test_sim ]; then ./tests/test_sim; fi
	./masterplanner --smoke --ticks 50

clean:
	rm -f masterplanner $(OBJS) tests/test_world tests/test_sim

.PHONY: all test clean