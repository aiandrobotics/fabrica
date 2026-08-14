# Requirements — Phase 3: Passive Follower Module

Requirements specification for the Passive Follower Module of the Fabrica Cloth Folding Robot, updated with **Heavy-Duty $\varnothing 14\text{ mm}$ Drive Axles** and **Standardized $8.0\text{ mm}$ Hex Torque Couplers** for synchronous column folding.

---

## 1. System Context & Overview

In the Fabrica $4 \times 3$ modular folding grid:
- The **Passive Follower Module** ($240.0 \times 240.0\text{ mm}$) is positioned in the outer grid columns directly below the Motorized Module (Row 1).
- It contains a full-size rotating folding flap ($220.0 \times 208.0 \times 4.0\text{ mm}$) integrated with a heavy-duty continuous $\varnothing 14.0\text{ mm}$ drive axle.
- **Synchronous Column Torque Transmission**: The drive axle has standardized torque couplers on both ends:
  - **Top End**: $8.0\text{ mm}$ Hex Socket to receive rotational torque from the module above (Motorized Module or Follower Module).
  - **Bottom End**: $8.0\text{ mm}$ Male Hex Drive Peg to transmit torque downward to the next Follower Module in the column.
  - When the single servo motor in Row 1 rotates, **all flaps in that column rotate together in unison**.

```
                   [Motorized / Follower Module Above]
                                    │
                         ▼ (Top 8.0mm Hex Socket)
       +=================[ 240mm Top Rail ]=================+
       | [Ø14.6mm Top Bearing Knuckle 360°]                 | [Dovetail Socket]
       |                                                    |
       |  ===============================================   |
       |  |                                             |   |
240mm  |  |           Full-Size Follower Flap           |   | 240mm Outer Rail
Hinge  |  |           (220 x 208 x 4.0 mm)              |   | [Open-Top Dovetail]
Axis   |  |     [Organic Gradient Circular Cutouts]     |   |
       |  |                                             |   |
       |  ===============================================   |
       |                                                    |
       | [Ø14.6mm Bottom Flex C-Snap Knuckle]               | [Dovetail Socket]
       +================[ 240mm Bottom Rail ]===============+
                         ▲ (Bottom 8.0mm Hex Peg)
                                    │
                     [Next Follower Module Below]
```

---

## 2. Component Specifications

### 2.1 Follower Outer Chassis Frame (`part_02_follower_frame.py`)
- **Overall Dimensions**: $240.0\text{ mm} \text{ (W)} \times 240.0\text{ mm} \text{ (H)} \times 15.0\text{ mm} \text{ (T)}$.
- **3-Sided U-Frame Geometry**:
  - Top rail ($Y = 240\text{ mm}$), bottom rail ($Y = 0$), and outer side rail ($X = 240\text{ mm}$).
  - Rail wall width: $15.0\text{ mm}$; bottom shell floor: $3.0\text{ mm}$.
  - Open inner side ($X = 0$) allowing the flap to swing unobstructed across the $0^\circ \to 180^\circ$ range.
- **Heavy-Duty Hinge Pivot Knuckles (Left Rail $X = 0$)**:
  - Outer knuckle barrel diameter: $\varnothing 20.0\text{ mm}$.
  - **Top Knuckle ($Y = 225\text{ to }240\text{ mm}$)**: $360^\circ$ closed cylindrical bearing bore ($\varnothing 14.6\text{ mm}$, providing $+0.3\text{ mm}$ radial rotating clearance around the $\varnothing 14.0\text{ mm}$ axle).
  - **Bottom Knuckle ($Y = 0\text{ to }15\text{ mm}$)**: Flex C-snap bearing socket ($\varnothing 14.6\text{ mm}$) with a $1.0\text{ mm}$ lead-in entry funnel and retention detent, enabling toolless downward snap-in without bending or delaminating 3D-printed layers.
- **TPU Landing Dampers**: $1.5\text{ mm}$ recessed pockets on the inner floor ledge to cushion the flap on return.
- **True Sliding Dovetail System (`part_10_frame_joiner.py`)**: Symmetrical double flared dovetail key ($12.0\text{ mm}$ neck flaring to $18.0\text{ mm}$ at $12.0\text{ mm}$ depth with $0.15\text{ mm}$ sliding clearance) that drops in vertically from the top, physically locking adjacent modules together with zero horizontal pull-apart play and high bending moment resistance.
- **3-Servo High-Capacity Wire Raceway**: Continuous $6.8\text{ mm} \times 8.6\text{ mm}$ filleted conduit through the joiner bridge to comfortably route 3 full servo motor harnesses (9 wires + connectors) with zero binding.
- **Cable Management**: $1.5\text{ mm}$ filleted wire pass-through ports and under-frame routing clips along perimeter rails.
- **Poka-Yoke & Relief**: $0.5\text{ mm}$ debossed `"FRONT ➔"` directional arrow and $0.4\text{ mm}$ Elephant's Foot bed relief chamfers.

---

### 2.2 Follower Folding Flap (`part_03_follower_flap.py`)
- **Overall Dimensions**: $239.0\text{ mm} \text{ (W)} \times 238.0\text{ mm} \text{ (L)} \times 2.4\text{ mm} \text{ (T)}$ full-deck overlapping paddle fused to a continuous $\varnothing 14.0\text{ mm}$ tubular drive axle.
- **Full-Deck 3-Rail Overlap ("Lid" Architecture)**:
  - Spans across the entire module footprint ($X \in [0, 239.0\text{ mm}]$, $Y \in [1.0, 239.0\text{ mm}]$), completely covering the 3 chassis frame rails (Bottom, Top, Right).
  - Lands directly onto $2.4\text{ mm}$ recessed hard-stop ledges ($Z = 12.6\text{ mm}$) machined into the frame rails.
  - **Zero Fabric Catch Points**: Eliminates all perimeter seam gaps so thin garments and loose threads can never slip between flap and frame.
  - **Rock-Solid $0^\circ$ Home Hard Stop**: Prevents flap sagging or over-travel under heavy garment loads.
  - **Optimized 2.4mm Blade Thickness**: High flexural stiffness (12 solid layers) while keeping moving blade mass light ($\approx 75\text{g}$).
  - Top face sits flush at $Z = 15.0\text{ mm}$.
- **Heavy-Duty Continuous Solid-Core Drive Axle ($\varnothing 14.0\text{ mm}$)**:
  - Spans the hinge axis at $(X = 0, Z = 8.0\text{ mm})$ across the full $240.0\text{ mm}$ length.
  - **100% Solid Central Core ($Y = 12.0\text{ to }228.0\text{ mm}$)**: Maximizes torsional rigidity and eliminates torsional twist when transmitting motor torque across multiple follower stages.
  - Hollow hex connector cavities located exclusively at the top and bottom ends ($12.0\text{ mm}$ deep).
- **Bottom Reinforcing Fillet Gusset**: Smooth curved structural transition from axle underside ($Z = 5.0\text{ mm}$) up to the blade floor ($Z = 12.6\text{ mm}$) providing $3\times$ torsional load distribution.
- **Dual Symmetrical Female Hex Coupler Sockets**:
  - **Top End ($Y = 240\text{ mm}$)**: $8.0\text{ mm}$ Flat-to-Flat female hexagonal torque drive socket ($12.0\text{ mm}$ engagement depth in $-Y$).
  - **Bottom End ($Y = 0\text{ mm}$)**: Identical $8.0\text{ mm}$ Flat-to-Flat female hexagonal torque drive socket ($12.0\text{ mm}$ engagement depth in $+Y$).
  - **100% Flat 3D Printability**: Zero protruding male pegs, allowing the flap to print 100% flat on the bed with clean surface finishes.
- **Organic Gradient Circular Cutouts (~45% Mass Reduction)**:
  - Multi-tiered circular cutouts (ranging from $\varnothing 12\text{ mm}$ to $\varnothing 34\text{ mm}$) distributed across the paddle face matching reference images `follower-module.png` and `3d-overview.png`.
  - $0.8\text{ mm}$ chamfers on all cutout edges.
- **Dual-Tone Accent Bevel**: $1.2\text{ mm}$ recessed perimeter shadow bevel along top perimeter edges.
- **Diamond Micro-Grip Texture**: $0.6\text{ mm}$ debossed diamond knurling pattern across the top garment-contact face to prevent cloth slippage.

---

### 2.3 Modular Double-Male Hex Drive Coupler Pin (`part_11_hex_drive_coupler.py`)
- **Overall Dimensions**: $8.0\text{ mm} \text{ (Hex)} \times 22.0\text{ mm} \text{ (Total Length)}$.
- **Double-Ended Hex Keys**: $7.7\text{ mm}$ Flat-to-Flat ($0.15\text{ mm}$ sliding fit clearance per side) with $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in entry chamfers on both ends.
- **Center Stop Flange**: $\varnothing 13.8\text{ mm} \times 1.0\text{ mm}$ collar that keeps the coupler centered across the module seam.
- **Through-Hole**: $\varnothing 3.2\text{ mm}$ central bore for mass reduction or optional M3 reinforcing tension rod.
- **Modular Wear Component**: Easily 3D printed and replaced in seconds without replacing the entire flap.

---

### 2.3 Follower Module Sub-Assembly (`assembly_follower_module.py`)
- **Components**:
  1. Follower Frame (Green `#2ecc71`).
  2. Follower Flap with $\varnothing 14\text{ mm}$ Axle (Orange `#e67e22`) mated via toolless Pin-Slide & Snap into the top bore and bottom C-snap.
  3. 2× $20\text{ mm}$ Flush Bridge Frame Joiners (Blue `#3498db`) mounted in outer frame sockets.
- **Kinematic Travel Verification**:
  - Unobstructed $0^\circ \text{ (flat rest)} \to 90^\circ \text{ (vertical)} \to 180^\circ \text{ (folded onto center base module)}$ sweep.
  - Zero collision (`overlap_volume_mm3 <= 0.001 mm³`) between flap and U-frame throughout the rotation arc.

---

## 3. Acceptance Criteria
- [ ] `./run.sh export_all` passes with exit code `0` and generates valid STEP/STL files.
- [ ] $\varnothing 14.0\text{ mm}$ drive axle rotates smoothly in $\varnothing 14.6\text{ mm}$ frame knuckles ($0.3\text{ mm}$ clearance).
- [ ] Hex couplers ($8.0\text{ mm}$ Hex) engage with adjacent active and follower module drive shafts with zero angular backlash.
