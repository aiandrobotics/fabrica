# Fabrica — Smart Open-Source Cloth Folding Robot

[![Firmware Tests](https://img.shields.io/badge/firmware%20tests-911%2F911%20passing-brightgreen.svg)](firmware/)
[![FreeCAD API](https://img.shields.io/badge/CAD-FreeCAD%20Python%20Parametric-blue.svg)](cad-designs/)
[![ESP-IDF](https://img.shields.io/badge/ESP--IDF-v6.0.2%20FreeRTOS-red.svg)](firmware/)
[![Mobile App](https://img.shields.io/badge/mobile%20app-air--robotics--app-orange.svg)](https://github.com/aiandrobotics/air-robotics-app)
[![License](https://img.shields.io/badge/license-MIT%20%2F%20Open%20Source-green.svg)](LICENSE)

**Fabrica** is a fully open-source, automated garment folding system designed to be built for **$80–$150** using standard desktop 3D-printed parts, off-the-shelf electronics, and embedded software.

Utilizing a modular grid of hinged 3D-printed panels and intelligent parallel servo motor actuation, Fabrica folds garments (including t-shirts, long-sleeve shirts, towels, and trousers) in **8 to 12 seconds** per item with a single physical button tap or wireless mobile command.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Project Subsystems](#project-subsystems)
  - [1. CAD Designs & 3D Printed Hardware (`cad-designs/`)](#1-cad-designs--3d-printed-hardware-cad-designs)
  - [2. Embedded Firmware (`firmware/`)](#2-embedded-firmware-firmware)
  - [3. Mobile Application (`mobile-app/` & External Repo)](#3-mobile-application-mobile-app--external-repo)
  - [4. Project Documentation (`docs/`)](#4-project-documentation-docs)
- [Hardware Wiring & Electrical Schematics](#hardware-wiring--electrical-schematics)
- [Bill of Materials (BOM)](#bill-of-materials-bom)
- [Repository Structure](#repository-structure)
- [Quick Start Guide](#quick-start-guide)
  - [Exporting CAD Assets](#exporting-cad-assets)
  - [Building & Flashing Firmware](#building--flashing-firmware)
  - [Running Firmware Tests](#running-firmware-tests)
  - [Connecting the Mobile App](#connecting-the-mobile-app)
- [Daily Operation](#daily-operation)
- [License & Community](#license--community)

---

## System Architecture

Fabrica operates through a tightly coupled hardware, embedded firmware, and wireless mobile ecosystem:

```mermaid
graph TD
    subgraph Ecosystem
        CAD[CAD Designs<br/>cad-designs/]
        Docs[Documentation<br/>docs/]
        Firmware[ESP32 Firmware<br/>firmware/]
        App["Mobile App (AIR Robotics)<br/>github.com/aiandrobotics/air-robotics-app"]
    end

    User([User]) -->|Physical Buttons 1–4| Interface[Interface Enclosure & Status LED]
    User -->|Wireless Control| App
    App -.->|Bluetooth LE (FAB0 GATT)| Firmware
    Interface --> Firmware
    Firmware -->|I2C / 50Hz PWM| PCA[PCA9685 16-Ch Driver]
    PCA -->|PWM Pulses| Servos[MG996R High-Torque Servos]
    CAD -->|3D Printed Parts| Panels[Modular Hinged Grid Panels]
    Servos --> Panels
    Docs -.->|Assembly & Schematics| User
```

---

## Key Features

- **Affordable & Accessible BOM ($80–$150)**: Sourced entirely with standard 3D-printable parts, an ESP32 microcontroller, a PCA9685 driver board, and widely available MG996R metal-gear servos.
- **Fast 8–12 Second Folding Cycle**: Fluid multi-servo trajectory execution enables simultaneous opposite panel sweeps, reducing total cycle time by ~40% compared to serialized folding machines.
- **Dual Operating Modes**:
  - **Standalone Daily Run Mode**: Instant 1-touch execution of Presets 1–4 via physical tactile buttons on the robot console. No phone or computer needed for daily laundry routines.
  - **Wireless Mobile App Mode**: Complete Bluetooth Low Energy (BLE) control for designing custom routines, previewing sequences, live servo jog calibration, and real-time telemetry streaming.
- **Modular & Parametric Grid**: Standard 4×3 grid (expandable up to 16 motorized modules) engineered in FreeCAD Python with sliding dovetails, captive wire conduits, and heavy-duty continuous Ø13mm hinge knuckles.
- **Robust Hardware E-Stop (<50ms Abort)**: Tapping any physical button or issuing a BLE stop command during active movement halts motion within 50ms and returns all panels to a safe home position.
- **Fail-Safe Flash Storage**: Non-volatile NVS flash persistence with IEEE 802.3 CRC32 checksum verification to protect stored garment sequences against data corruption.

---

## Project Subsystems

### 1. CAD Designs & 3D Printed Hardware (`cad-designs/`)

The mechanical system is built programmatically using parametric FreeCAD Python scripts located in [`cad-designs/`](cad-designs/). All parts are optimized for standard 256 × 256 × 256 mm FDM 3D printers (with built-in scaling down to 180mm beds).

- **Modular Panels**:
  - **Base Chassis (`base_module.py`)**: Rigid stationary platform with internal hexagonal weight-reduction web, non-slip TPU foot recesses, and captive cable channels.
  - **Motorized Module (`motorized_frame.py`, `motorized_flap.py`, `motorized_servo_cover.py`)**: Active folding module with integrated MG996R servo well, continuous Ø13.0mm hinge axle, 25T metal servo horn pocket, and quick-release vented snap-cover.
  - **Follower Module (`follower_frame.py`, `follower_flap.py`)**: Passive folding extension with dual Ø13.5mm bearing knuckles and 8.0mm hex torque drive sockets.
  - **Interface Enclosure (`interface_case.py`, `interface_panel.py`)**: Angled 15° control deck housing the 4 tactile push buttons, status LED diffuser, ESP32, and PCA9685 circuit boards.
  - **Hardware Interlocks (`frame_joiner.py`, `hex_drive_coupler.py`)**: Click-lock hollow sliding dovetail bridges with wire routing tunnels and double-male 8.0mm hex torque coupler pins.
- **Pre-Exported Assets**: Clean STEP and STL files available in [`cad-designs/exports/`](cad-designs/exports/).
- **Slicer Profile**: Bambu Studio / OrcaSlicer project file ready for printing in [`cad-designs/3d-print/fabrica-bambu-lab-256.3mf`](cad-designs/3d-print/fabrica-bambu-lab-256.3mf).

### 2. Embedded Firmware (`firmware/`)

The embedded firmware runs natively on the **ESP32 DevKit v1** using **ESP-IDF v6.0.2** and a dual-core FreeRTOS architecture:

- **Core 0 (Motion Engine & Actuation)**:
  - High-precision 50 Hz PWM servo trajectory generator driving the PCA9685 controller over I2C (`GPIO 21 SDA`, `GPIO 22 SCL`).
  - Fluid parallel sweeps (e.g. folding left and right flaps simultaneously).
  - 300ms fold dwell and 200ms inter-step delay tuning.
  - Sub-50ms latched Emergency Stop (E-Stop) preemption handler.
- **Core 1 (UI, BLE Wireless & Storage)**:
  - 4-Button debouncer with 50ms low-pass filter and multi-gesture detection (short press vs. 3-second hold).
  - Non-blocking multi-pattern status LED engine (`GPIO 2`).
  - NVS Flash Sequence Manager with IEEE 802.3 CRC32 integrity validation.
  - Apache NimBLE GATT Server supporting native iOS (`CoreBluetooth`) and Android (`BluetoothGatt`) central connections.
  - Adaptive real-time telemetry streaming (10 Hz high-rate in motion / 1 Hz low-rate when idle).
- **Factory Default Presets**:
  - **Button 1**: Adult T-Shirt (Left flap $\to$ Right flap $\to$ Bottom waist $\to$ Top collar).
  - **Button 2**: Long-Sleeve Shirt (Collar staging $\to$ Dual side tucks $\to$ Waist fold).
  - **Button 3**: Trousers / Jeans (Parallel leg align $\to$ Bottom fold).
  - **Button 4**: Towel / Linen (Symmetric half-fold $\to$ Quarter-fold).
- **Automated Test Coverage**: 11 unit and integration test suites passing **911/911 host checks** with zero warnings (`-Wall -Wextra -Werror`).

### 3. Mobile Application (`mobile-app/` & External Repo)

> **Repository**: [https://github.com/aiandrobotics/air-robotics-app](https://github.com/aiandrobotics/air-robotics-app)

The mobile companion app is maintained in its own dedicated repository. The local [`mobile-app/`](mobile-app/) directory in this repository provides wire protocol specifications, GATT architecture, and integration documentation.

- **Technology**: Cross-platform mobile application communicating over Bluetooth Low Energy (BLE).
- **Key Mobile Capabilities**:
  - **Hold-to-Pair Workflow**: Secure pairing window (120 seconds) activated by holding any physical robot button for 3 seconds.
  - **Visual Sequence Builder**: Create custom garment folding profiles with step-by-step motor angle sliders and timing parameters.
  - **Stateless Routine Preview (`0x01`)**: Test experimental folding profiles on the robot without overwriting saved button slots.
  - **1-Touch Button Assignment (`0x0A`)**: Burn custom routines into robot physical Buttons 1–4 with automatic CRC32 calculation.
  - **Live 10 Hz Telemetry & Mirroring (`FAB2`)**: Live motor position tracking ($0^\circ \text{ to } 180^\circ$ across all channels) and 1:1 status LED mirroring.
  - **Live Servo Jog Calibration (`0x0D`)**: Interactively calibrate servo horn alignment with automated 10-second thermal cutoffs.
  - **1-Tap Factory Reset (`0x0C`)**: Instantly restore the four factory default presets.
- **Generic BLE Scanner Interoperability**: Compatible out of the box with standard tools like **nRF Connect for Mobile** and **LightBlue** (detailed in the [Firmware BLE Playbook](firmware/README.md#app-store-ble-test-app-playbook)).

### 4. Project Documentation (`docs/`)

The [`docs/`](docs/) directory contains guides and reference manuals:
- **Assembly Guides**: Step-by-step mechanical assembly of 3D-printed chassis, hinge knuckles, and servo horns.
- **Hardware Wiring**: Schematics, power isolation rules, and wiring diagrams for the ESP32, PCA9685, buttons, and status LED.
- **Bill of Materials (BOM)**: Comprehensive parts list and sourcing options.
- **Operating Instructions**: Standalone operation, routine programming, emergency stop recovery, and maintenance.

---

## Hardware Wiring & Electrical Schematics

```
                  +--------------------------+
                  |      ESP32 DevKit v1     |
                  |                          |
                  |         3V3 Logic   (1)  |------------> PCA9685 VCC
                  |         GND         (2)  |----+-------> PCA9685 GND
                  |         GPIO 21 SDA (3)  |---|--------> PCA9685 SDA
                  |         GPIO 22 SCL (4)  |---|--------> PCA9685 SCL
                  |                          |   |
                  |         GPIO 2 LED       |   |
                  |         GPIO 4  (Btn 1)  |   |
                  |         GPIO 16 (Btn 2)  |   |
                  |         GPIO 17 (Btn 3)  |   |
                  |         GPIO 5  (Btn 4)  |   |
                  +--------------------------+   |
                                                 |
  +-------------------------------+              |
  | External Power Supply         |              |
  | Regulated 5V - 6V DC (10A-20A)|              |
  |                               |              |
  |                     (+) V+    |--------------|-------> PCA9685 V+ (Servo Power Rail)
  |                     (-) GND   |--------------+-------> Common Ground Rail
  +-------------------------------+
```

> [!WARNING]
> **Power Isolation Rule**: High-torque MG996R servos can draw peak stall currents above 2.5A each. Never power the PCA9685 servo power terminal (`V+`) from the ESP32 3.3V or 5V (VIN) pin. Always use an external regulated 5V–6V DC power supply capable of 10A–20A surge capacity, sharing a common ground with the ESP32.

### Pinout Table

| ESP32 Pin | Direction | Active Level | Target Component / Function |
|---|---|---|---|
| `GPIO 2` | Output | High (1) | Status LED (Built-in DevKit LED + External Diffuser) |
| `GPIO 4` | Input (Pull-Up) | Low (0) | Button 1 (`B1`): Adult T-Shirt Preset / E-Stop / Hold-to-Pair (3s) |
| `GPIO 16` | Input (Pull-Up) | Low (0) | Button 2 (`B2`): Long-Sleeve Preset / E-Stop / Hold-to-Pair (3s) |
| `GPIO 17` | Input (Pull-Up) | Low (0) | Button 3 (`B3`): Trousers Preset / E-Stop / Hold-to-Pair (3s) |
| `GPIO 5` | Input (Pull-Up) | Low (0) | Button 4 (`B4`): Towel Preset / E-Stop / Hold-to-Pair (3s) |
| `GPIO 21` | In/Out (Open-Drain) | — | PCA9685 I2C Data (`SDA`) |
| `GPIO 22` | Output (Open-Drain) | — | PCA9685 I2C Clock (`SCL`) |

---

## Bill of Materials (BOM)

| Item | Component | Qty | Purpose | Est. Cost (USD) |
|---|---|---|---|---|
| 1 | **ESP32 DevKit v1** | 1 | Main dual-core microcontroller board | \$4.00 – \$6.00 |
| 2 | **PCA9685 16-Channel PWM Board** | 1 | Dedicated I2C servo controller | \$3.00 – \$5.00 |
| 3 | **MG996R Metal-Gear Servos** | 4 | High-torque 180° flap actuators | \$24.00 – \$32.00 |
| 4 | **DC Power Supply (5V or 6V, 10A–20A)** | 1 | High-current isolated servo power | \$15.00 – \$25.00 |
| 5 | **Panel-Mount DC Barrel Jack (5.5x2.1mm)** | 1 | Power enclosure inlet | \$1.00 |
| 6 | **16mm Momentary Push Buttons** | 4 | Physical user control pad (B1–B4) | \$6.00 – \$10.00 |
| 7 | **Diffused Status LED + 220Ω Resistor** | 1 | Enclosure status feedback | \$0.50 |
| 8 | **PETG or PLA+ Filament (1kg Spools)** | 2 | 3D printed chassis and flaps | \$30.00 – \$40.00 |
| 9 | **M3 Fasteners (Screws & Nuts)** | 1 pack | Frame assembly and servo mounting | \$5.00 – \$8.00 |
| **Total** | | | | **\$88.50 – \$127.00** |

---

## Repository Structure

```
fabrica/
├── cad-designs/               # FreeCAD parametric scripts & 3D models
│   ├── base_module.py         # Stationary rigid base chassis
│   ├── motorized_frame.py     # Active motorized chassis (MG996R servo well)
│   ├── motorized_flap.py      # Active flap with 25T horn pocket
│   ├── motorized_servo_cover.py # Snap-cover with cooling gills
│   ├── follower_frame.py      # Passive follower chassis
│   ├── follower_flap.py       # Passive follower flap
│   ├── interface_case.py      # Dual-board electronics enclosure
│   ├── interface_panel.py     # 15° sloped button & LED faceplate
│   ├── frame_joiner.py        # Interlocking dovetail joiners
│   ├── hex_drive_coupler.py   # Double-male 8.0mm hex drive pin
│   ├── export_all.py          # Batch export script (STEP & STL)
│   ├── 3d-print/              # Bambu Studio 3MF slicer projects
│   └── exports/               # Exported STEP and STL assets
├── firmware/                  # ESP-IDF v6.0.2 FreeRTOS embedded C firmware
│   ├── main/                  # Firmware source modules
│   │   ├── main.c             # App startup & dual-core task launch
│   │   ├── config.h           # System pinout & operational constants
│   │   ├── command.h          # Source-agnostic command schema
│   │   ├── state_machine.c/h  # System state machine coordinator
│   │   ├── pca9685.c/h        # 16-channel 12-bit PWM I2C driver
│   │   ├── motion.c/h         # Parallel trajectory & sweep engine
│   │   ├── buttons.c/h        # 50ms debouncer & gesture detector
│   │   ├── led.c/h            # Non-blocking status LED pattern driver
│   │   ├── storage.c/h        # NVS flash preset storage with CRC32
│   │   ├── ble_transport.c/h  # Apache NimBLE GATT server (FAB0)
│   │   ├── remote_cmd.c/h     # BLE command parser & dispatcher
│   │   └── telemetry.c/h      # Adaptive 10 Hz / 1 Hz telemetry engine
│   ├── test/                  # Host unit test suites (911 passing checks)
│   └── Makefile               # Unit test runner
├── mobile-app/                # Mobile app integration guide & wire specs
│   └── README.md              # BLE GATT specs & external repository link
├── docs/                      # Technical documentation & guides
│   └── README.md              # Guides, wiring, BOM, and operations
├── specs/                     # System specifications & reference visuals
│   ├── mission.md             # High-level mission specification
│   └── reference-images/      # 3D renderings and architecture diagrams
└── CHANGELOG.md               # Project version and milestone history
```

---

## Quick Start Guide

### Exporting CAD Assets

To generate all STEP and STL files from the parametric FreeCAD Python scripts:

```bash
cd cad-designs
python3 export_all.py
```

To run an individual script headlessly:

```bash
./run.sh motorized_frame.py
```

### Building & Flashing Firmware

Ensure you have [ESP-IDF v6.0.2](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/) installed and sourced:

```bash
cd firmware
idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### Running Firmware Tests

Run the complete 11-suite host test harness (requires `gcc` or `clang`):

```bash
cd firmware
make test
```

To view verbose assertions across all 911 test checks:

```bash
make test-verbose
```

### Connecting the Mobile App

1. Clone and build the companion mobile app from its repository:  
   **[https://github.com/aiandrobotics/air-robotics-app](https://github.com/aiandrobotics/air-robotics-app)**
2. On the physical Fabrica robot, **hold any button (B1–B4) for 3 seconds** to enter BLE pairing mode (`LED_STATE_BLE_PAIRING`).
3. Scan for `Fabrica-XXXX` in the app and tap connect.
4. *Alternatively*, use **nRF Connect for Mobile** or **LightBlue** to connect and test commands directly using the [Firmware BLE Playbook](firmware/README.md#app-store-ble-test-app-playbook).

---

## Daily Operation

- **Fold Garments**: Tap **Button 1**, **2**, **3**, or **4** for the corresponding garment preset.
- **Emergency Stop**: Tap **any button** during movement to immediately abort motion (<50ms) and return all panels to rest.
- **Enter BLE Pairing**: Hold **any button for 3 seconds** in idle state.
- **Clear All BLE Bonds**: Hold **Button 1 + Button 4 simultaneously for 5 seconds**.

---

## License & Community

This project is fully open source under the MIT License. Contributions to CAD models, firmware improvements, documentation, and the [AIR Robotics App](https://github.com/aiandrobotics/air-robotics-app) are welcome.

