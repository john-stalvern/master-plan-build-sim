#!/usr/bin/env python3
"""Build the four cursor/placement markers for Master Planner (batch A item A5).

Renders assets/svg/cursor_<NAME>.svg to individual 16x16 PNGs, then montages
them into assets/cursors.png (64x16, one row: HOVER, VALID, INVALID, BULLDOZE).

Markers override the base-tile outline rule: the coloured 1px outline IS the
marker. Interiors stay fully transparent (alpha 0); no opaque background box.

Requires rsvg-convert and ImageMagick (montage, convert, identify).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG_DIR = HERE / "svg"
ATLAS = HERE / "cursors.png"

# Fixed atlas order, one row of four cells. Index -> (x, y) = (i*16, 0).
ORDER = [
    ("HOVER", "#E8E8E8"),
    ("VALID", "#50DC50"),
    ("INVALID", "#D23228"),
    ("BULLDOZE", "#6E6E6E"),
]
TILE = 16


def run(*cmd: str) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(cmd)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def pixel_rgba(img: Path, x: int, y: int) -> tuple[int, int, int, int]:
    """Return (r, g, b, a) of pixel (x, y) using ImageMagick at 8-bit depth."""
    out = run("convert", str(img), "-crop", f"1x1+{x}+{y}", "+repage",
              "-depth", "8", "txt:-")
    m = re.search(r"#([0-9A-Fa-f]{8})", out)
    if not m:
        raise RuntimeError(f"cannot parse pixel {x},{y} of {img}: {out!r}")
    h = m.group(1)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def main() -> int:
    # SVG sources present + XML-valid 16x16 with crispEdges.
    for name, _colour in ORDER:
        svg = SVG_DIR / f"cursor_{name}.svg"
        if not svg.exists():
            raise RuntimeError(f"missing SVG: {svg}")
        root = ET.parse(svg).getroot()
        if (root.get("width"), root.get("height"), root.get("viewBox")) != (
            "16", "16", "0 0 16 16"
        ):
            raise RuntimeError(f"{svg.name}: bad root dims {root.attrib}")
        if root.get("shape-rendering") != "crispEdges":
            raise RuntimeError(f"{svg.name}: missing shape-rendering=crispEdges")

    if not shutil.which("rsvg-convert") or not shutil.which("montage"):
        raise RuntimeError("rsvg-convert and ImageMagick montage are required")

    # Render individual PNGs, each exactly 16x16.
    rasters: list[Path] = []
    for name, _colour in ORDER:
        src = SVG_DIR / f"cursor_{name}.svg"
        dst = HERE / f"cursor_{name}.png"
        run("rsvg-convert", "-w", str(TILE), "-h", str(TILE), str(src), "-o", str(dst))
        dim = run("identify", "-format", "%wx%h", str(dst))
        if dim != "16x16":
            raise RuntimeError(f"{dst.name} rasterised to {dim}, expected 16x16")
        rasters.append(dst)

    # Montage into a single 64x16 sheet, zero gaps, transparent background.
    run("montage", *[str(p) for p in rasters], "-tile", "4x1",
        "-geometry", "16x16+0+0", "-background", "none", str(ATLAS))
    dim = run("identify", "-format", "%wx%h", str(ATLAS))
    if dim != "64x16":
        raise RuntimeError(f"atlas is {dim}, expected 64x16")

    # Per-cell verification on the atlas.
    print(f"atlas {ATLAS.name}: {dim} (4 cells, 4x1)")
    all_ok = True
    for i, (name, colour) in enumerate(ORDER):
        x = i * TILE
        ncolours = int(run("convert", str(ATLAS), "-crop", f"16x16+{x}+0",
                           "+repage", "-format", "%k", "info:"))
        centre = pixel_rgba(ATLAS, x + 8, 8)
        # Outline colour at (0,0) or, failing that, at (0,3).
        p00 = pixel_rgba(ATLAS, x + 0, 0)
        p03 = pixel_rgba(ATLAS, x + 0, 3)
        want = hex_rgb(colour)
        outline_ok = p00[:3] == want and p00[3] == 255
        outline_pos = "0,0"
        if not outline_ok:
            outline_pos = "0,3"
            outline_ok = p03[:3] == want and p03[3] == 255
        interior_ok = centre[3] == 0
        nonempty_ok = ncolours >= 2
        ok = nonempty_ok and interior_ok and outline_ok
        all_ok &= ok
        status = "OK" if ok else "FAIL"
        print(
            f"  {name:<8} cell x={x:<2} rgb={ncolours} (want>=2) "
            f"interior(8,8)={centre} alpha={centre[3]} (want 0) "
            f"outline@{outline_pos}={p00[:3] if outline_pos == '0,0' else p03[:3]} "
            f"(want {colour}) -> {status}"
        )
    print("RESULT:", "ALL OK" if all_ok else "FAILURES")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
