# Plan — Phase 2: Modular Base Module & Interlocking Joiners

## Task Group 1: Base Chassis Geometry (`parts/part_01_base_module.py`)
1. Create `parts/part_01_base_module.py` referencing single source of truth parameters from `params.py`.
2. Model monolithic 1-piece base chassis box (240 × 240 × 15 mm scaled).
3. Model internal 3.0 mm wall isometric hexagonal web lattice under top bed plate for ~30% PLA filament savings and zero bed warping.
4. Model 20.1 × 2.0 mm bottom corner sockets for press-fitting anti-slip silicone/rubber feet.
5. Model 0.5 mm debossed Poka-Yoke directional alignment arrow ("FRONT ➔") near front dovetail socket.
6. Model 0.4 mm debossed shirt collar & shoulder centering alignment reticles on top surface.
7. Model 1.5 mm recessed silent flip TPU bumper landing slots on top frame rim.
8. Model 1.5 mm filleted internal wire pass-through ports with 3.5 × 1.5 mm zip-tie strain-relief loops.
9. Apply 0.8 mm × 45° chamfers on weight-reduction hole edges and 0.6 mm micro-grip diamond texture on top surface.
10. Apply 0.4 mm × 45° Elephant's Foot relief chamfer along all bottom bed-contacting edges.
11. Model tapered female dovetail joiner sockets with 0.3 mm detent locking dimples on all 4 outer walls.

## Task Group 2: Click-Lock Hollow Dovetail Frame Joiner (`parts/part_10_frame_joiner.py`)
1. Create `parts/part_10_frame_joiner.py` referencing single source of truth parameters from `params.py`.
2. Model tapered male dovetail key matching base chassis female sockets with 0.2 mm press-fit clearance.
3. Model 0.3 mm flex-detent bump for tactile click-lock retention.
4. Model hollow internal wire conduit tunnel running through the center of the joiner.
5. Apply 0.4 mm chamfers to lead-in edges for smooth zero-force insertion.

## Task Group 3: FreeCAD MCP Visual & Interference Validation
1. Execute headless FreeCAD script build to generate STEP and STL outputs in `exports/`.
2. Perform FreeCAD MCP Visual Validation using `render_freecad_script` (Isometric, Front, Top, Right multi-view burst).
3. Perform cross-section topology inspection using `section_freecad_model` (XZ and YZ section cuts).
4. Perform interference verification using `check_interference` between `part_01_base_module` and `part_10_frame_joiner` (`overlap_volume_mm3 <= 0.001`).
