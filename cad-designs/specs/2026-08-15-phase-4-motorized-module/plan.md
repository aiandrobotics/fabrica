# Plan — Phase 4: Active Motorized Module

Implementation plan for the Active Motorized Module of the Fabrica Cloth Folding Robot, strictly aligned with `cad-designs/specs/roadmap.md`, `cad-designs/specs/tech-stack.md`, and reference architecture images (`specs/reference-images/motorized-module.png` and `3d-overview.png`).

---

## Task Group 1: Active Motorized Chassis Frame (`motorized_frame.py`)
1. Model the 4-sided outer chassis ($240.0 \times 240.0 \times 15.0\text{ mm}$) with $15.0\text{ mm}$ rigid outer perimeter rails, open-bottom interior cavity saving ~120g PLA, and $3.0\text{ mm}$ outer walls.
2. Model the integrated 4th left stiffener tie-bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$) with a Clean Solid Continuous Through-Dovetail Joint at $Y = 120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $0.25\text{ mm}$ clearance) and $3.0\text{ mm}$ continuous outer solid walls on both sides for 100% flush rotational clearance ($Z \le 3.0\text{ mm}$).
3. Model the dual $100\%$ solid $360^\circ$ closed cylindrical bearing knuckle tunnels centered at $Z = 8.0\text{ mm}$ with $1.5\text{ mm}$ ground clearance:
   - Top knuckle at $Y = 240\text{ mm}$ ($\varnothing 13.5\text{ mm}$ inner bore, $0.25\text{ mm}$ radial clearance) integrated with the motor mounting boss.
   - Bottom knuckle at $Y = 0\text{ mm}$ ($\varnothing 13.5\text{ mm}$ inner bore, $0.25\text{ mm}$ radial clearance).
   - C1-continuous concave blend ramps ($R_f = 12.0\text{ mm}$) smoothly transitioning knuckle barrels into the $Z = 15.0\text{ mm}$ frame deck.
4. Model the reinforced MG996R standard metal-gear servo mounting pocket at top-left ($Y \in [190, 240\text{ mm}]$) with:
   - $40.5 \times 20.0 \times 36.0\text{ mm}$ motor body cavity.
   - 4x M3 ($R=2.0\text{ mm}$) mounting screw bosses spaced at $48.0 \times 10.0\text{ mm}$.
   - $1.5\text{ mm}$ filleted wire conduit routing channels and zip-tie strain relief anchoring saddles.
   - Dual female snap-latch retention notches for toolless cover engagement.
5. Model 3x silent-flip TPU bumper slots ($1.5\text{ mm}$ recessed depth) along top landing rails.
6. Model 3-wall true open-top sliding female dovetail joiner sockets with $3.0\text{ mm}$ floor drop stops and $\varnothing 6.0\text{ mm}$ through-floor push-out access holes.
7. Model 4x bottom anti-slip rubber foot sockets ($\varnothing 12.0 \times 2.0\text{ mm}$) and $0.4\text{ mm}$ bottom Elephant's Foot relief chamfers.
8. Implement headless STEP and STL export in `construct_motorized_frame()`.

---

## Task Group 2: Monolithic Active Folding Flap (`active_flap.py`)
1. Model the full-size folding flap paddle body ($239.0 \times 238.0 \times 2.4\text{ mm}$) resting directly on frame landing rails ($Z = 15.0$ to $17.4\text{ mm}$).
2. Model the top-left servo clearance corner relief notch ($46.0 \times 26.0\text{ mm}$) providing collision-free rotation around the servo mounting bay and snap cover across full $0^\circ \to 180^\circ$ swing.
3. Model integrated continuous full-length $\varnothing 13.0\text{ mm}$ solid-core drive axle ($Y = 0$ to $240\text{ mm}$, centered at $X = 0, Z = 8.0\text{ mm}$) with bottom reinforcing fillet gusset.
4. Model the **Driven End ($Y = 240\text{ mm}$)**:
   - Integrated press-fit 25T standard metal servo horn cylindrical socket ($\varnothing 18.2 \times 3.0\text{ mm}$ outer boss, $\varnothing 6.0\text{ mm}$ spline receiver with $0.2\text{ mm}$ press-fit clearance).
   - Coaxial $\varnothing 3.2\text{ mm}$ M3 central retention screw through-hole with $\varnothing 6.0 \times 2.0\text{ mm}$ screw head counterbore for rigid mechanical lock to servo output spline.
5. Model the **Output End ($Y = 0\text{ mm}$)**:
   - Standardized $8.0\text{ mm}$ female hex torque drive socket ($12.0\text{ mm}$ deep) to transmit column torque to the Follower Module below via `hex_drive_coupler.py`.
6. Model multi-tiered organic gradient circular weight-reduction cutouts (~45% mass reduction, target blade weight $\le 75\text{g}$) matching reference visuals to minimize rotational inertia on the servo.
7. Model $1.2\text{ mm}$ recessed perimeter accent shadow bevel.
8. Model $0.6\text{ mm}$ diamond micro-grip knurling texture on the top garment-contacting face.
9. Model $0.8\text{ mm}$ hole and edge chamfers.
10. Implement headless STEP and STL export in `construct_active_flap()`.

---

## Task Group 3: Toolless Snap-Latch Servo Cover (`servo_cover.py`)
1. Model the low-profile protective motor enclosure shell ($48.0 \times 25.0 \times 12.0\text{ mm}$) contouring flush with the $Z = 15.0\text{ mm}$ frame deck.
2. Model dual cantilevered flexible snap-latch tabs with $0.4\text{ mm}$ retention detents mating into the frame mounting bay.
3. Model cable routing notch with smooth $1.5\text{ mm}$ bend radius for 3-wire servo lead exit.
4. Model passive convection ventilation cooling gills above the servo motor case.
5. Implement headless STEP and STL export in `construct_servo_cover()`.

---

## Task Group 4: Motorized Sub-Assembly & Kinematics (`assembly_motorized_module.py`)
1. Assemble Motorized Chassis Frame (Yellow), Monolithic Active Flap (Red), Snap-Latch Servo Cover (Black), Frame Joiners (Blue), and Hex Coupler Pin (Purple).
2. Position the active flap seated inside the frame with drive axle rotating smoothly in closed knuckles.
3. Validate kinematic $0^\circ \to 90^\circ \to 180^\circ$ full swing over onto the center base panel with zero collision (`0.00000 mm³` overlap).
4. Verify torque transfer alignment from servo horn socket at $Y = 240\text{ mm}$ through the active flap axle to the hex output coupler at $Y = 0\text{ mm}$.
5. Implement headless STEP and STL export in `construct_assembly_motorized_module()`.
