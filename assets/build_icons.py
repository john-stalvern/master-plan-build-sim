#!/usr/bin/env python3
"""Deterministic builder for the A1 tool icons and A2 metric icons.

Writes assets/svg/tool_<NAME>.svg (x11) and metric_<NAME>.svg (x5),
rasterises each to 16x16 with rsvg-convert, montages the two PNG strips
(assets/tools.png 176x16, assets/metrics.png 80x16), verifies dimensions
and per-cell colour counts, and writes assets/layout_icons.json.

Style: flat first-SimCity, integer-coordinate rects, shape-rendering=crispEdges,
no gradients/filters/text, 1px #141414 border on all four edges.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG_DIR = HERE / "svg"

OUTLINE = "#141414"   # border + dark detail
PALE = "#F0F0D2"      # glyph on dark swatches
LINE = "#E8E8E8"      # metric line art

# pal_tool[] order -- also the left-to-right strip order.
TOOL_ORDER = [
    "BULLDOZE", "ROAD", "RES", "COM", "IND", "PARK", "SCHOOL",
    "POLICE", "FIRE", "POWERPLANT", "POWERLINE",
]
TOOL_BASE = {
    "BULLDOZE": "#C84646", "ROAD": "#6E6E6E", "RES": "#3CA03C",
    "COM": "#3C64DC", "IND": "#966E32", "PARK": "#50DC50",
    "SCHOOL": "#9646C8", "POLICE": "#1E3282", "FIRE": "#D23228",
    "POWERPLANT": "#E6821E", "POWERLINE": "#DCC828",
}
# Bright swatches take a #141414 glyph; every other swatch takes #F0F0D2.
LIGHT_SWATCHES = {"PARK", "POWERPLANT", "POWERLINE"}

METRIC_ORDER = ["WALKABILITY", "GREEN", "AMENITIES", "YIELD", "LIVABILITY"]
ACCENT = {
    "WALKABILITY": "#6E6E6E", "GREEN": "#50DC50", "AMENITIES": "#9646C8",
    "YIELD": "#DCC828", "LIVABILITY": "#D23228",
}


class Canvas:
    """16x16 character canvas. '.'=leave base/transparent; other chars map to colours."""

    def __init__(self):
        self.g = [["." for _ in range(16)] for _ in range(16)]

    def px(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.g[y][x] = c

    def hline(self, x0, x1, y, c):
        for x in range(x0, x1 + 1):
            self.px(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.px(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            self.hline(x0, x1, y, c)

    def border(self):
        for x in range(16):
            self.px(x, 0, "#")
            self.px(x, 15, "#")
        for y in range(16):
            self.px(0, y, "#")
            self.px(15, y, "#")


def runs(c: Canvas):
    """Merge horizontal runs of identical cells in the interior (rows/cols 1..14)."""
    out = []
    for y in range(1, 15):
        x = 1
        while x <= 14:
            ch = c.g[y][x]
            if ch == ".":
                x += 1
                continue
            x0 = x
            while x <= 14 and c.g[y][x] == ch:
                x += 1
            out.append((x0, y, x - x0, 1, ch))
    return out


# ---------------------------------------------------------------- A1 tools
def t_bulldoze():
    c = Canvas(); c.border()
    for i in range(2, 14):
        c.px(i, i, "g"); c.px(i, 15 - i, "g")
    for i in range(3, 13):                 # thicken the X
        c.px(i, i + 1, "g"); c.px(i, 14 - i, "g")
    return c


def t_road():
    c = Canvas(); c.border()
    c.vline(3, 2, 13, "g"); c.vline(12, 2, 13, "g")
    for a, b in ((2, 4), (6, 8), (10, 12)):
        c.rect(7, a, 8, b, "g")            # dashed centre line
    return c


def t_res():
    c = Canvas(); c.border()
    for r, (x0, x1) in {2: (7, 8), 3: (6, 9), 4: (5, 10), 5: (4, 11), 6: (3, 12)}.items():
        c.hline(x0, x1, r, "g")            # roof
    c.rect(4, 7, 11, 13, "g")              # body
    c.rect(5, 8, 6, 9, "#"); c.rect(9, 8, 10, 9, "#")   # windows
    c.rect(7, 10, 8, 13, "#")              # door
    return c


def t_com():
    c = Canvas(); c.border()
    c.hline(2, 13, 2, "g")
    for r in (3, 4):
        for x in range(2, 14):
            c.px(x, r, "g" if (x - 2) % 2 == 0 else "#")  # striped awning
    c.hline(2, 13, 5, "g")
    c.vline(2, 6, 13, "g"); c.vline(13, 6, 13, "g")
    c.rect(4, 6, 11, 9, "g")               # display window
    c.rect(5, 7, 6, 8, "#"); c.rect(9, 7, 10, 8, "#")
    c.rect(7, 10, 8, 13, "g")              # door
    c.px(8, 12, "#")
    return c


def t_ind():
    c = Canvas(); c.border()
    c.rect(10, 2, 11, 5, "g")              # smokestack
    c.rect(2, 6, 13, 13, "g")              # plant body
    for x0 in (4, 7, 10):
        c.rect(x0, 9, x0 + 1, 11, "#")     # windows
    return c


def t_park():
    c = Canvas(); c.border()
    for r, (x0, x1) in {2: (6, 9), 3: (5, 10), 4: (4, 11), 5: (3, 12),
                       6: (3, 12), 7: (3, 12), 8: (4, 11), 9: (5, 10)}.items():
        c.hline(x0, x1, r, "g")            # canopy
    c.rect(7, 10, 8, 13, "g")              # trunk
    return c


def t_school():
    c = Canvas(); c.border()
    c.hline(2, 13, 3, "g"); c.hline(2, 13, 11, "g")
    c.vline(2, 4, 10, "g"); c.vline(13, 4, 10, "g")
    c.vline(7, 4, 10, "#")                 # book spine
    for y0 in (5, 8):
        c.rect(4, y0, 5, y0 + 1, "#")     # text blocks
        c.rect(10, y0, 11, y0 + 1, "#")
    return c


def t_police():
    c = Canvas(); c.border()
    for r, (x0, x1) in {2: (4, 11), 3: (3, 12), 4: (3, 12), 5: (3, 12),
                       6: (4, 11), 7: (4, 11), 8: (5, 10), 9: (6, 9),
                       10: (7, 8)}.items():
        c.hline(x0, x1, r, "g")            # shield
    c.hline(7, 8, 4, "#"); c.hline(6, 9, 5, "#"); c.hline(7, 8, 6, "#")  # star
    return c


def t_fire():
    c = Canvas(); c.border()
    rows = {2: (7, 8), 3: (6, 9), 4: (5, 10), 5: (5, 10), 6: (4, 11),
            7: (4, 11), 8: (3, 12), 9: (3, 12), 10: (3, 12), 11: (4, 11),
            12: (4, 11), 13: (5, 10)}
    for r, (x0, x1) in rows.items():
        c.hline(x0, x1, r, "g")
    for r in (5, 6, 7, 8):
        c.px(7, r, "."); c.px(8, r, ".")  # inner flame core
    return c


def t_plant():
    c = Canvas(); c.border()
    c.rect(3, 2, 4, 6, "g"); c.rect(11, 2, 12, 6, "g")  # stacks
    c.rect(2, 7, 13, 13, "g")                           # station
    c.rect(4, 9, 5, 10, "."); c.rect(10, 9, 11, 10, ".")  # windows
    for x, y in ((8, 8), (7, 9), (8, 9), (7, 10), (8, 10),
                 (7, 11), (8, 11), (7, 12)):
        c.px(x, y, ".")                                 # bolt cutout
    c.rect(7, 13, 8, 13, ".")                           # door
    return c


def t_line():
    c = Canvas(); c.border()
    c.px(7, 2, "g"); c.px(8, 2, "g")
    c.vline(7, 3, 13, "g"); c.vline(8, 3, 13, "g")      # mast
    c.hline(3, 12, 4, "g"); c.hline(4, 11, 7, "g")      # crossarms
    for r in range(9, 14):
        lx, rx = 7 - (r - 8), 8 + (r - 8)
        c.px(lx, r, "g"); c.px(rx, r, "g")              # splayed legs
        if r in (9, 11, 13):
            c.hline(lx, rx, r, "g")                     # lattice braces
    return c


TOOL_GLYPHS = {
    "BULLDOZE": t_bulldoze, "ROAD": t_road, "RES": t_res, "COM": t_com,
    "IND": t_ind, "PARK": t_park, "SCHOOL": t_school, "POLICE": t_police,
    "FIRE": t_fire, "POWERPLANT": t_plant, "POWERLINE": t_line,
}


# -------------------------------------------------------------- A2 metrics
def m_walk():
    c = Canvas(); c.border()
    for r in (2, 4, 6, 8, 10, 12):
        c.px(7, r, "w")                                  # dashed route
    c.rect(2, 5, 5, 9, "a"); c.px(3, 7, "."); c.px(4, 7, ".")  # FP1
    for x, y in ((2, 3), (3, 2), (4, 2), (5, 3)):
        c.px(x, y, "a")
    c.rect(9, 9, 12, 13, "a"); c.px(10, 11, "."); c.px(11, 11, ".")  # FP2
    for x, y in ((9, 7), (10, 6), (11, 6), (12, 7)):
        c.px(x, y, "a")
    return c


def m_green():
    c = Canvas(); c.border()
    for r, (x0, x1) in {3: (7, 8), 4: (5, 10), 5: (4, 11), 6: (3, 12),
                       7: (3, 12), 8: (4, 11), 9: (5, 10), 10: (7, 8)}.items():
        c.hline(x0, x1, r, "a")                          # leaf
    for r in range(4, 11):
        c.px(7, r, "w")                                  # midrib
    for x, y in ((9, 6), (9, 7), (5, 8), (5, 9)):
        c.px(x, y, "w")                                  # side veins
    c.px(7, 11, "w"); c.px(6, 12, "w"); c.px(5, 13, "w")  # stem
    return c


def m_amenities():
    c = Canvas(); c.border()
    c.rect(2, 4, 7, 12, "a")                             # school
    c.hline(3, 6, 7, "w"); c.hline(3, 6, 9, "w")
    c.vline(4, 7, 9, "w")                                # book pages + spine
    c.rect(9, 4, 13, 12, "a")                            # shop
    c.hline(9, 13, 5, "w")                               # awning
    c.rect(10, 8, 12, 9, "w")                            # window
    return c


def m_yield():
    c = Canvas(); c.border()
    c.vline(2, 3, 12, "w"); c.hline(2, 13, 12, "w")      # axes
    c.rect(4, 9, 5, 11, "a")
    c.rect(7, 6, 8, 11, "a")
    c.rect(10, 4, 11, 11, "a")                           # rising bars
    return c


def m_livability():
    c = Canvas(); c.border()
    rows = {4: ((4, 6), (9, 11)), 5: ((3, 7), (8, 12)), 6: ((3, 12),),
            7: ((3, 12),), 8: ((4, 11),), 9: ((5, 10),), 10: ((6, 9),),
            11: ((7, 8),)}
    for r, segs in rows.items():
        for x0, x1 in segs:
            c.hline(x0, x1, r, "a")                      # heart
    c.px(5, 5, "w"); c.px(5, 6, "w")                     # glint
    return c


METRIC_GLYPHS = {
    "WALKABILITY": m_walk, "GREEN": m_green, "AMENITIES": m_amenities,
    "YIELD": m_yield, "LIVABILITY": m_livability,
}


def emit_svg(path: Path, base: str | None, rects):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
         f'viewBox="0 0 16 16" shape-rendering="crispEdges">']
    if base:
        p.append(f'<rect x="0" y="0" width="16" height="16" fill="{base}"/>')
    for x, y, w, h, col in rects:
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}"/>')
    p += [
        '<rect x="0" y="0" width="16" height="1" fill="#141414"/>',
        '<rect x="0" y="15" width="16" height="1" fill="#141414"/>',
        '<rect x="0" y="0" width="1" height="16" fill="#141414"/>',
        '<rect x="15" y="0" width="1" height="16" fill="#141414"/>',
        '</svg>',
    ]
    path.write_text("\n".join(p) + "\n")


def build_svgs():
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    for name in TOOL_ORDER:
        gcol = OUTLINE if name in LIGHT_SWATCHES else PALE
        cmap = {"g": gcol, "#": OUTLINE}
        rects = []
        for x, y, w, h, ch in runs(TOOL_GLYPHS[name]()):
            if ch not in cmap:
                raise ValueError(f"tool {name}: unknown glyph char {ch!r}")
            rects.append((x, y, w, h, cmap[ch]))
        emit_svg(SVG_DIR / f"tool_{name}.svg", TOOL_BASE[name], rects)
    for name in METRIC_ORDER:
        cmap = {"w": LINE, "a": ACCENT[name]}
        rects = []
        for x, y, w, h, ch in runs(METRIC_GLYPHS[name]()):
            if ch not in cmap:
                raise ValueError(f"metric {name}: unknown glyph char {ch!r}")
            rects.append((x, y, w, h, cmap[ch]))
        emit_svg(SVG_DIR / f"metric_{name}.svg", None, rects)


def write_layout():
    data = {
        "group": "icons",
        "strips": [
            {
                "file": "assets/tools.png",
                "size": "176x16",
                "cells": [{"name": n, "x": i * 16, "y": 0}
                          for i, n in enumerate(TOOL_ORDER)],
            },
            {
                "file": "assets/metrics.png",
                "size": "80x16",
                "cells": [{"name": n, "x": i * 16, "y": 0}
                          for i, n in enumerate(METRIC_ORDER)],
            },
        ],
        "notes": (
            "A1 tools: pal_tool[] order, 11 x 16x16 swatches on one row. "
            "A2 metrics: transparent interior, #E8E8E8 line art plus one "
            "contract accent per icon. Build with assets/build_icons.py."
        ),
    }
    (HERE / "layout_icons.json").write_text(json.dumps(data, indent=2) + "\n")


def tool(*cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(cmd)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def main():
    build_svgs()
    for exe in ("rsvg-convert", "montage", "convert", "identify"):
        if not shutil.which(exe):
            print(f"missing required tool: {exe}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="mp-icons-") as tmp:
        tmpdir = Path(tmp)
        for strip, names, prefix in (("tools", TOOL_ORDER, "tool"),
                                     ("metrics", METRIC_ORDER, "metric")):
            rasters = []
            for i, name in enumerate(names):
                src = SVG_DIR / f"{prefix}_{name}.svg"
                root = ET.parse(src).getroot()
                if (root.get("width"), root.get("height"), root.get("viewBox")) != (
                        "16", "16", "0 0 16 16"):
                    raise RuntimeError(f"{src.name}: bad root dims {root.attrib}")
                dst = tmpdir / f"{strip}_{i:02d}.png"
                tool("rsvg-convert", "-w", "16", "-h", "16", str(src), "-o", str(dst))
                dim = tool("identify", "-format", "%wx%h", str(dst))
                if dim != "16x16":
                    raise RuntimeError(f"{src.name}: raster {dim}, expected 16x16")
                rasters.append(str(dst))

            out = HERE / f"{strip}.png"
            tool("montage", *rasters, "-tile", f"{len(names)}x1",
                 "-geometry", "16x16+0+0", "-background", "none", str(out))
            dim = tool("identify", "-format", "%wx%h", str(out))
            expected = f"{len(names) * 16}x16"
            if dim != expected:
                raise RuntimeError(f"{out.name}: {dim}, expected {expected}")
            for i, name in enumerate(names):
                k = tool("convert", str(out), "-crop", f"16x16+{i * 16}+0",
                         "+repage", "-format", "%k", "info:")
                if int(k) < 2:
                    raise RuntimeError(f"{out.name} cell {name}: only {k} colour")
            print(f"{out.name}: {dim}  ({len(names)} cells, >=2 colours each)")

    write_layout()
    print("layout_icons.json written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
