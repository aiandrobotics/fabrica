# Plan — Phase 2: Modular Base Module & Interlocking Joiners

## Task Group 1: Base Chassis Geometry (`base_module.py`)
1. Create `base_module.py` referencing single source of truth parameters from `params.py`.
2. Model monolithic 1-piece 4-wall base chassis box (240 × 240 × 15 mm scaled) with 15.0 mm outer perimeter rails.
3. Model open-bottom interior underside cavity (Z = 0 to 12.6 mm) saving ~150g PLA and eliminating warping.
4. Model Ø12.0 × 2.0 mm bottom corner sockets for press-fitting anti-slip silicone/rubber feet.
5. Model 1.5 mm filleted internal wire pass-through ports into the open central cavity.
6. Apply 0.8 mm × 45° chamfers on circular weight-reduction cutouts and 0.6 mm micro-grip diamond texture on top deck.
7. Apply 0.4 mm × 45° Elephant's Foot relief chamfer along all bottom bed-contacting edges.
8. Model open-top female sliding dovetail joiner sockets with 3.0 mm bottom stops and Ø6.0 mm push-out access holes on all 4 outer walls.

## Task Group 2: Click-Lock Hollow Dovetail Frame Joiner (`frame_joiner.py`)
1. Create `frame_joiner.py` referencing single source of truth parameters from `params.py`.
2. Model tapered male dovetail key matching base chassis female sockets with 0.2 mm press-fit clearance.
3. Model 0.3 mm flex-detent bump for tactile click-lock retention.
4. Model hollow internal wire conduit tunnel running through the center of the joiner.
5. Apply 0.4 mm chamfers to lead-in edges for smooth zero-force insertion.

## Task Group 3: FreeCAD MCP Visual & Interference Validation
1. Execute headless FreeCAD script build to generate STEP and STL outputs in `exports/`.
2. Perform FreeCAD MCP Visual Validation using `render_freecad_script` (Isometric, Front, Top, Right multi-view burst).
3. Perform cross-section topology inspection using `section_freecad_model` (XZ and YZ section cuts).
4. Perform interference verification using `check_interference` between `base_module` and `frame_joiner` (`overlap_volume_mm3 <= 0.001`).
