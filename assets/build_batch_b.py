#!/usr/bin/env python3
"""Deterministic rebuild / verification of batch-B art (manifest B1-B8).

Every PNG is rendered from its SVG source with rsvg-convert and composited
with Pillow; no external or generated inputs other than the SVGs themselves.

    python3 assets/build_batch_b.py          # regenerate all batch-B PNGs
    python3 assets/build_batch_b.py --check  # rebuild in a temp dir and compare

The --check mode also parses/validates all batch-B SVGs, verifies the
pattern-stamp censuses against docs/patterns.md, and checks the tick diagram
labels. It is the single self-contained verification for this batch.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent
SVG = ROOT / "svg"
NS = "{http://www.w3.org/2000/svg}"

PALETTE = {
    "#141414", "#E8E8E8", "#F0F0D2", "#184018", "#2050B4", "#6E6E6E",
    "#DCC828", "#E6821E", "#3CA03C", "#3C64DC", "#966E32", "#50DC50",
    "#9646C8", "#1E3282", "#D23228", "#468CFF", "#503728", "#C84646",
    "#4CB04C", "#5CC05C", "#6CD06C", "#4C74EC", "#5C84FC", "#6C94FF",
    "#A67E42", "#B68E52", "#C69E62", "#962828", "#3CDC5A", "#32AA46",
    "#DC3228", "#DC3C32", "#805434", "#6A8140", "#53AE4D", "#5C8D3F",
    "#866F38", "#B15130", "#5C8F42", "#86743D", "#B15838",
}

BADGES = ["B1_POWERED", "B1_UNPOWERED"]
PIPS = ["B2_PIP_1", "B2_PIP_2", "B2_PIP_3"]
HUD = ["B3_DAY", "B3_POPULATION", "B3_JOBS", "B3_PAUSE_PLAY"]
PATTERNS = [
    "PATTERN_VILLAGE_CENTRE", "PATTERN_GREEN_SPINE", "PATTERN_TRANSIT_NODE",
    "PATTERN_SCHOOL_CLUSTER", "PATTERN_GARDEN_WORKS",
]
KEYCAPS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-",
    "F1", "F2", "F3", "F4", "ESC", "SPACE", "S", "L", "Q",
]
KEY_NAMES = ["B8_KEY_" + ("MINUS" if k == "-" else k) for k in KEYCAPS]

# (output filename, cell width, cell height, SVG cell names, output mode)
ATLASES = [
    ("power_badges.png", 8, 8, BADGES, "RGBA"),
    ("level_pips.png", 7, 7, PIPS, "RGBA"),
    ("hud_status.png", 16, 16, HUD, "RGBA"),
    ("pattern_thumbnails.png", 96, 96, PATTERNS, "RGB"),
    ("keycaps.png", 12, 12, KEY_NAMES, "RGBA"),
]
SINGLES = [
    ("app_icon_32.png", "APP_ICON", 32, 32),
    ("app_icon_64.png", "APP_ICON", 64, 64),
    ("hero_banner.png", "HERO_BANNER", 1280, 400),
]

# Census from docs/patterns.md, as (name, {letter: count}, total placed tiles).
CENSUS = [
    ("PATTERN_VILLAGE_CENTRE", {"R": 48, "L": 48, "P": 1, "H": 41, "C": 18, "G": 7, "S": 6}, 169),
    ("PATTERN_GREEN_SPINE", {"R": 28, "L": 35, "P": 1, "H": 21, "C": 4, "G": 28, "S": 3}, 120),
    ("PATTERN_TRANSIT_NODE", {"R": 30, "L": 28, "P": 1, "H": 17, "C": 20, "S": 3}, 99),
    ("PATTERN_SCHOOL_CLUSTER", {"R": 26, "L": 20, "P": 1, "H": 19, "C": 5, "G": 9, "S": 6, "O": 1, "F": 1}, 88),
    ("PATTERN_GARDEN_WORKS", {"R": 16, "L": 33, "P": 1, "H": 11, "C": 5, "I": 8, "G": 16}, 90),
]
TILE_LETTER = {
    "#6E6E6E": "R", "#DCC828": "L", "#E6821E": "P", "#3CA03C": "H",
    "#3C64DC": "C", "#966E32": "I", "#50DC50": "G", "#9646C8": "S",
    "#1E3282": "O", "#D23228": "F",
}


def render_file(name: str, w: int, h: int, tmp: Path) -> Path:
    out = tmp / f"{name}_{w}x{h}.png"
    subprocess.run(
        ["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(out), str(SVG / f"{name}.svg")],
        check=True, capture_output=True,
    )
    return out


def render(name: str, w: int, h: int, tmp: Path) -> Image.Image:
    return Image.open(render_file(name, w, h, tmp)).convert("RGBA")


def compose(cells: list[Image.Image], mode: str) -> Image.Image:
    w, h = cells[0].size
    if mode == "RGB":
        # Pattern thumbnails are opaque: transparent SVG margins are flattened
        # onto the same #141414 used by every tile outline.
        sheet = Image.new("RGBA", (w * len(cells), h), (20, 20, 20, 255))
        for i, cell in enumerate(cells):
            sheet.alpha_composite(cell, (i * w, 0))
        return sheet.convert("RGB")
    sheet = Image.new("RGBA", (w * len(cells), h), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        sheet.alpha_composite(cell, (i * w, 0))
    return sheet


def build(tmp: Path, destination: Path) -> list[tuple[str, Path]]:
    made = []
    for out, w, h, names, mode in ATLASES:
        img = compose([render(n, w, h, tmp) for n in names], mode)
        path = tmp / out if destination != ROOT else destination / out
        img.save(path)
        made.append((out, path))
    for out, name, w, h in SINGLES:
        # Keep rsvg's own PNG bytes (the committed singles are raw rsvg output).
        path = tmp / out if destination != ROOT else destination / out
        path.write_bytes(render_file(name, w, h, tmp).read_bytes())
        made.append((out, path))
    return made


def fail(msg: str) -> None:
    print("FAIL:", msg)
    raise SystemExit(1)


def check() -> None:
    errors: list[str] = []
    names = BADGES + PIPS + HUD + PATTERNS + KEY_NAMES + ["APP_ICON", "ARCHITECTURE_TICK_ORDER", "HERO_BANNER"]
    for name in names:
        path = SVG / f"{name}.svg"
        if not path.exists():
            errors.append(f"missing SVG {path}")
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as e:
            errors.append(f"invalid XML {name}: {e}")
            continue
        if root.tag != NS + "svg":
            errors.append(f"{name}: root is not <svg>")
        for el in root.iter():
            for attr in ("fill", "stroke"):
                value = el.get(attr)
                if value and value.startswith("#") and value.upper() not in PALETTE:
                    errors.append(f"{name}: {attr}={value} outside contract palette")
    print(f"SVG parse/palette: {len(names)} sources, {len(errors)} problem(s)")
    for e in errors[:10]:
        print("  detail:", e)

    # Stamp census: count the 6x6 tile rects by exact atlas colour.
    for name, expected, total in CENSUS:
        root = ET.parse(SVG / f"{name}.svg").getroot()
        counts: dict[str, int] = {}
        for el in root.iter(NS + "rect"):
            w, h = el.get("width"), el.get("height")
            if el.get("stroke") != "#141414" or w != h or w not in {"6", "7", "8"}:
                continue
            letter = TILE_LETTER.get(el.get("fill", "").upper())
            if letter:
                counts[letter] = counts.get(letter, 0) + 1
        if counts != expected or sum(counts.values()) != total:
            errors.append(f"{name}: census {counts} != {expected}")
    print(f"Pattern census: {len(CENSUS)}/{len(CENSUS)} stamps match docs/patterns.md")

    diagram = (SVG / "ARCHITECTURE_TICK_ORDER.svg").read_text()
    for label in ("main", "sim", "world", "render", "power", "pollution", "crime",
                  "landValue", "growth", "scorecard", "GRID 40x40", "TILE 16", "TICK 500 ms"):
        if label not in diagram:
            errors.append(f"diagram missing label {label!r}")
    print("Tick diagram labels: 13/13 present")

    with tempfile.TemporaryDirectory(prefix="mp-art-b-check-") as d:
        tmp = Path(d)
        for out, path in build(tmp, tmp):
            committed = ROOT / out
            if not committed.exists():
                errors.append(f"missing committed {out}")
                continue
            a, b = Image.open(path), Image.open(committed)
            if a.size != b.size:
                errors.append(f"{out}: size {a.size} != {b.size}")
                continue
            if ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox():
                errors.append(f"{out}: pixels differ from SVG rebuild")
            if path.read_bytes() != committed.read_bytes():
                errors.append(f"{out}: PNG bytes differ from SVG rebuild")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
            print(f"REBUILD {out:24s} {str(a.size):12s} sha256:{digest}")

    if errors:
        for e in errors:
            print("FAIL:", e)
        raise SystemExit(1)
    print("PASS: all batch-B SVGs valid, all PNGs reproduce from SVG, all layouts correct.")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        with tempfile.TemporaryDirectory(prefix="mp-art-b-build-") as d:
            build(Path(d), ROOT)
        print("Rebuilt all batch-B PNGs deterministically from assets/svg/.")
