# Embedded Firmware — Fabrica Cloth Folding Robot

This directory contains the production-grade embedded C / FreeRTOS firmware running natively on the **ESP32 Dev Board v1** for the **Fabrica Cloth Folding Robot**.

---

## System Overview

The Fabrica firmware coordinates the physical user interface, non-volatile sequence storage, system state machine, and the **PCA9685 16-channel 12-bit PWM driver** over I2C to actuate high-torque servo motors (MG996R) driving modular cloth-folding grids.

* **Target Microcontroller**: ESP32 Dev Board v1 (Xtensa dual-core LX6 @ 240 MHz, 520 KB SRAM, 4 MB SPI Flash)
* **Actuation Driver**: PCA9685 16-Channel 12-Bit PWM Driver over I2C (`GPIO 21 SDA`, `GPIO 22 SCL`)
* **User Interface**: 4 Push Buttons (`B1–B4`) + 1 Multi-Pattern Status LED (`GPIO 2`)
* **Operating Architecture**: Dual-Core FreeRTOS (Core 0: Motion & I2C Bus / Core 1: UI, Buttons, NimBLE Wireless, Telemetry & NVS Storage)
* **Operating Modes**:
  1. **Daily Run Mode (Physical Buttons B1–B4)**: Instant 1-touch execution of Presets 1–4 (pre-seeded with 4 factory defaults out of the box), synchronized parallel dual-servo sweeps, 300ms fold dwell, 200ms inter-step delay, and $<50\text{ms}$ Emergency Stop preemption on any button tap.
  2. **Wireless Mobile Programming & Control (BLE)**: Custom sequence creation, live servo calibration jogging, stateless sequence previewing, real-time 10 Hz / 1 Hz adaptive telemetry streaming, and assigning custom sequences to Buttons 1–4 are handled visually over Bluetooth Low Energy.

---

## Hardware Pinout & Wiring Specifications

### 1. ESP32 Dev Board v1 Pin Allocations

| Signal Name | ESP32 GPIO | Direction | Pin Configuration | Active Level | Connected Peripheral |
|---|---|---|---|---|---|
| `STATUS_LED_GPIO` | `GPIO 2` | Output | Push-Pull / No Pull | High (1) | Status LED (Built-in on DevKit) |
| `BTN1_GPIO` | `GPIO 4` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 1 (B1): Preset 1 (Default: Adult T-Shirt) / E-Stop / Hold-to-Pair (3s) |
| `BTN2_GPIO` | `GPIO 16` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 2 (B2): Preset 2 (Default: Long-Sleeve Shirt) / E-Stop / Hold-to-Pair (3s) |
| `BTN3_GPIO` | `GPIO 17` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 3 (B3): Preset 3 (Default: Trousers / Jeans) / E-Stop / Hold-to-Pair (3s) |
| `BTN4_GPIO` | `GPIO 5` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | Tactile Button 4 (B4): Preset 4 (Default: Towel / Linen) / E-Stop / Hold-to-Pair (3s) |
| `I2C_SDA_GPIO` | `GPIO 21` | In/Out | Open-Drain + Pull-Up | — | PCA9685 SDA (I2C Data) |
| `I2C_SCL_GPIO` | `GPIO 22` | Output | Open-Drain + Pull-Up | — | PCA9685 SCL (I2C Clock) |

> **B1 + B4 Hardware Bond Reset**: Holding **Button 1 + Button 4 simultaneously for 5 seconds** clears all stored BLE bonds from NVS flash (`CMD_CLEAR_BLE_BONDS`) and resets the wireless subsystem.

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
           CORE 0 (Motion Engine)           CORE 1 (UI, BLE Wireless & System Coordination)
           ----------------------           ------------------------------------------------
           * app_main (Command & Motion)    * app_ble_task (Priority 4, NimBLE GATT Server)
           * Real-time 50Hz PWM Trajectory  * app_telem_task (Priority 3, Adaptive Telemetry)
           * 300ms Fold Dwell Timing        * app_ui_task (Priority 5, 50ms Debounce)
           * 200ms Inter-Step Delays        * Short Tap vs 3s Hold (BLE Pairing)
           * PCA9685 I2C Bus Management     * System State Machine Coordinator
           * <50ms E-Stop Preemption Abort  * app_led_task (Priority 2, Status LED Engine)
                                            * NVS Flash Storage Manager
                                \              /
                                 \            /
                               [ FreeRTOS IPC ]
                               - Unified Command Queue (xCommandQueue)
                               - System Event Group (xEventGroupHandle)
```

---

## Factory Preset Library

The firmware is pre-seeded on initial boot with 4 factory folding routines verified against standard garment geometries, exercising all 4 servo flap motors:

* **Preset 1 (Adult T-Shirt, 4 Steps)**:
  - Step 1: Left Flap fold ($0^\circ \to 180^\circ \to 0^\circ$, Ch 0)
  - Step 2: Right Flap fold ($0^\circ \to 180^\circ \to 0^\circ$, Ch 1)
  - Step 3: Bottom Flap fold ($0^\circ \to 180^\circ \to 0^\circ$, Ch 2)
  - Step 4: Top / Collar Flap fold ($0^\circ \to 180^\circ \to 0^\circ$, Ch 3)
  > *Tapping Button 1 immediately tests all 4 flap motors in sequence!*
* **Preset 2 (Long-Sleeve Shirt, 5 Steps)**:
  - Step 1: Synchronized parallel dual-sleeve fold (Left & Right Flaps together, Ch 0 + 1)
  - Step 2: Top / Collar Flap fold (Ch 3)
  - Step 3: Left Body Flap fold (Ch 0)
  - Step 4: Right Body Flap fold (Ch 1)
  - Step 5: Bottom Flap fold (Ch 2)
* **Preset 3 (Trousers / Jeans, 3 Steps)**:
  - Step 1: Vertical half fold (Left Flap, Ch 0)
  - Step 2: Bottom fold (Bottom Flap, Ch 2)
  - Step 3: Top waistband fold (Top Flap, Ch 3)
* **Preset 4 (Towel / Linen, 4 Steps)**:
  - Step 1: Left half fold (Left Flap, Ch 0)
  - Step 2: Right quarter fold (Right Flap, Ch 1)
  - Step 3: Bottom fold (Bottom Flap, Ch 2)
  - Step 4: Top final fold (Top Flap, Ch 3)

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
* Tapping **any physical button** while folding motion is active immediately halts PWM pulses, commands all 16 servos flat to $0^\circ$ in $<50\text{ms}$, and latches `STATE_ESTOP` (Status LED emits **5 rapid flashes**).
* Tap any button again or send Opcode `0x02` (`CMD_STOP_SEQUENCE`) over BLE to clear E-Stop back to `STATE_IDLE_RUN`.

### 3. Status LED Visual Feedback Patterns

| Pattern | Sequence Timing | System State | Meaning |
|---|---|---|---|
| **Soft Heartbeat** | 10% duty cycle / 0.5 Hz | `LED_STATE_IDLE` | Ready for garment / idle |
| **Solid ON** | Continuous ON | `LED_STATE_RUNNING` | Folding routine actively executing |
| **Solid ON (1.0s)** | 1.0s solid ON pulse | `LED_STATE_BLE_CONNECTED` | Phone connected & bonded |
| **Solid ON (2.0s)** | 2.0s solid ON pulse | `LED_STATE_SAVE_SUCCESS` | Preset sequence saved in NVS |
| **Fast Double-Blink** | 100ms ON / 100ms OFF / 100ms ON / 500ms OFF | `LED_STATE_BLE_PAIRING` | BLE Pairing Mode active (indefinite on 0 bonds, 120s for multi-device) |
| **Fast Double-Blink (3.0s)** | 3 double-blinks over 3.0s | `LED_STATE_IDENTIFY` | Visual locator (`CMD_IDENTIFY_ROBOT`, `0x0E`) |
| **Input Error** | 3 fast flashes (60ms ON / 60ms OFF) | `LED_STATE_INPUT_ERROR` | Empty preset or invalid argument |
| **Emergency Stop** | 5 rapid flashes (50ms ON / 50ms OFF) | `LED_STATE_ESTOP` | Emergency stop latched |

---

## BLE Wireless Interface & App Store Test App Playbook

The robot can be fully monitored, calibrated, and controlled using off-the-shelf App Store BLE scanner apps (**nRF Connect for Mobile** or **LightBlue**) on iOS and Android with zero custom code required.

### 1. GATT Services & Characteristics Hierarchy

**Primary Custom Service UUID**: `0000FAB0-0000-1000-8000-00805F9B34FB`

| Characteristic | Short UUID | 128-bit Full UUID | Properties | Descriptors | Description |
|---|---|---|---|---|---|
| **Control Point** | `FAB1` | `0000FAB1-0000-1000-8000-00805F9B34FB` | `Write`, `Write Without Response` | `0x2901` User Desc: *"Fabrica Control Point (FAB1)"* | Command ingress for routine triggers, raw preview, jog calibration, and E-Stop |
| **Telemetry** | `FAB2` | `0000FAB2-0000-1000-8000-00805F9B34FB` | `Read`, `Notify` | CCCD `0x2902`, `0x2901` User Desc: *"Fabrica Status & Telemetry (FAB2)"* | Real-time 31-byte binary packet (10 Hz in motion, 1 Hz idle) |
| **Button Sequences** | `FAB3` | `0000FAB3-0000-1000-8000-00805F9B34FB` | `Read`, `Write`, `Notify` | CCCD `0x2902`, `0x2901` User Desc: *"Fabrica Button Sequences 1-4 (FAB3)"* | Complete 212-byte table of all 4 button folding routines with auto-CRC32 |

**Standard Device Information Service (`0x180A`)**:
- Model Number (`0x2A24`): `"Fabrica-DevKit-v1"`
- Firmware Revision (`0x2A26`): `"v1.13.0"`
- Manufacturer Name (`0x2A29`): `"AIR Robotics"`

---

### 2. Step-by-Step Pairing Walkthrough (nRF Connect / LightBlue)

1. **Pairing Window (Out-of-the-Box Auto-Start or 3-Second Hold)**:
   - **New / Wiped Unit (0 Bonds)**: Fabrica automatically enters **indefinite BLE pairing mode** upon boot or after a hardware bond reset (`B1 + B4` 5s hold) without requiring any button press. It remains open until the first phone pairs. The Status LED immediately begins a **fast double-blink** (`LED_STATE_BLE_PAIRING`).
   - **Adding a Second Device (Multi-Device Pairing)**: Hold **Button 1 (or any button B1–B4) for 3 seconds**. This opens a **120-second (2-minute) pairing window** for the new device.
   - The device advertises as `Fabrica-XXXX` (where `XXXX` is derived from the ESP32 BT MAC address).
2. **Scan and Connect**:
   - In **nRF Connect** or **LightBlue**, scan for `Fabrica-XXXX` and tap **Connect**.
   - The firmware proactively initiates SMP security: tap **Pair** / **Bond** on the phone prompt.
   - The Status LED illuminates solid ON for 1.0 second (`LED_STATE_BLE_CONNECTED`) confirming the bond.
   - *Future connections reconnect automatically without pressing any buttons!*
3. **Enable Notifications**:
   - In nRF Connect, find service `0000FAB0-...`.
   - Tap the three-down-arrows icon on `FAB2` (`0000FAB2-...`) to subscribe to real-time telemetry notifications.
   - Tap the three-down-arrows icon on `FAB3` (`0000FAB3-...`) to subscribe to button sequence updates.

---

### 3. Ready-to-Paste Hexadecimal Command Cheat Sheet (`FAB1`)

Tap `FAB1` (`0000FAB1-...`), select **Write**, choose format **Byte Array** (or **HEX** in LightBlue), and paste any of the following commands:

#### A. Motion & Routine Execution
| Action | Opcode / Wire Format | Hex Payload to Paste | Description |
|---|---|---|---|
| **Run Preset 1** | `[0x00][0x01]` | `0001` | Execute stored Button 1 routine (Adult T-Shirt) |
| **Run Preset 2** | `[0x00][0x02]` | `0002` | Execute stored Button 2 routine (Long-Sleeve Shirt) |
| **Run Preset 3** | `[0x00][0x03]` | `0003` | Execute stored Button 3 routine (Trousers / Jeans) |
| **Run Preset 4** | `[0x00][0x04]` | `0004` | Execute stored Button 4 routine (Towel / Linen) |
| **Preview Raw Routine** | `[0x01][step_count][steps...]` | `0102010000010100` | Stateless preview: Step 1 (Ch 0), Step 2 (Ch 1) without modifying NVS |
| **Stop Motion / Clear** | `[0x02]` | `02` | Clean stop, exit calibration, or clear latched E-Stop |
| **Emergency Stop** | `[0x03]` | `03` | Fast-path abort (<50ms), home all 16 channels to $0^\circ$, latch `STATE_ESTOP` |

#### B. Live Servo Jog Calibration
*Transitions the robot into `STATE_CALIBRATING` with 10s stationary thermal cutoff and 15s inactivity auto-home.*

| Channel | Target Angle | Hex Payload to Paste | Physical Flap Actuated |
|---|---|---|---|
| **Ch 0** | $0^\circ$ (Flat) | `0D0000` | Left flap to flat |
| **Ch 0** | $45^\circ$ | `0D002D` | Left flap to $45^\circ$ |
| **Ch 0** | $90^\circ$ | `0D005A` | Left flap vertical |
| **Ch 0** | $180^\circ$ (Folded) | `0D00B4` | Left flap full fold |
| **Ch 1** | $90^\circ$ | `0D015A` | Right flap vertical |
| **Ch 2** | $90^\circ$ | `0D025A` | Bottom flap vertical |
| **Ch 3** | $90^\circ$ | `0D035A` | Top collar flap vertical |

#### C. Preset Configuration & Synchronization
| Action | Opcode / Wire Format | Hex Payload to Paste | Description |
|---|---|---|---|
| **Save Preset 1 (Compact)** | `[0x0A][preset_id][step_count][steps...]` | `0A0102010000010100` | Program Preset 1 with 2 steps (Ch 0, then Ch 1). Auto-calculates CRC32. |
| **Sync Presets (`FAB3`)** | `[0x0B]` | `0B` | Triggers immediate 212-byte table notification on `FAB3` |
| **Restore Factory Presets**| `[0x0C]` | `0C` | Restores Presets 1–4 to hardcoded defaults in NVS |
| **Visual Robot Locator** | `[0x0E]` | `0E` | Pulses Status LED for 3.0s (`LED_STATE_IDENTIFY`) |
| **Request Telemetry** | `[0x10]` | `10` | Requests immediate single-shot 31-byte notification on `FAB2` |
| **Pause Telemetry Stream** | `[0x11][0x00]` | `1100` | Pauses periodic background streaming loop |
| **Resume Telemetry Stream**| `[0x11][0x01]` | `1101` | Resumes periodic background streaming loop |

---

### 4. 31-Byte Real-Time Telemetry Decoder Cheat Sheet (`FAB2`)

When subscribed to `FAB2`, notifications arrive formatted as a packed 31-byte Little-Endian struct:

```
Byte Offset:   0  1  2  3  4  5 [6-7] [8 .. 23]  24 [25-26] 27 28 [29-30]
Field:        [S][L][B][I][T][P][ELAP] [ANGLES] [ST] [HEAP] [R][E] [SEQ ]
```

| Offset | Length | Field Name | Type | Value Interpretation |
|---|---|---|---|---|
| **0** | 1B | `system_state` | `uint8_t` | `0` = IDLE, `1` = RUNNING_MOTION, `2` = ESTOP, `3` = ERROR, `4` = CALIBRATING |
| **1** | 1B | `led_state` | `uint8_t` | `0` = IDLE, `1` = RUNNING, `2` = SAVE_SUCCESS, `3` = INPUT_ERROR, `4` = ESTOP, `5` = PAIRING, `6` = CONNECTED, `7` = IDENTIFY |
| **2** | 1B | `active_button_id`| `uint8_t` | Currently executing preset slot (`1–4`), or `0` for raw preview / idle |
| **3** | 1B | `current_step_idx` | `uint8_t` | Active 0-based step index (`0–15`) |
| **4** | 1B | `total_steps` | `uint8_t` | Total steps in active routine (`0–16`) |
| **5** | 1B | `step_progress_pct`| `uint8_t` | Mid-sweep progress percentage ($0\% \text{ to } 100\%$) |
| **6–7** | 2B | `elapsed_step_time_ms`| `uint16_t` (LE) | Elapsed time in active step (milliseconds, Little-Endian) |
| **8–23** | 16B | `channel_angles` | `uint8_t[16]` | Live commanded angles ($0^\circ \text{ to } 180^\circ$) for servo channels 0 to 15 |
| **24** | 1B | `last_cmd_status` | `uint8_t` | `0` = OK, `1` = ERR_BUSY, `2` = ERR_INVALID_STEP, `3` = ERR_MOTOR_BOUNDS, `4` = ERR_ROUTINE_FULL, `5` = ERR_CRC_MISMATCH, `6` = ERR_INVALID_ARG |
| **25–26**| 2B | `free_heap_kb` | `uint16_t` (LE) | Current free internal SRAM in KB (~190–220 KB) |
| **27** | 1B | `ble_rssi_dbm` | `int8_t` | Connected central RSSI in dBm (signed int8, `-128` when disconnected) |
| **28** | 1B | `error_code` | `uint8_t` | Hardware fault bitmask (`BIT0` = I2C Fault, `BIT1` = NVS Fault, `BIT2` = E-Stop Active) |
| **29–30**| 2B | `sequence_counter` | `uint16_t` (LE) | Monotonically increasing packet counter for drop detection |

---

### 5. Programming Custom Sequences on `FAB3`

You can write directly to `FAB3` using either the **compact format** (5 to 50 bytes) or the **full 54-byte format**:

* **Compact Format**: `[preset_id (1-4)][step_count (1-16)][steps...]`
  - Each step is 3 bytes: `[motor_count (1-2)][motor_id_1][motor_id_2]`
  - Example: `01 02 01 00 00 01 01 00` saves a 2-step routine to Preset 1 (Step 1 moves Ch 0, Step 2 moves Ch 1).
  - The firmware automatically zero-pads unused steps and computes the valid IEEE 802.3 CRC32 before committing to NVS flash!

---

## Build & Test Instructions

### 1. Host-Based Unit, Integration & Stress Testing
Run the complete host test harness validating all firmware layers (Headers, UI, PCA9685, Storage, Motion, State Machine, E2E Stress, NimBLE Transport, Remote Commands, Telemetry, and Full BLE Integration):
```bash
make test
```
All **11 test suites** execute in $<2\text{s}$ with **911 automated checks passing** under `-Wall -Wextra -Werror`:
```
- test/test_headers.c          (62 checks)
- test/test_ui_subsystem.c     (75 checks)
- test/test_pca9685.c          (50 checks)
- test/test_storage.c          (64 checks)
- test/test_motion.c           (48 checks)
- test/test_state_machine.c    (149 checks)
- test/test_e2e_stress.c       (118 checks)
- test/test_ble_transport.c    (115 checks)
- test/test_remote_cmd.c       (82 checks)
- test/test_telemetry.c        (70 checks)
- test/test_ble_integration.c  (78 checks - including 200-cycle endurance run)
--------------------------------------------------------------------------------
Total: 911 / 911 checks passed (100% Success)
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
