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
### 1. Compact Flat Horizontal Form Factor & Multi-Board Architecture
- **Dimensions**: Outer rectangular chassis dimensions of $140.0\text{ mm} \ (W) \times 120.0\text{ mm} \ (D) \times 45.0\text{ mm} \ (H)$, assembled height of $48.0\text{ mm}$ with top faceplate.
- **Volume Optimization**: Width reduced to $140.0\text{ mm}$ (41% narrower footprint) by arranging the Power Distribution Board vertically alongside the ESP32 and PCA9685 boards.
- **Direct Wall Snap-Fit System**: 4x Cantilever snap tabs integrated directly on the panel clicking into 4x matching through-wall retention windows ($12.0\text{ mm} \times 3.5\text{ mm}$) cut through the front and rear perimeter walls (at $X \in \{35.0, 105.0\text{ mm}\}$), eliminating internal mounting bosses and maximizing internal routing volume.
- **Top Interaction Controls**:
  - 4x Standardized $\varnothing 16.0\text{ mm}$ round button holes with $0.8\text{ mm}$ top entry chamfers on $24.0\text{ mm}$ inline pitch.
  - 1x Standardized circular round $\varnothing 6.0\text{ mm}$ status LED window with $0.8\text{ mm}$ top chamfer and $\varnothing 8.5\text{ mm} \times 1.2\text{ mm}$ underside retention lip.

### 2. Triple-Board Internal Mounting Bays
1. **Power Distribution Board (PDB) / Buck Converter (Left Bay)**:
   - Mounting Pattern: $24.0\text{ mm} \ (X) \times 37.0\text{ mm} \ (Y)$ M3 hole pitch for $32.0\text{ mm} \times 45.0\text{ mm}$ PCB oriented vertically along Y.
   - External Port: $\varnothing 11.5\text{ mm}$ high-current DC barrel jack (5.5×2.1mm) on Left Wall ($X=0$) directly feeding the PDB screw terminals.
2. **ESP32 Microcontroller Board (Front-Right Bay)**:
   - Mounting Pattern: $23.0\text{ mm} \ (X) \times 46.0\text{ mm} \ (Y)$ M3 hole pitch for $28.5\text{ mm} \times 51.5\text{ mm}$ PCB oriented along Y.
   - External Port: $12.0\text{ mm} \times 7.5\text{ mm}$ Micro-USB / USB-C cutout on Front Wall ($Y=0$) for firmware flashing and telemetry.
3. **PCA9685 16-Channel PWM Servo Driver (Rear-Right Bay)**:
   - Mounting Pattern: $55.88\text{ mm} \ (X) \times 19.05\text{ mm} \ (Y)$ ($2.20" \times 0.75"$) M2.5 hole pitch for $62.5\text{ mm} \times 25.4\text{ mm}$ PCB.
   - Pin Orientation: 16 servo pin headers face directly towards the rear wall wire slots.

### 3. Thermal & Structural Integrity
- **Ventilation**: Passive convection cooling chimney slots located on the bottom base directly below the PDB, PCA9685 driver, and ESP32 board to prevent heat buildup.
- **Fastening**: 4-sided toolless direct wall snap-fit system with 4x retention windows cut through the front/rear perimeter walls and 4x cantilever snap tabs on the panel, eliminating internal boss clutter.

### 4. 16 Discrete Motor Wire Ports & Integrated Dovetail Wire Raceway
- **16 Discrete Vertical Slots**: 16 individual vertical wire slots ($4.0\text{ mm} \times 16.0\text{ mm}$, reaching from $Z=8.0\text{ mm}$ to $Z=24.0\text{ mm}$) on $6.0\text{ mm}$ pitch with $2.0\text{ mm}$ solid structural pillars between each slot located on the right half of the rear wall ($X \in [41.0, 135.0\text{ mm}]$) directly behind the PCA9685 pin headers, allowing individual dedicated routing for each servo motor.
- **Integrated External Male Dovetail Key on Left End**: Flared male sliding dovetail key located on the left end of the rear wall ($X = 25.0\text{ mm}$ behind the PDB where no wire holes exist) with exact size and shape matching `frame_joiner.py` ($11.6\text{ mm}$ neck $\rightarrow$ $17.6\text{ mm}$ flare, $12.0\text{ mm}$ height, $45^\circ$ entry chamfers) with a high-capacity internal wire raceway conduit ($6.8\text{ mm} \times 8.6\text{ mm}$ with $1.0\text{ mm}$ corner fillets) passing directly into the enclosure power bay.
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
