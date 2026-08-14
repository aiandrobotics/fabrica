# Requirements — Phase 3: Passive Follower Module

Requirements specification for the Passive Follower Module of the Fabrica Cloth Folding Robot.

---

## Scope
1. **Follower Outer Frame (`part_02_follower_frame.py`)**: Passive U-shaped chassis frame holding the folding flap and interlocking with adjacent base and motorized modules in the $4 \times 3$ grid.
2. **Follower Folding Flap (`part_03_follower_flap.py`)**: Free-rotating cloth-folding paddle driven by garment motion and adjacent active flap pushers.
3. **Follower Module Assembly (`assembly_follower_module.py`)**: Sub-assembly integrating frame, rotating flap, and interlocking joiners with verified $0^\circ \to 180^\circ$ kinematic travel.

---

## Decisions & Feature Specifications

### 1. Pivot Hinge Architecture (Pin-Slide & C-Snap)
- **Top Pivot Interface**: $360^\circ$ closed cylindrical bore ($\varnothing 5.6\text{ mm}$, providing $+0.3\text{ mm}$ rotating clearance per side around the $\varnothing 5.0\text{ mm}$ pin).
- **Bottom Pivot Interface**: Flexible C-snap socket with a $0.5\text{ mm}$ lead-in entry funnel and retention detent, allowing toolless downward snap-in without putting bending stress on the 3D-printed pin layers.
- **Flap Hinge Pins**: Integrated top and bottom male pins ($\varnothing 5.0\text{ mm} \times 8.0\text{ mm}$) featuring $1.5\text{ mm} \times 45^\circ$ entry chamfers for self-aligning insertion.

### 2. Flap Panel Design & Weight Optimization
- **Panel Dimensions**: $232.0 \times 114.0 \times 4.0\text{ mm}$ with $1.0\text{ mm}$ radial clearance against frame cavity walls.
- **Gradient Circular Cutouts**: Progressive pattern of circular cutouts providing ~45% mass reduction (target flap mass $\le 80\text{g}$), drastically reducing rotational inertia during rapid garment flips.
- **Dual-Tone Accent Bevel**: $1.2\text{ mm}$ recessed perimeter shadow bevel along top edges for high-end product aesthetics.
- **Diamond Micro-Grip Texture**: $0.6\text{ mm}$ debossed diamond knurling pattern across the top garment-contact face to prevent cloth slippage during folding.

### 3. Chassis Interlocking & Cable Management
- **20.0 mm Inter-Module Bridge Gap (`MODULE_GAP`)**: $20.0\text{ mm}$ spacing between adjacent module frames providing bend relief for thick folded garments (hoodies, denim, towels), flap sweep clearance, and generous cable management.
- **20.0 mm Flush Bridge Joiners (`part_10_frame_joiner.py`)**: 3-axis symmetrical double dovetail joiner with a $20.0\text{ mm}$ central flush bridge body that spans between frames, preventing fabric from sagging into the inter-module gap.
- **High-Capacity Wire Raceway**: Continuous $5.8\text{ mm} \times 7.2\text{ mm}$ filleted conduit through the joiner bridge to pass pre-crimped 3-pin servo plugs and power harnesses.
- **Modular Dovetail Sockets**: 4-wall symmetrical female dovetail sockets with $0.3\text{ mm}$ detent locking dimples matching `part_10_frame_joiner.py`.
- **Under-Frame Cable Clips**: Integrated $1.5\text{ mm}$ filleted wire pass-through ports and under-chassis cable routing clips for secure wire harness distribution.
- **TPU Dampers**: $1.5\text{ mm}$ recessed landing pockets for silent flap rest during high-speed return cycles.
- **Poka-Yoke Alignment**: $0.5\text{ mm}$ debossed directional arrow (`"FRONT ➔"`) on the front face.
- **Elephant's Foot Relief**: $0.4\text{ mm}$ chamfer along bottom bed edges.

---

## Constraints
- **FDM Printability**: 100% supportless printing across all components.
- **Parametric Single Source of Truth**: All dimensions multiplied by `params.SCALE` and referenced directly from `params.py`.
- **Layer Orientation Integrity**: Hinge pin insertion must not shear PLA layer lines during snap assembly.

---

## Non-Goals
- Active motorization (MG996R servo mounting is exclusive to Phase 4 Motorized Modules).
- Foldable hinge inter-module links in V1 (rigid inter-module dovetail joiners used).
- Integrated button controls (exclusive to Phase 5 Interface Module).

---

## Context & Relationships
- Mates with **Base Module** (`part_01_base_module.py`) and **Motorized Module** (`part_04_motorized_frame.py`) via **Click-Lock Frame Joiners** (`part_10_frame_joiner.py`).
- Forms columns 1 and 3 of the standard $4 \times 3$ folding grid layout.
