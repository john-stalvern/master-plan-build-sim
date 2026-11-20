#!/usr/bin/env python3
"""Build A3 overlay legend keys and A4 overlay heat cells.

Generates SVG sources in assets/svg/ and rasters them with rsvg-convert.
Ramp colours use the exact integer math of render.c lerp_color():
t = a + trunc((b-a)*v/255), sampled at v = i*255//4 for i = 0..4.

Atlases are rendered from a single combined SVG (one <g> per cell) rather
than compositing PNGs: compositing semi-transparent cells would compound
alpha, and ImageMagick's -geometry/-composite offsets are error-prone.

Requires rsvg-convert and ImageMagick identify.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG_DIR = HERE / "svg"
MODES = ["LANDVALUE", "POLLUTION", "POWER", "CRIME"]
FILES = {
    "LANDVALUE": "legend_landvalue.png",
    "POLLUTION": "legend_pollution.png",
    "POWER": "legend_power.png",
    "CRIME": "legend_crime.png",
}
ENDPOINTS = {
    "LANDVALUE": ((150, 40, 40), (60, 220, 90)),
    "POLLUTION": ((50, 170, 70), (220, 50, 40)),
    "CRIME": ((50, 170, 70), (220, 60, 50)),
}
OFF, ON = (80, 55, 40), (70, 140, 255)
OUTLINE = "#141414"
INK = "#E8E8E8"
ACCENT = {
    "LANDVALUE": "#3CDC5A",
    "POLLUTION": "#DC3228",
    "CRIME": "#DC3C32",
    "POWER": "#468CFF",
}
HEAT_ALPHA = 0.6  # 153/255


def trunc_div(n: int, d: int) -> int:
    """C-style integer division: truncate toward zero."""
    q = abs(n) // d
    return -q if n < 0 else q


def lerp(a: tuple[int, int, int], b: tuple[int, int, int], v: int) -> tuple[int, int, int]:
    return (a[0] + trunc_div((b[0] - a[0]) * v, 255),
            a[1] + trunc_div((b[1] - a[1]) * v, 255),
            a[2] + trunc_div((b[2] - a[2]) * v, 255))


def hx(c: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % c


def ramp_steps(mode: str) -> list[str]:
    """Five hex step colours sampled at v = i*255//4 (i = 0..4)."""
    if mode == "POWER":
        # Binary: OFF, OFF, split step (sample x=90 falls in the ON half), ON, ON.
        return [hx(OFF), hx(OFF), hx(ON), hx(ON), hx(ON)]
    a, b = ENDPOINTS[mode]
    return [hx(lerp(a, b, i * 255 // 4)) for i in range(5)]


def svg_open(w: int, h: int) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" shape-rendering="crispEdges">')


def rect(x: int, y: int, w: int, h: int, fill: str, opacity: float | None = None) -> str:
    op = "" if opacity is None else f' fill-opacity="{opacity}"'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{op}/>'


def frame() -> str:
    return (rect(0, 0, 16, 1, OUTLINE) + rect(0, 15, 16, 1, OUTLINE) +
            rect(0, 0, 1, 16, OUTLINE) + rect(15, 0, 1, 16, OUTLINE))


def group(x: int, y: int, inner: str) -> str:
    return f'<g transform="translate({x},{y})">{inner}</g>'


# ---------------------------------------------------------------- SVG bodies
def ramp_body(mode: str) -> str:
    steps = ramp_steps(mode)
    body = ""
    for i, colour in enumerate(steps):
        x = i * 36
        if mode == "POWER" and i == 2:
            # left-half OFF / right-half ON, no blended colours
            body += rect(x, 0, 18, 10, hx(OFF))
            body += rect(x + 18, 0, 18, 10, hx(ON))
        else:
            body += rect(x, 0, 36, 10, colour)
    return body


GLYPHS: dict[str, list[tuple[int, int, int, int, str]]] = {
    "LANDVALUE": [
        (2, 13, 12, 1, INK),
        (3, 11, 2, 2, INK),
        (6, 9, 2, 4, INK),
        (9, 7, 2, 6, INK),
        (12, 5, 2, 8, ACCENT["LANDVALUE"]),
    ],
    "POLLUTION": [
        (4, 13, 8, 1, INK),
        (6, 5, 4, 1, INK),
        (6, 5, 1, 9, INK),
        (9, 5, 1, 9, INK),
        (8, 1, 2, 2, ACCENT["POLLUTION"]),
        (6, 3, 2, 2, ACCENT["POLLUTION"]),
        (10, 3, 2, 2, ACCENT["POLLUTION"]),
    ],
    "CRIME": [
        (3, 2, 10, 1, INK),
        (3, 3, 1, 6, INK),
        (12, 3, 1, 6, INK),
        (4, 9, 1, 2, INK),
        (11, 9, 1, 2, INK),
        (5, 11, 6, 1, INK),
        (6, 12, 4, 1, INK),
        (7, 13, 2, 1, INK),
        (7, 5, 2, 4, ACCENT["CRIME"]),
        (7, 10, 2, 1, ACCENT["CRIME"]),
    ],
    "POWER": [
        (9, 2, 3, 1, ACCENT["POWER"]),
        (8, 3, 3, 2, ACCENT["POWER"]),
        (7, 5, 4, 1, ACCENT["POWER"]),
        (6, 6, 4, 1, INK),
        (7, 7, 3, 2, INK),
        (6, 9, 3, 1, INK),
        (5, 10, 2, 2, INK),
    ],
}


def glyph_body(mode: str) -> str:
    body = frame()  # transparent interior, 1px #141414 frame
    for x, y, w, h, fill in GLYPHS[mode]:
        body += rect(x, y, w, h, fill)
    return body


FONT = {
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
}


def tag_body(key: str) -> str:
    body = rect(0, 0, 16, 16, OUTLINE) + frame()  # full-bleed dark + 1px frame
    for glyph, x0 in (("F", 2), (key[-1], 8)):
        for row, bits in enumerate(FONT[glyph]):
            for col, bit in enumerate(bits):
                if bit == "1":
                    body += rect(x0 + col, 4 + row, 1, 1, INK)
    return body


def heat_body(mode: str, step: int) -> str:
    colour = ramp_steps(mode)[step]
    body = ""
    # Non-overlapping border rects: overlap would compound alpha
    # (0.6 over 0.6 = 0.84) and break the <=153 requirement.
    body += rect(0, 0, 16, 1, OUTLINE, HEAT_ALPHA)
    body += rect(0, 15, 16, 1, OUTLINE, HEAT_ALPHA)
    body += rect(0, 1, 1, 14, OUTLINE, HEAT_ALPHA)
    body += rect(15, 1, 1, 14, OUTLINE, HEAT_ALPHA)
    body += rect(1, 1, 14, 14, colour, HEAT_ALPHA)  # interior fill
    return body


def ramp_svg(mode: str) -> str:
    return svg_open(180, 10) + ramp_body(mode) + "</svg>\n"


def glyph_svg(mode: str) -> str:
    return svg_open(16, 16) + glyph_body(mode) + "</svg>\n"


def tag_svg(key: str) -> str:
    return svg_open(16, 16) + tag_body(key) + "</svg>\n"


def heat_svg(mode: str, step: int) -> str:
    return svg_open(16, 16) + heat_body(mode, step) + "</svg>\n"


# ---------------------------------------------------------------- shell helpers
def run(*cmd: str) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(cmd)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def write(name: str, text: str) -> Path:
    p = SVG_DIR / name
    p.write_text(text)
    return p


def raster(src: Path, dst: Path, w: int, h: int) -> None:
    run("rsvg-convert", "-w", str(w), "-h", str(h), str(src), "-o", str(dst))
    dim = run("identify", "-format", "%wx%h", str(dst))
    if dim != f"{w}x{h}":
        raise RuntimeError(f"{dst.name} rasterised to {dim}, expected {w}x{h}")


def combined_png(tmp: Path, name: str, out: Path, w: int, h: int, groups: list[str]) -> None:
    """Render a single combined SVG made of translated cell groups."""
    src = tmp / name
    src.write_text(svg_open(w, h) + "".join(groups) + "</svg>\n")
    raster(src, out, w, h)


def main() -> int:
    for tool in ("rsvg-convert", "identify"):
        if not shutil.which(tool):
            print(f"required tool missing: {tool}", file=sys.stderr)
            return 1
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = HERE / ".legend-build-tmp"
    tmp.mkdir(exist_ok=True)

    for mode in MODES:
        # ramp: authoritative per-mode SVG -> final PNG
        raster(write(f"legend_ramp_{mode}.svg", ramp_svg(mode)),
               HERE / FILES[mode], 180, 10)
        # glyph + five heat cells: validate each source rasterises at 16x16
        raster(write(f"legend_glyph_{mode}.svg", glyph_svg(mode)),
               tmp / f"check_glyph_{mode}.png", 16, 16)
        for s in range(5):
            raster(write(f"heat_{mode}_S{s}.svg", heat_svg(mode, s)),
                   tmp / f"check_heat_{mode}_S{s}.png", 16, 16)

    for key in ("F1", "F2", "F3", "F4"):
        raster(write(f"legend_tag_{key}.svg", tag_svg(key)),
               tmp / f"check_{key}.png", 16, 16)

    # Atlases: one combined SVG per atlas, rendered in a single rsvg pass.
    combined_png(tmp, "a_glyphs.svg", HERE / "legend_glyphs.png", 64, 16,
                 [group(i * 16, 0, glyph_body(m)) for i, m in enumerate(MODES)])
    combined_png(tmp, "a_tags.svg", HERE / "legend_tags.png", 64, 16,
                 [group(i * 16, 0, tag_body(f"F{i+1}")) for i in range(4)])
    combined_png(tmp, "a_heat.svg", HERE / "heat.png", 80, 64,
                 [group(s * 16, r * 16, heat_body(m, s))
                  for r, m in enumerate(MODES) for s in range(5)])
    keys_groups = []
    for r, mode in enumerate(MODES):
        y = r * 16
        keys_groups += [group(0, y, tag_body(f"F{r+1}")),
                        group(16, y, glyph_body(mode)),
                        group(32, y + 3, ramp_body(mode))]
    combined_png(tmp, "a_keys.svg", HERE / "legend_keys.png", 212, 64, keys_groups)

    layout = {
        "group": "legends",
        "ramps": [
            {"mode": m, "file": f"assets/{FILES[m]}", "size": "180x10",
             "steps": ramp_steps(m)} for m in MODES
        ],
        "atlases": [
            {"file": "assets/legend_glyphs.png", "size": "64x16",
             "cells": [{"name": m, "x": i * 16, "y": 0} for i, m in enumerate(MODES)]},
            {"file": "assets/legend_tags.png", "size": "64x16",
             "cells": [{"name": f"F{i+1}", "x": i * 16, "y": 0} for i in range(4)]},
            {"file": "assets/heat.png", "size": "80x64",
             "cells": [{"name": f"{m}_S{s}", "x": s * 16, "y": r * 16}
                       for r, m in enumerate(MODES) for s in range(5)]},
            {"file": "assets/legend_keys.png", "size": "212x64",
             "rows": [{"name": m, "y": r * 16, "tag_x": 0, "glyph_x": 16,
                       "ramp_x": 32, "ramp_y": r * 16 + 3}
                      for r, m in enumerate(MODES)]},
        ],
        "notes": (
            "Ramp steps sampled at v=i*255//4 for i=0..4 using render.c "
            "lerp_color(): t=a+trunc((b-a)*v/255) per channel. POWER is "
            "binary: its ramp is OFF,OFF,(left-half OFF / right-half ON),"
            "ON,ON with no blended colours; the step-2 hex recorded is the "
            "ON half (the colour at sample x=90), and heat cell POWER_S2 "
            "uses that same ON colour. Heat cells carry fill and 1px "
            "#141414 outline at alpha 153 (60%); no pixel exceeds "
            "alpha 153. legend_keys.png is a reference composite; the "
            "individual PNGs remain authoritative."
        ),
    }
    (HERE / "layout_legends.json").write_text(json.dumps(layout, indent=2) + "\n")

    for p in tmp.iterdir():
        if p.is_file():
            p.unlink()
    tmp.rmdir()

    print("built 4 ramps, 4 glyphs, 4 tags, 20 heat cells (32 SVG sources)")
    print("PNGs: legend_{landvalue,pollution,power,crime}.png, "
          "legend_glyphs.png, legend_tags.png, legend_keys.png, heat.png")
    print("layout_legends.json written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
