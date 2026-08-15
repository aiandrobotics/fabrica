# Roadmap — CAD Designs

Each phase is a small, independently buildable and testable unit of work matching the reference architecture images (`specs/reference-images/`).
Build, validate, and commit before moving to the next phase.

---

## Phase 0 — Project Constitution & CAD Specs ✅
- Create `specs/mission.md`, `specs/tech-stack.md`, and `specs/roadmap.md` tailored for Fabrica Cloth Folding Robot.
- Establish default **256 × 256 × 256 mm** build plate target with support for scaling down to **180 × 180 × 180 mm** via the `SCALE` parameter in `params.py`.
- Incorporate FreeCAD MCP server tools (`render_freecad_script`, `inspect_freecad_assembly`, `section_freecad_model`, `check_interference`) and `freecad-visual-validation` skill rules into project specs.
- Review reference images (`base-module.png`, `follower-module.png`, `motorized-module.png`, `interface-module.png`, `3d-overview.png`, `sub-part-breakdown.png`) and lock component sub-part breakdowns.

---

## Phase 1 — Parametric Foundations (`params.py` & Directory Skeleton) ✅
- Apply `freecad-project` skill conventions for project structure, `params.py` template, `run.sh` entrypoint, and automated export pipeline.
- Create `params.py` with `SCALE = 1.0` as the first line, defining single source of truth dimensions (default 256mm build plate `BUILD_PLATE_X/Y/Z = 256.0 * SCALE`), `SCALE_180 = 180.0 / 256.0`, FDM clearances (`FIT_CLEARANCE`, `PRESS_FIT_CLEARANCE`), wall thicknesses, servo mounting parameters, `TEXTURE_HEIGHT = 0.6 mm`, `HOLE_CHAMFER = 0.8 mm`, `ELEPHANTS_FOOT_CHAMFER = 0.4 mm`, `CONTROL_DECK_ANGLE = 15.0°`, `ACCENT_BEVEL_DEPTH = 1.2 mm`, `TPU_BUMPER_DEPTH = 1.5 mm`, `RETICLE_DEBOSS_DEPTH = 0.4 mm`, `DC_JACK_DIAMETER = 11.5 mm`, `FOOT_PAD_DIA = 20.1 mm`, `FOOT_PAD_DEPTH = 2.0 mm`, `JOINER_DETENT = 0.3 mm`, `WIRE_PORT_FILLET = 1.5 mm`, `PROJECT_DIR`, and `EXPORT_DIR`.
- Setup directory layout adhering to `freecad-project` structure: `parts/`, `assemblies/`, `exports/`, `3d-print/`, `media/`, `run.sh` (executable via `chmod +x run.sh`), `export_all.py`, and `.gitignore`.
- Smoke test: `python params.py` executes cleanly without error and prints key parametric dimensions.

---

## Phase 2 — Modular Base Module & Interlocking Joiners (`part_01_base_module.py`, `part_09_frame_joiner.py`) ✅
- **Monolithic Base Chassis Module** (`part_01_base_module.py`): Model 1-piece rigid stationary base chassis fusing top plate and outer frame box, featuring an internal 3.0 mm wall isometric hexagonal web lattice (~30% PLA filament saving & zero 240mm bed warping), 20.1×2.0 mm bottom corner sockets for press-fitting anti-slip silicone/rubber feet (recoil & slide prevention), 0.5 mm debossed Poka-Yoke directional alignment arrows ("FRONT ➔"), 0.4 mm debossed garment shirt collar & shoulder centering alignment reticles, 1.5 mm recessed silent flip TPU bumper landing slots, 1.5 mm filleted internal wire pass-through ports with zip-tie strain-relief loops, 0.8 mm hole edge chamfers, 0.6 mm top micro-grip diamond texture, 0.4 mm bottom Elephant's Foot relief chamfers, and click-lock dovetail joiner sockets with detent dimples.
- **Click-Lock Hollow Dovetail Frame Joiner** (`part_09_frame_joiner.py`): Model tapered dovetail interlocking joiner peg featuring a 0.3 mm flex-detent bump for tactile click-lock retention and an internal hollow wire conduit tunnel, locking adjacent frames mechanically without screws while serving as a hidden internal wire raceway across grid rows.
- **Visual Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` (multi-view burst) and `section_freecad_model` (print orientation & wall thickness check). Confirm PASS report.

---

## Phase 3 — Passive Follower Module (`part_02_follower_frame.py`, `part_03_follower_flap.py`, `assembly_follower_module.py`, `part_10_hex_drive_coupler.py`) ✅
- **Follower Outer Frame** (`part_02_follower_frame.py`): Model rigid 4-sided follower module chassis (green) featuring dual 100% solid 360° closed cylindrical bearing bores ($\varnothing 13.5\text{ mm}$), C1-continuous concave blend ramps ($R_f = 12.0\text{ mm}$), an open-bottom interior saving ~120g PLA, an integrated 4th stiffener tie-bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$) with clean solid continuous through-dovetail joint at $Y=120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $0.25\text{ mm}$ clearance) with $3.0\text{ mm}$ solid continuous outer walls on both sides, 4x bottom anti-slip rubber foot sockets ($\varnothing 12.0 \times 2.0\text{ mm}$), 3x top rail silent-flip TPU bumper slots ($1.5\text{ mm}$), 0.4mm bottom Elephant's Foot relief chamfers, and true open-top sliding dovetail joiner sockets with $\varnothing 6.0\text{ mm}$ true through-floor push-out access holes.
- **Follower Folding Flap** (`part_03_follower_flap.py`): Model rotating full-size follower flap panel (orange) resting on frame rails ($Z=15.0$ to $17.4\text{ mm}$) with integrated continuous full-length $\varnothing 13.0\text{ mm}$ solid drive axle ($Y=0$ to $240\text{ mm}$, centered at $X=0, Z=8.0\text{ mm}$) rotating directly in closed knuckles, dual $8.0\text{ mm}$ female hex torque sockets ($12.0\text{ mm}$ deep), $0.6\text{ mm}$ micro-grip diamond surface texture, $0.8\text{ mm}$ hole edge chamfers, $1.2\text{ mm}$ recessed perimeter shadow bevel, and gradient circular weight-reduction cutouts (~45% mass reduction).
- **Hex Drive Coupler Pin** (`part_10_hex_drive_coupler.py`): Model modular double-male $8.0\text{ mm}$ hex torque coupler with central locating stop collar and self-aligning chamfers.
- **Follower Sub-Assembly** (`assembly_follower_module.py`): Assemble Follower Frame + Follower Flap + Part 09 Frame Joiners + Part 10 Compact Hex Drive Coupler. Toolless assembly with 0.000 mm³ interference.
- **Visual & Kinematic Validation**: FreeCAD MCP multi-view verification and interference check confirming PASS across all components.

---

## Phase 4 — Active Motorized Module (`part_04_motorized_frame.py`, `part_05_active_flap.py`, `part_06_servo_cover.py`, `assembly_motorized_module.py`)
- **Motorized Outer Frame** (`part_04_motorized_frame.py`): Model rigid 4-sided motorized module chassis (yellow) sharing the standardized Follower chassis architecture:
  - $240 \times 240 \times 15\text{ mm}$ outer envelope with $15.0\text{ mm}$ rigid outer perimeter rails, open-bottom interior saving ~120g PLA, and integrated 4th stiffener tie-bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$) with clean solid continuous through-dovetail joint at $Y=120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $3.0\text{ mm}$ solid outer walls) for $100\%$ flush rotation clearance.
  - Dual 100% solid 360° closed cylindrical bearing knuckles centered at $Z = 8.0\text{ mm}$ with $1.5\text{ mm}$ ground clearance and C1-continuous concave blend ramps ($R_f = 12.0\text{ mm}$).
  - Integrated reinforced MG996R / standard metal-gear servo mounting bay with mounting screw bosses, $1.5\text{ mm}$ filleted wire pass-through conduit, and snap-cover interface.
  - 4x bottom anti-slip rubber foot sockets ($\varnothing 12.0 \times 2.0\text{ mm}$), 3x top rail silent-flip TPU bumper slots ($1.5\text{ mm}$), 0.4mm bottom Elephant's Foot relief chamfers, and true open-top sliding dovetail joiner sockets with $\varnothing 6.0\text{ mm}$ push-out access holes.
- **Monolithic Active Folding Flap** (`part_05_active_flap.py`): Model 1-piece active folding flap panel (red) with integrated continuous solid-core $\varnothing 13.0\text{ mm}$ drive axle (zero rotational play):
  - Resting on frame rails ($Z = 15.0$ to $17.4\text{ mm}$) with corner clearance cutout for the servo housing.
  - **Driven End ($Y = 240\text{ mm}$)**: Integrated press-fit 25T metal servo horn socket for direct 1-piece drive without separate couplers.
  - **Output End ($Y = 0\text{ mm}$)**: Standardized $8.0\text{ mm}$ female hex torque socket to transmit synchronous rotational torque downward to the Follower Module column via Part 10.
  - $0.6\text{ mm}$ micro-grip diamond surface texture, $0.8\text{ mm}$ hole edge chamfers, $1.2\text{ mm}$ recessed perimeter shadow bevel, and gradient circular weight-reduction cutouts (~45% mass reduction, reducing blade weight to ~75g and minimizing rotational inertia on the servo).
- **Toolless Snap-Latch Servo Cover** (`part_06_servo_cover.py`): Model protective housing cover (black) with a toolless snap-latch mechanism and wire strain relief routing for 5-second motor swap outs.
- **Motorized Sub-Assembly** (`assembly_motorized_module.py`): Assemble Motorized Frame + Snap Cover + Monolithic Active Flap + Part 09 Frame Joiners + Part 10 Hex Coupler.
- **Visual & Kinematic Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` (detail close-ups of integrated servo horn socket & motor bay) and `check_interference` confirming `0.00000 mm³` overlap across all driven interfaces.

---

## Phase 5 — Interface Module & Electronics Enclosure (`part_07_interface_panel.py`, `part_08_controller_case.py`, `assembly_interface_module.py`)
- **15° Angled Interface Control Faceplate** (`part_07_interface_panel.py`): Model ergonomic 15° forward-angled control deck top faceplate (yellow) housing 4 tactile button cutouts, a status LED bar diffuser window, 0.8 mm hole edge chamfers, and 0.6 mm micro-grip diamond surface texture.
- **Ventilated Controller Case** (`part_08_controller_case.py`): Model protective electronics enclosure (green) featuring an 11.5 mm DC power barrel jack / USB-C PD mounting cutout, zip-tie wire strain-relief saddles, 0.4 mm bottom Elephant's Foot relief chamfers, 0.5 mm debossed Poka-Yoke directional alignment arrows ("FRONT ➔"), click-lock dovetail joiner sockets with detent dimples, 1.5 mm filleted internal wire pass-through ports, and passive convection cooling chimney slots underneath the Raspberry Pi Pico 2W and PCA9685 driver board to prevent thermal throttling.
- **Interface Sub-Assembly** (`assembly_interface_module.py`): Assemble Controller Case + 15° Angled Interface Faceplate.
- **Visual Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` and `inspect_freecad_assembly` (exploded view with dimensions). Confirm PASS report.

---

## Phase 6 — Full 4×3 Garment Folding Grid Assembly (`assemblies/assembly_4x3_grid.py`)
- Build full 4×3 grid assembly model bringing together 2 Base Modules, 4 Follower Modules, 6 Motorized Modules, and 1 Interface Control Pad Module connected by Click-Lock Hollow Dovetail Wire-Channel Joiners.
- Validate kinematic panel flip positions (0° flat rest, 90° vertical fold, 180° flipped fold).
- Export full `assembly_4x3_grid.step` and `assembly_4x3_grid.stl`.
