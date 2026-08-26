# Requirements — Phase 1: Project Skeleton, Hardware Configuration & Diagnostics

## Scope

Phase 1 delivers the base firmware skeleton and build infrastructure for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1** microcontroller. It encompasses:
1. Root and component build configuration files (`CMakeLists.txt`, `main/CMakeLists.txt`, `Makefile`, `sdkconfig.defaults`).
2. Single-source-of-truth hardware pinout mapping, system timing constants, and configuration header (`main/config.h`).
3. Source-agnostic unified command protocol, routine data structures, and event models (`main/command.h`).
4. System boot sequence, chip telemetry diagnostics, heap monitoring, and FreeRTOS IPC queue allocation (`main/main.c`).
5. Host test verification harness (`test/test_headers.c`).

---

## Decisions & Technical Specifications

### 1. Framework & Toolchain Compatibility
- **Target Microcontroller**: ESP32 Dev Board v1 (ESP-WROOM-32 / Xtensa Dual-Core 32-bit LX6 @ 240 MHz).
- **Framework**: Espressif ESP-IDF v5.x / v6.x native C toolchain with modern API header inclusions (`esp_chip_info.h`, `esp_flash.h`, `esp_system.h`, `freertos/FreeRTOS.h`, `freertos/queue.h`, `freertos/event_groups.h`).
- **Language Standard**: C99 / C11 with strict standard integer type definitions (`stdint.h`, `stdbool.h`, `stddef.h`).
- **Build System**: CMake 3.16+ with Ninja generator.

### 2. Hardware Pinout Allocations (`config.h`)

| Signal Name | ESP32 GPIO | Direction | Pull Mode | Active Level | Target Peripheral / Function |
|---|---|---|---|---|---|
| `STATUS_LED_GPIO` | `GPIO_NUM_2` | Output | None | High (1) | Visual status indicator LED (Built-in DevKit LED) |
| `BTN1_GPIO` | `GPIO_NUM_0` | Input | Internal Pull-Up | Low (0) | B1: Preset 1 Run / Cycle & Nudge Flap ($15^\circ$) |
| `BTN2_GPIO` | `GPIO_NUM_4` | Input | Internal Pull-Up | Low (0) | B2: Preset 2 Run / Stage & Toggle Flap ($30^\circ$) |
| `BTN3_GPIO` | `GPIO_NUM_16` | Input | Internal Pull-Up | Low (0) | B3: Preset 3 Run / Lock Step & Drop Flaps |
| `BTN4_GPIO` | `GPIO_NUM_17` | Input | Internal Pull-Up | Low (0) | B4: Preset 4 Run / Save to NVS & Exit |
| `I2C_SDA_GPIO` | `GPIO_NUM_21` | I/O | Open-Drain + Pull-Up | — | PCA9685 I2C Serial Data Bus |
| `I2C_SCL_GPIO` | `GPIO_NUM_22` | Output | Open-Drain + Pull-Up | — | PCA9685 I2C Serial Clock Bus |

### 3. System Limits & Timing Parameters (`config.h`)

| Parameter | Macro Constant | Value | Description |
|---|---|---|---|
| Routine Step Capacity | `MAX_STEPS_PER_ROUTINE` | `16` | Maximum steps per folding routine preset |
| Concurrent Flap Motion | `MAX_MOTORS_PER_STEP` | `2` | Maximum servos actuated simultaneously in 1 step |
| Servo Channels | `TOTAL_SERVO_CHANNELS` | `16` | Total physical PWM channels on PCA9685 |
| Debounce Filter Time | `BUTTON_DEBOUNCE_MS` | `50` ms | Low-pass button debounce filter window |
| Short Press Upper Bound | `BUTTON_SHORT_PRESS_MAX_MS` | `500` ms | Maximum duration classified as a tap |
| Long Press Threshold | `BUTTON_LONG_PRESS_MS` | `3000` ms | Continuous hold duration to enter Programming Mode |
| Inactivity Timeout | `PROGRAMMING_TIMEOUT_MS` | `20000` ms | Auto-exit duration for visual staging mode |
| Fold Dwell Time | `FOLD_DWELL_TIME_MS` | `300` ms | Flap hold duration at $180^\circ$ |
| Inter-Step Settling Delay | `INTER_STEP_DELAY_MS` | `200` ms | Pause between consecutive folding steps |
| Flap Rest Angle | `HOME_ANGLE_DEG` | `0.0f` | Flat tabletop resting position ($0^\circ$) |
| Flap Identification Angle | `NUDGE_ANGLE_DEG` | `15.0f` | Tactile/visual flap identification angle |
| Flap Visual Staging Angle | `STAGE_ANGLE_DEG` | `30.0f` | Flap staging hold angle |
| Flap Full Fold Angle | `FOLD_ANGLE_DEG` | `180.0f` | Complete fold flip articulation |
| PCA9685 I2C Address | `PCA9685_I2C_ADDR` | `0x40` | Default hardware I2C address |
| PCA9685 PWM Frequency | `PCA9685_PWM_FREQ_HZ` | `50` Hz | 20 ms frame period for servo motors |
| PCA9685 Resolution | `PCA9685_PWM_RES_BITS` | `12` | 4096-step PWM count resolution |
| Servo Min Pulse | `SERVO_MIN_PULSE_US` | `500` $\mu\text{s}$ | $0^\circ$ pulse width ($\approx 102$ counts @ 50 Hz) |
| Servo Max Pulse | `SERVO_MAX_PULSE_US` | `2500` $\mu\text{s}$ | $180^\circ$ pulse width ($\approx 512$ counts @ 50 Hz) |

### 4. Scalable Command Protocol & Data Structures (`command.h`)
- **Transport Sources (`cmd_source_t`)**:
  - `SOURCE_PHYSICAL_BUTTON`: Front panel 4-button control deck.
  - `SOURCE_BLE`: Bluetooth Low Energy GATT service (future mobile app).
  - `SOURCE_WIFI`: Wi-Fi / Local WebSocket JSON RPC interface (future mobile app / smart home).
  - `SOURCE_INTERNAL_TIMER`: Inactivity timeouts and safety watchdog triggers.
- **Command Types (`cmd_type_t`)**:
  - `CMD_RUN_PRESET`: Trigger saved preset routine (Preset 1–4).
  - `CMD_RUN_RAW_SEQUENCE`: Trigger unsaved custom routine directly.
  - `CMD_EMERGENCY_STOP`: Immediate motion halt and panel homing.
  - `CMD_ENTER_PROGRAM_MODE`: Transition to visual staging mode for target preset.
  - `CMD_CYCLE_NUDGE_MOTOR`: Increment target motor channel and trigger $15^\circ$ nudge.
  - `CMD_STAGE_TOGGLE_MOTOR`: Toggle target motor between $30^\circ$ staged and $0^\circ$ flat.
  - `CMD_LOCK_STEP`: Commit staged motor(s) to routine buffer.
  - `CMD_SAVE_EXIT_PROGRAM`: Write routine buffer to NVS flash and exit to Run Mode.
  - `CMD_JOG_MOTOR_ANGLE`: Manual live angle calibration ($0^\circ \dots 180^\circ$).
  - `CMD_GET_TELEMETRY`: Request live status packet.
  - `CMD_SYNC_PRESETS`: Synchronize routine presets with mobile app.
- **Sequence Schema**:
  ```c
  typedef struct {
      uint8_t motor_count;
      uint8_t motor_ids[MAX_MOTORS_PER_STEP];
  } fold_step_t;

  typedef struct {
      uint8_t step_count;
      fold_step_t steps[MAX_STEPS_PER_ROUTINE];
      uint32_t checksum;
  } fold_routine_t;

  typedef union {
      uint8_t preset_id;
      fold_routine_t raw_routine;
      struct {
          uint8_t channel;
          float angle_deg;
      } jog_param;
  } cmd_payload_t;

  typedef struct {
      cmd_type_t type;
      cmd_source_t source;
      cmd_payload_t payload;
  } command_t;
  ```
- **Unified Command Queue**:
  - Depth: `COMMAND_QUEUE_LENGTH = 16` items.

### 5. Boot Sequence & Diagnostics (`main.c`)
- On startup in `app_main()`:
  1. Print startup banner with project identity: `Fabrica Cloth Folding Robot - ESP32 Firmware`.
  2. Query `esp_chip_info()` and output:
     - Chip model (e.g. ESP32).
     - Silicon revision.
     - Number of CPU cores (Dual-Core Xtensa LX6).
     - Supported features (Wi-Fi 802.11b/g/n, Bluetooth V4.2 BR/EDR/BLE).
  3. Query `esp_flash_get_size()` and output detected SPI flash size in MB.
  4. Query `esp_get_minimum_free_heap_size()` and output initial free heap statistics.
  5. Allocate FreeRTOS unified command queue (`xCommandQueue`) and system event group (`xSystemEvents`).
  6. Verify successful queue handle creation and log system ready state.

---

## Constraints
- **Zero Dynamic Allocation in Motion Loop**: Real-time queues and structs must use fixed-size static allocations.
- **Forward Compatibility**: Header structures in `command.h` must not require modifications when Phase 8 BLE / Wi-Fi transports are activated.
- **SDK Independence**: Headers must cleanly compile under host C compilers for unit testing without hard dependencies on target-only ESP-IDF assembly macros.

---

## Non-Goals
- Active I2C transactions or servo motor movement (covered in Phase 3 & Phase 5).
- Button interrupt service routines or debouncing tasks (covered in Phase 2).
- NVS flash read/write operations (covered in Phase 4).
- BLE / Wi-Fi network stack activation (covered in Phase 8).

---

## Context
Phase 1 builds upon the mission defined in `firmware/specs/mission.md` and aligns with the dual-core architecture in `firmware/specs/tech-stack.md`. It provides the foundational headers and boot verification required by all subsequent firmware modules.
