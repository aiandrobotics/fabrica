# Plan — Phase 3: Passive Follower Module

Implementation plan for the Passive Follower Module of the Fabrica Cloth Folding Robot, strictly aligned with `specs/reference-images/follower-module.png` and `3d-overview.png`.

---

## Task Group 1: Passive Follower U-Frame (`part_02_follower_frame.py`)
1. Model the 3-sided U-frame chassis ($240.0 \times 240.0 \times 15.0\text{ mm}$) with $15.0\text{ mm}$ perimeter rails, $3.0\text{ mm}$ bottom shell, and an open inner swing side.
2. Model the top hinge knuckle ($Y = 240\text{ mm}$) with a $360^\circ$ closed cylindrical bore ($\varnothing 5.6\text{ mm}$).
3. Model the bottom hinge knuckle ($Y = 0\text{ mm}$) with a flex C-snap socket ($\varnothing 5.6\text{ mm}$) and $0.5\text{ mm}$ lead-in entry funnel.
4. Model $1.5\text{ mm}$ recessed TPU bumper landing pockets on the inner floor ledge.
5. Model 3-wall female dovetail sockets for $20\text{ mm}$ bridge joiners (`part_10_frame_joiner.py`).
6. Model under-frame wire routing channels, $1.5\text{ mm}$ filleted wire ports, $0.5\text{ mm}$ debossed `"FRONT ➔"` Poka-Yoke arrow, and $0.4\text{ mm}$ Elephant's Foot relief.
7. Implement headless STEP and STL export.

---

## Task Group 2: Full-Size Follower Flap Panel (`part_03_follower_flap.py`)
1. Model the full-size folding flap paddle body ($230.0 \times 230.0 \times 4.0\text{ mm}$).
2. Model coaxial top and bottom male pivot pins ($\varnothing 5.0\text{ mm} \times 8.0\text{ mm}$) with $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in chamfers along the hinge edge.
3. Model the multi-tiered organic gradient circular weight-reduction cutouts (~45% mass reduction, target weight $\le 80\text{g}$) matching reference visuals.
4. Model $1.2\text{ mm}$ recessed perimeter accent shadow bevel.
5. Model $0.6\text{ mm}$ diamond micro-grip knurling texture on the top garment face.
6. Model $0.8\text{ mm}$ hole and edge chamfers.
7. Implement headless STEP and STL export.

---

## Task Group 3: Follower Sub-Assembly & Kinematics (`assembly_follower_module.py`)
1. Assemble Follower U-Frame (Green), Full-Size Flap (Orange), and $20\text{ mm}$ Bridge Joiners (Blue).
2. Position the flap seated inside the U-frame with pins mated inside the top bore and bottom C-snap.
3. Validate kinematic $0^\circ \to 90^\circ \to 180^\circ$ full swing over onto the center base panel with zero collision.
4. Export `assembly_follower_module.step` and `assembly_follower_module.stl`.
