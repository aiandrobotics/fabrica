# Tech Stack — CAD Designs

## CAD Toolchain

| Layer | Tool |
|---|---|
| Parametric Modelling | FreeCAD 1.1.0+ (Python scripting API) |
| Geometry Kernel | OpenCASCADE (OCC) via `Part` workbench |
| Headless Execution | `freecadcmd` (`/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd` or `freecadcmd` on PATH) |
| GUI Inspection | FreeCAD GUI (`/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`) |
| Export Format — CAD | STEP (AP214) via `shape.exportStep()` |
| Export Format — Print | STL (binary) / 3MF via `shape.exportStl()` |
| Parameters | `params.py` — single source of truth; all dimensions driven by parameters & `SCALE` |
| Visual Validation | FreeCAD MCP Server (v3) via `freecad-visual-validation` skill |

## FreeCAD MCP Visual Validation Toolchain (v3)

All part and assembly Python scripts must be visually and analytically validated using the FreeCAD MCP server tools before final approval:

1. **`render_freecad_script`**: Multi-view bursts (`Isometric`, `Front`, `Top`, `Right`, `Bottom`), custom elevation/azimuth angles, and close-up detail inspection.
2. **`inspect_freecad_assembly`**: Exploded assembly rendering (`explode_factor`), part highlighting (`highlight_objects`), focus zooming (`focus_object`), and dimension labels (`show_dimensions`).
3. **`section_freecad_model`**: Diagnostic cross-section cuts (`XZ`, `YZ`, `XY`), wireframe mesh topology (`wireframe`), and orientation/print-face analysis (`orientation_check`).
4. **`check_interference`**: Precise Boolean intersection volume calculations (`overlap_volume_mm3`) between mating part pairs. `overlap_volume_mm3 > 0.001` on clearance joints indicates a design error.

## FreeCAD Python & Parametric Conventions

- `SCALE = 1.0` is always defined in `params.py` (default for **256 × 256 × 256 mm** build plate; set `SCALE = 180.0 / 256.0` to scale down to **180 × 180 × 180 mm** build plates).
- All dimensions are defined in **millimetres** (mm).
- Primitives: `Part.makeBox`, `Part.makeCylinder`, `Part.makeHollowBox`, etc.
- Boolean operations: `.fuse()`, `.cut()`, `.common()`; use `Part.makeCompound()` when assembling multiple tool shapes to avoid silent boolean failures in OpenCASCADE.
- Fillets & Chamfers: always wrapped in `try/except` to prevent script execution failure on edge topology changes.
- Script outputs: Every `construct_*()` function cleans existing files before exporting new shapes.
- **CRITICAL Pattern for Sweeps/Threads**: Any `Part.Wire(helix).makePipeShell()` or complex extrusion must be generated at the origin (`App.Vector(0,0,0)`) wrapped in `Part.Solid()` and immediately fused to its core (`.fuse()`). Only *after* the feature solid is finalized should it be repositioned using `.Placement` to interact with the main body. Creating sweeps off-origin results in disjoint bounding boxes and silent boolean (`.cut`) failures in OpenCASCADE.

## FDM Print Constraints & Build Volume Specs

| Parameter | Default Value (256mm Plate) | Scaled Value (180mm Plate via `SCALE`) |
|---|---|---|
| Build plate volume | 256 × 256 × 256 mm | 180 × 180 × 180 mm (`SCALE = 180/256`) |
| Default nozzle size | 0.4 mm | 0.4 mm |
| Default layer height | 0.2 mm | 0.2 mm |
| Inter-part fit clearance | 0.4 mm (sliding fit) | Scaled proportionally |
| Press-fit clearance | 0.2 mm (servo horn couplers) | Scaled proportionally |
| Min wall thickness (structural) | 3.0 mm | 2.1 mm |
| Min wall thickness (cosmetic) | 2.0 mm | 1.4 mm |
| Overhang rule | ≤ 45° without mandatory support | ≤ 45° without mandatory support |

## Parametric Parameters (defined in `params.py`)

| Parameter | Default Value | Description |
|---|---|---|
| `BUILD_PLATE_SIZE` | 256.0 mm | Target build volume dimension |
| `SCALE` | 1.0 | Global parametric scaling multiplier (e.g. `180/256` for 180mm plate) |
| `PANEL_WIDTH` | 240.0 mm | Standard width for modular panels |
| `PANEL_HEIGHT` | 240.0 mm | Standard height for modular panels |
| `PANEL_THICKNESS` | 12.0 mm | Structural thickness for panel bodies |
| `FIT_CLEARANCE` | 0.4 mm | Sliding/hinge clearance between mating parts |
| `PRESS_FIT_CLEARANCE` | 0.2 mm | Clearance for servo horn drive adapters & joiners |
| `WALL_THICKNESS` | 3.0 mm | Standard outer wall thickness |
| `SERVO_MOUNT_WIDTH` | 40.5 mm | MG996R servo motor body width footprint |
| `SERVO_MOUNT_DEPTH` | 20.0 mm | MG996R servo motor body depth footprint |
| `TEXTURE_HEIGHT` | 0.6 mm | Micro-grip diamond texture height on panel surfaces |
| `HOLE_CHAMFER` | 0.8 mm | 45° chamfer on circular weight-reduction hole edges |
| `ELEPHANTS_FOOT_CHAMFER` | 0.4 mm | 45° relief chamfer on bottom bed-contacting edges |
| `CONTROL_DECK_ANGLE` | 15.0° | Ergonomic forward tilt angle for interface panel |
| `TPU_BUMPER_DEPTH` | 1.5 mm | Recessed pocket depth for silent flip TPU shock dampers |
| `RETICLE_DEBOSS_DEPTH` | 0.4 mm | Deboss depth for garment collar & shoulder centering guide lines |
| `DC_JACK_DIAMETER` | 11.5 mm | Mounting cutout diameter for external DC power supply jack |
| `BUTTON_HOLE_DIA` | 16.0 mm | Mounting cutout diameter for top interface tactile push buttons |
| `FOOT_PAD_DIA` | 20.1 mm | Sockets for press-fitting anti-slip silicone/rubber feet |
| `FOOT_PAD_DEPTH` | 2.0 mm | Recessed depth for tabletop anti-slip rubber pads |
| `JOINER_DETENT` | 0.3 mm | Flex detent bump on dovetail joiners for click-lock retention |
| `WIRE_PORT_FILLET` | 1.5 mm | Smooth radius fillet on internal cable pass-through ports |
| `ACCENT_BEVEL_DEPTH` | 1.2 mm | Recessed perimeter shadow bevel for dual-tone panel aesthetics |

## File & Folder Structure

```
cad-designs/
├── specs/                          ← project constitution (mission.md, tech-stack.md, roadmap.md, and phase specs)
├── params.py                       ← single source of truth (dimensions, SCALE, clearances)
├── base_module.py                  ← monolithic base chassis (4-wall frame, open-bottom cavity, wire ports, micro-grip texture, circular cutouts, dovetail sockets)
├── follower_frame.py               ← passive follower 4-sided frame (360° closed bore, 4th wall dovetail joint, 4x rubber feet, TPU bumpers, open-top dovetail sockets)
├── follower_flap.py                ← passive follower flap (continuous Ø13mm axle, dual 8mm hex sockets, gradient ~45% mass cutouts, 0.8mm hole chamfers, 0.6mm micro-grip texture, 1.2mm bevel)
├── follower_assembly.py            ← follower module sub-assembly (FollowerFrame + FollowerFlap + FrameJoiners + HexCoupler)
├── motorized_frame.py              ← active motorized 4-sided frame (servo mounting bay, 4th wall dovetail joint, 4x rubber feet, TPU bumpers, dovetail sockets)
├── motorized_flap.py               ← monolithic active folding flap (integrated Ø13mm axle, 25T servo horn pocket, 8mm hex output socket, ~45% mass cutouts, micro-grip texture)
├── motorized_servo_cover.py        ← toolless snap-latch servo housing cover with wire strain relief and cooling gills
├── motorized_assembly.py           ← motorized module sub-assembly (MotorizedFrame + MotorizedServoCover + MotorizedFlap + FrameJoiners + HexCoupler + Servo)
├── interface_case.py                ← dual-board enclosure case (housing PCA9685 + ESP32 DevKit, 11.5mm DC jack, zip-tie saddles, cooling chimneys, dovetail sockets)
├── interface_panel.py               ← 15° angled ergonomic control deck faceplate (4 button cutouts, LED status window, hole chamfers, micro-grip texture)
├── interface_assembly.py            ← interface module sub-assembly (InterfaceCase + InterfacePanel + PCA9685 + ESP32 + 4 Buttons + Status LED)
├── frame_joiner.py                 ← click-lock hollow dovetail frame joiner peg (0.3mm detent bump + internal wire raceway)
├── hex_drive_coupler.py            ← modular double-male 8.0mm hex torque drive coupler pin
├── assembly_4x3_grid.py            ← full 4x3 grid assembly model (2 Base + 4 Follower + 6 Motorized + Interface)
├── export_all.py                   ← batch script to export all STEP and STL models
├── run.sh                          ← CLI entrypoint for building and exporting CAD models
├── README.md
└── exports/                        ← target directory for generated STL and STEP files
```
