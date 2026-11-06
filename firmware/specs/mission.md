# Firmware Mission Specification

## Project Purpose

Develop, implement, and validate robust, modular, production-grade embedded firmware for **Fabrica** — an open-source, automated cloth folding robot.

The `firmware` sub-system provides the real-time embedded software executing natively on the **ESP32 Dev Board v1**. It controls the physical 4-button and status LED interface, manages non-volatile sequence storage, coordinates multi-state system workflows, and commands the **PCA9685 16-channel 12-bit PWM driver** over I2C to actuate up to 16 high-torque servo motors (e.g., MG996R) driving the modular folding grid panels.

The firmware is designed to be:
- **Autonomous & Standalone**: Complete computer-free operation for daily laundry folding out of the box via 4 physical preset buttons (Presets 1–4 pre-seeded with factory defaults exercising all 4 folding flaps, including the top collar flap).
- **First-Class Mobile Connected**: Native Bluetooth Low Energy (BLE) integration, enabling users to visually program and assign custom button sequences from their phone, start/stop execution, and stream live motor positions.
- **Deterministic & Real-Time**: Dual-core FreeRTOS architecture ensuring rock-solid motion timing, smooth multi-servo articulation, and zero UI lag.
- **Fail-Safe & Resilient**: Instant Emergency Stop (E-Stop) on any button press or BLE stop command during motion, empty preset protection, and non-volatile flash memory persistence.
- **Modular & Scalable**: Seamlessly supports 1 to 16 servo channels across customizable grid layouts (standard 4×3 grid, expandable to custom configurations).

---

## Core Firmware Subsystems & Scalable Architecture

```mermaid
graph TD
    subgraph Input & Transport Sources
        BTN[4 Push Buttons<br/>B1, B2, B3, B4]
        BLE[NimBLE GATT Server<br/>Mobile App Control (Core 1)]
    end

    subgraph ESP32 Dual-Core Firmware
        subgraph Core 1: System Management & UI
            BTN_DEBOUNCE[Button Scanner & Debouncer<br/>50ms Low-Pass Filter]
            TRANSPORT_LAYER[Command Ingestion Layer<br/>Source-Agnostic Abstraction]
            CMD_Q[("Unified Command Queue<br/>command_t Pipeline")]
            SM[State Machine Engine<br/>Run vs Program vs Telemetry]
            LED_TASK[LED Pattern Engine<br/>Non-Blocking Feedback]
            NVS_MGR[NVS Flash Storage<br/>Preset & Routine Manager]
        end

        subgraph Core 0: Motion & Hardware Control
            MOTION_TASK[Motion Execution Task<br/>Trajectory & Delay Generator]
            I2C_DRIVER[PCA9685 I2C Driver<br/>50Hz PWM Bus]
            ESTOP[E-Stop Override Handler<br/>Instant Abort & Safe Home]
        end
    end

    subgraph Actuation & Feedback
        LED[1 Status LED]
        PCA[PCA9685 16-Ch PWM Driver]
        SERVOS[Servo Motor Array<br/>Channels 0-15]
    end

    BTN -->|GPIO State| BTN_DEBOUNCE
    BTN_DEBOUNCE -->|BTN_EVENT| TRANSPORT_LAYER
    BLE -->|BLE Command Frames| TRANSPORT_LAYER
    TRANSPORT_LAYER -->|Dispatched command_t| CMD_Q
    CMD_Q --> SM
    SM -->|State Changes| LED_TASK
    SM -->|Load/Save Sequences| NVS_MGR
    SM -->|Run Sequence Command| MOTION_TASK
    TRANSPORT_LAYER -->|E-Stop Event| ESTOP
    ESTOP -->|Preempt & Abort| MOTION_TASK
    LED_TASK -->|GPIO Levels| LED
    MOTION_TASK -->|Angle/Pulse Commands| I2C_DRIVER
    I2C_DRIVER -->|I2C 50Hz PWM| PCA
    PCA -->|PWM Pulses| SERVOS
```

### 1. Unified Command Architecture & Mobile Integration
* **Source-Independent Command Pipeline**: Core firmware logic (Motion Engine, State Machine, NVS Storage) is fully decoupled from physical inputs. All events are formatted as standardized `command_t` objects (with source metadata: `SOURCE_PHYSICAL_BUTTON`, `SOURCE_BLE`, `SOURCE_INTERNAL_TIMER`) and posted to a unified FreeRTOS command queue.
* **Mobile App Integration**: The firmware provides native mobile app integration via Apache NimBLE GATT services on Core 1:
  - **Wireless Button Configuration & Dual-Mode Writes**: Remotely record, edit, and organize folding sequences per button (Buttons 1–4) over BLE via canonical `FAB3` transport, supporting active motion write locks (`CMD_STATUS_ERR_BUSY`), auto-CRC32 calculation on zero-checksum writes, factory default restoration (`CMD_RESTORE_FACTORY_PRESETS`), and dual-mode write semantics (`Write Without Response` for time-critical E-Stop/Jog, `Write With Response` for sequence/flash commits).
  - **Start/Stop Sequence Execution**: Remotely trigger, stop, or emergency abort folding routines directly from the mobile app, protected by busy re-entrancy guards (`CMD_STATUS_ERR_BUSY`), empty sequence validation (`CMD_STATUS_ERR_INVALID_STEP`), and dedicated 100% completion notifications.
  - **Client-Side Garment Profiles (Stateless Robot Execution)**: Custom garment profiles (e.g. T-Shirts, Hoodies, Jeans, Towels, Kids Wear), categorization, and profile sharing are managed client-side in the mobile app. The ESP32 acts as a high-performance execution engine: users can preview any profile directly on the robot (`CMD_RUN_RAW_SEQUENCE`, reporting `active_button_id == 0`) or bind a profile to physical Buttons 1–4 (`CMD_SET_BUTTON_SEQUENCE` or `FAB3` write).
  - **Adaptive Real-Time Status, LED Mirroring & Motor Telemetry**: Stream sequence execution progress (active step, total steps, progress %), visual LED state mirroring (for 1:1 mobile app UI sync), and live motor positions ($0^\circ-180^\circ$ for channels 0–15) adaptively over BLE: 10 Hz during active motion/calibration, and throttled to 1 Hz (or on-change) during idle/programming to conserve mobile device battery and prevent iOS background app suspension.
  - **Unit Identification & Calibration**: Wirelessly trigger visual unit identification (`CMD_IDENTIFY_ROBOT`, 3.0s LED pulse train), configure LED mode (`CMD_SET_LED_MODE`: Auto, Manual Override, Stealth/Night Mode), and perform live integer servo angle jogging (`CMD_JOG_MOTOR_ANGLE`) with motion safety interlocks, 10s thermal de-energize cutoffs, and 15s auto-home exit.
  - **Hold-to-Pair BLE Security & RPA Privacy**: Pairing a new mobile device (including on first boot) requires holding any physical button (B1–B4) for **3 seconds** to open a **120-second (2-minute) BLE Pairing Window** (`LED_STATE_BLE_PAIRING` fast double-blink). Outside this window, unbonded connection attempts are rejected, while up to 4 already-bonded devices in NVS (`"ble_bonds"`, with automatic FIFO eviction on a 5th device and manual B1+B4 5-second reset) auto-reconnect seamlessly using Resolvable Private Address (RPA) privacy resolution (IRK / persistent UUID token).
  - **Lightweight On-Device Storage**: NVS stores only the 4 user-programmed button sequences, bonded BLE identity keys, and factory defaults, eliminating firmware reflashes when new garment types are created.

### 2. Dual-Core FreeRTOS Partitioning
* **Core 0 (Motion Engine & Hardware Bus)**: Dedicated to deterministic servo motion execution, I2C bus communication with the PCA9685 driver, inter-step dwell timings, and immediate E-Stop abort processing.
* **Core 1 (UI, BLE Wireless & System Coordination)**: Dedicated to the Apache NimBLE BLE stack (`app_ble_task`), real-time telemetry streaming (`app_telem_task`), physical button scanning and debouncing (`app_ui_task`), 3-second hold gesture detection for BLE pairing, the non-blocking LED visual feedback generator (`app_led_task`), system state machine coordination, and Non-Volatile Storage (NVS) read/write operations. Isolating wireless communications to Core 1 guarantees zero timing jitter on Core 0 real-time motion and PWM actuation.

### 3. Daily Run Mode Engine
* **Instant Recall**: A single short tap (<500ms) on **B1–B4** loads and executes the corresponding saved folding routine from Flash.
* **Synchronized Motion Execution**: Supports single-motor sweeps and parallel dual-motor sweeps ($0^\circ \rightarrow 180^\circ \rightarrow 0^\circ$ with 300ms fold dwell and 200ms inter-step delay).
* **Safe Completion**: All 16 channels verify flat home position ($0^\circ$) at cycle end, and the system safely idles.
* **Emergency Stop (E-Stop)**: Tapping any button during an active folding cycle immediately halts PWM output, resets all 16 servos to $0^\circ$, delivers a 5-flash rapid alert, and aborts the routine.

### 4. Wireless Mobile Sequence Configuration & Calibration
* **Minimal Physical Pad, Rich Phone Programming**: To keep the physical control pad effortless and free of hidden modes, custom sequence programming is handled entirely on the mobile application over BLE rather than by multi-button combinations on the unit.
* **Direct Button Assignment (`CMD_SET_BUTTON_SEQUENCE` / `FAB3`)**: Users visually build folding sequences on their phone (up to 16 steps, up to 2 simultaneous motors per step) and assign them directly to physical Buttons 1–4 stored in ESP32 NVS Flash.
* **Stateless Sequence Preview (`CMD_RUN_RAW_SEQUENCE`)**: Test and preview custom garment routines directly from the phone before committing them to a physical button slot.
* **Factory Preset Restoration (`CMD_RESTORE_FACTORY_PRESETS`)**: Instant 1-tap restoration of the 4 built-in factory garment presets exercising all 4 motors (Preset 1: Adult T-Shirt [4 steps: Ch 0 $\to$ 1 $\to$ 2 $\to$ 3], Preset 2: Long-Sleeve Shirt [5 steps], Preset 3: Trousers/Jeans [3 steps], Preset 4: Towel/Linen [4 steps]).
* **Live Servo Jog (`CMD_JOG_MOTOR_ANGLE`)**: Interactive servo angle control from the mobile app for panel identification and mechanical calibration.

### 5. Visual Feedback Engine (LED Controller)
* Non-blocking software timer / task driving distinct status patterns with strict preemption restoration:
  1. **Idle / Ready**: Soft heartbeat (10% duty cycle / 0.5 Hz) or OFF awaiting input.
  2. **Running Sequence**: Solid ON throughout the entire motion cycle.
  3. **Save & Sync Success**: Solid ON for 2.0 seconds when a preset is saved or restored.
  4. **Input Error / Invalid Routine**: 3 fast flashes (60ms ON / 60ms OFF).
  5. **Emergency Stop (E-Stop)**: 5 rapid flashes (50ms ON / 50ms OFF).
  6. **BLE Pairing Window**: Fast double-blink (100ms ON / 100ms OFF / 100ms ON / 500ms OFF) awaiting physical button press to authorize a new mobile device.
  7. **BLE Connected**: Solid ON for 1.0 second confirming connection, restoring prior base state.
  8. **Identify Robot**: 3 fast double-blinks (100ms ON / 100ms OFF / 100ms ON / 500ms OFF) for 3.0 seconds, restoring prior base state.
* **Visual Mode Control (`CMD_SET_LED_MODE`)**: Supports runtime selection between Auto (State-driven), Manual Pattern Override (`led_state_t`), and Stealth/Night Mode (suppresses idle heartbeat while preserving motion/error alerts).
* **Strict Preemption Hierarchy**: Transient patterns automatically preserve and restore the underlying base state (`return_to_prior_base = true`) to prevent display glitches across state transitions.

---

## Target Hardware & Pinout Specifications

| Peripheral | Component / Interface | Pin / Channel | Description |
|---|---|---|---|
| **MCU** | ESP32 Dev Board v1 (ESP-WROOM-32) | — | 240 MHz dual-core, 520KB SRAM, 4MB Flash |
| **PWM Driver** | PCA9685 16-Channel 12-Bit Driver | I2C (SDA: `GPIO 21`, SCL: `GPIO 22`) | 50 Hz PWM frequency, I2C address `0x40` |
| **Status LED** | 5mm Diffused Red/Blue LED | `GPIO 2` | Active-high visual status indicator |
| **Button 1 (B1)** | Tactile Push Button | `GPIO 4` (Pull-up) | Preset 1 Routine (Default: Adult T-Shirt) / E-Stop |
| **Button 2 (B2)** | Tactile Push Button | `GPIO 16` (Pull-up) | Preset 2 Routine (Default: Long-Sleeve Shirt) / E-Stop |
| **Button 3 (B3)** | Tactile Push Button | `GPIO 17` (Pull-up) | Preset 3 Routine (Default: Trousers / Jeans) / E-Stop |
| **Button 4 (B4)** | Tactile Push Button | `GPIO 5` (Pull-up) | Preset 4 Routine (Default: Towel / Linen) / E-Stop |
| **Servos** | MG996R High-Torque Servos (up to 16) | PCA9685 Channels 0–15 | $0^\circ$ to $180^\circ$ panel actuation |

---

## Target Audience & Use Cases

* **Daily Laundry Automation**: Consumers and makers using 1-touch preset buttons to quickly fold t-shirts, polo shirts, trousers, and towels out of the box.
* **Classroom & STEM Robotics**: Students and educators learning embedded systems, I2C communication, FreeRTOS multi-threading, state machines, and real-time motor control.
* **Mobile App Control & Custom Programming**: Users connecting over Bluetooth Low Energy (BLE) to visually create custom folding sequences, assign them to Buttons 1–4, start/stop routines, and monitor live motor positions.
* **AI Vision Integration (Future)**: Camera-based fabric vision models running on mobile or cloud to suggest folding parameters.

---

## Firmware Success Criteria

- **100% Deterministic Execution**: Zero dropped FreeRTOS ticks, zero blocking delays on Core 1 UI loop, and precise $\pm 10\text{ms}$ motion timing on Core 0.
- **Zero-Latency E-Stop / Stop**: Start/stop commands and emergency stop trigger within $< 50\text{ms}$ of button tap or wireless BLE command, cutting active PWM commands and homing all panels.
- **Real-Time Telemetry & LED Mirroring**: Adaptive streaming of packed 30-byte telemetry frames (`telemetry_packet_t`: system state, LED state mirroring, active button ID, step progress, all 16 motor angles, and command status, Little-Endian encoded) over BLE notifications (10 Hz in active motion, 1 Hz when idle) without requiring hardware current sensors.
- **Fail-Safe Mobile Control**: Re-entrancy guards rejecting concurrent execution requests (`CMD_STATUS_ERR_BUSY`), empty sequence validation (`CMD_STATUS_ERR_INVALID_STEP`), motion safety interlocks prohibiting servo jogging during running cycles or E-Stop, 15-second calibration auto-home, and `<50ms` E-Stop preemption with BLE clear recovery.
- **Reliable Button Sequence Persistence**: 100% NVS data persistence for the 4 user-programmed button sequences and factory defaults across reboots and power cuts with CRC32 integrity checks, active motion sequence write locks (`ERR_BUSY`), and auto-CRC calculation on zero-checksum writes.
- **Stateless Mobile Profile Execution**: Zero-friction client-side garment profile management, supporting direct preview execution of custom routines (`CMD_RUN_RAW_SEQUENCE`, reporting `active_button_id == 0`) and 1-touch binding to physical buttons (`CMD_SET_BUTTON_SEQUENCE` or `FAB3`).
- **Proof-of-Presence BLE Security & RPA Privacy**: 100% rejection of unauthorized BLE centrals unless authorized via physical button press within a 120-second pairing window; seamless auto-reconnect for up to 4 bonded devices in NVS with Resolvable Private Address (RPA) privacy resolution across 15-minute rotation intervals.
- **Robust Error Handling**: Graceful rejection of invalid inputs (3rd motor stage attempts, empty step locks, out-of-bounds channels) with clear visual and wireless BLE feedback.
- **Unified Transport Ingress**: Decoupled command pipeline supporting physical buttons and NimBLE GATT feeding a single thread-safe FreeRTOS queue.
- **Clean ESP-IDF Build**: Clean compilation under ESP-IDF CMake / Ninja build system with zero compiler warnings.
