#!/usr/bin/env python3
"""Build assets/tiles.png and assets/preview.png from assets/svg/.

22 sprites, 16x16 each, in a 7x4 row-major grid (112x64 px). Cell 21 is the
pickleball court; the six remaining cells of the last row are transparent
montage padding (the renderer reads only cells 0..21).
Requires rsvg-convert and ImageMagick (montage, convert, identify).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG_DIR = HERE / "svg"
ATLAS = HERE / "tiles.png"
PREVIEW = HERE / "preview.png"
COLS, ROWS, TILE = 7, 4, 16

# Fixed row-major order. Index = name -> (x, y) = ((i % 7) * 16, (i // 7) * 16).
ORDER = [
    "T_EMPTY", "T_WATER", "T_ROAD", "T_POWERLINE", "T_POWERPLANT", "T_RES", "T_COM",
    "T_IND", "T_PARK", "T_SCHOOL", "T_POLICE", "T_FIRE", "T_RES_L1", "T_RES_L2",
    "T_RES_L3", "T_COM_L1", "T_COM_L2", "T_COM_L3", "T_IND_L1", "T_IND_L2", "T_IND_L3",
    "tile_pickleball",
]
assert len(ORDER) == 22 and len(ORDER) <= COLS * ROWS


def run(*cmd: str) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(cmd)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def main() -> int:
    missing = [n for n in ORDER if not (SVG_DIR / f"{n}.svg").exists()]
    if missing:
        print("missing SVGs:", ", ".join(missing), file=sys.stderr)
        return 1
    if not shutil.which("rsvg-convert") or not shutil.which("montage"):
        print("rsvg-convert and ImageMagick montage are required", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="mp-atlas-") as tmp:
        tmpdir = Path(tmp)
        rasters = []
        for i, name in enumerate(ORDER):
            src = SVG_DIR / f"{name}.svg"
            dst = tmpdir / f"{i:02d}_{name}.png"
            run("rsvg-convert", "-w", str(TILE), "-h", str(TILE),
                str(src), "-o", str(dst))
            dim = run("identify", "-format", "%wx%h", str(dst))
            if dim != "16x16":
                raise RuntimeError(f"{name} rasterised to {dim}, expected 16x16")
            rasters.append(str(dst))

        # Tile the 22 rasters into one 7x4 sheet with zero gaps. The six unused
        # cells of the final row are transparent montage padding.
        run("montage", *rasters, "-tile", f"{COLS}x{ROWS}",
            "-geometry", "16x16+0+0", "-background", "none", str(ATLAS))

    dim = run("identify", "-format", "%wx%h", str(ATLAS))
    expected = f"{COLS * TILE}x{ROWS * TILE}"
    if dim != expected:
        raise RuntimeError(f"atlas is {dim}, expected {expected}")

    # 4x nearest-neighbour upscale for human inspection (crisp pixel edges).
    run("convert", str(ATLAS), "-filter", "point", "-resize", "400%",
        "-strip", str(PREVIEW))
    pdim = run("identify", "-format", "%wx%h", str(PREVIEW))
    if pdim != "448x256":
        raise RuntimeError(f"preview is {pdim}, expected 448x256")

    # Every cell must contain more than one colour (i.e. actually drawn).
    bad = []
    for i, name in enumerate(ORDER):
        x, y = (i % COLS) * TILE, (i // COLS) * TILE
        colours = run("convert", str(ATLAS), "-crop", f"16x16+{x}+{y}",
                      "+repage", "-format", "%k", "info:")
        if int(colours) < 2:
            bad.append(name)
    if bad:
        raise RuntimeError(f"empty atlas cells: {', '.join(bad)}")

    print(f"atlas  {ATLAS.name}: {dim}  ({len(ORDER)} cells, {COLS}x{ROWS})")
    print(f"preview {PREVIEW.name}: {pdim}  (4x nearest-neighbour)")
    print(f"all {len(ORDER)} cells non-empty (>=2 colours each)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
