# Plan — Phase 4: Active Motorized Module (Horizontal Drive & Modular Horn Adapter Architecture)

Implementation plan for the Active Motorized Module of the Fabrica Cloth Folding Robot, strictly aligned with `cad-designs/specs/roadmap.md`, `cad-designs/specs/tech-stack.md`, and reference technical drawings (`specs/reference-images/mg996r-servo.png`).

---

## Task Group 1: Active Motorized Chassis Frame (`motorized_frame.py`)
1. Model the 4-sided outer chassis ($240.0 \times 240.0 \times 15.0\text{ mm}$) with $15.0\text{ mm}$ rigid outer perimeter rails, open-bottom interior cavity, and 100% planar flat bottom trim at $Z = 0.0\text{ mm}$.
2. Model the continuous inner enclosure wall ($X \in [38.0, 48.0\text{ mm}], Y \in [185.0, 240.0\text{ mm}]$) completely sealing the motor bay from the central cavity.
3. Model the solid front mounting towers ($Y \in [185.0, 195.5\text{ mm}]$) with 4x M3 clearance through-holes ($\varnothing 3.4\text{ mm}$) centered at $(X = 34.95\text{ mm}, Z = 4.75 / 15.25\text{ mm})$ and $(X = -14.45\text{ mm}, Z = 4.75 / 15.25\text{ mm})$ with 4x captive hexagonal nut housings ($W_{af} = 5.8\text{ mm}$, depth $3.2\text{ mm}$) on the front face.
4. Model the rear slide-in slot ($Y = 240.0\text{ mm}$) with internal ear channels ($X \in [-17.5, 38.0\text{ mm}]$).
5. Model dual $100\%$ solid $360^\circ$ closed cylindrical bearing knuckle tunnels centered at $Z_{pivot} = 10.0\text{ mm}$ ($\varnothing 13.5\text{ mm}$ inner bore, $0.25\text{ mm}$ radial clearance) with C1-continuous concave blend ramps ($R_f = 12.0\text{ mm}$).
6. Model true open-top sliding female dovetails, TPU bumper slots, anti-slip foot sockets, and Elephant's Foot relief chamfers.
7. Implement headless STEP and STL export in `construct_motorized_frame()`.

---

## Task Group 2: Modular Circular Servo Horn Drive Adapter (`servo_drive_adapter.py`)
1. Model the $\varnothing 19.0\text{ mm}$ circular flange disk of $7.0\text{ mm}$ thickness spanning $Y \in [178.0, 185.0\text{ mm}]$ centered at $(X=0, Z=10.0\text{ mm})$.
2. Model 4x M2/M2.5 screw through-holes ($\varnothing 2.2\text{ mm}$) in a $90^\circ$ cross on $\varnothing 14.0\text{ mm}$ bolt circle for bolting directly to the MG996R round horn disk.
3. Model central $\varnothing 6.5\text{ mm}$ counterbore for screwdriver access to the M3 spline lock screw.
4. Model male 8.0mm hex drive peg ($7.7\text{ mm}$ flat-to-flat, $10.5\text{ mm}$ length extending along $-Y$ into the flap) with $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in chamfer.
5. Implement headless STEP and STL export in `construct_servo_drive_adapter()`.

---

## Task Group 3: Symmetrical Dual-Hex Active Folding Flap (`motorized_flap.py`)
1. Model the full-size folding flap paddle body ($239.0 \times 238.0 \times 2.4\text{ mm}$) resting directly on frame landing rails ($Z = 15.0$ to $17.4\text{ mm}$).
2. Model the top-left servo clearance corner relief notch ($45.0 \times 55.0\text{ mm}$) providing collision-free rotation around the motor bay across full $0^\circ \to 180^\circ$ swing.
3. Model integrated continuous solid-core drive axle ($\varnothing 12.9\text{ mm}$) along $X = 0$ spanning $Y = 0.5$ to $178.0\text{ mm}$, centered at $Z_{pivot} = 10.0\text{ mm}$.
4. Model **Driven Top End ($Y = 178.0\text{ mm}$)** with standardized $8.0\text{ mm}$ female hex torque socket ($10.5\text{ mm}$ deep) receiving the `servo_drive_adapter` male hex peg.
5. Model **Output Bottom End ($Y = 0.5\text{ mm}$)** with standardized $8.0\text{ mm}$ female hex torque socket ($10.5\text{ mm}$ deep) transmitting torque down the column via `hex_drive_coupler`.
6. Model multi-tiered organic circular cutouts (~45% mass reduction), $0.6\text{ mm}$ diamond micro-grip knurling texture, and $1.2\text{ mm}$ perimeter shadow bevel.
7. Implement headless STEP and STL export in `construct_motorized_flap()`.

---

## Task Group 4: Full Enclosure Slide-In Hood Cover (`motorized_servo_cover.py`)
1. Model top plate ($X \in [-17.0, 43.5\text{ mm}], Y \in [186.0, 240.0\text{ mm}], Z \in [15.0, 21.2\text{ mm}]$).
2. Model integrated rear face cap ($X \in [-17.0, 37.5\text{ mm}], Y \in [237.5, 240.0\text{ mm}], Z \in [0.0, 21.2\text{ mm}]$) that completely seals the rear slide-in opening.
3. Model lateral slide-in retention tongues engaging into frame side grooves.
4. Model internal hollow clearance pocket clearing the motor casing.
5. Implement headless STEP and STL export in `construct_motorized_servo_cover()`.

---

## Task Group 5: Motorized Sub-Assembly & Interference Verification (`motorized_assembly.py`)
1. Assemble Motorized Frame (Gold), Motorized Flap (Red), Servo Cover (Purple), 2x Frame Joiners (Blue), Hex Coupler Pin (Yellow), Servo Drive Adapter (Orange), and MG996R Servo CAD reference model (Cyan).
2. Validate kinematic $0^\circ \to 90^\circ \to 180^\circ$ swing with zero collision (`0.00000 mm³` overlap).
3. Export `motorized_assembly.step` and `motorized_assembly.stl`.
