# Requirements — Phase 2: Modular Base Module & Interlocking Joiners

## Scope
Implement `parts/part_01_base_module.py` and `parts/part_09_frame_joiner.py` to create the stationary central chassis column and toolless interlocking frame joiners for the Fabrica Cloth Folding Robot 4×3 grid architecture.

## Decisions
- **Monolithic 1-Piece Base Chassis**: Consolidate the base top plate and outer frame box into 1 single solid chassis script (`part_01_base_module.py`) for maximum structural backbone rigidity and zero assembly effort.
- **Click-Lock Hollow Dovetail Joiners**: Eliminate magnets in favor of 100% 3D-printed tapered dovetail keys (`part_09_frame_joiner.py`) featuring 0.3 mm detent bumps and internal wire conduits.
- **Parametric Single Source of Truth**: All dimensions, clearances, chamfers, and wall thicknesses must strictly import from `params.py`.

## Constraints
- **Build Plate Footprint**: Must fit within standard **256 × 256 × 256 mm** build plates (240 × 240 × 15 mm base module) and scale down to **180 × 180 × 180 mm** via `SCALE = 180.0 / 256.0` in `params.py`.
- **FDM Printability**: Must print inverted flat on the build bed with **0 support material**.
- **Bed Relief**: 0.4 mm × 45° Elephant's Foot relief chamfer on all bottom print edges.
- **Garment Surface**: 0.6 mm micro-grip diamond texture and 0.8 mm hole edge chamfers to prevent fabric slipping and thread snagging.
- **Recoil Stability**: Ø20.1 × 2.0 mm bottom sockets for press-fitting anti-slip silicone/rubber feet.
- **Poka-Yoke Alignment**: 0.5 mm debossed "FRONT ➔" arrow near front dovetail socket.

## Non-goals
- Actuator mounting pockets (servo pockets are scoped to Phase 4).
- Hinged flap rotation pivot arms (follower hinge bores are scoped to Phase 3).
- Photorealistic material rendering or FEA stress simulation.

## Context
The central column of the 4×3 garment folding grid consists of two stationary Base Modules. All motorized side panels flip inward over these base modules. The Base Module serves as the mechanical spine, cable hub, and visual centerpiece of the robot.
