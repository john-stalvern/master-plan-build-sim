#!/usr/bin/env python3
"""Generate ``demo.bin`` — a ready-to-load example plan for Master Planner.

The output is byte-for-byte the format written by ``world_save()``:
    "MPv1" | world[40][40] (6 bytes/tile) | world_trees[40][40] (1 byte/tile)
        4  +      9600                    +      1600              = 11204 bytes

Deterministic and dependency-free (Python stdlib only). Terrain is the same
river/lake/forest that ``world_init()`` produces, so the demo looks like a real
game world. Re-running this script always yields the same bytes.

Usage:
    python3 tools/make_demo.py            # writes ./demo.bin
    python3 tools/make_demo.py plan.bin   # write directly to the load path
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

GRID = 40
MAGIC = b"MPv1"
MASK = 0xFFFFFFFF

# TileType (docs/CONTRACT.md, addendum v1.2 — append-only).
EMPTY, WATER, ROAD, POWERLINE, POWERPLANT = 0, 1, 2, 3, 4
RES, COM, IND, PARK, SCHOOL, POLICE, FIRE, PICKLEBALL = 5, 6, 7, 8, 9, 10, 11, 12


def tile_hash(x: int, y: int) -> int:
    """Exact 32-bit reproduction of world.c:tile_hash (unsigned wraparound)."""
    h = ((x * 374761393 + y * 668265263) & MASK) ^ 0x5BF03635
    h = ((h ^ (h >> 13)) * 1274126177) & MASK
    return h ^ (h >> 16)


def terrain() -> tuple[list[list[int]], list[list[int]]]:
    """Same deterministic world as world_init(): river, lake, ~18% trees."""
    tiles = [[EMPTY] * GRID for _ in range(GRID)]
    trees = [[0] * GRID for _ in range(GRID)]
    for y in range(GRID):
        river_x = 27 + (y * y // 13 % 5) - 2  # meanders x=25..29
        for x in range(GRID):
            dx, dy = x - 8, y - 31
            if river_x - 1 <= x <= river_x + 1:
                tiles[y][x] = WATER
            elif dx * dx + dy * dy <= 10:
                tiles[y][x] = WATER
            elif tile_hash(x, y) % 100 < 18:
                trees[y][x] = 1
    return tiles, trees


def build_plan() -> bytes:
    tiles, trees = terrain()

    def put(x: int, y: int, t: int) -> None:
        """world_place(): only empty land is buildable; building clears trees."""
        if 0 <= x < GRID and 0 <= y < GRID and tiles[y][x] == EMPTY:
            tiles[y][x] = t
            trees[y][x] = 0

    def rect(x0: int, y0: int, x1: int, y1: int, t: int) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(x, y, t)

    def hline(y: int, x0: int, x1: int, t: int) -> None:
        rect(x0, y, x1, y, t)

    def vline(x: int, y0: int, y1: int, t: int) -> None:
        rect(x, y0, x, y1, t)

    def convert(x: int, y: int, t: int) -> None:
        """In-place type change (the CTRL+click park -> court model)."""
        tiles[y][x] = t
        trees[y][x] = 0

    # --- Power first (it must survive the road crossings below) ---
    # One plant + spine per neighbourhood column; power floods the 8-neighbours.
    for px in (5, 13, 21):
        put(px, 2, POWERPLANT)
        vline(px, 3, 19, POWERLINE)

    # --- Street grid: three east-west roads, three north-south roads ---
    for y in (4, 12, 20):
        hline(y, 2, 23, ROAD)
    for x in (6, 14, 22):
        vline(x, 4, 20, ROAD)

    # --- Homes on the frontage of each spine ---
    rect(3, 5, 4, 11, RES)
    rect(7, 5, 12, 11, RES)
    rect(15, 5, 20, 11, RES)
    rect(3, 13, 4, 19, RES)
    rect(7, 14, 12, 19, RES)
    rect(15, 14, 19, 19, RES)

    # --- Main-street retail on the south side of the middle road ---
    hline(13, 7, 12, COM)
    hline(13, 15, 20, COM)

    # --- Green heart, services and a little industry ---
    rect(3, 21, 4, 23, IND)
    rect(7, 21, 12, 23, PARK)
    rect(15, 21, 20, 22, PARK)
    put(10, 24, SCHOOL)
    put(3, 24, POLICE)
    put(20, 23, FIRE)
    # Two infill schools inside the residential bands: homes near both a
    # school and main-street retail score on the amenities metric.
    convert(10, 16, SCHOOL)
    convert(17, 16, SCHOOL)

    # --- CTRL+click a park -> pickleball court (addendum v1.2) ---
    if tiles[22][9] == PARK:
        convert(9, 22, PICKLEBALL)

    out = bytearray(MAGIC)
    for row in tiles:
        for t in row:
            out += struct.pack("<6B", t, 0, 0, 0, 0, 0)  # Tile: type,level,powered,landValue,pollution,crime
    for row in trees:
        out += bytes(row)
    assert len(out) == 4 + GRID * GRID * 7 == 11204
    return bytes(out)


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo.bin")
    dest.write_bytes(build_plan())
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
