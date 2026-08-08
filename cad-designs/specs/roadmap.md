# Roadmap — CAD Designs

Each phase is a small, independently buildable and testable unit of work matching the reference architecture images (`specs/reference-images/`).
Build, validate, and commit before moving to the next phase.

---

## Phase 0 — Project Constitution & CAD Specs ✅
- Create `specs/mission.md`, `specs/tech-stack.md`, and `specs/roadmap.md` tailored for Fabrica Cloth Folding Robot.
- Establish default **256 × 256 × 256 mm** build plate target with support for scaling down to **180 × 180 × 180 mm** via the `SCALE` parameter in `params.py`.
- Incorporate FreeCAD MCP server tools (`render_freecad_script`, `inspect_freecad_assembly`, `section_freecad_model`, `check_interference`) and `freecad-visual-validation` skill rules into project specs.
- Review reference images (`base-module.png`, `follower-module.png`, `motorized-module.png`, `interface-module.png`, `3d-overview.png`) and lock component sub-part breakdowns.

---

## Phase 1 — Parametric Foundations (`params.py` & Directory Skeleton) ✅
- Apply `freecad-project` skill conventions for project structure, `params.py` template, `run.sh` entrypoint, and automated export pipeline.
- Create `params.py` with `SCALE = 1.0` as the first line, defining single source of truth dimensions (default 256mm build plate `BUILD_PLATE_X/Y/Z = 256.0 * SCALE`), `SCALE_180 = 180.0 / 256.0`, FDM clearances (`FIT_CLEARANCE`, `PRESS_FIT_CLEARANCE`), wall thicknesses, servo mounting parameters, `TEXTURE_HEIGHT = 0.6 mm`, `HOLE_CHAMFER = 0.8 mm`, `ELEPHANTS_FOOT_CHAMFER = 0.4 mm`, `CONTROL_DECK_ANGLE = 15.0°`, `TPU_BUMPER_DEPTH = 1.5 mm`, `RETICLE_DEBOSS_DEPTH = 0.4 mm`, `DC_JACK_DIAMETER = 11.5 mm`, `FOOT_PAD_DIA = 20.1 mm`, `FOOT_PAD_DEPTH = 2.0 mm`, `JOINER_DETENT = 0.3 mm`, `WIRE_PORT_FILLET = 1.5 mm`, `PROJECT_DIR`, and `EXPORT_DIR`.
- Setup directory layout adhering to `freecad-project` structure: `parts/`, `assemblies/`, `exports/`, `3d-print/`, `media/`, `run.sh` (executable via `chmod +x run.sh`), `export_all.py`, and `.gitignore`.
- Smoke test: `python params.py` executes cleanly without error and prints key parametric dimensions.

---

## Phase 2 — Modular Base Module & Interlocking Joiners (`part_01_base_module.py`, `part_10_frame_joiner.py`)
- **Monolithic Base Chassis Module** (`part_01_base_module.py`): Model 1-piece rigid stationary base chassis fusing top plate and outer frame box, featuring an internal 3.0 mm wall isometric hexagonal web lattice (~30% PLA filament saving & zero 240mm bed warping), 20.1×2.0 mm bottom corner sockets for press-fitting anti-slip silicone/rubber feet (recoil & slide prevention), 0.5 mm debossed Poka-Yoke directional alignment arrows ("FRONT ➔"), 0.4 mm debossed garment shirt collar & shoulder centering alignment reticles, 1.5 mm recessed silent flip TPU bumper landing slots, 1.5 mm filleted internal wire pass-through ports with zip-tie strain-relief loops, 0.8 mm hole edge chamfers, 0.6 mm top micro-grip diamond texture, 0.4 mm bottom Elephant's Foot relief chamfers, and click-lock dovetail joiner sockets with detent dimples.
- **Click-Lock Hollow Dovetail Frame Joiner** (`part_10_frame_joiner.py`): Model tapered dovetail interlocking joiner peg featuring a 0.3 mm flex-detent bump for tactile click-lock retention and an internal hollow wire conduit tunnel, locking adjacent frames mechanically without screws while serving as a hidden internal wire raceway across grid rows.
- **Visual Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` (multi-view burst) and `section_freecad_model` (print orientation & wall thickness check). Confirm PASS report.

---

## Phase 3 — Passive Follower Module (`part_02_follower_frame.py`, `part_03_follower_flap.py`, `assembly_follower_module.py`)
- **Follower Outer Frame** (`part_02_follower_frame.py`): Model passive follower module U-frame (green) featuring a top 360° closed cylindrical bearing bore, a bottom flex C-snap socket with a 0.5 mm lead-in funnel, 1.5 mm recessed silent flip TPU bumper slots, 0.4 mm bottom Elephant's Foot relief chamfers, 0.5 mm debossed Poka-Yoke directional alignment arrows ("FRONT ➔"), 1.5 mm filleted internal wire pass-through ports with zip-tie strain-relief loops, click-lock dovetail joiner sockets with detent dimples, and integrated under-frame cable routing clips.
- **Follower Folding Flap** (`part_03_follower_flap.py`): Model rotating follower flap panel (orange) with integrated top & bottom male pivot pins featuring 45° lead-in chamfers (1.5 mm), 0.6 mm micro-grip diamond surface texture, 0.8 mm hole edge chamfers, and gradient circular weight-reduction cutouts (~45% mass reduction, reducing panel weight to ~80g and minimizing rotational inertia on active servo modules).
- **Follower Sub-Assembly** (`assembly_follower_module.py`): Assemble Follower Frame + Follower Flap (Pin-Slide & Snap: slide top chamfered pin into 360° closed bore, snap bottom chamfered pin into C-snap socket) + Frame Joiners. Toolless 3-second assembly with zero pin layer damage.
- **Visual & Kinematic Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` and `section_freecad_model` to verify 0° to 180° rotation clearance and pivot pin engagement. Confirm PASS report.

---

## Phase 4 — Active Motorized Module (`part_04_motorized_frame.py` to `part_07_active_flap.py`, `assembly_motorized_module.py`)
- **Motorized Outer Frame** (`part_04_motorized_frame.py`): Model motorized U-frame (yellow) with integrated MG996R servo mounting pocket, 1.5 mm recessed silent flip TPU bumper slots, 0.4 mm bottom Elephant's Foot relief chamfers, 0.5 mm debossed Poka-Yoke directional alignment arrows ("FRONT ➔"), 1.5 mm filleted internal wire pass-through ports with zip-tie strain-relief loops, and click-lock dovetail joiner sockets with detent dimples.
- **Motorized Drive Shaft** (`part_05_motorized_shaft.py`): Model driven hinge shaft (green) featuring an integrated press-fit metal servo horn pocket for direct 1-piece drive without separate couplers, eliminating rotational slop.
- **Toolless Snap-Latch Servo Cover** (`part_06_servo_cover.py`): Model protective housing cover (black) with a toolless snap-latch mechanism and wire strain relief routing for 5-second motor swap outs.
- **Active Folding Flap** (`part_07_active_flap.py`): Model active folding flap panel (red) featuring corner cutout for servo clearance, 0.6 mm micro-grip diamond surface texture, 0.8 mm hole edge chamfers, and gradient circular weight-reduction cutouts (~45% mass reduction, reducing panel weight to ~80g and minimizing rotational inertia on active servo modules).
- **Motorized Sub-Assembly** (`assembly_motorized_module.py`): Assemble Motorized Frame + Shaft + Cover + Active Flap + Frame Joiners.
- **Visual & Kinematic Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` (detail close-ups of integrated servo horn socket) and `check_interference` on drive shaft interfaces. Confirm PASS report.

---

## Phase 5 — Interface Module & Electronics Enclosure (`part_08_interface_panel.py`, `part_09_controller_case.py`, `assembly_interface_module.py`)
- **15° Angled Interface Control Faceplate** (`part_08_interface_panel.py`): Model ergonomic 15° forward-angled control deck top faceplate (yellow) housing 4 tactile button cutouts, a status LED bar diffuser window, 0.8 mm hole edge chamfers, and 0.6 mm micro-grip diamond surface texture.
- **Ventilated Controller Case** (`part_09_controller_case.py`): Model protective electronics enclosure (green) featuring an 11.5 mm DC power barrel jack / USB-C PD mounting cutout, zip-tie wire strain-relief saddles, 0.4 mm bottom Elephant's Foot relief chamfers, 0.5 mm debossed Poka-Yoke directional alignment arrows ("FRONT ➔"), click-lock dovetail joiner sockets with detent dimples, 1.5 mm filleted internal wire pass-through ports, and passive convection cooling chimney slots underneath the Raspberry Pi Pico 2W and PCA9685 driver board to prevent thermal throttling.
- **Interface Sub-Assembly** (`assembly_interface_module.py`): Assemble Controller Case + 15° Angled Interface Faceplate.
- **Visual Validation**: Apply `freecad-visual-validation` skill using `render_freecad_script` and `inspect_freecad_assembly` (exploded view with dimensions). Confirm PASS report.

---

## Phase 6 — Full 4×3 Garment Folding Grid Assembly (`assemblies/assembly_4x3_grid.py`)
- Build full 4×3 grid assembly model bringing together 2 Base Modules, 4 Follower Modules, 6 Motorized Modules, and 1 Interface Control Pad Module connected by Click-Lock Hollow Dovetail Wire-Channel Joiners.
- Validate kinematic panel flip positions (0° flat rest, 90° vertical fold, 180° flipped fold).
- Export full `assembly_4x3_grid.step` and `assembly_4x3_grid.stl`.
- **Visual Validation**: Apply `freecad-visual-validation` skill across all assembly steps:
  1. `render_freecad_script`: Full multi-view burst (`Isometric`, `Front`, `Top`, `Right`, `Back`).
  2. `inspect_freecad_assembly`: Exploded view (`explode_factor = 1.2`, `show_dimensions = true`) and part interface highlighting (`highlight_objects`).
  3. `check_interference`: Compute Boolean overlap volume (`overlap_volume_mm3`) on all touching part pairs to ensure zero unexpected intersections (`overlap_volume_mm3 <= 0.001`).
  4. `section_freecad_model`: Cross-section cut at primary panel hinges and controller mount.
  5. Confirm PASS report.

---

## Phase 7 — Automated Export & Validation Pipeline (`export_all.py`, `run.sh`)
- Implement `export_all.py` batch script to generate clean STEP (AP214) and binary STL exports for all 10 part scripts, 3 module sub-assemblies, and the full 4×3 grid assembly in both 256 mm (default) and 180 mm (`SCALE`) configurations.
- Verify 100% manifold topology pass across all generated STL files.
- Final visual validation pass using FreeCAD MCP tools across all parts and full grid assembly; tag CAD release commit.

---

## Out of Scope (v1)
- Finite Element Analysis (FEA) structural stress simulation in Python.
- Photorealistic material/texture rendering.
