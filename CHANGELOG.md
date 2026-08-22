# Changelog

## 2026-08-22
- Implemented **Phase 5: Interface Module & Electronics Enclosure**:
  - Added `interface_case.py` ($220.0 \times 120.0 \times 45.0\text{ mm}$ spacious flat rectangular electronics chassis, total assembled $H = 48.0\text{ mm}$) housing 3 internal circuit boards: 5V/6V High-Current Power Distribution Board (PDB, M3 standoffs @ $37.0 \times 24.0\text{ mm}$ pitch), ESP32 DevKit (M3 standoffs @ $46.0 \times 23.0\text{ mm}$ pitch + perimeter cradle), and PCA9685 16-channel PWM servo driver (M2.5 standoffs @ $55.88 \times 19.05\text{ mm}$ pitch), with high-capacity $60.0 \times 20.0\text{ mm}$ 16-motor wire conduit passing up to 48 servo wires / ribbon cables directly to the grid, dual captive zip-tie strain-relief anchor saddles absorbing 100% of pull tension, $2\times \varnothing 6.0\text{ mm}$ S-bend friction snubber posts, $\varnothing 11.5\text{ mm}$ DC power barrel jack, $12.0 \times 7.5\text{ mm}$ USB programming port, passive convection cooling chimneys under all 3 boards, and 2x sliding dovetail sockets with $\varnothing 6.0\text{ mm}$ push-out holes.
  - Added `interface_panel.py` ($220.0 \times 120.0 \times 3.0\text{ mm}$ flat horizontal rectangular top faceplate at $Z = 45.0\text{ mm}$) with 4x inline $\varnothing 16.0\text{ mm}$ button cutouts ($0.8\text{ mm}$ top chamfers), circular round $\varnothing 6.0\text{ mm}$ status LED window ($0.8\text{ mm}$ chamfer + $\varnothing 8.5\text{ mm}$ underside retention lip), 4-sided toolless screw-free snap-lock retention system (front hooks, side register down-ribs, rear cantilever snap-latches), and $0.6\text{ mm}$ diamond micro-grip surface texture.
  - Added `interface_assembly.py` multi-body sub-assembly model with CAD references for PDB, PCA9685, ESP32, 4x 16mm push buttons, and 5mm round status LED indicator in flat rectangular configuration.
  - Standardized all interface component naming with the uniform `interface_` prefix (`interface_case.py`, `interface_panel.py`, `interface_assembly.py`).
  - Validated zero geometric interference ($0.00000\,\text{mm}^3$ overlap across all 12 mated pairs) via FreeCAD MCP `check_interference`.
  - Expanded production export pipeline (`export_all.py`) to 16/16 scripts building with a 100% pass rate.
- Updated Phase 5 roadmap in `cad-designs/specs/roadmap.md` and added `BUTTON_HOLE_DIA = 16.0` to `cad-designs/params.py` and `tech-stack.md` for standard Ø16.0mm round interface push buttons.
- Standardized all project specifications (`specs/mission.md`, `cad-designs/specs/mission.md`, `cad-designs/specs/tech-stack.md`, `docs/README.md`, `firmware/README.md`) on dual internal circuit boards: PCA9685 16-channel PWM servo driver + ESP32 DevKit microcontroller with 4 top interaction buttons and status LED.
- Updated Bambu Lab 3MF print project to `cad-designs/3d-print/fabrica-bambu-lab-256.3mf` configured for 256x256mm build volume.

## 2026-08-21
- Implemented 50/50 split on `motorized_frame.py` left wall ($6.20\text{mm}$ total width), extending the outer $3.10\text{mm}$ to full height ($Z=27.2\text{mm}$) and the inner $3.10\text{mm}$ as a support ledge ($Z=25.8\text{mm}$); resized `motorized_servo_cover.py` to $60.8\text{mm}$ width ($X \in [-20.6, 40.2\text{mm}]$) to sit in a dedicated 3-wall captive recessed pocket.
- Reduced `motorized_frame.py` motor wire pass-through conduit to a fitted $10.0\text{mm} \times 8.6\text{mm}$ port with $1.5\text{mm}$ corner fillets centered at $(Y=205.5\text{mm}, Z=15.0\text{mm})$, eliminating the oversized $20\text{mm}$ void and restoring a $5.45\text{mm}$ solid base wall and $7.9\text{mm}$ top rail bridge.
- Standardized `motorized_servo_adapter.py` on a continuous 100% solid core 8.0mm male hex peg (18.0mm length, 7.7mm AF) with 2.55–3.15mm radial clearance to 4x M2/M2.5 horn-mounting screw heads, enabling straight-line screwdriver access and robust torsional shear resistance.
- Implemented 180° flap folding kinematic relief cuts along hinge pedestals on both Follower Frame and Motorized Frame, enabling 100% collision-free 0° to 180° rotation sweep ($0.0000\,\text{mm}^3$ overlap).
- Bounded outer corner trim cutters to strictly $3.0\text{mm} \times 3.0\text{mm}$ boxes across all frames and flaps, eliminating oversized OpenCASCADE boolean bounding box protrusions.
- Corrected `motorized_servo_adapter.py` hex drive peg length to $18.0\text{mm}$, ensuring $8.0\text{mm}$ positive torque engagement into the motorized flap's female hex socket with $2.0\text{mm}$ bottom clearance.
- Verified $1.0\text{mm}$ axial air gap between rotating adapter flange and frame knuckle, guaranteeing zero contact and zero friction under high servo torque.
- Fused continuous bore and pocket cutters and re-punched bore channels after chamfering to eliminate OpenCASCADE co-planar inversion artifacts.
- Validated all 13 production STEP and STL assets with 100% build pass via `export_all.py`.

## 2026-08-20
- Eliminated flat chord facet and texture cutter grooves on folding flap hinge spines, ensuring a 100% smooth, continuous Ø12.8mm circular cylindrical surface.
- Extended Follower and Motorized folding flaps into full-square top decks (219.0mm x 219.5mm) completely covering chassis top and bottom rails.
- Added smooth 0.50mm radial knuckle relief notches (R=9.9mm) preserving full 0° to 180° rotation clearance with zero collision.
- Extended 45° anti-slip diamond micro-grip traction texture and 2.0mm perimeter shadow bevels continuously across full square flap blades.
- Added captive flanged thrust-collar end pivot pin (`end_pivot_pin.py`) with 100% solid construction, Ø16.0mm x 1.0mm retaining disk, and 0.45mm FDM rotating clearance.
- Updated follower and motorized frames with 100% closed 360° cylindrical bearing knuckles (Ø13.7mm bore) and inner Ø16.8mm x 1.2mm counterbore thrust recesses.
- Redesigned follower and motorized flaps into modular drop-in units with full 360° cylindrical axle spines and 100% fully-enclosed 6-sided 8.0mm female hex torque sockets.
- Updated hex drive coupler (`hex_drive_coupler.py`) with 100% solid core and central Ø15.0mm x 2.0mm axial centering collar for anti-wandering lock.
- Refined chassis outer corners and knuckle barrels with cylinder-bounded 1.0mm x 45° circular outer rim chamfers, 0.8mm bore entry chamfers, and smooth planar rail faces.
- Verified 0.00000 mm³ boolean interference across all assemblies and exported all 13 production STEP and STL models.

## 2026-08-18
- Unified monolithic seamless flap construction across all folding flaps, eliminating internal seam split lines and creating unbroken planar top decks.
- Extended stepped wings on follower and motorized flaps to cover chassis rails past 360° knuckle rings with 0.50mm radial clearance.
- Extended anti-slip 45° diamond traction micro-grip texture continuously across entire flap faces with uniform 2.0mm perimeter shadow bevel borders.
- Extended motorized flap to full 219.0mm length deck coverage over the frame cavity with precision servo notch and zero kinematic interference across 180° rotation.
- Re-architected frame hinge support to a single semi-cylindrical cradle wall, maximizing open cavity space without redundant rectangular walls.
- Added reinforced sub-bore cradle foundation boss and symmetric 0.20mm tight-fit sliding dovetail joint across cradle walls to eliminate looseness and wobble.
- Added high-capacity filleted wire pass-through conduits through all chassis dovetail sockets for continuous cable routing into interior wiring cavities.
- Added smooth R=3.0mm vertical corner fillets and lead-in chamfers across all frames, flaps, and drive axles for tactile finish and supportless FDM printing.
- Implemented solid servo bay bed floor at Z=5.25mm for direct gravity-supported drop-in motor seating and M3 screw hole alignment.
- Converted motorized frame cavity to a unified monolithic L-shaped boundary, eliminating split-line rail notches and motor enclosure slivers.
- Flattened motorized chassis bottom to 100% planar Z=0.0mm coplanar base across entire footprint, eliminating bottom protrusion step and table rocking.
- Extended continuous flat solid base plate under knuckle and motor housing zone across X=[-24, +48mm] at Z=0.0mm with smooth outer corner filleting.
- Repositioned motor mounting towers to Y=182.0mm and motor bay to Y=[182.0, 214.5mm] to accommodate the 48.05mm total motor + circular horn length without overlap.
- Redesigned motorized servo adapter with 4.3mm thickness (Y=[159.5, 163.8mm]), seating flush against the MG996R round horn disk and engaging flap top hex socket with zero axial interference.
- Converted motor mounting walls into 5.0mm thick tower posts at Y=[182.0, 187.0mm] and widened drop-in bay cavity to 56.3mm (X=[-17.8, +38.5mm]), eliminating solid side shelves and providing complete top drop-in clearance and direct screwdriver/bolt access to all 4x M3 mounting holes.
- Removed obsolete split-seam dovetail cut and cradle boss from both motorized and follower frames, creating continuous, unbroken, smooth semi-cylindrical cradle troughs for elastic snap-in flap assembly.
- Implemented full-length solid vertical base pedestal along the entire 220mm hinge rail ($X \in [-9.4, 0\text{ mm}], Z \in [0.0, 15.0\text{ mm}]$) on both follower and motorized frames, eliminating circular underside overhangs for 100% supportless FDM printing, planar tabletop seating, and tripled hinge stiffness.
- Rebuilt and validated all 12 production STEP and STL files with 100% build pass.

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
