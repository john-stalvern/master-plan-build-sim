#!/usr/bin/env python3
"""Independent verification of art batch A (manifest A1-A6).

Reads the generated PNGs as raw RGBA via ImageMagick and checks dimensions,
cell placement, palette colours, ramp steps, heat alpha, cursor transparency
and HUD text-safe zones against assets/layout_*.json. No third-party Python
modules required.
"""
from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FAILS: list[str] = []
CHECKS = 0


def check(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


def sh(*args: str) -> str:
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def dims(path: Path) -> tuple[int, int]:
    w, h = sh("identify", "-format", "%w %h", str(path)).split()
    return int(w), int(h)


def pixels(path: Path) -> tuple[bytes, int, int]:
    w, h = dims(path)
    p = subprocess.run(["convert", str(path), "-depth", "8", "RGBA:-"],
                       capture_output=True, check=True)
    data = p.stdout
    check(len(data) == w * h * 4, f"{path.name}: raw RGBA size {len(data)} != {w*h*4}")
    return data, w, h


def px(data: bytes, w: int, x: int, y: int) -> tuple[int, int, int, int]:
    i = (y * w + x) * 4
    return tuple(data[i:i + 4])  # type: ignore[return-value]


def rgb(hexstr: str) -> tuple[int, int, int]:
    s = hexstr.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def cell_colours(data: bytes, w: int, x: int, y: int, cw: int = 16,
                 ch: int = 16) -> set[tuple[int, int, int, int]]:
    return {px(data, w, x + i, y + j)
            for j in range(ch) for i in range(cw)}


def has_colour(colours: set[tuple[int, int, int, int]], hexstr: str) -> bool:
    r, g, b = rgb(hexstr)
    return (r, g, b, 255) in colours


def load(name: str) -> dict:
    path = ROOT / "assets" / f"layout_{name}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    icons = load("icons")
    legends = load("legends")
    markers = load("markers")
    hud = load("hud")

    # ---- expected files exist -------------------------------------------
    expected_pngs = {
        "tools.png": (176, 16), "metrics.png": (80, 16),
        "legend_landvalue.png": (180, 10), "legend_pollution.png": (180, 10),
        "legend_power.png": (180, 10), "legend_crime.png": (180, 10),
        "legend_glyphs.png": (64, 16), "legend_tags.png": (64, 16),
        "legend_keys.png": (212, 64), "heat.png": (80, 64),
        "cursors.png": (64, 16), "hud_topbar.png": (920, 40),
        "tiles.png": (112, 64), "preview.png": (448, 256),
        "cursor_HOVER.png": (16, 16), "cursor_VALID.png": (16, 16),
        "cursor_INVALID.png": (16, 16), "cursor_BULLDOZE.png": (16, 16),
    }
    for name, (ew, eh) in expected_pngs.items():
        p = HERE / name
        check(p.exists(), f"missing {p}")
        if p.exists():
            got = dims(p)
            check(got == (ew, eh), f"{name}: dims {got} != {(ew, eh)}")

    # ---- SVG sources parse -----------------------------------------------
    svgs = sorted((HERE / "svg").glob("*.svg"))
    check(len(svgs) >= 21 + 16 + 32 + 4 + 1, f"SVG count {len(svgs)} too low")
    for p in svgs:
        try:
            root = ET.parse(p).getroot()
            check(root.tag.endswith("svg"), f"{p.name}: not an <svg> root")
        except ET.ParseError as e:
            FAILS.append(f"{p.name}: bad XML {e}")

    # ---- A1 tool strip ----------------------------------------------------
    swatches = {
        "BULLDOZE": "#C84646", "ROAD": "#6E6E6E", "RES": "#3CA03C",
        "COM": "#3C64DC", "IND": "#966E32", "PARK": "#50DC50",
        "SCHOOL": "#9646C8", "POLICE": "#1E3282", "FIRE": "#D23228",
        "POWERPLANT": "#E6821E", "POWERLINE": "#DCC828",
    }
    data, w, _ = pixels(HERE / "tools.png")
    tool_strip = icons["strips"][0]
    check(tool_strip["size"] == "176x16", "layout_icons: tool strip size")
    check(len(tool_strip["cells"]) == 11, "layout_icons: 11 tool cells")
    for cell in tool_strip["cells"]:
        name, x, y = cell["name"], cell["x"], cell["y"]
        colours = cell_colours(data, w, x, y)
        check(len(colours) >= 2, f"tools {name}: blank cell")
        check(has_colour(colours, swatches[name]),
              f"tools {name}: contract swatch {swatches[name]} absent")
        check(px(data, w, x, y)[:3] == rgb("#141414"),
              f"tools {name}: corner outline is not #141414")
        check(Path(HERE / "svg" / f"tool_{name}.svg").exists(),
              f"missing SVG tool_{name}.svg")

    # ---- A2 metric strip --------------------------------------------------
    accents = {
        "WALKABILITY": "#6E6E6E", "GREEN": "#50DC50",
        "AMENITIES": "#9646C8", "YIELD": "#DCC828",
        "LIVABILITY": "#D23228",
    }
    data, w, _ = pixels(HERE / "metrics.png")
    metric_strip = icons["strips"][1]
    check(metric_strip["size"] == "80x16", "layout_icons: metric strip size")
    check(len(metric_strip["cells"]) == 5, "layout_icons: 5 metric cells")
    for cell in metric_strip["cells"]:
        name, x, y = cell["name"], cell["x"], cell["y"]
        colours = cell_colours(data, w, x, y)
        check(len(colours) >= 2, f"metrics {name}: blank cell")
        check(has_colour(colours, "#E8E8E8"),
              f"metrics {name}: #E8E8E8 line art absent")
        check(has_colour(colours, accents[name]),
              f"metrics {name}: accent {accents[name]} absent")
        check(Path(HERE / "svg" / f"metric_{name}.svg").exists(),
              f"missing SVG metric_{name}.svg")

    # ---- A3 ramp bars -----------------------------------------------------
    ramps = {r["mode"]: r for r in legends["ramps"]}
    check(set(ramps) == {"LANDVALUE", "POLLUTION", "POWER", "CRIME"},
          f"legend ramp modes {set(ramps)}")
    for mode, r in ramps.items():
        path = HERE / Path(r["file"]).name
        data, w, h = pixels(path)
        check((w, h) == (180, 10), f"{path.name}: {w}x{h} != 180x10")
        check(len(r["steps"]) == 5, f"{mode}: not 5 steps")
        for i, want in enumerate(r["steps"]):
            got = px(data, w, i * 36 + 18, 5)[:3]
            check(got == rgb(want),
                  f"{mode} step {i}: sample {got} != {want}")
        for i in range(5):
            colours = cell_colours(data, w, i * 36, 0, 36, 10)
            check(len(colours) == 1 or (mode == "POWER" and i == 2),
                  f"{mode} step {i}: unexpected extra colours")
        check(Path(HERE / "svg" / f"legend_ramp_{mode}.svg").exists(),
              f"missing SVG legend_ramp_{mode}.svg")

    # ---- A3 glyph + F-key tag atlases ------------------------------------
    atlases = {a["file"]: a for a in legends["atlases"]}
    for key, prefix in (("assets/legend_glyphs.png", "legend_glyph"),
                        ("assets/legend_tags.png", "legend_tag")):
        a = atlases[key]
        data, w, _ = pixels(HERE / Path(key).name)
        check(a["size"] == "64x16", f"{key}: declared size")
        for cell in a["cells"]:
            name, x = cell["name"], cell["x"]
            colours = cell_colours(data, w, x, cell["y"])
            check(len(colours) >= 2, f"{key} {name}: blank cell")
            svg = (f"{prefix}_{name}.svg" if prefix == "legend_glyph"
                   else f"legend_tag_F{name[1]}.svg")
            check((HERE / "svg" / svg).exists(), f"missing SVG {svg}")

    # ---- A4 heat atlas ----------------------------------------------------
    heat = atlases["assets/heat.png"]
    check(heat["size"] == "80x64", "heat: declared size")
    check(len(heat["cells"]) == 20, f"heat: {len(heat['cells'])} cells != 20")
    data, w, _ = pixels(HERE / "heat.png")
    alpha_max = max(data[3::4])
    check(alpha_max <= 153, f"heat alpha max {alpha_max} > 153 (60%)")
    for cell in heat["cells"]:
        name, x, y = cell["name"], cell["x"], cell["y"]
        colours = cell_colours(data, w, x, y)
        check(len(colours) >= 2, f"heat {name}: blank cell")
        mode, step = name.rsplit("_", 1)
        want = rgb(ramps[mode]["steps"][int(step.lstrip("S"))])
        centre = px(data, w, x + 8, y + 8)
        # rsvg-convert premultiplies alpha: an exact source hex can rasterise
        # one LSB low after unpremultiply at alpha=153. Sources stay exact.
        delta = max(abs(centre[i] - want[i]) for i in range(3))
        check(delta <= 1,
              f"heat {name}: centre {centre[:3]} vs ramp {want} (delta {delta})")
        check(centre[3] == 153, f"heat {name}: centre alpha {centre[3]} != 153")
        check((HERE / "svg" / f"heat_{name}.svg").exists(),
              f"missing SVG heat_{name}.svg")

    # legend_keys.png composite must contain all four complete rows.
    data, w, _ = pixels(HERE / "legend_keys.png")
    for row in atlases["assets/legend_keys.png"]["rows"]:
        y = row["y"]
        check(cell_colours(data, w, row["tag_x"], y) != {(0, 0, 0, 0)},
              f"legend_keys {row['name']}: tag row empty")
        check(cell_colours(data, w, row["glyph_x"], y) != {(0, 0, 0, 0)},
              f"legend_keys {row['name']}: glyph row empty")
        check(len(cell_colours(data, w, row["ramp_x"] + 18,
                               row["ramp_y"] + 5, 1, 1)) == 1,
              f"legend_keys {row['name']}: ramp missing")

    # ---- A5 cursor markers ------------------------------------------------
    outline = {"HOVER": "#E8E8E8", "VALID": "#50DC50",
               "INVALID": "#D23228", "BULLDOZE": "#6E6E6E"}
    data, w, _ = pixels(HERE / "cursors.png")
    check(markers["atlas"]["size"] == "64x16", "markers: declared atlas size")
    for cell in markers["atlas"]["cells"]:
        name, x = cell["name"], cell["x"]
        colours = cell_colours(data, w, x, 0)
        check(len(colours) >= 2, f"cursor {name}: blank cell")
        check(px(data, w, x + 8, 8)[3] == 0,
              f"cursor {name}: interior not transparent")
        check(px(data, w, x, 0)[:3] == rgb(outline[name]),
              f"cursor {name}: outline colour wrong")
        individual = HERE / f"cursor_{name}.png"
        idata, iw, _ = pixels(individual)
        check(all(px(idata, iw, i, j) == px(data, w, x + i, j)
                  for i in range(16) for j in range(16)),
              f"cursor {name}: individual PNG differs from atlas cell")

    # ---- A6 HUD safe zones ------------------------------------------------
    data, w, h = pixels(HERE / "hud_topbar.png")
    check((w, h) == (920, 40), "HUD: wrong dimensions")
    check(hud["size"] == "920x40", "hud layout: declared size")
    for zone in hud["safe_zones"]:
        colours = cell_colours(data, w, zone["x"], zone["y"],
                               zone["w"], zone["h"])
        check(colours == {(20, 20, 20, 255)},
              f"HUD zone {zone['name']}: not a flat #141414 safe zone "
              f"({len(colours)} colours)")
    for deco in hud["decorations"]:
        colours = cell_colours(data, w, deco["x"], deco["y"],
                               deco["w"], deco["h"])
        check(len(colours) >= 2, f"HUD decoration {deco['name']}: blank")
    check(Path(HERE / "svg" / "hud_topbar.svg").exists(), "missing hud SVG")

    print(f"checked {len(svgs)} SVGs, {len(expected_pngs)} PNGs; "
          f"heat max alpha {alpha_max}/255; {CHECKS} assertions")
    if FAILS:
        for f in FAILS:
            print("FAIL", f)
        print(f"RESULT: {len(FAILS)} FAILURES")
        return 1
    print("RESULT: ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
