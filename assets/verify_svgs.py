#!/usr/bin/env python3
"""One-off validation of the 21 tile SVGs against the card's hard style rules."""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG = HERE / "svg"
EXPECTED_BASE = {
    "T_EMPTY": "#184018", "T_WATER": "#2050B4", "T_ROAD": "#6E6E6E",
    "T_POWERLINE": "#DCC828", "T_POWERPLANT": "#E6821E", "T_RES": "#3CA03C",
    "T_COM": "#3C64DC", "T_IND": "#966E32", "T_PARK": "#50DC50",
    "T_SCHOOL": "#9646C8", "T_POLICE": "#1E3282", "T_FIRE": "#D23228",
    "T_RES_L1": "#4CB04C", "T_RES_L2": "#5CC05C", "T_RES_L3": "#6CD06C",
    "T_COM_L1": "#4C74EC", "T_COM_L2": "#5C84FC", "T_COM_L3": "#6C94FF",
    "T_IND_L1": "#A67E42", "T_IND_L2": "#B68E52", "T_IND_L3": "#C69E62",
}
OUTLINE = "#141414"
fails = []
for name, want in EXPECTED_BASE.items():
    p = SVG / (name + ".svg")
    if not p.exists():
        fails.append(f"{name}: MISSING")
        continue
    text = p.read_text()
    try:
        root = ET.parse(p).getroot()
    except ET.ParseError as e:
        fails.append(f"{name}: bad XML {e}")
        continue
    if (root.get("width"), root.get("height"), root.get("viewBox")) != (
        "16", "16", "0 0 16 16"
    ):
        fails.append(f"{name}: bad root dims {root.attrib}")
    if root.get("shape-rendering") != "crispEdges":
        fails.append(f"{name}: missing shape-rendering=crispEdges")
    for bad in ("gradient", "filter", "<text", "<circle", "<line", "<polygon", "<path"):
        if bad in text.lower():
            fails.append(f"{name}: forbidden construct {bad}")
    # Integer-only coordinates.
    for attr in ("x", "y", "width", "height", "rx", "ry"):
        for val in re.findall(rf'\b{attr}="([^"]+)"', text):
            if not re.fullmatch(r"\d+(?:\.\d+)?", val):
                fails.append(f"{name}: non-integer {attr}={val}")
            elif "." in val:
                fails.append(f"{name}: fractional {attr}={val}")
    # First painted rect must be the full-bleed exact base.
    rects = list(root.iter("{http://www.w3.org/2000/svg}rect"))
    if not rects or not (
        rects[0].get("x", "0") in ("0", None)
        and rects[0].get("y", "0") in ("0", None)
        and rects[0].get("width") == "16"
        and rects[0].get("height") == "16"
        and rects[0].get("fill", "").upper() == want
    ):
        first = rects[0].attrib if rects else None
        fails.append(f"{name}: base fill wrong: {first} (want {want})")
    # Four-rect dark border present.
    borders = [
        r for r in rects
        if r.get("fill", "").upper() == OUTLINE and (
            (r.get("width") == "16" and r.get("height") == "1")
            or (r.get("width") == "1" and r.get("height") == "16")
        )
    ]
    if len(borders) < 4:
        fails.append(f"{name}: only {len(borders)} border rects")
    # Rasterise.
    out = Path("/tmp") / f"check_{name}.png"
    r = subprocess.run(
        ["rsvg-convert", "-w", "16", "-h", "16", str(p), "-o", str(out)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        fails.append(f"{name}: rsvg failed {r.stderr.strip()}")
        continue
    dim = subprocess.run(["identify", "-format", "%wx%h", str(out)],
                         capture_output=True, text=True).stdout.strip()
    if dim != "16x16":
        fails.append(f"{name}: raster {dim}")

print(f"checked {len(EXPECTED_BASE)} svgs")
for f in fails:
    print("FAIL", f)
print("RESULT:", "ALL OK" if not fails else f"{len(fails)} FAILURES")
sys.exit(1 if fails else 0)
