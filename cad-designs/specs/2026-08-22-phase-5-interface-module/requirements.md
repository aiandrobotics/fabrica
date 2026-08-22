# Requirements — Phase 5: Interface Module & Electronics Enclosure

## Scope
Phase 5 covers the complete 3D mechanical CAD modeling, parametric definitions, and multi-body assembly validation for:
1. `interface_case.py`: Protective lower electronics chassis housing the dual circuit boards, power input, wire channels, and cooling vents.
2. `interface_panel.py`: 15° forward-angled ergonomic user interaction top deck with 4x Ø16mm push button cutouts and a multi-color status LED window.
3. `interface_assembly.py`: Complete sub-assembly model verifying clearance, fastener alignments, and cable pass-throughs.

---

## Decisions & Hardware Specifications

### 1. Triple Internal Circuit Boards

- **Power Distribution Board (PDB) / 5V-6V Step-Down Buck Module**:
  - PCB Envelope: $45.0\text{ mm} \times 32.0\text{ mm} \times 12.0\text{ mm}$ with heavy-duty input and output screw terminal blocks.
  - Mounting Holes: 4x $\varnothing 3.0\text{ mm}$ corner mounting holes.
  - Hole Pitch (Center-to-Center): **$37.0\text{ mm} \times 24.0\text{ mm}$**.
  - Mounting Method: 4x raised M3 cylindrical standoffs ($H = 5.0\text{ mm}$, $\varnothing_{outer} = 6.0\text{ mm}$) with $\varnothing 2.6\text{ mm}$ core pilot holes.
  - Placement: Upper-left bay directly behind the DC barrel jack ($Y = 94.0\text{ mm}$), receiving external power and distributing regulated $5\text{V}/6\text{V}$ high-current bus to the PCA9685 servo rail and clean logic power to the ESP32.

- **PCA9685 16-Channel 12-Bit PWM Servo Driver Board**:
  - PCB Envelope: $62.5\text{ mm} \times 25.4\text{ mm} \times 12.0\text{ mm}$ (standard Adafruit / generic breakout footprint).
  - Mounting Holes: 4x $\varnothing 2.5\text{ mm}$ corner mounting holes.
  - Hole Pitch (Center-to-Center): **$55.88\text{ mm}$ ($2.20"$)** along the long axis $\times$ **$19.05\text{ mm}$ ($0.75"$)** along the short axis.
  - Edge Margins: $3.31\text{ mm}$ from long ends, $3.18\text{ mm}$ from side edges.
  - Mounting Method: 4x raised M2.5 cylindrical standoffs ($H = 5.0\text{ mm}$, $\varnothing_{outer} = 5.0\text{ mm}$) with $\varnothing 2.2\text{ mm}$ core pilot holes for M2.5 self-tapping fasteners or brass heat-set inserts.
  - Connector Orientations: 16x 3-pin male servo headers ($Z = 12.0\text{ mm}$ clearance) facing toward the internal wire raceways leading to frame dovetail conduit ports.

- **WROOM-32 / ESP-32S Development Board (ESP32 DevKit V1 / NodeMCU-32S)**:
  - PCB Envelope: $51.5\text{ mm} \times 28.5\text{ mm} \times 12.0\text{ mm}$ (30-pin standard) / up to $54.5\text{ mm} \times 28.0\text{ mm}$ (38-pin).
  - Pin Header Footprint: 2 rows of 15/19 pins on $2.54\text{ mm}$ ($0.1"$) pitch, $22.86\text{ mm}$ ($0.9"$) row spacing.
  - Mounting Architecture (Universal Hybrid Standoff + Cradle):
    1. **Screw Standoffs**: 4x M3 standoffs spaced at **$46.0\text{ mm} \times 23.0\text{ mm}$** center-to-center with $\varnothing 2.6\text{ mm}$ core pilot holes for boards featuring corner mounting holes.
    2. **Perimeter Retention Cradle**: $52.0\text{ mm} \times 29.0\text{ mm}$ perimeter retention cradle with corner capture ledges ensuring boards without mounting holes (standard DevKitC clones) snap firmly into place.
  - External USB Programming Port: $11.0\text{ mm} \times 6.5\text{ mm}$ rectangular cutout with $1.0\text{ mm}$ edge chamfers on the chassis wall, accommodating both Micro-USB and USB-C cable overmolds.

### 2. User Interaction Controls
- **4x Top Interaction Buttons**:
  - Diameter: $\varnothing 16.0\text{ mm}$ standard circular panel cutout (`BUTTON_HOLE_DIA = 16.00`).
  - Spacing: Equidistant linear arrangement along the 15° angled top deck ($28.0\text{ mm}$ center-to-center pitch).
  - Hole Details: $0.8\text{ mm} \times 45^\circ$ top chamfer for flush bezel seating and smooth finger touch.
  - Intended Functions: `Button 1: Start / Fold`, `Button 2: Pause / Stop`, `Button 3: Mode / Preset Select`, `Button 4: Reset / Calibrate`.
- **Multi-State Status LED Indicator**:
  - Light Aperture: Standardized **$\varnothing 6.0\text{ mm}$ circular round window** with $0.8\text{ mm} \times 45^\circ$ top chamfer and $\varnothing 8.5\text{ mm} \times 1.5\text{ mm}$ underside retention counterbore (fits standard 5mm round LEDs and snap-in clip bezels).
  - Purpose: Multi-color visual feedback (Ready, Active Fold Cycle, Paused, Fault/Stall, WiFi Connected).

### 3. Case Enclosure & Ergonomics
- **Enclosure Profile**: Spacious flat horizontal rectangular unibody box ($220.0\text{ mm} \ (W) \times 120.0\text{ mm} \ (D) \times 45.0\text{ mm} \ (H)$ chassis + $3.0\text{ mm}$ top plate, total $H = 48.0\text{ mm}$) with a 100% continuous flush top perimeter rim and $>25.0\text{ mm}$ overhead volume for wiring harnesses.
- **Power Inlet**: $\varnothing 11.5\text{ mm}$ circular hole on left wall for standard panel-mount DC barrel jack (5.5×2.1mm) powering the high-current servo power bus directly into the PDB.
- **Ventilation**: Passive convection cooling chimney slots located on the bottom base directly below the PDB, PCA9685 driver, and ESP32 board to prevent heat buildup.
- **Fastening**: 4-sided toolless direct wall snap-fit system with 4x retention windows cut through the front/rear perimeter walls and 4x cantilever snap tabs on the panel, eliminating internal boss clutter.

### 4. 16 Extended Full-Height Vertical Motor Wire Ports & Clean Interior Chamber
- **16 Full-Height Vertical Slots**: 16 individual full-height vertical wire slots ($3.5\text{ mm} \times 32.0\text{ mm}$, reaching from $Z=5.0\text{ mm}$ near floor to $Z=37.0\text{ mm}$) on $6.0\text{ mm}$ pitch with $2.5\text{ mm}$ solid structural pillars between each slot directly behind the PCA9685 pin headers, allowing individual dedicated routing for each servo motor.
- **Clean Floor & Chamber**: 100% smooth, unobstructed floor with zero internal wire traps, snubber posts, or saddle obstacles.
- **Pull-Tension Isolation & Strain Relief**:
  - Dual Captive Zip-Tie Anchor Saddles: $12.0\text{ mm} \times 6.0\text{ mm}$ saddles with $3.0\text{ mm} \times 2.5\text{ mm}$ underpasses positioned right in front of the exit port. Tightening a zip-tie collar against the inner shoulder absorbs 100% of external cable pulling force, leaving zero mechanical tension on PCB pins or solder joints.
  - Dual S-Bend Friction Snubber Posts: $2\times \varnothing 6.0\text{ mm}$ cylindrical friction posts for optional hardware-free S-curve wire routing.

### 5. Grid Attachment & Dovetail Joint System
- **Main Board Interlocking**: The interface module casing attaches directly and rigidly to the main folding board chassis (Base, Follower, or Motorized frames) using the standardized sliding dovetail joint system.
- **Dovetail Geometry & Dimensions**:
  - Neck Width: $12.0\text{ mm}$ at the chassis interface seam.
  - Flared Width: $18.0\text{ mm}$ inside the pocket, creating a robust mechanical interlock preventing lateral or pull-out separation.
  - Socket Depth: $12.0\text{ mm}$ insertion depth for maximum torsional and bending stiffness.
  - Drop-Stop Floor: $3.0\text{ mm}$ solid bottom floor maintaining a 100% flush top surface alignment with adjacent frames.
  - Push-Out Toolless Removal: $\varnothing 6.0\text{ mm}$ through-floor push-out hole for effortless joiner ejection.
  - Internal Wire Raceway Conduit: Smooth radiused internal cable pass-through channel aligned concentric with the dovetail tunnel, routing the 16x PWM servo lines and power buses invisibly from the controller enclosure into the main folding grid.

---

## Constraints
- **FDM Printability**: All overhangs $\le 45^\circ$, bottom Elephant's Foot relief chamfers ($0.4\text{ mm}$), and 100% planar bed-contact faces.
- **Grid Compatibility**: Dovetail sockets match the universal sliding dovetail geometry ($12\text{ mm}$ neck $\to 18\text{ mm}$ flare $\times 12\text{ mm}$ depth, $0.20\text{ mm}$ tolerance per side) and $1.5\text{ mm}$ filleted wire conduit ports.
- **Parametric Cohesion**: All dimensions driven by `params.py` (`SCALE = 1.0`).

---

## Non-Goals
- Integrated high-voltage AC mains power supply (module is strictly low-voltage DC 5V/6V powered).
- On-board touchscreen display (user interaction is strictly via the 4 physical buttons + status LED + wireless mobile app).
- Direct PCB design / Gerber generation (strictly 3D mechanical enclosure CAD).
