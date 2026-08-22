# Requirements — Phase 5: Interface Module & Electronics Enclosure

## Scope
Phase 5 covers the complete 3D mechanical CAD modeling, parametric definitions, and multi-body assembly validation for:
1. `controller_case.py`: Protective lower electronics chassis housing the dual circuit boards, power input, wire channels, and cooling vents.
2. `interface_panel.py`: 15° forward-angled ergonomic user interaction top deck with 4x Ø16mm push button cutouts and a multi-color status LED window.
3. `assembly_interface_module.py`: Complete sub-assembly model verifying clearance, fastener alignments, and cable pass-throughs.

---

## Decisions & Hardware Specifications

### 1. Dual Internal Circuit Boards
- **PCA9685 16-Channel 12-Bit PWM Servo Driver Board**:
  - PCB Envelope: $62.5 \times 25.4 \times 12.0\text{ mm}$ (including screw terminal & 3-pin headers).
  - Mounting Hole Pattern: 4x M2.5 holes ($56.5\text{ mm} \times 19.5\text{ mm}$ rectangular spacing).
  - Mounting Method: Raised M2.5 screw bosses with $\varnothing 2.2\text{ mm}$ core pilot holes.
  - Connector Orientations: 16x 3-pin servo headers facing toward internal wire raceways leading to frame dovetail conduit ports.
- **ESP32 Microcontroller Board (ESP32 DevKit V1 / NodeMCU-32S)**:
  - PCB Envelope: $51.5 \times 28.5 \times 10.0\text{ mm}$.
  - Mounting Hole Pattern: 4x M3 holes ($46.0\text{ mm} \times 23.0\text{ mm}$ rectangular spacing).
  - Mounting Method: Raised M3 screw bosses with $\varnothing 2.6\text{ mm}$ core pilot holes.
  - Programming Port: Micro-USB / USB-C port aligned flush with outer enclosure port cutout.

### 2. User Interaction Controls
- **4x Top Interaction Buttons**:
  - Diameter: $\varnothing 16.0\text{ mm}$ standard circular panel cutout (`BUTTON_HOLE_DIA = 16.00`).
  - Spacing: Equidistant linear arrangement along the 15° angled top deck ($28.0\text{ mm}$ center-to-center pitch).
  - Hole Details: $0.8\text{ mm} \times 45^\circ$ top chamfer for flush bezel seating and smooth finger touch.
  - Intended Functions: `Button 1: Start / Fold`, `Button 2: Pause / Stop`, `Button 3: Mode / Preset Select`, `Button 4: Reset / Calibrate`.
- **Multi-State Status LED Indicator**:
  - Light Aperture: Dedicated $12.0 \times 4.0\text{ mm}$ rectangular or $\varnothing 5.0\text{ mm}$ circular diffuser window with internal retention lip.
  - Purpose: Multi-color visual feedback (Ready, Active Fold Cycle, Paused, Fault/Stall, WiFi Connected).

### 3. Case Enclosure & Ergonomics
- **Deck Angle**: $15.0^\circ$ ergonomic forward tilt (`CONTROL_DECK_ANGLE = 15.0`).
- **Power Inlet**: $\varnothing 11.5\text{ mm}$ circular hole for standard panel-mount DC barrel jack (5.5×2.1mm) powering the high-current servo power bus.
- **Ventilation**: Passive convection cooling chimney slots ($2.0\text{ mm} \times 15.0\text{ mm}$) located on the bottom base directly below the PCA9685 driver and ESP32 board to prevent heat buildup.
- **Fastening**: 4x corner M3 countersunk screws securing the faceplate to the lower case.

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
