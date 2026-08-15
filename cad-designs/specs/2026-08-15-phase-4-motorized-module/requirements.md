# Requirements — Phase 4: Active Motorized Module (Horizontal Drive & Modular Horn Adapter Architecture)

Requirements specification for the Active Motorized Module of the Fabrica Cloth Folding Robot, featuring **Horizontal Inline MG996R Servo Bay with Inner Enclosure Wall**, **Solid Mounting Towers with Captive Hex Nut Housings**, **100% Flat Bottom Base ($Z = 0.0\text{ mm}$)**, **Unified Hinge Pivot Axis ($Z_{pivot} = 10.0\text{ mm}$)**, **Modular Circular Servo Horn Drive Adapter (`servo_drive_adapter.py`)**, **Symmetrical Dual-Ended 8.0mm Female Hex Active Flap Axle**, **Full Enclosure Slide-In Hood Cover**, and **Synchronous Column Hex Torque Transmission**.

---

## 1. System Context & Overview

In the Fabrica $4 \times 3$ modular folding grid:
- The **Active Motorized Module** ($240.0 \times 240.0\text{ mm}$) is positioned in **Row 1 (Top)** of the outer folding columns (Left & Right columns).
- It houses a standard high-torque MG996R metal-gear servo mounted **horizontally flat on its $20.0\text{ mm}$ side** along the rear rail ($Y = 185\text{..}240\text{ mm}$).
- **100% Flat Base Plane ($Z = 0.0\text{ mm}$)**: All frame bases sit completely flush on the table surface without any downward bumps or steps.
- **Unified Hinge Centerline ($Z_{pivot} = 10.0\text{ mm}$)**: Identical pivot axis height across all active and passive follower modules for seamless multi-module column torque coupling.
- **Modular Circular Servo Horn Drive Adapter (`servo_drive_adapter.py`)**:
  - Solves the FDM printability limitation of 3D-printing micro 25T metal gear splines.
  - Bolted directly onto the standard circular servo horn ($\varnothing 20\text{ mm}$) included in the MG996R kit via 4x screws on a $\varnothing 14.0\text{ mm}$ bolt pattern.
  - Extends an $8.0\text{ mm}$ male hex torque peg ($7.7\text{ mm}$ flat-to-flat, $10.5\text{ mm}$ length) along $-Y$ into the active flap.
- **Symmetrical Dual-Ended Female Hex Flap**:
  - The `motorized_flap` features identical $8.0\text{ mm}$ female hex sockets at both ends ($Y = 0.5\text{ mm}$ and $Y = 178.0\text{ mm}$), identical to `follower_flap`.
- **Synchronous Column Torque Transmission**:
  - Rotational torque is transmitted from the servo through the metal horn, into the 3D-printed drive adapter, down the active flap axle, and through the `hex_drive_coupler` into the follower flap below.

```
                    [Row 1 Top Frame Boundary]
                                 │
           ┌───────────────────────────────────────────┐
           │ Horizontal MG996R Servo (Flat on 20mm side)│
           │ Output Spline centered at (X=0, Z=10.0mm) │
           └─────────────────────┬─────────────────────┘
                                 ▼ (Standard Ø20mm Round Metal Horn)
           ┌───────────────────────────────────────────┐
           │ Modular Servo Drive Adapter (7mm disk)    │
           │ Male 8.0mm Hex Peg at (X=0, Z=10.0mm)     │
           └─────────────────────┬─────────────────────┘
                                 ▼ (Top 8.0mm Female Hex Socket)
         +=================[ 240mm Top Rail ]=================+
         | [Full Hood Cover]           [Ø13.5mm Top Knuckle]  | [Dovetail Socket]
         | [Inner Enclosure Wall]                             |
         |  ===============================================   |
         |  |                                             |   |
240mm    |  |            Active Motorized Flap            |   | 240mm Outer Rail
Hinge    |  |            (239 x 238 x 2.4 mm)             |   | [Open-Top Dovetail]
Axis     |  |     [Organic Gradient Circular Cutouts]     |   |
(Z=10mm) |  |                                             |   |
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
- **100% Planar Flat Base Plane**: Trimmed coplanar at $Z = 0.0\text{ mm}$ across the entire chassis.
- **Continuous Inner Enclosure Wall ($X \in [38.0, 48.0\text{ mm}], Y \in [185.0, 240.0\text{ mm}]$)**:
  - Solid internal wall connecting the top rail ($Y = 240\text{ mm}$) to the inner knuckle bridge and tie-bar, completely enclosing the motor chamber from the central cavity.
- **Solid Front Mounting Towers ($Y \in [185.0, 195.5\text{ mm}]$)**:
  - Inner tower at $X \in [30.5, 44.0\text{ mm}]$; Outer tower at $X \in [-18.0, -10.5\text{ mm}]$.
  - 4x horizontal M3 clearance through-holes ($\varnothing 3.4\text{ mm}$):
    - Inner pair: $(X = 34.95\text{ mm}, Z = 4.75\text{ mm})$ and $(X = 34.95\text{ mm}, Z = 15.25\text{ mm})$.
    - Outer pair: $(X = -14.45\text{ mm}, Z = 4.75\text{ mm})$ and $(X = -14.45\text{ mm}, Z = 15.25\text{ mm})$.
    - Spacing: $\Delta Z = 10.50\text{ mm}$ (centered about $Z_{pivot} = 10.0\text{ mm}$), $\Delta X = 49.40\text{ mm}$ matching MG996R tabs.
  - 4x Captive Hex Nut Housings ($W_{af} = 5.8\text{ mm}$, depth $3.2\text{ mm}$) on front face ($Y = 185.0\text{ mm}$) to hold M3 nuts captive.
- **Rear Slide-In Entry**: Slotted opening at $Y = 240.0\text{ mm}$ ($X \in [-11.0, 31.0\text{ mm}]$) with internal ear slide channels ($X \in [-17.5, 38.0\text{ mm}]$) for horizontal servo insertion.
- **Dual Hinge Pivot Knuckles (Left Rail $X = 0$)**:
  - Centered at $Z_{pivot} = 10.0\text{ mm}$ with $3.5\text{ mm}$ ground clearance.
  - Top Knuckle ($Y \in [170, 185\text{ mm}]$): $360^\circ$ closed solid cylindrical bearing tunnel ($\varnothing 13.5\text{ mm}$).
  - Bottom Knuckle ($Y \in [0, 15\text{ mm}]$): $360^\circ$ closed solid cylindrical bearing tunnel ($\varnothing 13.5\text{ mm}$).
  - C1-Continuous Concave Blend Ramps ($R_f = 12.0\text{ mm}$) smoothly transitioning into the frame deck.
- **Dovetails, Bumpers & Feet**:
  - 3-wall true open-top sliding female dovetail sockets on outer walls with $3.0\text{ mm}$ drop stops and $\varnothing 6.0\text{ mm}$ push-out holes.
  - 3x silent-flip TPU bumper slots ($1.5\text{ mm}$ depth).
  - 4x bottom anti-slip rubber foot sockets ($\varnothing 12.0 \times 2.0\text{ mm}$).

---

### 2.2 Modular Circular Servo Horn Drive Adapter (`servo_drive_adapter.py`)
- **Flange Disk**: $\varnothing 19.0\text{ mm}$ circular flange, $7.0\text{ mm}$ thick base disk ($Y \in [178.0, 185.0\text{ mm}]$, centered at $X=0, Z=10.0\text{ mm}$).
- **Horn Fastening Interface**:
  - 4x M2/M2.5 clearance through-holes ($\varnothing 2.2\text{ mm}$) arranged in a $90^\circ$ cross on a $\varnothing 14.0\text{ mm}$ bolt circle to screw directly into the metal round horn.
  - Coaxial $\varnothing 6.5\text{ mm}$ central counterbore allowing screwdriver access to the M3 servo spline lock screw.
- **Male Hex Drive Peg**:
  - $8.0\text{ mm}$ nominal male hex peg ($7.7\text{ mm}$ flat-to-flat with clearance, $10.5\text{ mm}$ length extending along $-Y$ into the flap from $Y = 178.0\text{ mm}$ to $167.5\text{ mm}$).
  - $1.5\text{ mm} \times 45^\circ$ self-aligning lead-in entry chamfer on the hex peg tip.

---

### 2.3 Monolithic Active Folding Flap (`motorized_flap.py`)
- **Overall Dimensions**: $239.0\text{ mm} \text{ (W)} \times 238.0\text{ mm} \text{ (H)} \times 2.4\text{ mm} \text{ (T)}$.
- **Operating Height**: Resting plane at $Z = 15.0$ to $17.4\text{ mm}$.
- **Continuous Solid-Core Drive Axle**:
  - $\varnothing 13.0\text{ mm}$ solid-core continuous drive axle along $X = 0$ ($Y = 0.5$ to $178.0\text{ mm}$), centered at $Z = 10.0\text{ mm}$.
  - Fused with bottom reinforcing fillet gusset between knuckles ($Y \in [15.5, 169.5\text{ mm}]$).
- **Dual Symmetrical 8.0mm Female Hex Sockets**:
  - **Driven Top End ($Y = 178.0\text{ mm}$)**: $8.0\text{ mm}$ female hex socket ($10.5\text{ mm}$ deep) receiving the `servo_drive_adapter` male hex peg.
  - **Output Bottom End ($Y = 0.5\text{ mm}$)**: $8.0\text{ mm}$ female hex socket ($10.5\text{ mm}$ deep) receiving the `hex_drive_coupler` pin.
- **Weight Reduction & Aesthetics**:
  - Multi-tiered organic circular cutouts (~45% mass reduction, target blade weight $\le 75\text{g}$).
  - $0.6\text{ mm}$ diamond micro-grip knurling texture on top garment face.
  - $1.2\text{ mm}$ recessed perimeter shadow bevel.

---

### 2.4 Full Enclosure Slide-In Hood Cover (`motorized_servo_cover.py`)
- **Top Face Plate**: $60.5\text{ mm} \text{ (W)} \times 54.0\text{ mm} \text{ (L)} \times 6.2\text{ mm} \text{ (T)}$ spanning $X \in [-17.0, 43.5\text{ mm}], Y \in [186.0, 240.0\text{ mm}], Z \in [15.0, 21.2\text{ mm}]$.
- **Integrated Rear Face Cap**: $54.5\text{ mm} \text{ (W)} \times 2.5\text{ mm} \text{ (T)} \times 21.2\text{ mm} \text{ (H)}$ completely sealing the rear slide-in slot ($Z \in [0.0, 21.2\text{ mm}]$).
- **Lateral Slide-in Retention Tongues**: Engage into frame side grooves at $Z \in [13.6, 14.8\text{ mm}]$.
- **Underside Clearance Hollow**: Generous pocket clearing the MG996R top casing.

---

### 2.5 Motorized Sub-Assembly (`motorized_assembly.py`)
- **Assembly Components**:
  1. `MotorizedFrame` (Gold/Amber)
  2. `MotorizedFlap` (Crimson Red)
  3. `MotorizedServoCover` (Slate Purple)
  4. 2x `FrameJoiner` (Blue)
  5. `HexDriveCoupler` (Gold/Yellow, bottom port)
  6. `ServoDriveAdapter` (Orange/Silver, top drive port)
  7. MG996R Servo CAD reference model (Cyan)
- **Kinematics & Interference**:
  - Zero interference (`0.00000 mm³` overlap) across all mating pairs.

---

## 3. Parametric Dimension Matrix

| Feature | Parameter / Dimension | Value | Reference |
|---|---|---|---|
| Frame Dimensions | `PANEL_WIDTH`, `PANEL_HEIGHT`, `BASE_PANEL_THICKNESS` | $240.0 \times 240.0 \times 15.0\text{ mm}$ | `params.py` |
| Frame Base Elevation | Planar Flat Bed Trim | $Z = 0.0\text{ mm}$ (100% flat) | `motorized_frame.py` |
| Hinge Pivot Centerline | `PIVOT_Z` | $10.0\text{ mm}$ above table | `params.py` |
| Drive Axle Diameter | `DRIVE_SHAFT_DIAMETER` | $\varnothing 13.0\text{ mm}$ | `params.py` |
| Knuckle Bore Diameter | `DRIVE_SHAFT_DIAMETER + 2*BEARING_ROTATING_CLEARANCE` | $\varnothing 13.5\text{ mm}$ ($0.25\text{ mm}$ radial) | `params.py` |
| Servo Mounting Holes | Top & Bottom spacing per ear ($\Delta Z$), Ear-to-Ear spacing ($\Delta X$) | $\Delta Z = 10.5\text{ mm}$, $\Delta X = 49.4\text{ mm}$ | `specs/reference-images/mg996r-servo.png` |
| Captive Hex Nut Housings | Regular Hexagon Across-Flats / Depth | $W_{af} = 5.8\text{ mm}$, depth $3.2\text{ mm}$ | `motorized_frame.py` |
| Servo Drive Adapter Disk | Flange Diameter / Thickness | $\varnothing 19.0\text{ mm} \times 7.0\text{ mm}$ ($Y \in [178.0, 185.0\text{ mm}]$) | `servo_drive_adapter.py` |
| Adapter Male Hex Peg | Across-Flats / Length / Lead-in Chamfer | $7.7\text{ mm} \times 10.5\text{ mm}$, $1.5\text{ mm} \times 45^\circ$ | `servo_drive_adapter.py` |
| Flap Hex Sockets (Both Ends) | `HEX_COUPLER_SIZE`, Depth | $8.0\text{ mm}$ Flat-to-Flat, $10.5\text{ mm}$ deep | `params.py` |
| Active Flap Axle Span | $Y_{start} \to Y_{end}$ | $Y = 0.5\text{ mm}$ to $Y = 178.0\text{ mm}$ | `motorized_flap.py` |
