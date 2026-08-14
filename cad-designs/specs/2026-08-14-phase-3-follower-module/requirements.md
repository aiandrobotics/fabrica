# Requirements — Phase 3: Passive Follower Module

Requirements specification for the Passive Follower Module of the Fabrica Cloth Folding Robot, derived directly from system reference images (`follower-module.png`, `3d-overview.png`), `specs/mission.md`, and `cad-designs/specs/roadmap.md`.

---

## 1. System Context & Overview

In the Fabrica $4 \times 3$ modular folding grid:
- The **Passive Follower Module** is a $240.0 \times 240.0\text{ mm}$ square modular unit positioned in the outer grid columns (paired with adjacent motorized modules).
- It contains a full-size rotating folding flap ($230.0 \times 230.0 \times 4.0\text{ mm}$) that rests horizontally at $0^\circ$ inside a 3-sided U-frame chassis and swings a full $180^\circ$ arc over onto the central stationary base chassis to fold the garment.

```
       +=================[ 240mm Top Rail ]=================+
       | [Top Knuckle 360°]                                 | [Dovetail Socket]
       |                                                    |
       |                                                    |
       |  ===============================================   |
       |  |                                             |   |
240mm  |  |           Full-Size Follower Flap           |   | 240mm Outer Rail
Hinge  |  |           (230 x 230 x 4.0 mm)              |   | [Dovetail Socket]
Axis   |  |     [Organic Gradient Circular Cutouts]     |   |
       |  |                                             |   |
       |  ===============================================   |
       |                                                    |
       | [Bottom C-Snap]                                    | [Dovetail Socket]
       +================[ 240mm Bottom Rail ]===============+
                     (Open Inward Swing Side)
```

---

## 2. Component Specifications

### 2.1 Follower Outer Chassis Frame (`part_02_follower_frame.py`)
- **Overall Dimensions**: $240.0\text{ mm} \text{ (W)} \times 240.0\text{ mm} \text{ (H)} \times 15.0\text{ mm} \text{ (T)}$.
- **3-Sided U-Frame Geometry**:
  - Top rail ($Y = 240\text{ mm}$), bottom rail ($Y = 0$), and outer side rail ($X = 240\text{ mm}$).
  - Rail wall width: $15.0\text{ mm}$; bottom shell floor: $3.0\text{ mm}$.
  - Open inner side ($X = 0$) allowing the flap to swing unobstructed into the center base module across the $0^\circ \to 180^\circ$ range.
- **Hinge Pivot Knuckles (Left Rail $X = 0$)**:
  - **Top Knuckle ($Y = 240\text{ mm}$)**: $360^\circ$ closed cylindrical bearing bore ($\varnothing 5.6\text{ mm}$, providing $+0.3\text{ mm}$ radial rotating clearance around the $\varnothing 5.0\text{ mm}$ male pin).
  - **Bottom Knuckle ($Y = 0$)**: Flex C-snap bearing socket ($\varnothing 5.6\text{ mm}$) with a $0.5\text{ mm}$ lead-in entry funnel and retention detent, enabling toolless downward snap-in without bending or delaminating 3D-printed pin layers.
- **TPU Landing Dampers**: $1.5\text{ mm}$ recessed pockets on the inner floor ledge to cushion the flap on return.
- **True Sliding Dovetail System (`part_10_frame_joiner.py`)**: Symmetrical double flared dovetail key ($12.0\text{ mm}$ neck flaring to $18.0\text{ mm}$ at $12.0\text{ mm}$ depth with $0.15\text{ mm}$ sliding clearance) that drops in vertically from the top, physically locking adjacent modules together with zero horizontal pull-apart play and high bending moment resistance.
- **3-Servo High-Capacity Wire Raceway**: Continuous $6.8\text{ mm} \times 8.6\text{ mm}$ filleted conduit through the joiner bridge to comfortably route 3 full servo motor harnesses (9 wires + connectors) with zero binding.
- **Modular Dovetail Sockets**: 3-wall matching flared female dovetail sockets on the U-frame perimeter.
- **Cable Management**: $1.5\text{ mm}$ filleted wire pass-through ports and under-frame routing clips along perimeter rails.
- **Poka-Yoke & Relief**: $0.5\text{ mm}$ debossed `"FRONT ➔"` directional arrow and $0.4\text{ mm}$ Elephant's Foot bed relief chamfers.

---

### 2.2 Follower Folding Flap (`part_03_follower_flap.py`)
- **Overall Dimensions**: $230.0\text{ mm} \times 230.0\text{ mm} \times 4.0\text{ mm}$ (sized with $5.0\text{ mm}$ clearance to U-frame inner perimeter).
- **Integrated Male Hinge Pivot Pins**:
  - Coaxial top and bottom male pivot pins ($\varnothing 5.0\text{ mm} \times 8.0\text{ mm}$) located at $(X = 0, Y = 0)$ and $(X = 0, Y = 230\text{ mm})$.
  - $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in cone chamfers.
- **Organic Gradient Circular Cutouts (~45% Mass Reduction)**:
  - Multi-tiered circular cutouts (ranging from $\varnothing 12\text{ mm}$ to $\varnothing 34\text{ mm}$) distributed across the paddle face matching reference images `follower-module.png` and `3d-overview.png`.
  - Target flap mass $\le 80\text{g}$ to minimize rotational inertia during rapid garment flips.
  - $0.8\text{ mm}$ chamfers on all cutout edges.
- **Dual-Tone Accent Bevel**: $1.2\text{ mm}$ recessed perimeter shadow bevel along top perimeter edges.
- **Diamond Micro-Grip Texture**: $0.6\text{ mm}$ debossed diamond knurling pattern across the top garment-contact face to prevent cloth slippage.

---

### 2.3 Follower Module Sub-Assembly (`assembly_follower_module.py`)
- **Components**:
  1. Follower Frame (Green `#2ecc71`).
  2. Follower Flap (Orange `#e67e22`) mated via toolless Pin-Slide & Snap into the top bore and bottom C-snap.
  3. 2× $20\text{ mm}$ Flush Bridge Frame Joiners (Blue `#3498db`) mounted in outer frame sockets.
- **Kinematic Travel Verification**:
  - Unobstructed $0^\circ \text{ (flat rest)} \to 90^\circ \text{ (vertical)} \to 180^\circ \text{ (folded onto center base module)}$ sweep.
  - Zero collision (`overlap_volume_mm3 <= 0.001 mm³`) between flap and U-frame throughout the rotation arc.

---

## 3. Constraints & FDM Best Practices
- **100% Supportless Printing**: All parts print flat on standard $\ge 256 \times 256\text{ mm}$ build plates with zero supports.
- **Parametric Consistency**: All dimensions strictly governed by `params.py` (`SCALE = 1.0`).
- **Layer Line Strength**: Flap hinge pins print horizontally or with generous fillet transitions to prevent layer shearing.

---

## 4. Acceptance Criteria
- [ ] `./run.sh export_all` passes with exit code `0` and generates valid STEP/STL files.
- [ ] Visual inspection matches `specs/reference-images/follower-module.png` and `3d-overview.png`.
- [ ] Kinematic rotation $0^\circ \to 180^\circ$ has zero interference with frame rails.
