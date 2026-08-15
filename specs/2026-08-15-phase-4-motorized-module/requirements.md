# Requirements — Phase 4: Active Motorized Module

Requirements specification for the Active Motorized Module of the Fabrica Cloth Folding Robot, featuring **Integrated MG996R Servo Bay**, **Heavy-Duty $\varnothing 13\text{ mm}$ Monolithic Active Flap Axle**, **Direct Press-Fit 25T Metal Servo Horn Socket with M3 Retention**, **Toolless Snap-Latch Motor Cover**, and **Synchronous Column Hex Torque Transmission**.

---

## 1. System Context & Overview

In the Fabrica $4 \times 3$ modular folding grid:
- The **Active Motorized Module** ($240.0 \times 240.0\text{ mm}$) is positioned in **Row 1 (Top)** of the outer folding columns (Left & Right columns).
- It houses a standard high-torque MG996R (or compatible metal-gear coreless/brushless standard servo, 15–35 kg-cm) that directly drives the active flap.
- **Direct 1-Piece Drive**: The active flap features an integrated continuous $\varnothing 13.0\text{ mm}$ drive axle with a direct press-fit 25T servo horn pocket at $Y = 240\text{ mm}$, eliminating backlash from separate coupler adapters.
- **Synchronous Column Torque Transmission**:
  - The single servo in Row 1 powers the entire column.
  - Rotational torque is transmitted from the servo horn at $Y = 240\text{ mm}$ through the monolithic $\varnothing 13.0\text{ mm}$ active flap axle down to the $8.0\text{ mm}$ hex socket at $Y = 0\text{ mm}$.
  - Via the **Part 11 Hex Drive Coupler Pin**, torque enters the Follower Module below, causing all flaps in the column to flip in perfect synchrony.

```
                    [Row 1 Top Frame Boundary]
                                 │
                     ┌───────────────────────┐
                     │ MG996R Standard Servo │
                     │   (Direct 25T Spline) │
                     └───────────┬───────────┘
                                 ▼ (Direct 25T Horn Socket + M3 Screw)
         +=================[ 240mm Top Rail ]=================+
         | [MG996R Bay + Snap Cover]   [Ø13.5mm Top Knuckle]  | [Dovetail Socket]
         |                                                    |
         |  ===============================================   |
         |  |                                             |   |
240mm    |  |            Active Motorized Flap            |   | 240mm Outer Rail
Hinge    |  |            (239 x 238 x 2.4 mm)             |   | [Open-Top Dovetail]
Axis     |  |     [Organic Gradient Circular Cutouts]     |   |
(Z=8mm)  |  |                                             |   |
         |  ===============================================   |
         |                                                    |
         | [Ø13.5mm Bottom Bearing Knuckle 360°]              | [Dovetail Socket]
         +================[ 240mm Bottom Rail ]===============+
                           ▲ (Bottom 8.0mm Hex Socket + Part 11 Pin)
                                      │
                 [Row 2: Passive Follower Module Below]
```

---

## 2. Component Specifications

### 2.1 Motorized Outer Chassis Frame (`motorized_frame.py`)
- **Overall Dimensions**: $240.0\text{ mm} \text{ (W)} \times 240.0\text{ mm} \text{ (H)} \times 15.0\text{ mm} \text{ (T)}$.
- **4-Sided Rigid Chassis Architecture**:
  - Standardized outer envelope sharing the Follower chassis design: $15.0\text{ mm}$ rigid outer perimeter rails, $3.0\text{ mm}$ bottom shell floor, and an open-bottom center cavity saving ~120g PLA.
  - **4th Left Stiffener Tie-Bar ($X \in [11, 25\text{ mm}]$, $Z \in [0, 3.0\text{ mm}]$)**:
    - Clean Solid Continuous Through-Dovetail Joint at $Y = 120\text{ mm}$ ($4.0\text{ mm}$ neck $\to 8.0\text{ mm}$ flare $\times 8.0\text{ mm}$ depth, $0.25\text{ mm}$ clearance).
    - $3.0\text{ mm}$ solid continuous outer walls on both sides.
    - $100\%$ flush at $Z = 3.0\text{ mm}$, giving $100\%$ kinematic clearance for $180^\circ$ flap rotation.
    - Zero support required during 3D printing.
- **Integrated Servo Mounting Bay (Top-Left, $Y \in [190, 240\text{ mm}]$)**:
  - **Motor Well**: Precision cavity ($41.0 \times 20.5 \times 36.0\text{ mm}$) for standard MG996R servo body ($40.5 \times 20.0 \times 36.0\text{ mm}$).
  - **Mounting Bosses**: 4x M3 screw mounting bosses spaced at standard $48.0\text{ mm} \times 10.0\text{ mm}$ pattern.
  - **Conduit & Strain Relief**: Smooth $1.5\text{ mm}$ filleted wire conduit channels with zip-tie anchor saddles leading wires into the dovetail joiner wire raceway.
  - **Snap Cover Interface**: Recessed perimeter lip with dual cantilever snap-latch engagement slots for toolless cover locking.
- **Dual Hinge Pivot Knuckles (Left Rail $X = 0$)**:
  - **Hinge Center Axis**: Centered at $Z = 8.0\text{ mm}$, providing **$1.5\text{ mm}$ Ground Clearance** beneath the $\varnothing 13.0\text{ mm}$ solid drive axle ($Z \in [1.5, 14.5\text{ mm}]$).
  - **Top Knuckle ($Y \in [225, 240\text{ mm}]$)**: $360^\circ$ closed solid cylindrical bearing tunnel ($\varnothing 13.5\text{ mm}$, $0.25\text{ mm}$ radial clearance) integrated with the servo mounting bulkhead.
  - **Bottom Knuckle ($Y \in [0, 15\text{ mm}]$)**: $360^\circ$ closed solid cylindrical bearing tunnel ($\varnothing 13.5\text{ mm}$, $0.25\text{ mm}$ radial clearance).
  - **C1-Continuous Concave Blend Ramps**: Smooth $R_f = 12.0\text{ mm}$ tangent concave filleted ramps transitioning seamlessly from $\varnothing 19.0\text{ mm}$ knuckle barrels into the $Z = 15.0\text{ mm}$ frame deck.
  - **100% Planar Flat Underside**: Both knuckles trimmed coplanar at $Z = 0.0\text{ mm}$ for zero-support 3D printing.
- **Dovetail Joiner Sockets**:
  - 3-wall true open-top sliding female dovetail sockets on outer sides ($12.0\text{ mm}$ neck, $18.0\text{ mm}$ flare, $12.0\text{ mm}$ depth, $0.15\text{ mm}$ clearance per side).
  - $3.0\text{ mm}$ bottom floor drop stop and $\varnothing 6.0\text{ mm}$ through-floor push-out access holes.
- **Accessories & Features**:
  - 3x silent-flip TPU bumper slots ($1.5\text{ mm}$ recessed depth) on top landing rails.
  - 4x bottom corner sockets ($\varnothing 12.0 \times 2.0\text{ mm}$) for anti-slip silicone/rubber feet.
  - $0.4\text{ mm}$ Elephant's Foot relief chamfers on all bed-facing edges.

---

### 2.2 Monolithic Active Folding Flap (`active_flap.py`)
- **Overall Dimensions**: $239.0\text{ mm} \text{ (W)} \times 238.0\text{ mm} \text{ (H)} \times 2.4\text{ mm} \text{ (T)}$.
- **Operating Height**: Resting position at $Z = 15.0\text{ mm}$ to $17.4\text{ mm}$, flush with adjacent base and follower flaps.
- **Top-Left Motor Corner Clearance**:
  - Rectangular corner cutout ($46.0\text{ mm} \text{ (W)} \times 26.0\text{ mm} \text{ (H)}$) at top-left $(X \in [0, 46\text{ mm}], Y \in [214, 240\text{ mm}])$ clearing the servo bay and snap cover across full $0^\circ \to 180^\circ$ rotation.
- **Continuous Heavy-Duty Solid Drive Axle**:
  - $\varnothing 13.0\text{ mm}$ solid-core continuous drive axle along $X = 0$ ($Y = 0$ to $240\text{ mm}$), centered at $Z = 8.0\text{ mm}$.
  - Seamlessly fused along the flap edge with bottom $R=3.0\text{ mm}$ fillet reinforcing gusset.
- **Driven End ($Y = 240\text{ mm}$)**:
  - Direct press-fit 25T standard metal servo horn cylindrical socket ($\varnothing 18.2 \times 3.0\text{ mm}$ outer cylindrical boss, $\varnothing 6.0\text{ mm}$ spline receiver with $0.2\text{ mm}$ press-fit clearance).
  - Coaxial $\varnothing 3.2\text{ mm}$ through-hole with $\varnothing 6.0 \times 2.0\text{ mm}$ counterbore for the M3 central servo horn lock screw.
- **Output End ($Y = 0\text{ mm}$)**:
  - Standardized $8.0\text{ mm}$ female hex torque drive socket ($12.0\text{ mm}$ deep, $8.05\text{ mm}$ flat-to-flat).
  - Receives Part 11 Hex Drive Coupler Pin to transmit synchronous torque down the column.
- **Weight Reduction & Dynamic Optimization**:
  - Multi-tiered organic circular cutouts (~45% mass reduction, target blade weight $\le 75\text{g}$).
  - Reduces rotational moment of inertia by ~50%, ensuring rapid 0.3s snap-fold cycles without servo thermal overload.
- **Surface & Edge Aesthetics**:
  - $0.6\text{ mm}$ diamond micro-grip knurling pattern on top garment face to prevent garment slippage during dynamic fold acceleration.
  - $1.2\text{ mm}$ recessed perimeter accent shadow bevel.
  - $0.8\text{ mm}$ chamfers on all weight-reduction circular hole edges.

---

### 2.3 Toolless Snap-Latch Servo Cover (`servo_cover.py`)
- **Dimensions**: Low-profile contoured shell ($48.0 \times 25.0 \times 12.0\text{ mm}$).
- **Material**: Optimized for PLA/PETG printing flat on top surface with zero supports.
- **Toolless Snap-Latch Retention**:
  - Dual cantilever flex-tabs with $0.4\text{ mm}$ retention detents engaging with matching slots in the frame servo bay.
  - Allows 5-second motor inspection and replacement without screwdrivers.
- **Cable Exit Notch**:
  - Smooth $1.5\text{ mm}$ filleted wire relief cutout guiding the 3-wire servo lead directly into the frame raceway.
- **Cooling Ventilation**:
  - Longitudinal passive convection cooling gills providing airflow to the servo aluminum heatsink body.

---

### 2.4 Motorized Sub-Assembly (`assembly_motorized_module.py`)
- **Assembly Components**:
  1. `MotorizedFrame` (Yellow)
  2. `ActiveFlap` (Red)
  3. `ServoCover` (Black)
  4. 2x `FrameJoiner` (Blue, seated in front and right open-top dovetails)
  5. `HexDriveCoupler` (Purple, inserted into bottom hex socket at $Y=0$)
  6. Standard MG996R Servo CAD reference model seated in the motor well.
- **Kinematics**:
  - Full $0^\circ \to 90^\circ \to 180^\circ$ sweep verification.
  - Zero interference (`0.00000 mm³` overlap) across all mating pairs.

---

## 3. Parametric Dimension Matrix

| Feature | Parameter / Dimension | Value | Reference |
|---|---|---|---|
| Frame Dimensions | `PANEL_WIDTH`, `PANEL_HEIGHT`, `PANEL_THICKNESS` | $240.0 \times 240.0 \times 15.0\text{ mm}$ | `params.py` |
| Servo Model Footprint | `SERVO_MOUNT_WIDTH/DEPTH/HEIGHT` | $40.5 \times 20.0 \times 36.0\text{ mm}$ | `params.py` |
| Servo Mounting Holes | `SERVO_HOLE_SPACING_X/Y`, `SERVO_SCREW_RADIUS` | $48.0 \times 10.0\text{ mm}$, $R=2.0\text{ mm}$ | `params.py` |
| Active Flap Dimensions | `PANEL_WIDTH - 1.0`, `PANEL_HEIGHT - 2.0` | $239.0 \times 238.0 \times 2.4\text{ mm}$ | `params.py` |
| Flap Rest Plane | Frame Rail Top | $Z = 15.0$ to $17.4\text{ mm}$ | Phase 3 Standard |
| Drive Axle Diameter | `DRIVE_SHAFT_DIAMETER` | $\varnothing 13.0\text{ mm}$ | `params.py` |
| Knuckle Bore Diameter | `DRIVE_SHAFT_DIAMETER + 2*BEARING_ROTATING_CLEARANCE` | $\varnothing 13.5\text{ mm}$ ($0.25\text{ mm}$ radial) | `params.py` |
| Hinge Axis Elevation | Axle Centerline | $Z = 8.0\text{ mm}$ ($1.5\text{ mm}$ ground clearance) | Phase 3 Standard |
| Servo Horn Socket (Top) | Direct 25T Spline Pocket + M3 Screw Bore | $\varnothing 18.2\text{ mm}$ boss, $\varnothing 6.0\text{ mm}$ spline, $\varnothing 3.2\text{ mm}$ M3 hole | `PRESS_FIT_CLEARANCE` |
| Hex Torque Socket (Bottom) | `HEX_COUPLER_SIZE`, `HEX_COUPLER_DEPTH` | $8.0\text{ mm}$ Flat-to-Flat, $12.0\text{ mm}$ deep | `params.py` |
| 4th Tie-Bar Stiffener | Dovetail Joint at $Y = 120\text{ mm}$ | Neck $4\text{ mm}$, Flare $8\text{ mm}$, Depth $8\text{ mm}$, $Z \in [0, 3\text{ mm}]$ | Phase 3 Standard |
| Sliding Dovetail Sockets | `DOVETAIL_NECK_WIDTH`, `DOVETAIL_FLARE_WIDTH`, `DOVETAIL_DEPTH` | $12.0\text{ mm}$, $18.0\text{ mm}$, $12.0\text{ mm}$ ($0.15\text{ mm}$ clearance) | `params.py` |
| Dovetail Push-Out Hole | Push-out cylinder | $\varnothing 6.0\text{ mm}$ through-floor | Phase 3 Standard |
| Rubber Foot Sockets | Corner anti-slip pads | $4\times \varnothing 12.0 \times 2.0\text{ mm}$ | Phase 3 Standard |
| TPU Bumper Slots | `TPU_BUMPER_DEPTH` | $3\times (15.0 \times 4.0 \times 1.5\text{ mm})$ | `params.py` |
| Texture & Chamfers | `TEXTURE_HEIGHT`, `HOLE_CHAMFER`, `ELEPHANTS_FOOT_CHAMFER` | $0.6\text{ mm}$, $0.8\text{ mm}$, $0.4\text{ mm}$ | `params.py` |
| Shadow Bevel | `ACCENT_BEVEL_DEPTH` | $1.2\text{ mm}$ recessed border | `params.py` |

---

## 4. Key Architectural Decisions

1. **Direct Monolithic 25T Spline Socket**: Rather than using bolt-on plastic horns or fragile set-screw couplers, the active flap directly integrates the 25T servo horn geometry with an M3 through-bore. This provides maximum rigidity, zero rotational backlash, and eliminates loose fasteners during high-cycle folding operations.
2. **Standardized 4th Wall Dovetail Stiffener**: The motorized chassis reuses the proven Phase 3 4th wall tie-bar design with a solid through-dovetail joint at $Y=120\text{ mm}$ ($Z \le 3.0\text{ mm}$), ensuring knuckle alignment under servo torque without interfering with flap rotation.
3. **Toolless Snap-Latch Enclosure**: The snap cover enables rapid servo inspection and replacement in 5 seconds while providing passive ventilation to prevent servo overheating during continuous batch folding.
4. **Column Synchronous Drive Continuity**: By outputting torque via the standardized $8.0\text{ mm}$ hex socket at $Y=0$, the motorized module seamlessly links with downstream follower modules using the shared Part 11 hex drive coupler pin.

---

## 5. Non-Goals

- **No Onboard Logic Board in Motorized Module**: The microcontroller (Raspberry Pi Pico 2W) and PCA9685 driver board reside exclusively in the **Phase 5 Interface Module / Controller Case**, not in the motorized module frame.
- **No Complex Geared Transmissions**: Direct 1:1 servo actuation is employed to maximize simplicity, reliability, and minimize part count.
- **No Multi-Piece Glued Flap Assemblies**: The active flap is printed as a single monolithic component with integrated continuous axle and torque sockets.
