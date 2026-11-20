#!/usr/bin/env python3
"""Build assets/hud_topbar.png from assets/svg/hud_topbar.svg and verify it.

The HUD strip is a flat 920x40 background. The application paints all live
text on top, so the four text-safe zones must be completely quiet (#141414).

Requires rsvg-convert and ImageMagick (identify, convert).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG = HERE / "svg" / "hud_topbar.svg"
PNG = HERE / "hud_topbar.png"
LAYOUT = HERE / "layout_hud.json"
WIDTH, HEIGHT = 920, 40
BASE = "#141414"


def run(*cmd: str) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(cmd)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def main() -> int:
    if not SVG.is_file() or SVG.stat().st_size == 0:
        print(f"FAIL: missing or empty {SVG}", file=sys.stderr)
        return 1
    if not shutil.which("rsvg-convert") or not shutil.which("convert"):
        print("FAIL: rsvg-convert and ImageMagick convert are required", file=sys.stderr)
        return 1

    # 1. Source SVG is XML-valid with the exact contract dimensions, crisp edges,
    #    no gradients/filters and no text elements.
    root = ET.parse(SVG).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    if (root.get("width"), root.get("height"), root.get("viewBox")) != (
        "920", "40", "0 0 920 40"
    ):
        raise RuntimeError(f"bad root dims: {root.attrib}")
    if root.get("shape-rendering") != "crispEdges":
        raise RuntimeError("missing shape-rendering=crispEdges")
    text = SVG.read_text().lower()
    for bad in ("<text", "gradient", "filter", "<path", "<circle", "<line", "<polygon"):
        if bad in text:
            raise RuntimeError(f"forbidden construct: {bad}")
    rects = list(root.iter(f"{ns}rect"))
    if not rects or not (
        rects[0].get("x", "0") == "0"
        and rects[0].get("y", "0") == "0"
        and rects[0].get("width") == "920"
        and rects[0].get("height") == "40"
        and rects[0].get("fill", "").upper() == BASE
    ):
        raise RuntimeError("first rect is not the full-bleed 920x40 #141414 base")
    print(f"SVG  {SVG.relative_to(HERE.parent.parent)}: XML valid, "
          f"width=920 height=40, crispEdges, no text/gradient/filter, "
          f"{len(rects)} integer rects")

    # 2. Rasterise deterministically to exactly 920x40.
    run("rsvg-convert", "-w", str(WIDTH), "-h", str(HEIGHT), str(SVG), "-o", str(PNG))
    if PNG.stat().st_size == 0:
        raise RuntimeError("PNG is empty")
    dim = run("identify", "-format", "%wx%h", str(PNG))
    if dim != "920x40":
        raise RuntimeError(f"PNG is {dim}, expected 920x40")
    print(f"PNG  {PNG.name}: rasterised {dim}, non-empty "
          f"({PNG.stat().st_size} bytes)")

    # 3. Every pixel in every safe zone must be exactly #141414 (one colour,
    #    and that colour is the base). Zones come from layout_hud.json.
    layout = json.loads(LAYOUT.read_text())
    for zone in layout["safe_zones"]:
        name, x, y, w, h = (
            zone["name"], zone["x"], zone["y"], zone["w"], zone["h"]
        )
        crop = f"{w}x{h}+{x}+{y}"
        colours = run("convert", str(PNG), "-crop", crop, "+repage",
                      "-format", "%k", "info:")
        # IMv7 renders %[pixel:p{..}] as "srgb(20,20,20)"; %[hex:p{..}] gives
        # the canonical "141414", which we prefix to compare against #141414.
        corner = "#" + run("convert", str(PNG), "-crop", crop, "+repage",
                           "-format", "%[hex:p{0,0}]", "info:").lower()
        if colours != "1":
            raise RuntimeError(f"{name} crop {crop}: {colours} colours, expected 1")
        if corner != BASE.lower():
            raise RuntimeError(f"{name} crop {crop}: {corner}, expected {BASE}")
        print(f"ZONE {name:<5} crop {crop:<12}: colours={colours} "
              f"pixel(0,0)={corner}  -> QUIET")

    print("RESULT: ALL OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
