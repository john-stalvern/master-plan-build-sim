# Asset requirements manifest (PM consolidated from all 6 profiles, 2026-11-20)

Sources: mp-gui, mp-design, mp-qa, mp-architect (direct replies), mp-sim,
mp-art (kanban comments). Base 21-tile atlas = T7 (in production, excluded).
Style for ALL items: flat first-SimCity look, exact CONTRACT/render.c palette,
1px #141414 outline, integer coords, readable at target size, SVG sources in
assets/svg/, PNG via rsvg-convert. Gradients ONLY in legend ramps.

## MUST-HAVE (batch A — card T9)
| # | Asset | Spec | Requested by |
|---|---|---|---|
| A1 | Tool palette icons ×11 | 16×16 SVG + 176×16 PNG strip, order = render.c pal_tool[] (bulldoze, road, res, com, ind, park, school, police, fire, plant, line); glyph contrasts on each tool's contract swatch | gui, design, qa, architect, art |
| A2 | Scorecard metric icons ×5 | 16×16 SVG + 80×16 strip: walkability(footprints), green(leaf), amenities(school+shop), yield(bar chart), livability(heart); monochrome #E8E8E8 line art + one contract accent each | all |
| A3 | Overlay legend keys ×4 | per mode: 180×10 ramp bar (5 steps) + 16×16 glyph + F-key tag; ramps MUST match render.c overlay_scale(): landValue #962828→#3CDC5A, pollution #32AA46→#DC3228, crime #32AA46→#DC3C32, power OFF #503728 / ON #468CFF | gui, design, qa, architect, sim |
| A4 | Overlay heat cells | 4 ramps × 5 steps = 20 alpha cells 16×16 (alpha ≤60%), same hexes as A3; PNG atlas 80×64 + SVG sources | architect |
| A5 | Cursor/placement markers ×4 | 16×16 SVG+PNG: hover outline #E8E8E8, valid #50DC50, invalid #D23228, bulldoze #6E6E6E; transparent fill | gui, design, qa, architect |
| A6 | Top-bar HUD strip | 920×40 SVG: MASTER PLANNER lockup + text-safe zones for day/pop counters + pause glyph slot; flat palette on #141414 | architect, gui |

## NICE-TO-HAVE (batch B — card T10)
| # | Asset | Spec | Requested by |
|---|---|---|---|
| B1 | Powered/unpowered badge ×2 | 8×8 bolt #DCC828 / dim #6E6E6E | sim, art |
| B2 | Development-level pips ×3 | 7×7 pale #F0F0D2 on #141414 outline | sim, art |
| B3 | HUD status icons ×4 | 16×16: day/sun, population, jobs, pause/play; neutral + contract accents | design, qa, gui |
| B4 | Pattern-stamp thumbnails ×5 | 96×96 SVG+PNG mini-grids from docs/patterns.md census, atlas colours only | gui, design, architect, art |
| B5 | App/window icon | SVG master + 32×32 & 64×64 PNG; orange plant glyph on dark green | architect |
| B6 | Architecture + tick-order diagram | one SVG ~1000×600: modules world/sim/render/main + tick pipeline power→pollution→crime→landValue→growth→scorecard | architect, sim |
| B7 | README hero banner | 1280×400 SVG + PNG: stylised 40×40 plan slice + sidebar mock, contract palette only | gui, design, architect |
| B8 | Keycap badge sheet | 12×12 badges: 1-9,0,-,F1-F4,ESC,SPACE,S,L,Q | gui, design |

## NOT art-profile work (PM assigned elsewhere)
- Golden smoke-plan + overlay screenshots (qa, sim requests): captured by
  mp-qa AFTER integration from the running app — added to T5 QA scope.
- Stamp ghost-preview valid/blocked markers: covered by A5.

## Delivery rules
- Every batch: assets/README.md updated with exact atlas layouts (name→x,y),
  all PNGs regenerated deterministically from SVG via rsvg-convert.
- Integration cards are created by PM when each art card completes.

## Delivery status (mp-art, 2026-11-20)

- A1-A6: **DELIVERED** (card t_b077b1b9, merged to main). See
  `assets/README.md` for every atlas layout and `assets/layout_*.json` for
  machine-readable cell coordinates. Files: `assets/tools.png`, `metrics.png`,
  `legend_landvalue.png`, `legend_pollution.png`, `legend_power.png`,
  `legend_crime.png`, `legend_glyphs.png`, `legend_tags.png`,
  `legend_keys.png`, `heat.png`, `cursors.png`, the four `cursor_*.png`
  singles, `hud_topbar.png`, their 53 SVG sources and four `build_*.py`
  builders. `assets/verify_ui.py` ran 387 pixel/layout assertions, all pass.
- A4 note: all heat-cell pixels use alpha 153 (60%); rsvg's premultiplied
  alpha can shift an occasional rasterised channel by 1 LSB, while the SVG
  source hexes are exact.
- B1-B8: **DELIVERED** (card t_7a59442e, merged to main). SVGs in
  `assets/svg/`, eight generated PNGs in `assets/`, layouts in
  `assets/README.md`, deterministic rebuild + check in
  `assets/build_batch_b.py`. B1 power badges 16x8; B2 pips 21x7; B3 HUD icons
  64x16; B4 pattern thumbnails 480x96 (5x96x96); B5 app icon 32+64; B6 diagram
  1000x600 SVG; B7 hero 1280x400 SVG+PNG; B8 keycaps 240x12 (20x12x12).
- Base `tiles.png` (21 cells) untouched by batch B; the 22nd (pickleball) tile
  belongs to follow-up card t_2fe9672c, not to this card.
- Batch B verification: `python3 assets/build_batch_b.py --check` passes
  (37 SVGs, 5/5 stamp censuses, 13/13 diagram labels, 8/8 PNGs byte-identical
  to a fresh SVG rebuild).
