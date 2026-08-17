# Changelog

## 2026-08-17
- Standardized True Square 220.0mm x 220.0mm modular panel architecture across all modules with symmetrical 230.0mm inter-module pitch and 10.0mm seam gaps.
- Decoupled all physical hardware features (MG996R servo motor bay, M3 fastener bosses, snap-fit lids, 8.0mm hex torque couplers, sliding dovetails, silicone foot sockets, and FDM clearances) from build plate scaling parameters, locking them to unscaled 1:1 physical constants.
- Standardized canonical top-level 6-module universal garment folding robot assembly as `cad-designs/assembly.py`, exporting `assembly.step` and `assembly.stl`.
- Updated `cad-designs/export_all.py` to automatically batch build and export all 3 assemblies and 9 individual printable parts (26 STEP & STL production files) in a single pass.
- Completed comprehensive FreeCAD visual, manifold solid, and 3D Boolean interference validation with 0.00000 mm³ overlap across all mating component interfaces.
- Marked Phase 4 (Active Motorized Module) as completed and production certified for 3D printing.

## 2026-08-15
- Re-architected Active Motorized Module (`cad-designs/motorized_frame.py`, `motorized_flap.py`, `motorized_servo_cover.py`, `motorized_assembly.py`) with a **horizontal inline direct-drive servo mount**, eliminating the $+22\text{ mm}$ top motor bump and creating a **100% flush, coplanar top deck ($Z = 15.0\text{..}17.5\text{ mm}$)** across the entire module with $0.00000\text{ mm}^3$ interference across all 9 mating pairs.
- Updated Active Flap (`motorized_flap.py`) to a full rectangular blade with integrated continuous $\varnothing 13.0\text{ mm}$ drive axle, 25T metal horn socket, bottom $8.0\text{ mm}$ hex torque socket, and gradient mass-reduction cutouts.
- Designed flush low-profile slide-in servo lid (`motorized_servo_cover.py`) with side retention tongues and passive cooling gills.
- Updated Base Module chassis (`cad-designs/base_module.py`) to the clean 4-wall open-bottom frame architecture, removing debossed directional reticles/lines and top TPU bumper slots for a completely flat and uniform top deck, while retaining circular mass-reduction cutouts, diamond knurling, sliding dovetails, and anti-slip feet.
- Synchronized all CAD specs in `cad-designs/specs/` (`requirements.md`, `plan.md`, `roadmap.md`, `tech-stack.md`) to match the latest 4-wall open-bottom chassis architecture and standardized `motorized_` / `follower_` naming conventions.
- Standardized CAD naming conventions with `motorized_` and `follower_` prefixes (`motorized_frame.py`, `motorized_flap.py`, `motorized_servo_cover.py`, `motorized_assembly.py`, `follower_frame.py`, `follower_flap.py`, `follower_assembly.py`).
- Implemented Phase 4 Active Motorized Module (`cad-designs/motorized_frame.py`, `cad-designs/active_flap.py`, `cad-designs/servo_cover.py`, `cad-designs/assembly_motorized_module.py`) with 0.00000 mm³ interference across all mating pairs.
- Designed 4-sided active motorized chassis frame (`motorized_frame.py`) with dual Ø13.5mm closed bearing knuckles, integrated MG996R servo mounting bay with M3 screw bosses, cable routing conduit, and snap-latch cover sockets.
- Modeled monolithic active folding flap (`active_flap.py`) with continuous Ø13.0mm solid-core drive axle, integrated 25T metal servo horn socket with M3 central retention screw counterbore, bottom 8.0mm female hex torque socket, and corner servo clearance notch.
- Modeled toolless snap-latch protective servo cover (`servo_cover.py`) featuring dual cantilever snap tabs with 0.4mm detents, wire exit notch, and top convection cooling ventilation gills.
- Created complete motorized module sub-assembly script (`assembly_motorized_module.py`) with MG996R servo CAD reference, frame joiners, and hex coupler pin.
- Verified visual bursts, exploded inspection, XZ section cuts, and boolean interference (`0.00000 mm³` overlap) via FreeCAD MCP tools.
- Updated `export_all.py` batch build pipeline to automatically build and export all 10 CAD parts and assemblies to `cad-designs/exports/`.

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
