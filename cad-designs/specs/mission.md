# CAD Designs Mission Specification

## Project Purpose

Design, model, and validate a complete, modular, 3D-printable mechanical hardware system for **Fabrica** — an open-source, automated cloth folding robot.

The `cad-designs` sub-system provides the 3D CAD models, STL/STEP export files, modular panel components, hinge mechanics, servo motor mounts, and controller enclosure needed to build the physical folding grid.

All CAD assets must be:
- **Printable**: Optimized for standard desktop FDM 3D printers (PLA/PETG) with a default **256 × 256 × 256 mm** build plate volume, clean overhangs (≤ 45°), and minimal support requirements. Parts can be dynamically scaled down to fit smaller 180 × 180 × 180 mm build beds.
- **Modular & Assembleable**: Modular panel units (Motorized, Follower, Base, Interface) that interlock into scalable grid arrangements (standard 4×3 configuration, expandable up to 16 motorized modules) with robust 3D-printed hinges, drive linkages, and hardware interfaces.
- **Parametric & Maintainable**: Built programmatically using parametric CAD scripts driven by a single configuration source, allowing seamless scaling, tolerance adjustment, and automated export.

## Core Mechanical Modules & Components

1. **Motorized Module Panel**:
   - Active folding panel incorporating integrated mounting brackets for standard high-torque PWM servos (e.g., MG996R).
   - Features drive shaft/horn couplers and heavy-duty hinge knuckle joints to articulate panels from 0° (flat rest) to 180° (flipped fold position).

2. **Follower Module Panel**:
   - Passive hinged panel attached to motorized or adjacent base panels.
   - Provides extended surface area for folding larger garments while articulating smoothly during folding cycles.

3. **Base Module Panel**:
   - Stationary structural chassis panel forming the rigid grid foundation.
   - Houses inter-panel connectors, wire routing channels, and table-gripping rubber foot pads.

4. **Interface & Enclosure Module**:
   - Control pad housing integrating 4 physical tactile buttons, status LED diffusers, and cable management.
   - Protective enclosure for the dual internal circuit boards: ESP32 microcontroller board, PCA9685 16-channel servo driver board, and power distribution terminals.

5. **Kinematic Linkages & Hardware Interfaces**:
   - Custom 3D-printable hinge pins, servo horn drive adapters, and panel coupler links.

## Reference System Configuration

Standard 4×3 Garment Folding Grid Assembly:
- **Grid Layout**: 4 rows × 3 columns of modular panels forming a flat folding table for garments (t-shirts, towels, trousers).
- **Actuation**: Parallel servo actuation capable of folding garments in 8–12 seconds per cycle.
- **Enclosure & Control**: Integrated ESP32 + PCA9685 dual-board controller housing with front-accessible physical 4-button and status LED interface pad.

## Target Audience & Use Case

Makers, STEM educators, and robotics enthusiasts building an affordable ($80–$150 total BOM), open-source automated laundry folding machine using standard FDM 3D printing and off-the-shelf electronics.

## Mechanical Success Criteria

- **Zero Geometric Errors**: 100% of exported STL files pass manifold topology checks (zero non-manifold edges, self-intersections, or open boundaries).
- **Interference-Free Kinematics**: All moving panel hinges and drive linkages achieve full 0° to 180° rotation without interference or binding.
- **Visual & Analytical Validation**: 100% of parts and assembly models pass visual, clearance, and kinematic validation.
- **Parametric Consistency**: Geometry builds cleanly across default (256 mm) and scaled (180 mm) build plate targets.
- **Automated Delivery**: Clean STEP (AP214) and binary STL file sets generated headlessly for slicing and assembly documentation.
