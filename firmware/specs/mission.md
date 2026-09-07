# Firmware Mission Specification

## Project Purpose

Develop, implement, and validate robust, modular, production-grade embedded firmware for **Fabrica** — an open-source, automated cloth folding robot.

The `firmware` sub-system provides the real-time embedded software executing natively on the **ESP32 Dev Board v1**. It controls the physical 4-button and status LED interface, manages non-volatile sequence storage, coordinates multi-state system workflows, and commands the **PCA9685 16-channel 12-bit PWM driver** over I2C to actuate up to 16 high-torque servo motors (e.g., MG996R) driving the modular folding grid panels.

The firmware is designed to be:
- **Autonomous & Standalone**: Complete computer-free operation for daily laundry folding (Presets 1–4) and visual sequence programming directly on the physical unit.
- **First-Class Mobile Connected**: Native Bluetooth Low Energy (BLE) integration, enabling users to program button sequences, start/stop execution, and stream live motor positions from the mobile app.
- **Deterministic & Real-Time**: Dual-core FreeRTOS architecture ensuring rock-solid motion timing, smooth multi-servo articulation, and zero UI lag.
- **Fail-Safe & Resilient**: Instant Emergency Stop (E-Stop) on any button press or BLE stop command during motion, empty preset protection, programming inactivity timeouts, and non-volatile flash memory persistence.
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
  - **Wireless Button Configuration**: Remotely record, edit, and organize folding sequences per button (Buttons 1–4) over BLE via canonical `FAB3` transport, supporting active motion write locks (`CMD_STATUS_ERR_BUSY`), auto-CRC32 calculation on zero-checksum writes, and factory default restoration (`CMD_RESTORE_FACTORY_PRESETS`).
  - **Start/Stop Sequence Execution**: Remotely trigger, stop, or emergency abort folding routines directly from the mobile app, protected by busy re-entrancy guards (`CMD_STATUS_ERR_BUSY`), empty sequence validation (`CMD_STATUS_ERR_INVALID_STEP`), and dedicated 100% completion notifications.
  - **Client-Side Garment Profiles (Stateless Robot Execution)**: Custom garment profiles (e.g. T-Shirts, Hoodies, Jeans, Towels, Kids Wear), categorization, and profile sharing are managed client-side in the mobile app. The ESP32 acts as a high-performance execution engine: users can preview any profile directly on the robot (`CMD_RUN_RAW_SEQUENCE`, reporting `active_button_id == 0`) or bind a profile to physical Buttons 1–4 (`CMD_SET_BUTTON_SEQUENCE` or `FAB3` write).
  - **Real-Time Status, LED Mirroring & Motor Telemetry**: Stream sequence execution progress (active step, total steps, progress %), visual LED state mirroring (for 1:1 mobile app UI sync), and live motor positions ($0^\circ-180^\circ$ for channels 0–15) in real time at 10 Hz over BLE without requiring expensive hardware current sensors.
  - **Unit Identification & Calibration**: Wirelessly trigger visual unit identification (`CMD_IDENTIFY_ROBOT`, 3.0s LED pulse train), configure LED mode (`CMD_SET_LED_MODE`: Auto, Manual Override, Stealth/Night Mode), and perform live integer servo angle jogging (`CMD_JOG_MOTOR_ANGLE`) with motion safety interlocks, 10s thermal de-energize cutoffs, and 15s auto-home exit.
  - **Proof-of-Presence BLE Security**: First-time connection from an unbonded mobile device requires a physical button press on the robot during a 30-second authorization window (which suppresses routine execution). Up to 4 trusted devices are bonded in NVS (`"ble_bonds"`, with automatic FIFO eviction on a 5th device and manual B1+B4 5-second factory reset) for instant, frictionless auto-reconnection on subsequent launches.
  - **Lightweight On-Device Storage**: NVS stores only the 4 user-programmed button sequences, bonded BLE identity keys, and factory defaults, eliminating firmware reflashes when new garment types are created.

### 2. Dual-Core FreeRTOS Partitioning
* **Core 0 (Motion Engine & Hardware Bus)**: Dedicated to deterministic servo motion execution, I2C bus communication with the PCA9685 driver, inter-step dwell timings, and immediate E-Stop abort processing.
* **Core 1 (UI & System Management)**: Dedicated to physical button scanning, debouncing, 3-second long-press detection, the non-blocking LED visual feedback generator, mode state management, and Non-Volatile Storage (NVS) read/write operations.

### 2. Daily Run Mode Engine
* **Instant Recall**: A single short tap (<500ms) on **B1–B4** loads and executes the corresponding saved folding routine from Flash.
* **Synchronized Motion Execution**: Supports single-motor sweeps and parallel dual-motor sweeps ($0^\circ \rightarrow 180^\circ \rightarrow 0^\circ$ with 300ms fold dwell and 200ms inter-step delay).
* **Safe Completion**: All 16 channels verify flat home position ($0^\circ$) at cycle end, and the system safely idles.
* **Emergency Stop (E-Stop)**: Tapping any button during an active folding cycle immediately halts PWM output, resets all 16 servos to $0^\circ$, delivers a 5-flash rapid alert, and aborts the routine.

### 3. Visual Staging Programming Engine
* **Direct Teaching**: Long-pressing any preset button for 3 seconds enters Visual Staging Mode without requiring a computer or smartphone.
* **Mechanical Identification (CYCLE - B1)**: Tapping B1 steps through servo channels 1–16, delivering a physical $15^\circ$ nudge on the target panel for instant visual and tactile identification.
* **Physical Staging (STAGE - B2)**: Tapping B2 lifts the identified flap to $30^\circ$ and holds it in place. Supports staging up to 2 flaps simultaneously for parallel folding. Tapping B2 again toggles an already-staged flap back to $0^\circ$.
* **Step Commitment (NEXT STEP - B3)**: Tapping B3 records the staged motor configuration into the temporary buffer, flashes the LED twice, drops the flaps flat ($0^\circ$), and advances the step index (up to 16 steps maximum).
* **Flash Persistence (SAVE & EXIT - B4)**: Tapping B4 writes the complete sequence to ESP32 NVS Flash memory, illuminates the LED solid for 2.0 seconds, and returns to Daily Run Mode.
* **Safety Failsafes**: Automatic 20-second inactivity timeout, empty step rejection, and 2-motor-per-step enforcement.

### 4. Visual Feedback Engine (LED Controller)
* Non-blocking software timer / task driving 10 distinct status patterns with strict preemption restoration:
  1. **Idle / Ready**: Soft heartbeat (10% duty cycle / 0.5 Hz) or OFF awaiting input.
  2. **Running Sequence**: Solid ON throughout the entire motion cycle.
  3. **Programming Mode**: Slow blink (1.0s ON / 1.0s OFF / 0.5 Hz).
  4. **Step Locked**: 2 fast flashes (80ms ON / 80ms OFF).
  5. **Save & Exit Success**: Solid ON for 2.0 seconds.
  6. **Input Error / Limit Reached**: 3 fast flashes (60ms ON / 60ms OFF).
  7. **Emergency Stop (E-Stop)**: 5 rapid flashes (50ms ON / 50ms OFF).
  8. **BLE Pairing Window**: Fast double-blink (100ms ON / 100ms OFF / 100ms ON / 500ms OFF) awaiting physical button press to authorize a new mobile device.
  9. **BLE Connected**: Solid ON for 1.0 second confirming connection, restoring prior base state.
  10. **Identify Robot**: 3 fast double-blinks (100ms ON / 100ms OFF / 100ms ON / 500ms OFF) for 3.0 seconds, restoring prior base state.
* **Visual Mode Control (`CMD_SET_LED_MODE`)**: Supports runtime selection between Auto (State-driven), Manual Pattern Override (`led_state_t`), and Stealth/Night Mode (suppresses idle heartbeat while preserving motion/error alerts).
* **Strict Preemption Hierarchy**: Transient patterns (4, 5, 6, 9, 10) automatically preserve and restore the underlying base state (`return_to_prior_base = true`) to prevent display glitches across state transitions.

---

## Target Hardware & Pinout Specifications

| Peripheral | Component / Interface | Pin / Channel | Description |
|---|---|---|---|
| **MCU** | ESP32 Dev Board v1 (ESP-WROOM-32) | — | 240 MHz dual-core, 520KB SRAM, 4MB Flash |
| **PWM Driver** | PCA9685 16-Channel 12-Bit Driver | I2C (SDA: `GPIO 21`, SCL: `GPIO 22`) | 50 Hz PWM frequency, I2C address `0x40` |
| **Status LED** | 5mm Diffused Red/Blue LED | `GPIO 2` | Active-high visual status indicator |
| **Button 1 (B1)** | Tactile Push Button | `GPIO 4` (Pull-up) | Button 1 Routine / Cycle & Nudge Flap |
| **Button 2 (B2)** | Tactile Push Button | `GPIO 16` (Pull-up) | Button 2 Routine / Stage & Hold Flap ($30^\circ$) |
| **Button 3 (B3)** | Tactile Push Button | `GPIO 17` (Pull-up) | Button 3 Routine / Lock Step & Drop Flaps |
| **Button 4 (B4)** | Tactile Push Button | `GPIO 5` (Pull-up) | Button 4 Routine / Save to NVS & Exit |
| **Servos** | MG996R High-Torque Servos (up to 16) | PCA9685 Channels 0–15 | $0^\circ$ to $180^\circ$ panel actuation |

---

## Target Audience & Use Cases

* **Daily Laundry Automation**: Consumers and makers using 1-touch preset buttons to quickly fold t-shirts, polo shirts, trousers, and towels.
* **Classroom & STEM Robotics**: Students and educators learning embedded systems, I2C communication, FreeRTOS multi-threading, state machines, and real-time motor control.
* **On-Device Visual Staging**: Users visually staging custom folding patterns directly on the machine using physical buttons.
* **Mobile App Control**: Users connecting over Bluetooth Low Energy (BLE) to configure button sequences, start/stop routines, and monitor live motor positions and sequence progress.
* **AI Vision Integration (Future)**: Camera-based fabric vision models running on mobile or cloud to suggest folding parameters.

---

## Firmware Success Criteria

- **100% Deterministic Execution**: Zero dropped FreeRTOS ticks, zero blocking delays on Core 1 UI loop, and precise $\pm 10\text{ms}$ motion timing on Core 0.
- **Zero-Latency E-Stop / Stop**: Start/stop commands and emergency stop trigger within $< 50\text{ms}$ of button tap or wireless BLE command, cutting active PWM commands and homing all panels.
- **Real-Time Telemetry & LED Mirroring**: 10 Hz streaming of packed 30-byte telemetry frames (`telemetry_packet_t`: system state, LED state mirroring, active button ID, step progress, all 16 motor angles, and command status) over BLE notifications without requiring hardware current sensors.
- **Fail-Safe Mobile Control**: Re-entrancy guards rejecting concurrent execution requests (`CMD_STATUS_ERR_BUSY`), empty sequence validation (`CMD_STATUS_ERR_INVALID_STEP`), motion safety interlocks prohibiting servo jogging during running cycles or E-Stop, 15-second calibration auto-home, and `<50ms` E-Stop preemption with BLE clear recovery.
- **Reliable Button Sequence Persistence**: 100% NVS data persistence for the 4 user-programmed button sequences and factory defaults across reboots and power cuts with CRC32 integrity checks, active motion sequence write locks (`ERR_BUSY`), and auto-CRC calculation on zero-checksum writes.
- **Stateless Mobile Profile Execution**: Zero-friction client-side garment profile management, supporting direct preview execution of custom routines (`CMD_RUN_RAW_SEQUENCE`, reporting `active_button_id == 0`) and 1-touch binding to physical buttons (`CMD_SET_BUTTON_SEQUENCE` or `FAB3`).
- **Proof-of-Presence BLE Security**: 100% rejection of unauthorized BLE centrals unless authorized via physical button press within a 30-second pairing window; seamless auto-reconnect for up to 4 bonded devices in NVS.
- **Robust Error Handling**: Graceful rejection of invalid inputs (3rd motor stage attempts, empty step locks, out-of-bounds channels) with clear visual and wireless BLE feedback.
- **Unified Transport Ingress**: Decoupled command pipeline supporting physical buttons and NimBLE GATT feeding a single thread-safe FreeRTOS queue.
- **Clean ESP-IDF Build**: Clean compilation under ESP-IDF CMake / Ninja build system with zero compiler warnings.
