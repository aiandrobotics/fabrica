# CAD Designs & 3D Printed Models — Fabrica Cloth Folding Robot

This directory contains parametric Python CAD source files (using FreeCAD's Python API), 3D printing assets (STEP / STL), parameter definitions, and assembly models for the **Fabrica Cloth Folding Robot**.

---

## Hardware Modules

| Module / Part | Script | Output Exports | Description |
|---|---|---|---|
| **Base Stationary Chassis** | [`base_module.py`](./base_module.py) | `base_module.step`, `base_module.stl` | Monolithic rigid stationary base plate with open-bottom hexagonal cavity, anti-slip foot pads, wire channels, and sliding dovetail sockets. |
| **Interlocking Frame Joiner** | [`frame_joiner.py`](./frame_joiner.py) | `frame_joiner.step`, `frame_joiner.stl` | Symmetric flared sliding dovetail bridge joiner (`18.0 × 33.6 × 12.0 mm`) with internal `6.8 × 8.6 mm` filleted wire raceway. |
| **Drive Coupler Pin** | [`drive_coupler.py`](./drive_coupler.py) | `drive_coupler.step`, `drive_coupler.stl` | Double-male 45° diamond tapered square coupler (`6.35 → 5.90 mm` × `12.0 mm` corner-relieved pegs, `66.0 mm` total length) with smooth `Ø12.6 mm` continuous journal body and `45°` conical shoulders. |
| **Click-Lock End Pivot Pin** | [`end_pivot_pin.py`](./end_pivot_pin.py) | `end_pivot_pin.step`, `end_pivot_pin.stl` | Outside-headed click-lock pivot pin (`32.5 mm` total length) with `Ø16.0 × 2.5 mm` outer cap, `Ø12.8 × 18.0 mm` journal, dual `Ø14.4 mm` cantilever snap barbs, and `6.35 → 5.90 mm` × `12.0 mm` 45° diamond tapered square peg. |
| **Follower Chassis Frame** | [`follower_frame.py`](./follower_frame.py) | `follower_frame.step`, `follower_frame.stl` | Passive follower chassis with dual `Ø13.7 mm` closed bearing knuckles, blend ramps, open-bottom weight reduction, and 4th wall dovetail tie-bar. |
| **Follower Folding Flap** | [`follower_flap.py`](./follower_flap.py) | `follower_flap.step`, `follower_flap.stl` | Full-size rotating follower flap with `Ø12.8 mm` drive axle, dual `14.0 mm` deep `6.50 mm` 45° diamond square sockets (`0.8 mm` entry bevel), solid un-grooved `2.4 mm` hinge neck (`X ∈ [0.0, 11.9 mm]`), and mass-reduction cutouts. |
| **Follower Sub-Assembly** | [`follower_assembly.py`](./follower_assembly.py) | `follower_assembly.step`, `follower_assembly.stl` | Complete Passive Follower sub-assembly uniting frame, flap, end pivot pin, frame joiners, and square drive coupler pin. |
| **Motorized Chassis Frame** | [`motorized_frame.py`](./motorized_frame.py) | `motorized_frame.step`, `motorized_frame.stl` | Active motorized chassis with dual closed knuckles, MG996R servo well, mounting bosses, cable conduit, and snap-cover retention slots. |
| **Servo Horn Drive Adapter** | [`motorized_servo_adapter.py`](./motorized_servo_adapter.py) | `motorized_servo_adapter.step`, `motorized_servo_adapter.stl` | `Ø20.0 × 7.5 mm` circular flange adapter bolting to MG996R round horn with `6.35 → 5.90 mm` 45° diamond tapered square drive peg (`6.3 mm` span + `12.0 mm` tapered engagement, `25.8 mm` total length). |
| **Motorized Folding Flap** | [`motorized_flap.py`](./motorized_flap.py) | `motorized_flap.step`, `motorized_flap.stl` | Monolithic active flap with `Ø12.8 mm` drive axle, dual `14.0 mm` deep `6.50 mm` 45° diamond square sockets (`0.8 mm` entry bevel), solid un-grooved `2.4 mm` hinge neck (`X ∈ [0.0, 11.9 mm]`), and servo clearance notch. |
| **Motorized Servo Cover** | [`motorized_servo_cover.py`](./motorized_servo_cover.py) | `motorized_servo_cover.step`, `motorized_servo_cover.stl` | Quick-release protective housing with dual snap-latch flex tabs, wire strain-relief notch, and convection cooling gills. |
| **Motorized Sub-Assembly** | [`motorized_assembly.py`](./motorized_assembly.py) | `motorized_assembly.step`, `motorized_assembly.stl` | Complete Active Motorized sub-assembly uniting frame, active flap, servo drive adapter, end pivot pin, servo cover, joiners, and MG996R servo reference. |
| **Interface Electronics Case** | [`interface_case.py`](./interface_case.py) | `interface_case.step`, `interface_case.stl` | Compact enclosure chassis (`140.0 × 141.8 × 45.0 mm`) housing PDB, ESP32-S3-DevKitC-1, and PCA9685 with rear dovetail wire raceway and 16 motor cable slots. |
| **Interface Control Panel** | [`interface_panel.py`](./interface_panel.py) | `interface_panel.step`, `interface_panel.stl` | Snap-lock top control deck (`140.0 × 120.0 × 3.0 mm`) with 4 × `Ø16.0 mm` button cutouts, `Ø6.0 mm` status LED window, and micro-grip grooves. |
| **Interface Sub-Assembly** | [`interface_assembly.py`](./interface_assembly.py) | `interface_assembly.step`, `interface_assembly.stl` | Complete Interface enclosure sub-assembly uniting case, control panel, PCB references, push buttons, and status LED diffuser. |
| **Full 6-Module Grid Assembly** | [`assembly.py`](./assembly.py) | `assembly.step`, `assembly.stl` | Complete 27-object universal garment folding assembly (2 Base + 2 Follower + 2 Motorized + 2 Drive Couplers + 2 End Pivot Pins + 7 Joiners). |

---

## Build & Export Pipeline

To generate and export all STEP and STL assets headlessly:

```bash
cd cad-designs
python3 export_all.py
```

To run an individual script:
```bash
./run.sh motorized_frame.py
```

---

## Specification Roadmap
Refer to [`specs/roadmap.md`](./specs/roadmap.md) and module design specifications in [`specs/`](./specs/).
