# CAD Designs & 3D Printed Models — Fabrica Cloth Folding Robot

This directory contains parametric Python CAD source files (using FreeCAD's Python API), 3D printing assets (STEP / STL), parameter definitions, and assembly models for the **Fabrica Cloth Folding Robot**.

---

## Hardware Modules

| Module / Part | Script | Output Exports | Description |
|---|---|---|---|
| **Base Stationary Chassis** | [`base_module.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/base_module.py) | `base_module.step`, `base_module.stl` | Monolithic rigid stationary base plate with internal hexagonal infill web, anti-slip foot pads, alignment reticles, and cable channels. |
| **Interlocking Frame Joiner** | [`frame_joiner.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/frame_joiner.py) | `frame_joiner.step`, `frame_joiner.stl` | Click-lock hollow dovetail bridge joiner locking adjacent modules with internal wire conduit. |
| **Hex Drive Coupler Pin** | [`hex_drive_coupler.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/hex_drive_coupler.py) | `hex_drive_coupler.step`, `hex_drive_coupler.stl` | Modular double-male 8.0mm hex torque coupler with central locating stop collar. |
| **Follower Chassis Frame** | [`follower_frame.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/follower_frame.py) | `follower_frame.step`, `follower_frame.stl` | Passive follower chassis with dual Ø13.5mm closed bearing knuckles, blend ramps, open-bottom weight reduction, and 4th wall dovetail tie-bar. |
| **Follower Folding Flap** | [`follower_flap.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/follower_flap.py) | `follower_flap.step`, `follower_flap.stl` | Full-size rotating follower flap blade with continuous Ø13.0mm solid drive axle, dual 8.0mm female hex torque sockets, and gradient mass-reduction cutouts. |
| **Follower Sub-Assembly** | [`assembly.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/assembly.py) | `assembly.step`, `assembly.stl` | Complete Passive Follower sub-assembly uniting frame, flap, frame joiners, and hex coupler pin. |
| **Motorized Chassis Frame** | [`motorized_frame.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/motorized_frame.py) | `motorized_frame.step`, `motorized_frame.stl` | Active motorized chassis with dual closed knuckles, MG996R servo well, mounting bosses, cable conduit, and snap-cover retention slots. |
| **Monolithic Active Flap** | [`active_flap.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/active_flap.py) | `active_flap.step`, `active_flap.stl` | Monolithic active flap with continuous Ø13.0mm drive axle, integrated 25T metal servo horn pocket + central M3 retention screw, bottom 8.0mm hex socket, and servo clearance notch. |
| **Toolless Servo Cover** | [`servo_cover.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/servo_cover.py) | `servo_cover.step`, `servo_cover.stl` | Quick-release protective housing with dual snap-latch flex tabs, wire strain-relief notch, and convection cooling gills. |
| **Motorized Sub-Assembly** | [`assembly_motorized_module.py`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/assembly_motorized_module.py) | `assembly_motorized_module.step`, `assembly_motorized_module.stl` | Complete Active Motorized sub-assembly uniting frame, active flap, servo cover, joiners, hex coupler pin, and servo reference solid. |

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
Refer to [`specs/roadmap.md`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/roadmap.md) and module design specifications in [`specs/`](file:///Users/intelligentmachine/Documents/workspace/fabrica/cad-designs/specs/).
