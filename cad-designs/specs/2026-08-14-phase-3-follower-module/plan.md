# Plan — Phase 3: Passive Follower Module

Implementation plan for the Passive Follower Module of the Fabrica Cloth Folding Robot, comprising the Follower Outer Frame (`part_02_follower_frame.py`), the Follower Folding Flap (`part_03_follower_flap.py`), and the Follower Module Sub-Assembly (`assembly_follower_module.py`).

---

## Task Group 1: Passive Follower Frame (`part_02_follower_frame.py`)
1. Model the rigid U-frame outer geometry ($240.0 \times 240.0 \times 10.0\text{ mm}$) with $3.0\text{ mm}$ outer structural walls and recessed internal cavity.
2. Model top $360^\circ$ closed cylindrical bearing bore ($\varnothing 5.6\text{ mm}$) for captive axial pin retention.
3. Model bottom flex C-snap socket with $0.5\text{ mm}$ lead-in funnel allowing toolless downward snap insertion without delamination.
4. Model $1.5\text{ mm}$ recessed silent-flip TPU bumper landing pockets on inner ledge.
5. Model $0.4\text{ mm}$ bottom Elephant's Foot relief chamfers along outer bed perimeters.
6. Model $0.5\text{ mm}$ debossed Poka-Yoke directional alignment arrow (`"FRONT ➔"`) on the front wall.
7. Model $1.5\text{ mm}$ filleted internal wire pass-through ports with integrated zip-tie strain-relief loops.
8. Model 4-wall click-lock female dovetail sockets with $0.3\text{ mm}$ detent locking dimples.
9. Model integrated under-frame cable routing clips.
10. Implement headless STEP and STL export functions.

---

## Task Group 2: Follower Folding Flap (`part_03_follower_flap.py`)
1. Model rotating follower panel body ($232.0 \times 114.0 \times 4.0\text{ mm}$) with $1.0\text{ mm}$ perimeter flip clearance.
2. Model integrated top and bottom male hinge pivot pins ($\varnothing 5.0\text{ mm} \times 8.0\text{ mm}$) featuring $1.5\text{ mm}$ $45^\circ$ lead-in insertion chamfers.
3. Model gradient circular weight-reduction cutouts (~45% mass reduction, target panel weight $\le 80\text{g}$) to minimize inertia during folding.
4. Model $1.2\text{ mm}$ recessed perimeter accent bevel for dual-tone panel aesthetics.
5. Model $0.6\text{ mm}$ top micro-grip diamond knurling texture for garment traction.
6. Model $0.8\text{ mm}$ hole and edge chamfers across all weight-reduction cutouts.
7. Implement headless STEP and STL export functions.

---

## Task Group 3: Follower Sub-Assembly & Kinematics (`assembly_follower_module.py`)
1. Create programmatic sub-assembly combining Follower Frame (`part_02`), Follower Flap (`part_03`), and 2× Click-Lock Frame Joiners (`part_10`).
2. Assign distinct visual color coding: Green Frame (`#2ecc71`), Orange Flap (`#e67e22`), Blue Joiners (`#3498db`).
3. Model and verify the toolless "Pin-Slide & Snap" assembly kinematics:
   - Step 1: Slide top chamfered pin into the $360^\circ$ closed bore.
   - Step 2: Push bottom pin through the $0.5\text{ mm}$ funnel into the flex C-snap socket.
4. Verify $0^\circ \to 90^\circ \to 180^\circ$ continuous folding arc without frame or joiner collisions.
5. Implement headless assembly STEP and STL export.
