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

## Task Group 2: Modular Circular Servo Horn Drive Adapter (`motorized_servo_adapter.py`)
1. Model the $\varnothing 20.0\text{ mm}$ circular flange disk of $7.5\text{ mm}$ thickness spanning $Y \in [156.3, 163.8\text{ mm}]$ centered at $(X=0, Z_{pivot}=15.0\text{ mm})$.
2. Model 4x M2/M2.5 screw through-holes ($\varnothing 2.5\text{ mm}$) in a $90^\circ$ cross on $\varnothing 14.0\text{ mm}$ bolt circle for bolting directly to the MG996R round horn disk.
3. Model central $\varnothing 8.0\text{ mm} \times 2.0\text{ mm}$ rear horn boss / screw head relief pocket.
4. Model male 45° diamond tapered square drive peg ($6.35 \to 5.90\text{ mm}$, $0.35\text{ mm}$ corner-relief clip, $18.3\text{ mm}$ total length extending along $-Y$ from $Y = 156.3\text{ mm}$ to $138.0\text{ mm}$: $6.3\text{ mm}$ straight knuckle span + $12.0\text{ mm}$ tapered engagement inside the flap socket) with $1.2\text{ mm} \times 45^\circ$ self-aligning nose chamfer.
5. Implement headless STEP and STL export in `construct_motorized_servo_adapter()`.

---

## Task Group 3: Symmetrical Dual-Socket Active Folding Flap (`motorized_flap.py`)
1. Model the full-size folding flap paddle body ($219.0 \times 219.5 \times 2.4\text{ mm}$) resting directly on frame landing rails ($Z = 15.0$ to $17.4\text{ mm}$).
2. Model the top-left servo clearance corner relief notch ($45.0 \times 55.0\text{ mm}$) providing collision-free rotation around the motor bay across full $0^\circ \to 180^\circ$ swing.
3. Model integrated continuous solid-core drive axle ($\varnothing 12.8\text{ mm}$) along $X = 0$ spanning $Y = 18.0$ to $142.5\text{ mm}$, centered at $Z_{pivot} = 15.0\text{ mm}$.
4. Model **Driven Top End** with standardized $6.50\text{ mm}$ 45° diamond female square torque socket ($14.0\text{ mm}$ deep, `SQUARE_DRIVE_SOCKET_DEPTH = 14.00`, with $0.8\text{ mm} \times 45^\circ$ entry bevel) receiving the `motorized_servo_adapter` tapered square peg.
5. Model **Output Bottom End** with standardized $6.50\text{ mm}$ 45° diamond female square torque socket ($14.0\text{ mm}$ deep, `SQUARE_DRIVE_SOCKET_DEPTH = 14.00`, with $0.8\text{ mm} \times 45^\circ$ entry bevel) transmitting torque down the column via `drive_coupler`.
6. Model multi-tiered organic circular cutouts (~45% mass reduction), $0.6\text{ mm}$ diamond micro-grip knurling texture keeping the hinge neck strip ($X \in [0.0, 11.9\text{ mm}]$) $100\%$ solid $2.4\text{ mm}$ un-grooved, and $1.2\text{ mm}$ perimeter shadow bevel.
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
1. Assemble Motorized Frame (Gold), Motorized Flap (Red), Servo Cover (Purple), 2x Frame Joiners (Blue), Drive Coupler Pin (Yellow), Servo Drive Adapter (Orange), and MG996R Servo CAD reference model (Cyan).
2. Validate kinematic $0^\circ \to 90^\circ \to 180^\circ$ swing with zero collision (`0.00000 mm³` overlap).
3. Export `motorized_assembly.step` and `motorized_assembly.stl`.
