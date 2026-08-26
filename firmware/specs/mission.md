# Firmware Mission Specification

## Project Purpose

Develop, implement, and validate robust, modular, production-grade embedded firmware for **Fabrica** — an open-source, automated cloth folding robot.

The `firmware` sub-system provides the real-time embedded software executing natively on the **ESP32 Dev Board v1**. It controls the physical 4-button and status LED interface, manages non-volatile sequence storage, coordinates multi-state system workflows, and commands the **PCA9685 16-channel 12-bit PWM driver** over I2C to actuate up to 16 high-torque servo motors (e.g., MG996R) driving the modular folding grid panels.

The firmware is designed to be:
- **Autonomous & Standalone**: Complete computer-free operation for daily laundry folding (Presets 1–4) and visual sequence programming directly on the physical unit.
- **Deterministic & Real-Time**: Dual-core FreeRTOS architecture ensuring rock-solid motion timing, smooth multi-servo articulation, and zero UI lag.
- **Fail-Safe & Resilient**: Instant Emergency Stop (E-Stop) on any button press during motion, empty preset protection, programming inactivity timeouts, and non-volatile flash memory persistence.
- **Modular & Scalable**: Seamlessly supports 1 to 16 servo channels across customizable grid layouts (standard 4×3 grid, expandable to custom configurations).

---

## Core Firmware Subsystems & Scalable Architecture

```mermaid
graph TD
    subgraph Input & Transport Sources
        BTN[4 Push Buttons<br/>B1, B2, B3, B4]
        BLE[Future BLE GATT Server<br/>Mobile App Control]
        WIFI[Future Wi-Fi / WebSockets<br/>Mobile App & Cloud]
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
    BLE -.->|Future BLE Packets| TRANSPORT_LAYER
    WIFI -.->|Future JSON/WS Frames| TRANSPORT_LAYER
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

### 1. Decoupled Command Architecture & Scalability
* **Source-Independent Command Pipeline**: Core firmware logic (Motion Engine, State Machine, NVS Storage) is fully decoupled from physical inputs. All events are formatted as standardized `command_t` objects (with source metadata: `SOURCE_PHYSICAL_BUTTON`, `SOURCE_BLE`, `SOURCE_WIFI`) and posted to a unified FreeRTOS command queue.
* **Seamless Mobile App Scaling**: In the initial v1.0 version, only the physical button transport is active. When wireless mobile connectivity is introduced in future releases, BLE and Wi-Fi drivers can directly inject commands and receive telemetry through the existing transport interface without touching core motion or state logic.

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
* Non-blocking software timer / task driving 7 distinct status patterns:
  1. **Idle / Ready**: Soft heartbeat (10% duty cycle / 0.5 Hz) or OFF awaiting input.
  2. **Running Sequence**: Solid ON throughout the entire motion cycle.
  3. **Programming Mode**: Slow blink (1.0s ON / 1.0s OFF / 0.5 Hz).
  4. **Step Locked**: 2 fast flashes (80ms ON / 80ms OFF).
  5. **Save & Exit Success**: Solid ON for 2.0 seconds.
  6. **Input Error / Limit Reached**: 3 fast flashes (60ms ON / 60ms OFF).
  7. **Emergency Stop (E-Stop)**: 5 rapid flashes (50ms ON / 50ms OFF).

---

## Target Hardware & Pinout Specifications

| Peripheral | Component / Interface | Pin / Channel | Description |
|---|---|---|---|
| **MCU** | ESP32 Dev Board v1 (ESP-WROOM-32) | — | 240 MHz dual-core, 520KB SRAM, 4MB Flash |
| **PWM Driver** | PCA9685 16-Channel 12-Bit Driver | I2C (SDA: `GPIO 21`, SCL: `GPIO 22`) | 50 Hz PWM frequency, I2C address `0x40` |
| **Status LED** | 5mm Diffused Red/Blue LED | `GPIO 2` | Active-high visual status indicator |
| **Button 1 (B1)** | Tactile Push Button | `GPIO 0` (BOOT / Pull-up) | Preset 1 / Cycle & Nudge Flap |
| **Button 2 (B2)** | Tactile Push Button | `GPIO 4` (Pull-up) | Preset 2 / Stage & Hold Flap ($30^\circ$) |
| **Button 3 (B3)** | Tactile Push Button | `GPIO 16` (Pull-up) | Preset 3 / Lock Step & Drop Flaps |
| **Button 4 (B4)** | Tactile Push Button | `GPIO 17` (Pull-up) | Preset 4 / Save to NVS & Exit |
| **Servos** | MG996R High-Torque Servos (up to 16) | PCA9685 Channels 0–15 | $0^\circ$ to $180^\circ$ panel actuation |

---

## Target Audience & Use Cases

* **Daily Laundry Automation**: Consumers and makers using 1-touch preset buttons to quickly fold t-shirts, polo shirts, trousers, and towels.
* **Classroom & STEM Robotics**: Students and educators learning embedded systems, I2C communication, FreeRTOS multi-threading, state machines, and real-time motor control.
* **Custom Garment Profiling**: Users visually staging custom folding patterns for unconventional garment sizes directly on the machine.
* **Future Mobile & Smart Home Integration**: Future app users connecting via BLE / Wi-Fi to create complex multi-panel folding choreography, monitor live diagnostics, and sync cloud garment profiles.

---

## Firmware Success Criteria

- **100% Deterministic Execution**: Zero dropped FreeRTOS ticks, zero blocking delays on Core 1 UI loop, and precise $\pm 10\text{ms}$ motion timing on Core 0.
- **Zero-Latency E-Stop**: Emergency stop triggers within $< 50\text{ms}$ of button tap or wireless command, cutting active PWM commands and homing all panels.
- **NVS Data Integrity**: 100% data persistence across reboots, power cuts, and routine re-programming cycles.
- **Robust Error Handling**: Graceful rejection of invalid inputs (3rd motor stage attempts, empty step locks, empty preset executions) with clear LED feedback.
- **Architectural Scalability**: Decoupled command pipeline allowing future Bluetooth LE and Wi-Fi drivers to interface with the core motion and storage engines with zero structural redesign.
- **Clean ESP-IDF Build**: Clean compilation under ESP-IDF CMake / Ninja build system with zero compiler warnings.
