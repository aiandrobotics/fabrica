# Requirements — Phase 3: Passive Follower Module

Requirements specification for the Passive Follower Module of the Fabrica Cloth Folding Robot, updated with **Heavy-Duty $\varnothing 13\text{ mm}$ Drive Axles**, **Standardized $8.0\text{ mm}$ Hex Torque Couplers**, and **4-Sided Rigid Chassis with Clean Solid Through-Dovetail Stiffener Joint**.

---

## 1. System Context & Overview

In the Fabrica $4 \times 3$ modular folding grid:
- The **Passive Follower Module** ($240.0 \times 240.0\text{ mm}$) is positioned in the outer grid columns directly below the Motorized Module (Row 1).
- It contains a full-size rotating folding flap ($239.0 \times 238.0 \times 2.4\text{ mm}$) integrated with a heavy-duty continuous $\varnothing 13.0\text{ mm}$ drive axle.
- **Synchronous Column Torque Transmission**: The drive axle has standardized torque couplers on both ends:
  - **Top End**: $8.0\text{ mm}$ Hex Socket to receive rotational torque from the module above (Motorized Module or Follower Module).
  - **Bottom End**: $8.0\text{ mm}$ Hex Socket connected via the double-male **Part 11 Hex Drive Coupler Pin** to transmit torque downward to the next Follower Module in the column.
  - When the single servo motor in Row 1 rotates, **all flaps in that column rotate together in unison**.

```
                    [Motorized / Follower Module Above]
                                     │
                          ▼ (Top 8.0mm Hex Socket)
        +=================[ 240mm Top Rail ]=================+
        | [Ø13.5mm Top Bearing Knuckle 360°]                 | [Dovetail Socket]
        |                                                    |
        |  ===============================================   |
        |  |                                             |   |
240mm   |  |           Full-Size Follower Flap           |   | 240mm Outer Rail
Hinge   |  |           (239 x 238 x 2.4 mm)              |   | [Open-Top Dovetail]
Axis    |  |     [Organic Gradient Circular Cutouts]     |   |
(Z=8mm) |  |                                             |   |
        |  ===============================================   |
        |                                                    |
        | [Ø13.5mm Bottom Bearing Knuckle 360°]              | [Dovetail Socket]
        +================[ 240mm Bottom Rail ]===============+
                          ▲ (Bottom 8.0mm Hex Socket + Part 11 Pin)
                                     │
                      [Next Follower Module Below]
```

---

## 2. Component Specifications

### 2.1 Follower Outer Chassis Frame (`follower_frame.py`)
- **Overall Dimensions**: $240.0\text{ mm} \text{ (W)} \times 240.0\text{ mm} \text{ (H)} \times 15.0\text{ mm} \text{ (T)}$.
- **4-Sided Rigid Chassis Geometry**:
  - Top rail ($Y = 240\text{ mm}$), bottom rail ($Y = 0$), and outer side rail ($X = 240\text{ mm}$).
  - Rail wall width: $15.0\text{ mm}$; bottom shell floor: $3.0\text{ mm}$; open-bottom center cavity saving ~120g PLA.
  - **4th Left Stiffener Tie-Bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$)**:
    - Anchors the front and back hinge knuckle barrels to prevent outward knuckle splay under high hinge torque.
    - Features a **Clean Solid Continuous Through-Dovetail Joint** at $Y = 120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $0.25\text{ mm}$ clearance).
    - $3.0\text{ mm}$ solid continuous outer walls on both the left ($X \in [11, 14\text{ mm}]$) and right ($X \in [22, 25\text{ mm}]$) sides.
    - $100\%$ flush at $Z = 3.0\text{ mm}$, providing $100\%$ kinematic clearance for $180^\circ$ flap rotation.
    - Prints $100\%$ flat on bed with zero supports, zero internal slits, and zero floating geometry.
- **Dual Hinge Pivot Knuckles (Left Rail $X = 0$)**:
  - **Hinge Center Axis**: Centered at $Z = 8.0\text{ mm}$, providing **$1.5\text{ mm}$ Ground Clearance** beneath the $\varnothing 13.0\text{ mm}$ solid drive axle ($Z \in [1.5, 14.5\text{ mm}]$).
  - **Dual 100% Solid 360° Closed Knuckle Tunnels**:
    - **Top Knuckle ($Y \in [225, 240\text{ mm}]$)**: $360^\circ$ continuous solid cylindrical bearing tunnel ($\varnothing 13.5\text{ mm}$, $0.25\text{ mm}$ radial clearance).
    - **Bottom Knuckle ($Y \in [0, 15\text{ mm}]$)**: $360^\circ$ continuous solid cylindrical bearing tunnel ($\varnothing 13.5\text{ mm}$, $0.25\text{ mm}$ radial clearance).
    - **C1-Continuous Concave Blend Ramps**: Smooth $R_f = 12.0\text{ mm}$ tangent concave filleted ramps transitioning seamlessly from $\varnothing 19.0\text{ mm}$ knuckle barrels into the $Z = 15.0\text{ mm}$ frame top deck.
  - **100% Planar Flat Underside**: Both knuckles trimmed coplanar at $Z = 0.0\text{ mm}$ for zero-support 3D printing and rock-solid tabletop stability.
- **TPU Landing Dampers**: 3x $1.5\text{ mm}$ recessed silent-flip TPU bumper slots along the top landing rail at $X = 232.5\text{ mm}$.
- **True Sliding Dovetail System (`frame_joiner.py`)**: Symmetrical double flared dovetail key ($8.0\text{ mm}$ neck flaring to $12.0\text{ mm}$ at $12.0\text{ mm}$ depth with $0.15\text{ mm}$ sliding clearance) that drops in vertically from the top, physically locking adjacent modules together with zero horizontal pull-apart play.
- **Through-Floor Access Holes**: $\varnothing 6.0\text{ mm}$ push-out access holes through the bottom floor under each dovetail socket for toolless finger disassembly.
- **Anti-Slip Rubber Feet**: 4x bottom corner sockets ($\varnothing 12.0 \times 2.0\text{ mm}$) for press-fitting anti-slip silicone/rubber grip pads.
- **Relief Chamfers**: $0.4\text{ mm}$ bottom Elephant's Foot relief chamfers along outer bed-contacting edges.

---

## 2.2 Follower Folding Flap (`follower_flap.py`)
- **Overall Dimensions**: $239.0\text{ mm} \text{ (W)} \times 238.0\text{ mm} \text{ (L)} \times 2.4\text{ mm} \text{ (T)}$ full-deck overlapping paddle fused to a continuous $\varnothing 13.0\text{ mm}$ solid-core drive axle.
- **Full-Deck 3-Rail Overlap ("Lid" Architecture)**:
  - Spans across the entire module footprint, completely covering the 3 chassis frame rails (Bottom, Top, Right).
  - Rests directly on top of frame rails ($Z = 15.0$ to $17.4\text{ mm}$).
  - **Zero Fabric Catch Points**: Eliminates all perimeter seam gaps so thin garments and loose threads can never slip between flap and frame.
  - **Rock-Solid $0^\circ$ Home Hard Stop**: Prevents flap sagging or over-travel under heavy garment loads.
  - **Optimized 2.4mm Blade Thickness**: High flexural stiffness (12 solid layers) while keeping moving blade mass light ($\approx 75\text{g}$).
- **Heavy-Duty Continuous Solid-Core Drive Axle ($\varnothing 13.0\text{ mm}$)**:
  - Spans the hinge axis at $(X = 0, Z = 8.0\text{ mm})$ across the full $240.0\text{ mm}$ length.
  - **100% Solid Central Core**: Maximizes torsional rigidity and eliminates torsional twist when transmitting motor torque across multiple follower stages.
  - Hollow hex connector cavities located exclusively at the top and bottom ends ($12.0\text{ mm}$ deep).
- **Bottom Reinforcing Fillet Gusset**: Smooth curved structural transition from axle underside up to the blade floor providing $3\times$ torsional load distribution.
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

## 2.3 Modular Double-Male Hex Drive Coupler Pin (`hex_drive_coupler.py`)
- **Overall Dimensions**: $8.0\text{ mm} \text{ (Hex)} \times 22.0\text{ mm} \text{ (Total Length)}$.
- **Double-Ended Hex Keys**: $7.7\text{ mm}$ Flat-to-Flat ($0.15\text{ mm}$ sliding fit clearance per side) with $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in entry chamfers on both ends.
- **Center Stop Flange**: $\varnothing 13.8\text{ mm} \times 1.0\text{ mm}$ collar that keeps the coupler centered across the module seam.
- **Through-Hole**: $\varnothing 3.2\text{ mm}$ central bore for mass reduction or optional M3 reinforcing tension rod.
- **Modular Wear Component**: Easily 3D printed and replaced in seconds without replacing the entire flap.

---

## 2.4 Follower Module Sub-Assembly (`assembly.py`)
- **Components**:
  1. Follower Frame (Green `#2ecc71`).
  2. Follower Flap with $\varnothing 13\text{ mm}$ Axle (Orange `#e67e22`).
  3. 2× Frame Joiners (Blue `#3498db`) mounted in outer frame sockets.
  4. 1× Hex Drive Coupler (Purple `#9b59b6`) mated in axle hex socket.
- **Kinematic Travel Verification**:
  - Unobstructed $0^\circ \text{ (flat rest)} \to 90^\circ \text{ (vertical)} \to 180^\circ \text{ (folded onto center base module)}$ sweep.
  - Zero collision (`overlap_volume_mm3 == 0.00000 mm³`) between all mating pairs throughout the rotation arc.

---

## 3. Acceptance Criteria
- [x] `./run.sh export_all` passes with exit code `0` and generates valid STEP/STL files for all 6 models.
- [x] $\varnothing 13.0\text{ mm}$ drive axle rotates smoothly in $\varnothing 13.5\text{ mm}$ frame knuckles ($0.25\text{ mm}$ clearance).
- [x] Hex couplers ($8.0\text{ mm}$ Hex) engage with adjacent active and follower module drive shafts with zero angular backlash.
- [x] 4th wall dovetail joint has $3.0\text{ mm}$ solid continuous outer walls, zero floating slivers, and zero supports.
- [x] `check_interference` confirms `0.00000 mm³` overlap across all assembly pairs.
