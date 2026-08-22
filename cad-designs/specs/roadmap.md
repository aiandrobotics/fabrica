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

## Phase 2 — Modular Base Module & Interlocking Joiners (`base_module.py`, `frame_joiner.py`) ✅
- **Monolithic Base Chassis Module** (`base_module.py`): Model 1-piece rigid stationary base chassis using the standardized 4-wall open-bottom frame architecture ($240 \times 240 \times 15\text{ mm}$) with $15.0\text{ mm}$ perimeter rails, open-bottom underside cavity saving ~150g PLA and eliminating warping, 4x bottom corner sockets ($\varnothing 12.0 \times 2.0\text{ mm}$) for anti-slip silicone/rubber feet, 1.5 mm filleted internal wire pass-through ports, 0.8 mm hole edge chamfers on circular mass-reduction cutouts, 0.6 mm top micro-grip diamond texture, 0.4 mm bottom Elephant's Foot relief chamfers, and true open-top sliding dovetail joiner sockets with $\varnothing 6.0\text{ mm}$ push-out access holes.
- **Click-Lock Hollow Dovetail Frame Joiner** (`frame_joiner.py`): Model tapered dovetail interlocking joiner peg featuring a 0.3 mm flex-detent bump for tactile click-lock retention and an internal hollow wire conduit tunnel, locking adjacent frames mechanically without screws while serving as a hidden internal wire raceway across grid rows.
- **Visual Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` (multi-view burst) and `section_freecad_model` (print orientation & wall thickness check). Confirm PASS report.

---

## Phase 3 — Passive Follower Module (`follower_frame.py`, `follower_flap.py`, `follower_assembly.py`, `hex_drive_coupler.py`) ✅
- **Follower Outer Frame** (`follower_frame.py`): Model rigid 4-sided follower module chassis (green) featuring dual 100% solid 360° closed cylindrical bearing bores ($\varnothing 13.5\text{ mm}$), C1-continuous concave blend ramps ($R_f = 12.0\text{ mm}$), an open-bottom interior saving ~120g PLA, an integrated 4th stiffener tie-bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$) with clean solid continuous through-dovetail joint at $Y=120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $0.25\text{ mm}$ clearance) with $3.0\text{ mm}$ solid continuous outer walls on both sides, 4x bottom anti-slip rubber foot sockets ($\varnothing 12.0 \times 2.0\text{ mm}$), 3x top rail silent-flip TPU bumper slots ($1.5\text{ mm}$), 0.4mm bottom Elephant's Foot relief chamfers, and true open-top sliding dovetail joiner sockets with $\varnothing 6.0\text{ mm}$ true through-floor push-out access holes.
- **Follower Folding Flap** (`follower_flap.py`): Model rotating full-size follower flap panel (orange) resting on frame rails ($Z=15.0$ to $17.4\text{ mm}$) with integrated continuous full-length $\varnothing 13.0\text{ mm}$ solid drive axle ($Y=0$ to $240\text{ mm}$, centered at $X=0, Z=8.0\text{ mm}$) rotating directly in closed knuckles, dual $8.0\text{ mm}$ female hex torque sockets ($12.0\text{ mm}$ deep), $0.6\text{ mm}$ micro-grip diamond surface texture, $0.8\text{ mm}$ hole edge chamfers, $1.2\text{ mm}$ recessed perimeter shadow bevel, and gradient circular weight-reduction cutouts (~45% mass reduction).
- **Hex Drive Coupler Pin** (`hex_drive_coupler.py`): Model modular double-male $8.0\text{ mm}$ hex torque coupler with central locating stop collar and self-aligning chamfers.
- **Follower Sub-Assembly** (`follower_assembly.py`): Assemble Follower Frame + Follower Flap + Frame Joiners + Compact Hex Drive Coupler. Toolless assembly with 0.000 mm³ interference.
- **Visual & Kinematic Validation**: FreeCAD MCP multi-view verification and interference check confirming PASS report.

---

## Phase 4 — Active Motorized Module (`motorized_frame.py`, `motorized_flap.py`, `motorized_servo_adapter.py`, `motorized_servo_cover.py`, `motorized_assembly.py`) ✅
- **Specs**: [plan.md](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/2026-08-15-phase-4-motorized-module/plan.md) | [requirements.md](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/2026-08-15-phase-4-motorized-module/requirements.md) | [validation.md](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/2026-08-15-phase-4-motorized-module/validation.md)
- **Motorized Outer Frame** (`motorized_frame.py`): Model rigid 4-sided motorized module chassis (yellow) with horizontal inline MG996R servo mounting bay:
  - $240 \times 240 \times 15\text{ mm}$ outer envelope with $15.0\text{ mm}$ perimeter rails, open-bottom interior saving ~120g PLA, and 100% planar flat base at $Z = 0.0\text{ mm}$.
  - Continuous inner enclosure wall ($X \in [38.0, 48.0\text{ mm}], Y \in [185.0, 240.0\text{ mm}]$) sealing the motor chamber from the central cavity.
  - Solid front mounting towers ($Y \in [185.0, 195.5\text{ mm}]$) with 4x M3 clearance through-holes ($\varnothing 3.4\text{ mm}$) and 4x front captive hex nut pockets ($W_{af} = 5.8\text{ mm}$, depth $3.2\text{ mm}$) accurately spaced per MG996R tabs.
  - Rear slide-in opening at $Y = 240.0\text{ mm}$ with ear slide channels ($X \in [-17.5, 38.0\text{ mm}]$).
  - Dual solid 360° closed cylindrical bearing knuckles centered at $Z_{pivot} = 10.0\text{ mm}$ with C1-continuous concave blend ramps ($R_f = 12.0\text{ mm}$).
- **Modular Circular Servo Horn Drive Adapter** (`motorized_servo_adapter.py`): Model $\varnothing 19.0\text{ mm} \times 7.0\text{ mm}$ circular flange adapter bolting directly to standard MG996R round horn via 4x screws, central M3 screw counterbore, and male 8.0mm hex drive peg with $45^\circ$ lead-in chamfer.
- **Symmetrical Dual-Hex Active Folding Flap** (`motorized_flap.py`): Model active folding flap panel (red) with integrated continuous solid-core $\varnothing 12.9\text{ mm}$ drive axle:
  - Full-size blade ($239 \times 238 \times 2.4\text{ mm}$) resting flush on frame rails ($Z = 15.0$ to $17.4\text{ mm}$).
  - Symmetrical 8.0mm female hex sockets at both top ($Y = 178.0\text{ mm}$, receiving `motorized_servo_adapter`) and bottom ($Y = 0.5\text{ mm}$, receiving `hex_drive_coupler`).
  - Multi-tiered organic circular cutouts (~45% mass reduction), $0.6\text{ mm}$ diamond knurling, and $1.2\text{ mm}$ perimeter shadow bevel.
- **Full Enclosure Slide-In Hood Cover** (`motorized_servo_cover.py`): Model full hood cover with top plate, rear face cap, lateral retention tongues, and motor clearance pocket.
- **Motorized Sub-Assembly** (`motorized_assembly.py`): Multi-body sub-assembly verifying $0.00000\text{ mm}^3$ interference across all mating component pairs.

---

## Phase 5 — Interface Module & Electronics Enclosure (`interface_case.py`, `interface_panel.py`, `interface_assembly.py`) ✅
- **Specs**: [plan.md](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/2026-08-22-phase-5-interface-module/plan.md) | [requirements.md](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/2026-08-22-phase-5-interface-module/requirements.md) | [validation.md](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/2026-08-22-phase-5-interface-module/validation.md)
- **Flat Horizontal Interface Control Faceplate** (`interface_panel.py`): Model flat rectangular control deck top faceplate ($220.0 \times 120.0 \times 3.0\text{ mm}$, yellow):
  - **4x Top Interaction Buttons**: 4x standardized $\varnothing 16.0\text{ mm}$ round tactile push button mounting holes / bezels spaced ergonomically across the top deck for direct user interaction with the folding system (e.g. Start/Fold, Stop/Pause, Preset/Mode, and Reset).
  - **Status LED Window**: Dedicated standardized $\varnothing 6.0\text{ mm}$ circular round status indicator aperture with $0.8\text{ mm}$ top chamfer and $\varnothing 8.5\text{ mm}$ underside retention lip for multi-color system state feedback (Ready, Folding, Paused, Fault, WiFi/Connected).
  - **Surface & Aesthetic Detailing**: $0.8\text{ mm}$ hole edge chamfers, $0.6\text{ mm}$ micro-grip diamond surface texture, $1.2\text{ mm}$ perimeter shadow bevel, and 100% screwless unibody top surface.
  - **4-Sided Toolless Snap-Lock Retention**: 2x front captive under-hook lugs, continuous left/right perimeter register down-ribs preventing sidewall bowing, and 2x rear cantilever snap-latches clicking into the chassis.
- **Spacious High-Capacity Triple-Board Controller Enclosure** (`interface_case.py`): Model protective modular flat rectangular electronics chassis with increased $45.0\text{ mm}$ height ($220.0 \times 120.0 \times 45.0\text{ mm}$, total assembled $H = 48.0\text{ mm}$, green) providing $>25\text{ mm}$ of overhead volume for cable bundles, housing 3 circuit boards:
  - **Power Distribution Board (PDB) / 5V-6V Step-Down Buck Module**: Dedicated internal mounting standoffs ($37.0 \times 24.0\text{ mm}$ M3 hole pattern on $45.0 \times 32.0\text{ mm}$ PCB) with screw terminal blocks positioned directly behind the DC barrel jack, regulating and distributing power to the servo rail and MCU.
  - **PCA9685 16-Channel 12-Bit PWM Servo Driver Board**: Dedicated internal mounting standoffs ($55.88 \times 19.05\text{ mm}$ / $2.20" \times 0.75"$ M2.5 hole pattern on $62.5 \times 25.4\text{ mm}$ PCB) for driving all motorized folding flap servos.
  - **ESP32 Microcontroller Board (WROOM-32 / ESP-32S DevKit)**: Dedicated internal mounting standoffs ($46.0 \times 23.0\text{ mm}$ hole pattern on $51.5 \times 28.5\text{ mm}$ PCB) + universal perimeter snap cradle and micro-USB / USB-C external programming port aperture for WiFi/Bluetooth control and robot logic execution.
  - **Power & External Connectivity**: $\varnothing 11.5\text{ mm}$ high-current DC barrel jack (5.5×2.1mm) inlet cutout directly feeding the PDB input, plus ESP32 USB programming cutout.
  - **High-Capacity 16-Motor Wire Conduit & Strain-Relief**: High-capacity $60.0 \times 20.0\text{ mm}$ rear conduit window supporting up to 48 servo wires / ribbon cables, dual captive zip-tie strain-relief anchor saddles ($12.0 \times 6.0\text{ mm}$) absorbing 100% of external cable pull tension, $2\times \varnothing 6.0\text{ mm}$ S-bend friction snubber posts for hardware-free wire tension relief, $38.0 \times 20.0\text{ mm}$ left-bay power/logic conduit, passive convection cooling chimneys, $0.4\text{ mm}$ Elephant's Foot relief chamfers, rear toolless pry-release access notches, and sliding dovetail joiner sockets with push-out access holes.
- **Interface Sub-Assembly** (`interface_assembly.py`): Multi-body sub-assembly model integrating Interface Case + Flat Interface Faceplate + Circuit Board CAD Reference models (PDB + PCA9685 + ESP32 DevKit) + 4 Push Buttons + Status LED Diffuser.
- **Visual Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` (multi-view bursts), `inspect_freecad_assembly` (exploded view with dimensions), and `check_interference` (confirming $0.0000\,\text{mm}^3$ overlap). Confirm PASS report.

---

## Phase 6 — Full 4×3 Garment Folding Grid Assembly (`assemblies/assembly_4x3_grid.py`)
- Build full 4×3 grid assembly model bringing together 2 Base Modules, 4 Follower Modules, 6 Motorized Modules, and 1 Interface Control Pad Module connected by Click-Lock Hollow Dovetail Wire-Channel Joiners.
- Validate kinematic panel flip positions (0° flat rest, 90° vertical fold, 180° flipped fold).
- Export full `assembly_4x3_grid.step` and `assembly_4x3_grid.stl`.
