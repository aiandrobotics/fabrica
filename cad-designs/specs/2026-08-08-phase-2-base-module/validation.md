# Validation — Phase 2: Modular Base Module & Interlocking Joiners

## Required Checks

### 1. Parametric Smoke Test
- Run `python3 params.py` to confirm single source of truth dimensions load cleanly with 0 errors.

### 2. Headless FreeCAD CAD Export Build
- Execute FreeCAD Python API scripts for `part_01_base_module.py` and `part_09_frame_joiner.py` using `freecadcmd`.
- Verify STEP (`.step`) and binary STL (`.stl`) files generate in `exports/`.
- Verify manifold solid geometry pass across all exported STL files (zero non-manifold edges, zero unclosed shells).

### 3. FreeCAD MCP Visual Validation
- Run `render_freecad_script` across 4 standard views: `Isometric`, `Front`, `Top`, `Right`.
- Run `section_freecad_model` to inspect cross-section cuts (`XZ` and `YZ` planes) to verify internal 3.0mm hex lattice wall thickness and hollow joiner wire conduit clearance.

### 4. Precision Clearance & Interference Check
- Run `check_interference` on `part_01_base_module` and `part_09_frame_joiner` mating pairs.
- **Pass Threshold**: `overlap_volume_mm3 <= 0.001`. Overlap > 0.001 mm³ on sliding joints indicates a clearance design error.

## Manual Review
- Visually inspect rendered images to confirm:
  - Micro-grip diamond texture is clearly visible on top face.
  - Collar and shoulder guide reticles are cleanly debossed.
  - Poka-Yoke "FRONT ➔" arrow is clearly visible.
  - Elephant's Foot relief chamfers are present on all bottom bed-contacting edges.

## Merge Criteria
- 100% pass on all Required Checks.
- STEP and STL export files generated cleanly.
- Visual inspection report PASS.
