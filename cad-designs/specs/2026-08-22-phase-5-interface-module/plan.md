# Implementation Plan — Phase 5: Interface Module & Electronics Enclosure

## Overview
Phase 5 implements the **Interface Module & Electronics Enclosure** for the Fabrica Cloth Folding Robot. This module attaches seamlessly into the 4×3 grid (or standalone beside it) via standardized dovetail joiners, housing the robot's primary control and power electronics (**ESP32 DevKit** + **PCA9685 16-Channel PWM Servo Driver**) beneath an ergonomic **15° forward-angled control deck** featuring **4x Ø16.0 mm tactile push buttons** and a **multi-state status LED diffuser window**.

---

## Task Group 1: Parametric Setup & CAD Reference Models
1. Verify `params.py` constants:
   - `INTERFACE_PANEL_WIDTH = 240.0` (or `220.0` matching modular frame width)
   - `INTERFACE_PANEL_HEIGHT = 120.0` (or matching grid increment)
   - `INTERFACE_PANEL_THICKNESS = 25.0`
   - `CONTROL_DECK_ANGLE = 15.0`
   - `BUTTON_HOLE_DIA = 16.00`
   - `DC_JACK_DIAMETER = 11.50`
2. Create CAD electronic component reference solids for accurate envelope fit & mounting boss location:
   - **PCA9685 Board Reference**: $62.5 \times 25.4 \times 12.0\text{ mm}$ with 4x M2.5 mounting holes ($56.5 \times 19.5\text{ mm}$ spacing) and terminal block + pin header envelopes.
   - **ESP32 DevKit V1 Reference**: $51.5 \times 28.5 \times 10.0\text{ mm}$ with 4x M3 mounting holes ($46.0 \times 23.0\text{ mm}$ spacing) and micro-USB / USB-C connector envelope.
   - **16mm Push Button Reference**: $\varnothing 16.0\text{ mm}$ threaded barrel with bezel and solder lug envelope ($25.0\text{ mm}$ depth).
   - **Status LED Reference**: $\varnothing 5.0\text{ mm}$ / rectangular light pipe diffuser solid.

---

## Task Group 2: Dual-Board Controller Enclosure Chassis (`controller_case.py`)
1. **Outer Chassis & Base Geometry**:
   - Monolithic rigid lower enclosure body with $3.0\text{ mm}$ structural outer walls, $0.4\text{ mm}$ Elephant's Foot relief chamfers, and anti-slip rubber foot sockets ($\varnothing 20.1 \times 2.0\text{ mm}$).
   - Front-sloped mating rim matching the 15° forward incline of the top faceplate.
2. **Internal Mounting Bosses & Electronics Layout**:
   - 4x M2.5 mounting standoffs with core pilot holes for the **PCA9685 16-Channel PWM Driver**.
   - 4x M3 mounting standoffs with core pilot holes for the **ESP32 DevKit**.
   - Height elevations ensuring component clearance above the base floor for passive airflow.
3. **Connectors, Wiring & Thermal Management**:
   - $\varnothing 11.5\text{ mm}$ circular cutout for panel-mount 5.5×2.1mm DC power barrel jack (high-current 5V/6V servo bus).
   - Rectangular side/rear cutout for ESP32 USB programming and debug access.
   - Internal zip-tie strain-relief saddles and wire raceways separating DC power, I2C signal, and 16-channel servo ribbon harnesses.
   - Convection cooling chimney ventilation slots positioned directly underneath both the PCA9685 driver IC and the ESP32 module.
4. **Grid Integration**:
   - Standardized sliding dovetail sockets ($12\text{ mm}$ neck $\to 18\text{ mm}$ flare $\times 12\text{ mm}$ depth) with $\varnothing 6.0\text{ mm}$ through-floor push-out access holes and $1.5\text{ mm}$ filleted wire pass-through ports connecting cleanly to adjacent grid frames.

---

## Task Group 3: 15° Angled Interface Faceplate (`interface_panel.py`)
1. **Ergonomic Control Deck Geometry**:
   - 15° forward-angled top surface providing optimal viewing and tactile interaction angles for tabletop operation.
   - $1.2\text{ mm}$ perimeter shadow accent bevel and $0.6\text{ mm}$ micro-grip diamond surface texture.
2. **Button & Indicator Cutouts**:
   - 4x inline $\varnothing 16.0\text{ mm}$ button cutouts with $0.8\text{ mm}$ entrance chamfers, spaced $28.0\text{ mm}$ apart for comfortable finger access.
   - Dedicated status LED diffuser window with internal retention lip for snap-in or glued translucent light pipe.
   - Debossed function icon reticles ($0.4\text{ mm}$ depth) above/around buttons (e.g. `[►] Fold`, `[❚❚] Pause`, `[≡] Mode`, `[↺] Reset`).
3. **Retention & Fastening**:
   - 4x recessed corner M3 screw counterbores mating directly with corner chassis bosses (or dual snap-fit retention clips) for secure, rattle-free assembly and easy service access.

---

## Task Group 4: Interface Sub-Assembly & Multi-Body Kinematics (`assembly_interface_module.py`)
1. **Assembly Construction**:
   - Combine `controller_case`, `interface_panel`, PCA9685 reference solid, ESP32 reference solid, 4x 16mm button reference solids, and status LED diffuser into a single multi-body assembly model.
2. **Clearance & Interference Verification**:
   - Validate zero volumetric overlap ($0.0000\,\text{mm}^3$) between all mating components using FreeCAD MCP `check_interference`.
   - Verify proper cable routing clearance around PCA9685 servo pin headers and ESP32 USB port.

---

## Task Group 5: Validation, Pipeline Export & Documentation
1. **Headless Visual Validation**:
   - Execute multi-view burst renders (`Isometric`, `Front`, `Top`, `Right`, `Bottom`) and exploded view via `render_freecad_script` and `inspect_freecad_assembly`.
2. **Production Pipeline Export**:
   - Integrate `interface_panel.py`, `controller_case.py`, and `assembly_interface_module.py` into `export_all.py`.
   - Verify 100% build pass rate across all STEP and STL production models.
3. **Documentation & Changelog**:
   - Update `CHANGELOG.md` with complete Phase 5 release details.
