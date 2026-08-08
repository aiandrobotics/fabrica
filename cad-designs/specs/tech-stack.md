# Tech Stack

## CAD Toolchain

| Layer | Tool |
|---|---|
| Parametric modelling | FreeCAD 1.1.0 (Python scripting API) |
| Geometry kernel | OpenCASCADE (OCC) via `Part` workbench |
| Headless execution | `freecadcmd` (`/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`) |
| GUI inspection | FreeCAD GUI (`/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`) |
| Export format — CAD | STEP (AP214) via `shape.exportStep()` |
| Export format — print | STL (binary) via `shape.exportStl()` |
| Parameters | `params.py` — single source of truth; all dimensions × `SCALE` |

## FreeCAD Python Conventions

- `SCALE = 1.0` is always the **first line** of `params.py`
- All dimensions are in **millimetres** (convert inches → mm in `params.py`)
- Primitives: `Part.makeBox`, `Part.makeHollowBox`, etc.
- Boolean ops: `.fuse()`, `.cut()`, `.common()`; use `Part.makeCompound()` for assembling thread cutters instead of `.fuse().removeSplitter()` to avoid silent boolean failures in OpenCASCADE.
- Fillets: always wrapped in `try/except`
- Every `construct_*()` function deletes existing exports before writing, then returns the shape
- Structural connections for segments rely on male threaded cylindrical pegs and female threaded holes. The thread is timed so that when fully tightened, the outer profiles (rectangular for legs, square transitions for rods) align seamlessly to form a uniform continuous member.
- **CRITICAL Pattern for Sweeps/Threads**: Any `Part.Wire(helix).makePipeShell()` or complex extrusion must be generated at the origin (`App.Vector(0,0,0)`) wrapped in `Part.Solid()` and immediately fused to its core (`.fuse()`). Only *after* the threaded solid is finalized should it be repositioned using `.Placement` to interact with the main body. Creating sweeps off-origin results in disjoint bounding boxes and silent boolean (`.cut`) failures in OpenCASCADE.

## FDM Print Constraints

| Parameter | Value |
|---|---|
| Build plate | 175 × 175 × 175 mm (default) |
| Default nozzle | 0.4 mm |
| Default layer height | 0.2 mm |
| Inter-part tolerance | 0.4 mm (sliding fit), 0.2 mm (press fit) |
| Min wall thickness | 3.0 mm (structural), 2.0 mm (cosmetic) |
| Overhang rule | ≤ 45° without support |

Long structural members (legs, rods) exceed the build plate and **must** be segmented into max 220 mm sub-parts (derived from $175\sqrt{2}$) with integrated threaded cylindrical male/female joint mechanisms.

## Fit Parameters (canonical — defined in `params.py`)

| Parameter | Value |
|---|---|
| `FIT_CLEARANCE` | 0.4 mm (sliding/friction fits between pegs and bores) |
| `PEG_THREAD_RADIUS` | Computed radius inside leg allowing wall clearance |
| `PEG_THREAD_PITCH` | 4.0 mm base thread pitch for connections |
| `THREAD_CLEARANCE` | 0.6 mm (shrinks male thread radius for post-print rotation) |
| `GENERAL_CLEARANCE` | 0.4 mm (clearance holes for pins/shafts) |
| `LEG_WIDTH` | 25.0 mm |
| `LEG_DEPTH` | 25.0 mm |
| `PEG_LENGTH` | 25.0 mm |

## Dimensions — 79" Variant (canonical model)

All values converted to mm from the reference images:

| Dimension | Imperial | Metric (mm) |
|---|---|---|
| Total length (deployed) | 51.1"–79" | 1298–2007 mm |
| Total height | 51.2" | 1300 mm |
| Total depth (rod-to-rod) | 19.3" | 490 mm |
| Foot spread (deployed) | 27.5" | 699 mm |
| Folded length | 56.3" | 1430 mm |
| Folded thickness | 4" | 102 mm |
| Leg Cross-section width | ~1.0" | 25 mm |
| Leg Cross-section depth | ~1.0" | 25 mm |
| Leg wall thickness | ~0.12" | 3 mm |

> Outer dimensions and wall are estimated from reference images; adjust in `params.py` if measured values differ.

## File & Folder Structure

```
clothes-drying-rack/
├── specs/                           ← project constitution (this folder)
├── params.py                        ← all dimensions + SCALE + paths 
├── part_01_leg_segment.py           ← rectangular hollow segment, integrated threaded peg one side
├── part_02_xframe_hinge_bottom.py   ← bottom hinge bracket (female threads)
├── part_03_xframe_hinge_top.py      ← top hinge bracket (clearance bore)
├── part_04_xframe_hinge_pin.py      ← locking pivot pin (male threads)
├── part_05_top_l_bracket.py         ← universal modular T-bracket (3 female sockets) for inline or top connections
├── part_06_drying_rod.py            ← universal stadium-profile rod segment
├── part_07_threaded_adapter_pin.py  ← male-to-male pin for female-to-female joints
├── part_08_foot_cap.py
├── part_09_rod_end_cap.py
├── assembly.py
├── export_all.py
├── run.sh
├── README.md
├── .gitignore
├── exports/
├── 3d-print/
└── media/
```
