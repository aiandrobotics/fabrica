# Tech Stack — ESP32 Firmware

## Firmware Toolchain & Build System

| Layer | Tool / Standard | Details |
|---|---|---|
| **Framework / SDK** | Espressif ESP-IDF (v5.x / v6.x) | Native C / FreeRTOS development framework |
| **Language Standard** | C99 / C11 | High-efficiency embedded C with strict type definitions (`stdint.h`, `stdbool.h`) |
| **Target Microcontroller** | ESP32 Dev Board v1 / ESP-WROOM-32 | Dual-core Xtensa 32-bit LX6 @ 240 MHz, 520 KB SRAM, 4 MB SPI Flash |
| **Build System** | CMake 3.16+ & Ninja | Standard ESP-IDF build flow (`idf.py build`, `idf.py flash`, `idf.py monitor`) |
| **Reference Baseline** | `poc/esp_hello_world` | ESP-IDF structure, `esp_chip_info.h`, `esp_flash.h`, FreeRTOS tasks, `driver/gpio.h` |
| **Non-Volatile Storage** | ESP-IDF NVS Flash (`nvs_flash.h`) | Key-value blob sequence storage for 4 physical Button Routines (user-programmed & factory defaults) |
| **I2C Actuation Driver** | I2C Master (`driver/i2c.h` / `driver/i2c_master.h`) | Dedicated 100 kHz bus driving PCA9685 16-channel PWM servo controller (`0x40`) |
| **Wireless Stack** | Apache NimBLE (ESP-IDF Native) | Ultra-lightweight, dedicated BLE GATT server (`nimble/`) for mobile app integration |
| **OS / RTOS** | FreeRTOS (ESP-IDF SMP port) | Preemptive dual-core task scheduling, queues, event groups, and software timers |

---

## ESP32 Dual-Core Architecture & Task Allocation

```mermaid
graph LR
    subgraph Core 0 [Core 0: Motion & Hardware Bus Engine]
        direction TB
        M_TASK["app_motion_task (Priority 10)"]
        I2C_MGR["PCA9685 PWM Driver (I2C NUM 0)"]
        ESTOP_ISR["E-Stop Abort Engine (<50ms)"]
        M_TASK --> I2C_MGR
        ESTOP_ISR -.->|Instant Preemption| M_TASK
    end

    subgraph Core 1 [Core 1: UI, BLE Wireless & System Coordination]
        direction TB
        BLE_TASK["app_ble_task (Priority 4)<br/>NimBLE GATT Server"]
        TELEM_TASK["app_telem_task (Priority 3)<br/>10Hz Progress & Motor Telemetry"]
        UI_TASK["app_ui_task (Priority 5)<br/>4-Button Debouncer (50ms)"]
        SM_CORE["State Machine Engine"]
        NVS_CORE["NVS Sequence Manager (Buttons 1-4)"]
        LED_TASK["app_led_task (Priority 2)<br/>Status LED Engine"]

        BLE_TASK -->|Dispatched command_t| CMD_Q
        UI_TASK -->|Dispatched command_t| CMD_Q
        CMD_Q --> SM_CORE
        SM_CORE --> LED_TASK
        SM_CORE --> NVS_CORE
        TELEM_TASK -.->|Notify Progress & Angles (FAB2)| BLE_TASK
        NVS_CORE -.->|Notify Config Changes (FAB3)| BLE_TASK
    end

    subgraph IPC [Inter-Core IPC]
        CMD_Q[("Unified Command Queue<br/>xCommandQueue (Depth: 16)")]
        STATE_GRP[("System Event Group<br/>xSystemEventGroup")]
    end

    SM_CORE -->|Trigger Motion| M_TASK
    UI_TASK -.->|E-Stop Flag| STATE_GRP
    BLE_TASK -.->|Wireless E-Stop / Stop| STATE_GRP
    STATE_GRP -.->|Abort Check| M_TASK
```

### Core 0 — Real-Time Motion & Actuation Engine
- **`app_motion_task` (Priority: 10, Core ID: 0)**:
  - Consumes motion execution commands from the inter-core queue.
  - Implements smooth single-servo and synchronized parallel dual-servo sweep trajectories ($0^\circ \rightarrow 180^\circ \rightarrow 0^\circ$).
  - Controls deterministic dwell delays (300ms fold dwell, 200ms inter-step delay) using `vTaskDelay()`.
  - Continuously samples the E-Stop / Stop abort event flag before and during step transitions ($<50\text{ms}$ preemption latency).
- **PCA9685 I2C Driver**: Direct register reads/writes over ESP32 hardware I2C peripheral (`I2C_NUM_0`).

### Core 1 — UI, Dedicated BLE Wireless, Telemetry & System Coordination
- **`app_ble_task` (Priority: 4, Core ID: 1)**:
  - Runs Apache NimBLE host stack and GATT server.
  - Ingests mobile app commands via Control Point (`FAB1`): Start/Stop, Remote Staging, Step Editing, Jog, E-Stop.
  - Publishes 10 Hz real-time sequence progress and motor positions (`FAB2`).
  - Synchronizes 4 button sequence configurations with mobile app (`FAB3`).
  - Manages low-latency BLE GAP connection parameters (7.5ms–15ms) and MTU exchanges.
- **`app_telem_task` (Priority: 3, Core ID: 1)**:
  - Tracks sequence progress (active step, total steps, completion %) and live motor positions ($0^\circ \text{ to } 180^\circ$ for channels 0–15).
  - Packs binary `telemetry_packet_t` and pushes at 10 Hz to subscribed BLE mobile clients.
- **`app_ui_task` (Priority: 5, Core ID: 1)**:
  - Scans and debounces 4 physical push buttons with a 50ms software low-pass filter.
  - Differentiates between Short Tap (<500ms) and Long Press (≥3000ms).
  - Coordinates physical mode transitions and button gesture translations.
- **`app_led_task` (Priority: 2, Core ID: 1)**:
  - Non-blocking pattern generator driving 9 visual pulse trains on `GPIO 2` (including `LED_STATE_BLE_PAIRING` and `LED_STATE_BLE_CONNECTED`).
- **`storage` Subsystem**:
  - Manages serialized read/write operations to ESP-IDF NVS flash for the 4 physical button routines, bonded BLE keys (`"ble_bonds"`), and factory default fallback with IEEE 802.3 CRC32 integrity validation.

---

## Hardware Pinout & Peripheral Configuration

### 1. ESP32 GPIO Pin Allocations

| Signal Name | ESP32 GPIO | Direction | Configuration | Active State | Description |
|---|---|---|---|---|---|
| `PIN_STATUS_LED` | `GPIO_NUM_2` | Output | Push-Pull / No Pull | High (1) | Visual status indicator LED (Built-in on DevKit) |
| `PIN_BTN_1` | `GPIO_NUM_4` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | B1: Button 1 Routine / Cycle & Nudge Flap ($15^\circ$) |
| `PIN_BTN_2` | `GPIO_NUM_16` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | B2: Button 2 Routine / Stage & Toggle Flap ($30^\circ$) |
| `PIN_BTN_3` | `GPIO_NUM_17` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | B3: Button 3 Routine / Lock Step & Drop Flaps |
| `PIN_BTN_4` | `GPIO_NUM_5` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0) | B4: Button 4 Routine / Save to NVS & Exit |
| `PIN_I2C_SDA` | `GPIO_NUM_21` | I/O | Open-Drain + External 4.7k Pull-Up | — | PCA9685 I2C Data line (SDA) |
| `PIN_I2C_SCL` | `GPIO_NUM_22` | Output | Open-Drain + External 4.7k Pull-Up | — | PCA9685 I2C Clock line (SCL) |

### 2. PCA9685 PWM Driver Configuration

| Parameter | Value | Description |
|---|---|---|
| **I2C Port** | `I2C_NUM_0` | Hardware I2C controller |
| **I2C Address** | `0x40` | Default address (`A0–A5` grounded) |
| **I2C Clock Speed** | `100000` Hz (100 kHz) | Standard mode (supports 400 kHz fast mode) |
| **PWM Output Frequency** | `50` Hz | Standard 20ms period for analog/digital RC servos |
| **Prescale Value** | `121` (`0x79`) | $\text{Prescale} = \text{round}\left(\frac{25\text{ MHz}}{4096 \times 50\text{ Hz}}\right) - 1 = 121$ |
| **PWM Resolution** | 12-bit (4096 counts) | Range $0$ to $4095$ counts per 20ms frame |
| **Servo Min Pulse ($0^\circ$)** | $500\ \mu\text{s}$ ($\approx 102$ counts) | Flap resting flat on table ($0^\circ$ home) |
| **Servo Nudge Pulse ($15^\circ$)** | $667\ \mu\text{s}$ ($\approx 137$ counts) | Identification nudge angle |
| **Servo Staged Pulse ($30^\circ$)** | $833\ \mu\text{s}$ ($\approx 171$ counts) | Visual staging angle held on table |
| **Servo Fold Pulse ($180^\circ$)** | $2500\ \mu\text{s}$ ($\approx 512$ counts) | Full fold flip articulation |

---

## Core Software Libraries & ESP-IDF Drivers

1. **System & FreeRTOS**:
   - `esp_system.h`, `esp_chip_info.h`, `esp_flash.h`: System telemetry, heap monitoring, chip diagnostics.
   - `freertos/FreeRTOS.h`, `freertos/task.h`, `freertos/queue.h`, `freertos/event_groups.h`, `freertos/timers.h`.
2. **GPIO Driver**:
   - `driver/gpio.h`: Pin resets, direction configuration, pull-up resistors, and state reading.
3. **I2C Master Driver**:
   - `driver/i2c.h` / `driver/i2c_master.h`: Bus communication with PCA9685 (`0x40`) protected by FreeRTOS mutex.
4. **Bluetooth Low Energy (NimBLE)**:
   - `nimble/nimble_port.h`, `nimble/nimble_port_freertos.h`, `host/ble_hs.h`, `services/gap/ble_svc_gap.h`, `services/gatt/ble_svc_gatt.h`.
   - Lightweight, robust BLE stack requiring only $\approx 40\text{ KB}$ SRAM.
5. **NVS Flash Storage**:
   - `nvs_flash.h`, `nvs.h`: Partition initialization, key-value blob read/write operations for the 4 button routines with IEEE 802.3 CRC32 integrity validation.
6. **Logging & Debugging**:
   - `esp_log.h`: Structured logging (`MAIN`, `BLE`, `TELEM`, `BUTTONS`, `LED`, `PCA9685`, `MOTION`, `STORAGE`, `SM`).

---

## System Timing & Configuration Constants (`config.h`)

| Constant | Value | Description |
|---|---|---|
| `MAX_STEPS_PER_ROUTINE` | `16` | Maximum steps allowable per folding preset routine |
| `MAX_MOTORS_PER_STEP` | `2` | Maximum servos allowed to fold synchronously in 1 step |
| `TOTAL_SERVO_CHANNELS` | `16` | Total physical servo channels on the PCA9685 driver |
| `TOTAL_PRESET_COUNT` | `4` | Physical preset buttons on device (B1 to B4) |
| `COMMAND_QUEUE_LENGTH` | `16` | Unified command queue depth |
| `BUTTON_DEBOUNCE_MS` | `50` ms | Low-pass debounce sampling window |
| `BUTTON_LONG_PRESS_MS` | `3000` ms | Continuous hold duration required to enter Programming Mode |
| `BUTTON_SHORT_PRESS_MAX_MS` | `500` ms | Upper bound for tap gesture detection in Daily Run Mode |
| `PROGRAMMING_TIMEOUT_MS` | `20000` ms | Inactivity timeout auto-exiting Programming Mode |
| `FOLD_DWELL_TIME_MS` | `300` ms | Dwell time holding flap at $180^\circ$ before returning |
| `INTER_STEP_DELAY_MS` | `200` ms | Settling delay between consecutive folding steps |
| `TELEMETRY_STREAM_HZ` | `10` Hz | Real-time sequence progress and motor angle streaming rate |
| `BLE_CONN_INTERVAL_MIN_MS` | `7.5f` ms | Minimum BLE connection interval (low latency) |
| `BLE_CONN_INTERVAL_MAX_MS` | `15.0f` ms | Maximum BLE connection interval |
| `NUDGE_ANGLE_DEG` | `15.0f` | Motor identification sweep angle |
| `STAGE_ANGLE_DEG` | `30.0f` | Visual staging hold angle |
| `HOME_ANGLE_DEG` | `0.0f` | Flat panel rest position |
| `FOLD_ANGLE_DEG` | `180.0f` | Complete flap fold angle |

---

## Sequence & Telemetry Data Structures

### 1. Folding Sequence Structures (NVS Flash Storage)

```c
// Individual step containing 1 or 2 simultaneous servo motions (3 bytes packed, 0 padding)
typedef struct __attribute__((packed)) {
    uint8_t motor_count;                     // Number of active motors (1 or 2)
    uint8_t motor_ids[MAX_MOTORS_PER_STEP];  // Zero-indexed servo IDs (0 to 15)
} fold_step_t;

// Complete routine sequence structure stored in NVS flash blob for Buttons 1 to 4 (53 bytes packed)
// 1 byte step_count + (16 * 3 bytes steps) + 4 bytes CRC32 checksum = exactly 53 bytes
typedef struct __attribute__((packed)) {
    uint8_t step_count;                       // Number of steps in sequence (1 to 16)
    fold_step_t steps[MAX_STEPS_PER_ROUTINE]; // Array of sequence steps (48 bytes)
    uint32_t checksum;                        // CRC32 integrity validation checksum (4 bytes)
} fold_routine_t;
```

### 2. High-Speed Sequence Progress & Motor Telemetry Packet (`telemetry_packet_t`)

Packed 29-byte binary frame broadcast at 10 Hz over BLE Notify (`FAB2`):

```c
typedef struct __attribute__((packed)) {
    uint8_t system_state;            // system_state_t (0: Idle, 1: Running, 2: Programming, 3: E-Stop, 4: Error)
    uint8_t active_button_id;        // Active button (1-4 if executing button routine, 0 if preview/idle)
    uint8_t current_step_idx;        // Active step index (0-indexed, 0 to 15)
    uint8_t total_steps;             // Total steps in active routine
    uint8_t step_progress_pct;       // Current step completion percentage (0-100%)
    uint16_t elapsed_step_time_ms;   // Elapsed time in active step (ms)
    uint8_t channel_angles[16];      // Live angles for channels 0-15 (0 to 180 deg)
    uint8_t last_cmd_status;         // Status of last command (0: OK, 1: ERR_INVALID_STEP, 2: ERR_BOUNDS, 3: ERR_FULL, 4: ERR_CRC)
    uint16_t free_heap_kb;           // ESP32 internal free DRAM in KB
    int8_t ble_rssi_dbm;             // BLE RSSI in dBm (-128 if disconnected)
    uint8_t error_code;              // Error bitmask (BIT0=I2C_Fail, BIT1=NVS_Fail, etc.)
    uint16_t sequence_counter;       // Monotonically increasing packet counter
} telemetry_packet_t;
```

---

## Scalable Command Protocol & Unified Ingress

All system inputs (Physical Buttons, NimBLE GATT, Timers) converge into the single, thread-safe FreeRTOS `xCommandQueue`.

```mermaid
graph LR
    subgraph Transports [Transport Ingress Sources]
        BTN_IN["Physical 4-Button Pad<br/>(Debounce & Gestures)"]
        BLE_IN["NimBLE GATT Server<br/>(Control Point FAB1 & Button Sync FAB3)"]
        TIMER_IN["RTOS Timers<br/>(Inactivity Watchdog)"]
    end

    subgraph CommandLayer [Unified Command Pipeline]
        CMD_STRUCT["command_t<br/>- type: cmd_type_t<br/>- source: cmd_source_t<br/>- payload: cmd_payload_t"]
        QUEUE[("Unified FreeRTOS Queue<br/>xCommandQueue (Depth: 16)")]
    end

    subgraph ExecutionEngine [Execution & Storage Subsystems]
        SM["State Machine Engine"]
        MOTION["Motion Task (Core 0)"]
        NVS["NVS Storage (Buttons 1-4)"]
    end

    BTN_IN -->|command_t| QUEUE
    BLE_IN -->|command_t| QUEUE
    TIMER_IN -->|command_t| QUEUE
    QUEUE --> SM
    SM --> MOTION
    SM --> NVS
```

### 1. Command Definitions (`command.h`)

```c
typedef enum {
    SOURCE_PHYSICAL_BUTTON = 0, /* On-board physical 4-button pad */
    SOURCE_BLE             = 1, /* Bluetooth LE GATT connection (Mobile App) */
    SOURCE_INTERNAL_TIMER  = 2  /* Internal RTOS timer / safety watchdog */
} cmd_source_t;

typedef enum {
    /* Execution & Control Commands */
    CMD_RUN_PRESET = 0,         /* Start saved Button 1-4 sequence */
    CMD_RUN_RAW_SEQUENCE,       /* Start unsaved raw routine preview directly */
    CMD_STOP_SEQUENCE,          /* Cleanly stop active folding sequence and home */
    CMD_EMERGENCY_STOP,         /* Immediate <50ms E-Stop abort & home all servos */

    /* Programming & Staging Commands */
    CMD_ENTER_PROGRAM_MODE,     /* Enter visual staging mode for target button (1 to 4) */
    CMD_CYCLE_NUDGE_MOTOR,      /* Cycle motor index and pulse 15° identification nudge */
    CMD_STAGE_TOGGLE_MOTOR,     /* Toggle target motor staged (30°) / rest (0°) */
    CMD_LOCK_STEP,              /* Commit staged motor(s) to step buffer */
    CMD_SAVE_EXIT_PROGRAM,      /* Commit buffer to NVS flash and exit */

    /* Remote Sequence Editor Commands */
    CMD_REMOTE_EDIT_STEP,       /* Insert, delete, update, or reorder steps in routine buffer */
    CMD_SET_BUTTON_SEQUENCE,    /* Directly overwrite Button 1-4 routine in NVS */
    CMD_GET_BUTTON_CONFIG,      /* Request current 4-button sequence configuration */

    /* Live Calibration & Jog */
    CMD_JOG_MOTOR_ANGLE,        /* Live position jog (0° to 180°) for calibration */

    /* Telemetry Control */
    CMD_GET_TELEMETRY,          /* Request single-shot telemetry snapshot */
    CMD_SET_TELEMETRY_STREAM    /* Enable or disable 10 Hz automatic streaming */
} cmd_type_t;

typedef struct {
    uint8_t action;             // 0: Insert, 1: Delete, 2: Update, 3: Reorder
    uint8_t step_index;         // 0 to 15
    fold_step_t step_data;      // Motor configuration
} step_edit_param_t;

typedef struct {
    uint8_t channel;            // 0 to 15
    float angle_deg;            // 0.0 to 180.0
} jog_param_t;

typedef struct {
    uint8_t button_id;          // 1 to 4
    fold_routine_t routine;     // Sequence data
} button_sync_param_t;

typedef union {
    uint8_t preset_id;                  // For CMD_RUN_PRESET, CMD_ENTER_PROGRAM_MODE (1 to 4)
    fold_routine_t raw_routine;         // For CMD_RUN_RAW_SEQUENCE
    button_sync_param_t button_sync;    // For CMD_SET_BUTTON_SEQUENCE
    step_edit_param_t step_edit;        // For CMD_REMOTE_EDIT_STEP
    jog_param_t jog_param;              // For CMD_JOG_MOTOR_ANGLE
    bool stream_enable;                 // For CMD_SET_TELEMETRY_STREAM
} cmd_payload_t;

typedef struct {
    cmd_type_t type;
    cmd_source_t source;
    cmd_payload_t payload;
} command_t;
```

---

## Bluetooth Low Energy (NimBLE) GATT Specifications

### 1. Primary Service & Characteristics

* **Service UUID**: `0000FAB0-0000-1000-8000-00805F9B34FB` (Fabrica Robot Service)

| Characteristic | UUID | Properties | MTU / Size | Function |
|---|---|---|---|---|
| **Control Point (`FAB1`)** | `0000FAB1-...` | Write, Write Without Resp | $\le 64$ Bytes | Ingests binary commands: Start/Stop, Staging, Edit, Jog, E-Stop, and E-Stop Clear |
| **Status & Telemetry (`FAB2`)** | `0000FAB2-...` | Notify, Read | $29$ Bytes | Streams 10 Hz sequence progress, live motor positions, and last command status |
| **Button Config Sync (`FAB3`)** | `0000FAB3-...` | Read, Write, Notify | $212$ Bytes | Reads/writes 4 button sequences (`fold_routine_t`, packed); notifies on changes |

#### Payload Framing & Semantics:
* **Control Point (`FAB1`)**: Accepts serialized binary commands matching `command_t`. Sending `CMD_STOP_SEQUENCE` over `FAB1` also serves to clear `STATE_ESTOP` back to `STATE_IDLE_RUN`. Command validation errors are reported via `last_cmd_status` on `FAB2`.
* **Telemetry (`FAB2`)**: Emits packed 29-byte `telemetry_packet_t` at 10 Hz containing system state, active step, progress %, 16 channel angles, and `last_cmd_status` (no hardware current sensing required).
* **Button Config Sync (`FAB3`)**:
  - **Packed Struct Guarantee**: Uses `__attribute__((packed))` on `fold_step_t` (3B) and `fold_routine_t` (53B) to guarantee zero struct padding bytes.
  - **GATT Read**: Returns the complete 212-byte table containing all 4 physical button routines ($4 \times 53\text{ bytes} = 212\text{ bytes}$, fitting cleanly within standard negotiated MTU).
  - **GATT Write**: Accepts either a 54-byte `button_sync_param_t` (1-byte button ID + 53-byte `fold_routine_t`) to overwrite a single preset, or a full 212-byte table.
  - **GATT Notify**: Automatically dispatched to mobile client whenever any button routine is modified (either locally via visual staging or remotely over BLE).

### 2. Standard Device Information Service (DIS `0x180A`)

* **Model Number String (`0x2A24`)**: `"Fabrica-DevKit-v1"`
* **Firmware Revision String (`0x2A26`)**: `"v1.13.0"` (used for mobile app protocol compatibility handshake)
* **Manufacturer Name String (`0x2A29`)**: `"Fabrica Robotics"`

### 3. Proof-of-Presence BLE Security & Bonding Architecture

* **Single Active Central Policy**: `max_connections = 1`. The robot stops advertising while connected to a mobile app to prevent connection hijacking.
* **First-Time Pairing Authorization**:
  - When an unbonded mobile phone initiates a connection, the ESP32 enters a **30-second Physical Authorization Window**.
  - The Status LED flashes `LED_STATE_BLE_PAIRING` (fast double-blink).
  - The user must physically press **any button (B1–B4)** on the robot to authorize pairing.
  - **Motion Suppression during Pairing**: While the 30-second authorization window is active, the first physical button press strictly authorizes the BLE bond and suppresses triggering routine execution.
  - **Bond Lifecycle & Eviction**: Supports up to 4 bonded devices in NVS (`"ble_bonds"`). When a 5th phone pairs, the oldest bond is evicted automatically (FIFO/LRU).
  - **Hardware Bond Factory Reset**: Holding physical buttons B1 + B4 simultaneously for 5 seconds at power-on or in idle clears all stored bonds in `"ble_bonds"` and confirms with 3 fast LED flashes.
  - Upon button press, the phone's identity key is securely bonded and stored into NVS (`"ble_bonds"` namespace).
  - The LED transitions to `LED_STATE_BLE_CONNECTED` (solid 1.0s pulse).
  - **Unauthorized Timeout**: If no button is pressed within 30 seconds, the ESP32 terminates the connection (`ble_gap_terminate`) and returns to advertising.
* **Frictionless Subsequent Auto-Reconnect**:
  - Any previously bonded mobile device is recognized automatically upon connection without requiring another physical button press.

### 4. Advertising & Connection Parameters

* **Device Name**: `Fabrica-XXXX` (where `XXXX` is derived from the last 2 bytes of the ESP32 BT MAC address).
* **Advertising Interval**: 100ms (fast advertising on startup or disconnect).
* **Connection Interval**: Min 7.5ms / Max 15ms (ensures low-latency responsive mobile jog control and $<50\text{ms}$ E-Stop delivery).
* **Mandatory ATT MTU Exchange**: Firmware negotiates ATT MTU $\ge 247$ bytes immediately upon connection (supports up to 512 bytes) to guarantee single-packet transfers for 29-byte telemetry and 212-byte sequence tables.

---

## FreeRTOS Task Budget & Memory Allocation

### 1. Task Partitioning & CPU Core Affinity

| Task Name | Core | Priority | Stack Size | Description |
|---|---|---|---|---|
| `app_motion_task` | Core 0 | 10 | 4096 Bytes | Real-time motion trajectories, I2C commands, $<50\text{ms}$ E-Stop |
| `app_ui_task` | Core 1 | 5 | 4096 Bytes | 4-button scanning, debouncing, gesture recognition, state machine |
| `app_ble_task` | Core 1 | 4 | 4096 Bytes | Apache NimBLE host stack, GATT server, MTU negotiation |
| `app_telem_task` | Core 1 | 3 | 2048 Bytes | Progress tracking, live motor position packing, and 10 Hz notify |
| `app_led_task` | Core 1 | 2 | 2048 Bytes | Status LED non-blocking pattern pulse train generator |

### 2. Internal SRAM & Heap Budget Analysis

* **Total Internal SRAM**: $520\text{ KB}$ ($\approx 320\text{ KB}$ available for application heap).
* **Firmware Baseline (Phases 1–7)**: Consumes $\approx 85\text{ KB}$.
* **Apache NimBLE Stack**: Consumes $\approx 40\text{ KB}$.
* **Telemetry & Sequence Buffers**: Consumes $\approx 4\text{ KB}$.
* **Net Available Application Free Heap**: $\ge 190\text{ KB}$ (substantial headroom, rock-solid long-term stability).

---

## File & Directory Structure

```
firmware/
├── specs/                          ← Project specifications (mission.md, tech-stack.md, roadmap.md)
├── CMakeLists.txt                  ← Root ESP-IDF project CMake file
├── Makefile                        ← Legacy GNU Make / helper entrypoint
├── sdkconfig.defaults              ← Default SDK configuration (240MHz, 1000Hz tick, 4MB flash, NimBLE enabled)
├── main/                           ← Main firmware component
│   ├── CMakeLists.txt              ← Component source registration
│   ├── main.c                      ← System initialization, chip diagnostics, task bootstrap
│   ├── config.h                    ← Single source of truth for pinouts, timings, limits, thresholds
│   ├── command.h                   ← Unified source-agnostic command protocol & event structures
│   ├── buttons.h / buttons.c       ← 4-button debouncing & gesture recognition (Tap vs Hold)
│   ├── led.h / led.c               ← Non-blocking multi-pattern LED controller engine
│   ├── pca9685.h / pca9685.c       ← I2C Master driver for PCA9685 16-channel PWM generator
│   ├── motion.h / motion.c         ← Real-time motion execution task, trajectory delays, E-Stop
│   ├── storage.h / storage.c       ← ESP-IDF NVS flash manager for 4 button sequences
│   ├── state_machine.h / .c        ← System state machine coordinating Run, Program & Calibration
│   ├── ble_transport.h / .c        ← Apache NimBLE GATT server (Control, Telemetry, Button Sync)
│   └── telemetry.h / telemetry.c   ← 10 Hz sequence progress & motor angle serialization
├── test/                           ← Host-based unit tests and mock hardware harness
└── README.md                       ← Build, flash, monitor instructions, hardware setup & mobile API guide
```
