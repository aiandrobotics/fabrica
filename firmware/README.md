# Embedded Firmware — Fabrica Cloth Folding Robot

This directory contains the production-grade embedded C / FreeRTOS firmware running natively on the **ESP32 Dev Board v1** for the **Fabrica Cloth Folding Robot**.

---

## System Overview

The Fabrica firmware coordinates the physical user interface, non-volatile sequence storage, system state machine, and the **PCA9685 16-channel 12-bit PWM driver** over I2C to actuate high-torque servo motors (MG996R) driving modular cloth-folding grids.

* **Target Microcontroller**: ESP32 Dev Board v1 (Xtensa dual-core LX6 @ 240 MHz, 520 KB SRAM, 4 MB SPI Flash)
* **Actuation Driver**: PCA9685 16-Channel 12-Bit PWM Driver over I2C (`GPIO 21 SDA`, `GPIO 22 SCL`)
* **User Interface**: 4 Push Buttons (`B1–B4`) + 1 Multi-Pattern Status LED (`GPIO 2`)
* **Operating Architecture**: Dual-Core FreeRTOS (Core 0: Motion & I2C Bus / Core 1: UI, Buttons & NVS Storage)
* **Operating Modes**:
  1. **Daily Run Mode**: Instant 1-touch execution of Presets 1–4, synchronized parallel dual-servo sweeps, 300ms fold dwell, 200ms inter-step delay, and $<50\text{ms}$ Emergency Stop preemption.
  2. **Visual Staging Programming Mode**: Computer-free on-device sequence teaching (3s hold entry, B1 cycle/nudge $15^\circ$, B2 stage/toggle $30^\circ$, B3 lock step, B4 save to NVS flash, 20s inactivity watchdog).

---

## Hardware Pinout & Wiring Specifications

### 1. ESP32 Dev Board v1 Pin Allocations

| Signal Name | ESP32 GPIO | Direction | Pin Configuration | Active Level | Connected Peripheral |
|---|---|---|---|---|---|
| `STATUS_LED_GPIO` | `GPIO 2` | Output | Push-Pull / No Pull | High (1) | Status LED (Built-in on DevKit) |
| `BTN1_GPIO` | `GPIO 4` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 1 (B1): Preset 1 / Cycle & Nudge |
| `BTN2_GPIO` | `GPIO 16` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 2 (B2): Preset 2 / Stage & Toggle |
| `BTN3_GPIO` | `GPIO 17` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 3 (B3): Preset 3 / Lock Step |
| `BTN4_GPIO` | `GPIO 5` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 4 (B4): Preset 4 / Save & Exit |
| `I2C_SDA_GPIO` | `GPIO 21` | In/Out | Open-Drain + Pull-Up | — | PCA9685 SDA (I2C Data) |
| `I2C_SCL_GPIO` | `GPIO 22` | Output | Open-Drain + Pull-Up | — | PCA9685 SCL (I2C Clock) |

### 2. PCA9685 PWM Driver Wiring & Power Isolation

```
           +------------------+              +----------------------+
           |  ESP32 DevKit    |              |  PCA9685 16-Ch PWM   |
           |                  |              |                      |
           |             3V3  |------------->| VCC (Logic Power)    |
           |             GND  |---+--------->| GND (Common Ground)  |
           |         GPIO 21  |---|--------->| SDA (I2C Data)       |
           |         GPIO 22  |---|--------->| SCL (I2C Clock)      |
           +------------------+   |          | OE  (Grounded/Active)|
                                  |          +----------------------+
                                  |                     |
     +-----------------------+    |                     |
     | External 5V/6V Supply |    |           [Servo Header Rails]
     | (10A - 20A DC)        |    |                     |
     |                   (+) |----+-------------------->| V+ (Servo Power)
     |                   (-) |------------------------->| GND (Common Ground)
     +-----------------------+
```

> **IMPORTANT**: Never power high-torque MG996R servos directly from the ESP32 3.3V or 5V (VIN) rail. Always use an external regulated 5V–6V DC power supply capable of delivering 10A–20A surge currents, with common ground shared between the ESP32 and PCA9685.

### 3. Physical Servo Flap Channel Mapping (Standard 4-Panel Grid)

| Channel | Identifier | Description | Resting Angle | Staged Angle | Fold Angle |
|---|---|---|---|---|---|
| **0** | `SERVO_FLAP_LEFT` | Left side folding flap | $0.0^\circ$ ($500\,\mu\text{s}$ / 102 counts) | $30.0^\circ$ ($833\,\mu\text{s}$ / 171 counts) | $180.0^\circ$ ($2500\,\mu\text{s}$ / 512 counts) |
| **1** | `SERVO_FLAP_RIGHT` | Right side folding flap | $0.0^\circ$ ($500\,\mu\text{s}$ / 102 counts) | $30.0^\circ$ ($833\,\mu\text{s}$ / 171 counts) | $180.0^\circ$ ($2500\,\mu\text{s}$ / 512 counts) |
| **2** | `SERVO_FLAP_BOTTOM` | Bottom / waist folding flap | $0.0^\circ$ ($500\,\mu\text{s}$ / 102 counts) | $30.0^\circ$ ($833\,\mu\text{s}$ / 171 counts) | $180.0^\circ$ ($2500\,\mu\text{s}$ / 512 counts) |
| **3** | `SERVO_FLAP_TOP` | Top / collar folding flap | $0.0^\circ$ ($500\,\mu\text{s}$ / 102 counts) | $30.0^\circ$ ($833\,\mu\text{s}$ / 171 counts) | $180.0^\circ$ ($2500\,\mu\text{s}$ / 512 counts) |
| **4–15** | Expansion Channels | Auxiliary folding modules | $0.0^\circ$ ($500\,\mu\text{s}$ / 102 counts) | $30.0^\circ$ ($833\,\mu\text{s}$ / 171 counts) | $180.0^\circ$ ($2500\,\mu\text{s}$ / 512 counts) |

---

## Dual-Core Architecture & Operating Mechanics

The firmware uses FreeRTOS symmetric multiprocessing to cleanly separate real-time hardware motion from the user interface and storage operations:

```
                  +----------------------------------------------+
                  |               ESP32 DUAL CORE                |
                  +----------------------------------------------+
                                |                              |
           CORE 0 (Motion Engine)           CORE 1 (System & UI Management)
           ----------------------           --------------------------------
           * app_motion_task (Priority 10)  * app_ui_task (Priority 5)
           * Real-time 50Hz PWM Trajectory  * 50ms Button Low-Pass Debounce
           * 300ms Fold Dwell Timing        * Short Tap vs 3s Long-Press
           * 200ms Inter-Step Delays        * Visual Staging State Machine
           * PCA9685 I2C Bus Management     * app_led_task (Priority 3)
           * <50ms E-Stop Preemption Abort  * NVS Flash Storage Manager
                                \              /
                                 \            /
                              [ FreeRTOS IPC ]
                              - Unified Command Queue (xCommandQueue)
                              - System Event Group (xEventGroupHandle)
```

---

## Factory Preset Library

The firmware is pre-seeded on initial boot with 4 factory folding routines verified against standard garment geometries:

* **Preset 1 (Adult T-Shirt, 3 Steps)**:
  - Step 1: Left Flap fold ($0^\circ \to 180^\circ \to 0^\circ$)
  - Step 2: Right Flap fold ($0^\circ \to 180^\circ \to 0^\circ$)
  - Step 3: Bottom Flap fold ($0^\circ \to 180^\circ \to 0^\circ$)
* **Preset 2 (Long-Sleeve Shirt, 4 Steps)**:
  - Step 1: Synchronized parallel dual-sleeve fold (Left & Right Flaps together)
  - Step 2: Left Body Flap fold
  - Step 3: Right Body Flap fold
  - Step 4: Bottom Flap fold
* **Preset 3 (Trousers / Jeans, 2 Steps)**:
  - Step 1: Vertical half fold (Left Flap)
  - Step 2: Bottom fold (Bottom Flap)
* **Preset 4 (Towel / Linen, 3 Steps)**:
  - Step 1: Left half fold (Left Flap)
  - Step 2: Right quarter fold (Right Flap)
  - Step 3: Bottom final press fold (Bottom Flap)

---

## Operator Manual

### 1. Daily Run Mode (Laundry Folding)
1. Place garment centered flat on the folding grid.
2. Short tap (<500ms) any button **B1–B4** to trigger the corresponding routine:
   - **B1**: Adult T-Shirt (Preset 1)
   - **B2**: Long-Sleeve Shirt (Preset 2)
   - **B3**: Trousers / Jeans (Preset 3)
   - **B4**: Towel / Linen (Preset 4)
3. Status LED illuminates **Solid ON** during execution and returns to **Heartbeat** upon completion.

### 2. Emergency Stop (E-Stop)
* Tapping **any button** while folding motion is active immediately halts PWM pulses, commands all 16 servos flat to $0^\circ$ in $<50\text{ms}$, and triggers **5 rapid flashes** on the Status LED.

### 3. Visual Staging Programming Mode (On-Device Teaching)
1. **Enter Mode**: Press and hold any preset button (**B1–B4**) for **3 seconds**. The Status LED transitions to a **Slow Blink (0.5 Hz)** and all flaps flatten.
2. **Cycle & Identify (B1)**: Tap B1 to cycle through servo channels 0–15. The target panel performs a brief $15^\circ$ mechanical twitch for visual identification.
3. **Stage Flap (B2)**: Tap B2 to lift the identified panel to $30^\circ$ and hold. Tap B2 again to unstage and return flat ($0^\circ$). Up to 2 flaps can be staged simultaneously for parallel folding.
4. **Lock Step (B3)**: Tap B3 to lock staged flap(s) into the step buffer. Staged flaps drop flat to $0^\circ$, the Status LED delivers **2 fast flashes**, and the step index advances.
5. **Save & Exit (B4)**: Tap B4 to commit the sequence to NVS flash storage with CRC32 integrity checksums. The Status LED illuminates **Solid ON for 2.0 seconds** before returning to Daily Run Mode.
6. **Safety Watchdog**: If 20 seconds elapse without any button interaction, all flaps drop flat to $0^\circ$, the buffer is discarded, and the unit safely exits to Run Mode.

### 4. Status LED Visual Feedback Patterns

| Pattern | Sequence Timing | System State |
|---|---|---|
| **Soft Heartbeat** | 10% duty cycle / 0.5 Hz | Idle / Ready for garment |
| **Solid ON** | Continuous ON | Routine in motion |
| **Slow Blink** | 1.0s ON / 1.0s OFF (0.5 Hz) | Visual Staging Programming Mode |
| **Double Flash** | 2 fast pulses (80ms ON / 80ms OFF) | Step locked into sequence buffer |
| **Save Success** | Solid ON for 2.0 seconds | Sequence committed to NVS flash |
| **Input Error** | 3 fast flashes (60ms ON / 60ms OFF) | 3rd motor attempt / empty preset |
| **Emergency Stop** | 5 rapid flashes (50ms ON / 50ms OFF) | E-Stop triggered mid-motion |

---

## Specifications & Documentation

* **[Mission Specification](file:///Users/intelligentmachine/Documents/workspace/fabrica/firmware/specs/mission.md)**: High-level firmware mission, operating modes, subsystem architecture, and success criteria.
* **[Tech Stack Specification](file:///Users/intelligentmachine/Documents/workspace/fabrica/firmware/specs/tech-stack.md)**: Embedded toolchain, ESP-IDF drivers, dual-core task distribution, pinouts, timing constants, PCA9685 configuration, and unified command protocol.
* **[Roadmap Specification](file:///Users/intelligentmachine/Documents/workspace/fabrica/firmware/specs/roadmap.md)**: Phased implementation roadmap and testable milestones from Phase 0 to Phase 8.

---

## Build & Test Instructions

### 1. Host-Based Unit & Stress Testing
Run the complete host test harness validating all subsystems (Headers, UI, PCA9685, Storage, Motion, State Machine, and End-to-End Stress):
```bash
make test
```
All 7 test suites execute in $<1\text{s}$ with 553 automated checks passing:
```
- test/test_headers.c        (43 checks)
- test/test_ui_subsystem.c   (61 checks)
- test/test_pca9685.c        (82 checks)
- test/test_storage.c        (66 checks)
- test/test_motion.c         (74 checks)
- test/test_state_machine.c  (167 checks)
- test/test_e2e_stress.c     (60 checks)
```

### 2. ESP-IDF Target Compilation
Build the firmware binary targeting the ESP32 Dev Board v1:
```bash
idf.py build
```

### 3. Flashing & Serial Monitor
Flash the firmware to an attached ESP32 Dev Board and monitor diagnostic output:
```bash
idf.py -p /dev/tty.usbserial-* flash monitor
```