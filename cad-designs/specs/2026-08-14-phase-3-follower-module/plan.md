# Plan — Phase 3: Passive Follower Module

Implementation plan for the Passive Follower Module of the Fabrica Cloth Folding Robot, strictly aligned with `specs/reference-images/follower-module.png` and `3d-overview.png`.

---

## Task Group 1: Passive Follower Frame (`follower_frame.py`)
1. Model the 4-sided chassis ($240.0 \times 240.0 \times 15.0\text{ mm}$) with $15.0\text{ mm}$ perimeter rails, open-bottom interior, and integrated 4th stiffener tie-bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$).
2. Model the dual $360^\circ$ closed cylindrical bearing knuckle tunnels ($\varnothing 13.5\text{ mm}$) at top ($Y = 240\text{ mm}$) and bottom ($Y = 0\text{ mm}$) centered at $Z = 8.0\text{ mm}$.
3. Model C1-continuous tangent concave blend ramps ($R_f = 12.0\text{ mm}$) for seamless knuckle-to-deck flow.
4. Model the Clean Solid Continuous Through-Dovetail Joint at $Y = 120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $0.25\text{ mm}$ clearance) with $3.0\text{ mm}$ solid continuous outer walls on both sides.
5. Model 3x silent-flip TPU bumper slots ($1.5\text{ mm}$ recessed depth) along the top landing rail.
6. Model 3-wall true open-top sliding female dovetail sockets with $3.0\text{ mm}$ floor drop stops and $\varnothing 6.0\text{ mm}$ push-out access holes for bridge joiners (`frame_joiner.py`).
7. Model 4x bottom anti-slip rubber foot sockets ($\varnothing 12.0 \times 2.0\text{ mm}$) and $0.4\text{ mm}$ bottom Elephant's Foot relief chamfers.
8. Implement headless STEP and STL export.

---

## Task Group 2: Full-Size Follower Flap Panel (`follower_flap.py`)
1. Model the full-size folding flap paddle body ($239.0 \times 238.0 \times 2.4\text{ mm}$) resting directly on frame landing rails ($Z = 15.0$ to $17.4\text{ mm}$).
2. Model integrated continuous full-length $\varnothing 13.0\text{ mm}$ solid-core drive axle ($Y = 0$ to $240\text{ mm}$, centered at $X = 0, Z = 8.0\text{ mm}$) with bottom reinforcing fillet gusset.
3. Model dual symmetrical $8.0\text{ mm}$ female hex torque drive sockets ($12.0\text{ mm}$ deep) at top and bottom ends.
4. Model multi-tiered organic gradient circular weight-reduction cutouts (~45% mass reduction, target weight $\le 80\text{g}$) matching reference visuals.
5. Model $1.2\text{ mm}$ recessed perimeter accent shadow bevel.
6. Model $0.6\text{ mm}$ diamond micro-grip knurling texture on the top garment face.
7. Model $0.8\text{ mm}$ hole and edge chamfers.
8. Implement headless STEP and STL export.

---

## Task Group 3: Modular Hex Drive Coupler Pin (`hex_drive_coupler.py`)
1. Model double-male $8.0\text{ mm}$ hex torque coupler ($22.0\text{ mm}$ total length) with $7.7\text{ mm}$ Flat-to-Flat ($0.15\text{ mm}$ sliding fit clearance per side).
2. Model central $\varnothing 13.8 \times 1.0\text{ mm}$ locating stop collar and $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in chamfers.
3. Implement headless STEP and STL export.

---

## Task Group 4: Follower Sub-Assembly & Kinematics (`assembly.py`)
1. Assemble Follower Frame (Green), Full-Size Flap (Orange), Frame Joiners (Blue), and Compact Hex Drive Coupler (Purple).
2. Position the flap seated inside the frame with axle ends rotating in closed knuckles.
3. Validate kinematic $0^\circ \to 90^\circ \to 180^\circ$ full swing over onto the center base panel with zero collision (`0.00000 mm³` overlap).
4. Export `assembly.step` and `assembly.stl`.
