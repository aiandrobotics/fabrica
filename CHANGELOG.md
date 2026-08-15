# Changelog

## 2026-08-14
- Implemented Phase 3 Passive Follower Module (`part_02_follower_frame.py`, `part_03_follower_flap.py`, `part_11_hex_drive_coupler.py`, `assembly_follower_module.py`) with 0.000 mm³ interference across all components.
- Designed 4-sided open-bottom follower frame with integrated male-female interlocking dovetail joint on the 4th stiffener tie-bar (flush at Z=3.0mm with 0.25mm clearance and zero floating slivers).
- Added 4x bottom anti-slip grip foot sockets (Ø12.0mm x 2.0mm) and top-rail silent-flip TPU bumper landing slots.
- Implemented dual 100% solid 360° closed cylindrical bearing knuckles with C1-continuous concave blend transition ramps.
- Designed full-size 240x240mm rotating follower flap resting on frame rails with continuous full-length Ø13.0mm drive axle, dual 8.0mm female hex torque sockets, and gradient circular weight-reduction cutouts (~45% mass reduction).
- Modeled compact 31.0mm solid double-male hex drive coupler bridging 10.0mm inter-module gaps with cylindrical bearing journal.
- Updated true open-top sliding dovetail sockets with Ø6.0mm through-floor push-out access holes across base and follower chassis.
- Optimized `part_10_frame_joiner.py` for fast headless execution, eliminating boolean meshing bottlenecks during STEP and STL export.
- Redesigned Click-Lock Dovetail Frame Joiner to be 100% 3-axis symmetrical ($X, Y, Z$) for zero-orientation Poka-Yoke assembly.
- Enlarged internal wire raceway in `part_10_frame_joiner.py` to $5.8\text{ mm} \times 7.2\text{ mm}$ with filleted corners to accommodate pre-crimped 3-pin servo connectors and multi-wire harnesses.
- Added 4-corner $45^\circ$ lead-in entry chamfers, $1.2\text{ mm}$ central indexing/pry lip collar, and tactile retention detents for effortless tool-free attachment and removal.

## 2026-08-08
- Created initial project scaffolding for `cad-designs`, `firmware`, `docs`, and `mobile-app` subdirectories.
- Added `specs/mission.md` detailing the project vision, high-level system architecture, four core deliverables, and roadmap.
- Added system reference images and CAD visuals under `specs/reference-images`.
- Refined CAD design specifications for Fabrica Cloth Folding Robot across `mission.md`, `tech-stack.md`, and `roadmap.md`.
- Implemented Phase 1 parametric foundation script (`params.py`), headless build script (`export_all.py`), executable shell entrypoint (`run.sh`), and standard directory layout.
- Optimized modular 4×3 grid architecture, consolidating the central column into a Monolithic Base Chassis Module and selecting Click-Lock Hollow Dovetail Frame Joiners for toolless assembly and hidden cable routing.
- Harmonized universal CAD design standards (Poka-Yoke directional arrows, Elephant's Foot bed relief, micro-grip diamond texture, hole chamfers, filleted wire ports, and click-lock dovetail sockets) across all 10 module part files.
- Added 1.2 mm recessed perimeter shadow bevel (`ACCENT_BEVEL_DEPTH`) for dual-tone panel aesthetics on the Follower Folding Flap.
- Implemented Phase 2 CAD parts (`part_01_base_module.py` and `part_10_frame_joiner.py`) with 3.0mm hex lattice, anti-slip foot sockets, garment reticles, TPU bumper slots, filleted wire ports, click-lock dovetail sockets, and 0.000 mm³ interference validation pass.
- Restructured `cad-designs` folder layout, moving all 10 individual part scripts directly under `cad-designs/` for flatter project architecture.
