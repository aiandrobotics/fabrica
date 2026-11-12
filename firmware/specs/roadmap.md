# Roadmap — ESP32 Firmware

Each phase is a small, independently buildable and testable unit of work.
Build, validate, and verify each milestone before moving to the next phase.

---

## Phase 0 — Project Constitution & Firmware Specs ✅
- Create `firmware/specs/mission.md`, `firmware/specs/tech-stack.md`, and `firmware/specs/roadmap.md`.
- Establish target hardware architecture: **ESP32 Dev Board v1**, **PCA9685 16-Channel 12-Bit PWM Driver**, **4 Push Buttons (B1–B4)**, **1 Status LED**, and **up to 16 MG996R Servos**.
- Define dual-core FreeRTOS task partition: Core 0 for real-time motion and I2C actuation; Core 1 for UI event loop, button debouncing, LED patterns, and NVS storage.
- Align code patterns and project structure with the reference implementation in `poc/esp_hello_world`.

---

## Phase 1 — Project Skeleton, Hardware Configuration & Diagnostics (`main.c`, `config.h`, `command.h`) ✅
- Create root `CMakeLists.txt`, `main/CMakeLists.txt`, `Makefile`, and `sdkconfig.defaults`.
- Create `main/config.h` as the single source of truth for GPIO pin assignments (`LED_GPIO 2`, `BTN1_GPIO 4`, `BTN2_GPIO 16`, `BTN3_GPIO 17`, `BTN4_GPIO 5`, `I2C_SDA_GPIO 21`, `I2C_SCL_GPIO 22`), PWM limits, timing constants, and system constraints.
- Create `main/command.h` defining the source-agnostic `command_t` schema (`SOURCE_PHYSICAL_BUTTON`, `SOURCE_BLE`) and unified command queue to guarantee forward compatibility with the mobile app.
- Implement `main/main.c` system startup and diagnostics (adapted from `poc/esp_hello_world/main/hello_world_main.c`):
  - Print ESP32 chip details (model, silicon revision, CPU cores, WiFi/BT features).
  - Print SPI flash size and monitor heap memory via `esp_get_minimum_free_heap_size()`.
  - Initialize FreeRTOS inter-task communication primitives (queues and event groups).
- **Validation**: Verified with host unit tests (`make test`, 50/50 pass), ESP-IDF build compilation, and live hardware flash/monitor on ESP32 over serial.

---

## Phase 2 — UI Subsystem: 4-Button Debouncer & Non-Blocking LED Pattern Engine (`buttons.c`, `led.c`) ✅
- **Status LED Pattern Engine** (`main/led.h`, `main/led.c`):
  - Implement non-blocking FreeRTOS software timer / task driving core visual state feedback patterns:
    1. `LED_STATE_IDLE`: Soft heartbeat (10% duty cycle / 0.5 Hz) or OFF awaiting input.
    2. `LED_STATE_RUNNING`: Solid ON continuous throughout routine execution.
    3. `LED_STATE_SAVE_SUCCESS`: Solid ON for 2.0 seconds then OFF.
    4. `LED_STATE_INPUT_ERROR`: 3 fast flashes (60ms ON / 60ms OFF).
    5. `LED_STATE_ESTOP`: 5 rapid flashes (50ms ON / 50ms OFF).
- **4-Button Debouncing & Gesture Recognition** (`main/buttons.h`, `main/buttons.c`):
  - Configure `GPIO 4`, `GPIO 16`, `GPIO 17`, and `GPIO 5` as inputs with internal pull-ups (`GPIO_PULLUP_ONLY`).
  - Implement 50ms low-pass debounce sampling.
  - Distinguish between **Short Tap** (<500ms) and **Long Press** (≥3000ms continuous hold).
  - Translate physical button gestures into standardized `command_t` structs and dispatch to the unified command queue.
- **Validation**: Verified with host unit test suite (`make test`, 111/111 checks pass with 100% success) covering debounce filtering, short tap, long press hold duration, zero release spurious triggers, and all 7 LED pattern sequences.

---

## Phase 3 — I2C PCA9685 16-Channel PWM Servo Driver (`pca9685.c`) ✅
- **I2C Master Initialization & Configuration** (`main/pca9685.h`, `main/pca9685.c`):
  - Initialize ESP32 I2C Master peripheral on `GPIO 21 (SDA)` and `GPIO 22 (SCL)` at 100 kHz with FreeRTOS mutex bus synchronization.
  - Configure PCA9685 controller (`0x40` address): wake from sleep, set prescale register for 50 Hz PWM ($20\text{ms}$ period), enable auto-increment mode, configure totem-pole output.
- **Angle to 12-Bit PWM Conversion**:
  - Implement conversion from degrees ($0^\circ \text{ to } 180^\circ$) to 12-bit PWM register counts ($500\,\mu\text{s} \to 2500\,\mu\text{s}$, $102 \to 512$ counts) with mechanical boundary clamping.
  - Implement single channel angle command: `pca9685_set_servo_angle(channel, angle_deg)`.
  - Implement synchronized multi-channel angle command: `pca9685_set_multi_servo_angles(mask, angle_deg)`.
  - Implement mechanical identification nudge ($15^\circ$) and visual staging hold ($30^\circ$).
  - Implement all-channel home reset ($0^\circ$ for all channels 0–15).
  - Implement low-power sleep and wake control (`pca9685_sleep()`).
- **Validation**: Verified with host unit test suite (`make test`, 82/82 checks pass, 193/193 total across all test suites) covering angle conversion math, bounds clamping, register writes, sleep/wake, multi-channel masks, and simulated homing across all 16 channels.

---

## Phase 4 — Non-Volatile Storage (NVS) Sequence Manager (`storage.c`) ✅
- **NVS Partition Initialization & Management** (`main/storage.h`, `main/storage.c`):
  - Initialize ESP-IDF NVS flash subsystem (`nvs_flash_init()`) with auto-erase and re-init on partition truncation or version update (`ESP_ERR_NVS_NO_FREE_PAGES` / `ESP_ERR_NVS_NEW_VERSION_FOUND`).
  - Implemented binary serialization schema for `fold_routine_t` and `fold_step_t` (Presets 1–4, up to 16 steps, max 2 motors per step).
  - Implemented IEEE 802.3 standard CRC32 integrity validation engine (`0xEDB88320` polynomial) to detect bit-rot and incomplete writes.
- **CRUD Operations & Factory Seeding**:
  - `storage_save_routine(preset_id, &routine)`: Atomic NVS blob write with automatic CRC32 calculation.
  - `storage_load_routine(preset_id, &routine)`: Read blob with CRC verification; graceful fallback to factory defaults on corruption or uninitialized slots.
  - `storage_erase_routine(preset_id)`: Remove individual preset slot from NVS.
  - `storage_init_factory_defaults()` / `storage_get_default_routine()`: Seed 4 default folding sequences (Adult T-shirt, Long-Sleeve Shirt, Trousers/Jeans, Towel/Linen) on initial boot using `"preset_init"` flag.
- **Validation**: Verified with host unit test suite (`make test`, 65/65 checks pass, 261/261 total across all test suites) covering CRC32 determinism, bit-mutation sensitivity, save/load/erase cycles, corruption fallbacks, boundary parameter rejection, and factory preset seeding.

---

## Phase 5 — Motion Engine & Daily Run Mode Execution (`motion.c`) ✅
- **Core 0 Real-Time Motion Task** (`main/motion.h`, `main/motion.c`):
  - High-priority FreeRTOS task pinned to Core 0 executing sequence steps sequentially (Step 1 to $N$).
  - **Single Motor Sweep**: Target servo sweeps $0^\circ \rightarrow 180^\circ$, dwells for 300ms, then returns $180^\circ \rightarrow 0^\circ$.
  - **Parallel Motor Sweep**: Both assigned servos sweep synchronously $0^\circ \rightarrow 180^\circ$, dwell for 300ms, and return synchronously $180^\circ \rightarrow 0^\circ$.
  - **Inter-Step Settling Delay**: 200ms pause between consecutive steps.
  - Turn LED Solid ON during execution; turn OFF when returning to Idle.
- **Daily Run Mode Trigger & Safeguards**:
  - Single short tap on B1–B4 triggers execution of Preset 1–4.
  - **Emergency Stop (E-Stop)**: Tapping **any button** while motion is active immediately halts PWM pulses, commands all 16 channels to $0^\circ$, delivers 5 rapid LED flashes, and aborts the routine in $<50\text{ms}$.
  - **Empty Preset Protection**: Tapping a button with 0 recorded steps produces 3 fast LED flashes without activating motors.
- **Validation**: Verified with host unit test suite (`make test`, 74/74 checks pass, 342/342 total across all test suites) covering single/parallel sweeps, dwell/settling delays, empty preset rejection, re-entrancy protection, and <50ms Emergency Stop preemption.

---

## Phase 6 — State Machine Coordinator & Minimal Physical Button Interface (`state_machine.c`) ✅
- **Minimal Physical UI & State Machine Coordinator** (`main/state_machine.h`, `main/state_machine.c`):
  - Keep physical buttons strictly focused on daily execution and safety:
    - **Short Tap (Idle)**: Triggers Preset 1–4 (`CMD_RUN_PRESET`), pre-seeded with 4 factory defaults out of the box.
    - **Any Tap (Running)**: Triggers immediate `<50ms` Emergency Stop (`CMD_EMERGENCY_STOP`).
    - **Single-Button Long Press (3s Hold in Idle)**: Dispatches `CMD_ENTER_BLE_PAIRING` to open the BLE pairing/discovery window (120s timed window when bonded peers exist, or indefinite when 0 bonds are stored; `LED_STATE_BLE_PAIRING`); custom sequence programming is offloaded to BLE GATT rather than multi-button programming modes on the physical pad.
  - **Wireless Sequence & Calibration Dispatch**:
    - `CMD_SET_BUTTON_SEQUENCE`: Saves a custom routine received over BLE to Button 1–4 in NVS flash and confirms with `LED_STATE_SAVE_SUCCESS` (2.0s solid ON).
    - `CMD_RESTORE_FACTORY_PRESETS`: Restores Buttons 1–4 to built-in factory default routines in NVS.
    - `CMD_RUN_RAW_SEQUENCE`: Previews an unsaved custom sequence directly over BLE without modifying NVS.
    - `CMD_JOG_MOTOR_ANGLE`: Live servo angle control over BLE for flap identification and mechanical calibration.
- **Validation**: Verified with host unit test suite (`make test`) covering state machine lifecycle, minimal button gesture translation, preset dispatch, wireless button sequence save/playback, factory preset restoration, servo jog, and Emergency Stop preemption.

---

## Phase 7 — End-to-End System Validation, Stress Testing & Preset Library ✅
- **Factory Preset Library (Exercising All 4 Motors)**:
  - Preset 1: Standard Adult T-Shirt (4 steps: Left Ch 0 $\to$ Right Ch 1 $\to$ Bottom Ch 2 $\to$ Top Collar Ch 3) — tests all 4 motors on Button 1.
  - Preset 2: Long-Sleeve Shirt (5 steps: Parallel dual-sleeve Ch 0+1 $\to$ Top Collar Ch 3 $\to$ Left body Ch 0 $\to$ Right body Ch 1 $\to$ Bottom Ch 2).
  - Preset 3: Trousers / Jeans (3 steps: Vertical fold Ch 0 $\to$ Bottom fold Ch 2 $\to$ Top waistband Ch 3).
  - Preset 4: Towel / Linen (4 steps: Left half fold Ch 0 $\to$ Right quarter fold Ch 1 $\to$ Bottom fold Ch 2 $\to$ Top final fold Ch 3).
  - Standardized named channel aliases (`SERVO_FLAP_LEFT`, `SERVO_FLAP_RIGHT`, `SERVO_FLAP_BOTTOM`, `SERVO_FLAP_TOP`) in `main/config.h`.
- **Stress & Endurance Testing**:
  - 100-cycle continuous run test verifying zero heap memory leaks and long-term state stability.
  - Stress testing E-Stop triggers under active mid-sweep conditions (<50ms abort latency, immediate 16-channel homing).
  - Automated verification of power loss and bit-rot resilience during NVS write operations (`ESP_ERR_INVALID_CRC` fallback).
  - 50-cycle rapid mode-switching stress test verifying state machine invariant stability.
- **System Documentation**: Comprehensive `firmware/README.md` with electrical wiring diagrams, PCA9685 power isolation, dual-core FreeRTOS architecture, full operator manual, and test instructions.
- **Validation**: Verified with host unit test suite (`make test`, 63/63 checks pass in `test_e2e_stress.c`, 566/566 total checks pass across all 7 test suites).

---

## Phase 8 — Wireless Transport: NimBLE GATT Server & iOS/Android Interop (`ble_transport.c`, `sdkconfig.defaults`) ✅
- **ESP-IDF Build & NimBLE Stack Configuration (`sdkconfig.defaults`, `main/CMakeLists.txt`)**:
  - Enable Bluetooth and Apache NimBLE host-only stack in `sdkconfig.defaults` (`CONFIG_BT_ENABLED=y`, `CONFIG_BT_NIMBLE_ENABLED=y`, `CONFIG_BT_NIMBLE_PINNED_TO_CORE_1=y`, `CONFIG_BT_NIMBLE_HOST_TASK_STACK_SIZE=4096`, `CONFIG_BT_NIMBLE_ATT_PREFERRED_MTU=512`, `CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1`, `CONFIG_BT_NIMBLE_MAX_BONDS=4`, `CONFIG_BT_NIMBLE_NVS_PERSIST=y`, `CONFIG_BT_NIMBLE_SM_LEGACY=y`, `CONFIG_BT_NIMBLE_SM_SC=y`, `CONFIG_BT_NIMBLE_RPA_TIMEOUT=900`).
  - Register `bt` component in `main/CMakeLists.txt` and initialize NimBLE host stack on Core 1 (`app_ble_task`, Priority 4, 4KB stack) to maintain zero timing jitter on Core 0 real-time servo motion.
- **BLE GAP Advertising & iOS/Android Discovery**:
  - Broadcast custom 128-bit service UUID `0000FAB0-0000-1000-8000-00805F9B34FB` with dynamic device name (`Fabrica-XXXX` derived from the last 2 bytes of the ESP32 factory BT MAC address) at a 100ms fast advertising interval.
  - **Advertising Packet Split (31-Byte Legacy Limit for iOS & Android Compatibility)**:
    - **Primary Advertisement Packet (21B)**: Flags (`0x06`: General Discoverable + BR/EDR Not Supported, 3B) + Complete List of 128-bit Service Class UUIDs (`0000FAB0-...`, 18B) $\le 31\text{B}$ legacy limit. Mandatory for iOS `CoreBluetooth` service-filtered and background scan discovery as well as Android `BluetoothLeScanner` UUID filters.
    - **Scan Response Packet (17B)**: Complete Local Name (`Fabrica-XXXX`, 14B) + Tx Power Level (3B) to guarantee immediate human-readable name resolution upon active scanning in off-the-shelf BLE scanner apps (**nRF Connect**, **LightBlue**) on both iOS and Android.
  - **Single Active Central Policy**: Enforce `max_connections = 1` (stops advertising while connected) with automatic advertising restart on central disconnect or link supervision timeout.
- **Firmware-Driven Connection Parameters & ATT MTU Negotiation (Zero Custom App Code Required)**:
  - **Peripheral-Initiated Connection Parameter Update (`ble_gap_update_params`)**:
    - Firmware proactively initiates L2CAP/GAP connection parameter negotiation from the peripheral side (after a 1.5s post-connect stabilization delay so initial GATT service discovery on iOS/Android completes unthrottled) using parameters compliant with both **Apple Bluetooth Accessory Design Guidelines** and **Android BluetoothGatt**:
      - Connection Interval Min: `15.0ms` (12 units, satisfies Apple $\ge 15\text{ms}$)
      - Connection Interval Max: `30.0ms` (24 units, satisfies Apple $\text{Min} + 15\text{ms} \le \text{Max}$)
      - Slave Latency: `0` (satisfies Apple $\le 30$)
      - Supervision Timeout: `4000ms` (400 units, satisfies $2000\text{ms} \le \text{Timeout} \le 6000\text{ms}$ and $> 3 \times \text{Interval Max} \times (\text{Latency}+1)$)
    - Because the firmware requests these connection parameters directly, low-latency operation is achieved automatically on both iOS and Android even when testing with generic App Store BLE apps (nRF Connect / LightBlue).
  - **Peripheral- & Central-Initiated ATT MTU Exchange (`ble_att_set_preferred_mtu(512)`)**:
    - Support ATT MTU negotiation up to 512 bytes ($\ge 247$ bytes target) for single-packet telemetry and 212-byte sequence table transfers.
    - Firmware handles automatic central-initiated MTU exchange from iOS (`185–517` bytes) AND proactively initiates peripheral-side MTU exchange (`ble_gattc_exchange_mtu`) upon connection so Android devices (which default to a 23-byte MTU) automatically upgrade MTU in off-the-shelf test apps without manual user intervention.
    - Implement offset-aware GATT Long Read (`ATT_READ_BLOB_REQ`, `ctxt->offset` slicing) on `FAB2` and `FAB3` so full payloads remain readable even if a legacy central restricts MTU to 23 bytes.
  - **Generic Attribute Service (`0x1801`) & Service Changed Indication (`0x2A05`)**:
    - Enable NimBLE standard GATT service (`ble_svc_gatt_init()`) with `0x2A05` Service Changed characteristic so iOS and Android OS BLE stacks automatically invalidate cached GATT attribute tables across firmware updates.
- **Zero-Bond Out-of-the-Box Auto-Pairing, Hold-to-Pair BLE Security, Native SMP Bonding & RPA Privacy (iOS & Android Native)**:
  - **Zero-Bond Auto-Pairing (Out-of-the-Box & Post-Wipe)**: When zero bonded centrals exist in NVS (brand new unit or immediately following a hardware bond reset), Fabrica automatically enters **indefinite BLE Pairing Mode** (`LED_STATE_BLE_PAIRING` fast double-blink) on boot/reset without requiring any button press, remaining open until the first phone pairs. When one or more bonds exist, Fabrica boots directly into `STATE_IDLE_RUN` awaiting auto-connection.
  - **3-Second Hold-to-Pair Entry (Priority Preemption)**: Holding **any physical button (B1–B4) for 3 seconds** while in `STATE_IDLE_RUN` (or `STATE_ESTOP` / `STATE_CALIBRATING`) dispatches `CMD_ENTER_BLE_PAIRING`. When $\ge 1$ devices are bonded, this opens a **120-second (2-minute) BLE Pairing Window** (`BLE_PAIRING_TIMEOUT_MS = 120000`), setting the status LED to `LED_STATE_BLE_PAIRING` (fast double-blink), and disconnecting any currently connected central (`ble_transport_enter_pairing_mode()`) so GAP advertising immediately resumes for the new phone. The 3-second hold works unconditionally on new/0-bond devices as well (keeping pairing active).
  - **Native BLE SMP "Just Works" LE Secure Connections & Peripheral Security Request**:
    - Configure NimBLE Security Manager (`ble_hs_cfg`): `sm_sc = 1` (LE Secure Connections), `sm_bonding = 1`, `sm_mitm = 0`, `sm_io_cap = BLE_HS_IO_NO_INPUT_OUTPUT`, and key distribution `BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID` for both central and peripheral (`ble_store_config_init()` persisting bonds in NVS).
    - Upon `BLE_GAP_EVENT_CONNECT`, the firmware proactively initiates link security (`ble_gap_security_initiate(conn_handle)`). This is essential for iOS `CoreBluetooth` (which never initiates pairing unless requested by the peripheral) and Android when testing with off-the-shelf apps like LightBlue or nRF Connect.
  - **Resolvable Private Address (RPA) Resolution & Unbonded Rejection**:
    - Both iOS and Android 10+ rotate BLE MAC addresses every ~15 minutes using Resolvable Private Addresses (RPAs). By exchanging and storing peer **Identity Resolving Keys (IRKs)** in NVS via standard NimBLE SMP bonding, the firmware resolves rotating RPAs across reconnections using native link-layer security (requiring zero custom app tokens).
    - **During Active Pairing Window (`state_machine_is_ble_pairing() == true`)**: New unbonded centrals are permitted to complete SMP pairing and bond into NVS (up to 4 trusted devices); upon `BLE_GAP_EVENT_ENC_CHANGE` success, the pairing window closes and the LED pulses `LED_STATE_BLE_CONNECTED` (1.0s solid ON).
    - **Outside Pairing Window (`state_machine_is_ble_pairing() == false`)**: Already-bonded iOS/Android centrals resolve via IRK/LTK and auto-reconnect seamlessly (`LED_STATE_BLE_CONNECTED`), while unbonded connection or pairing attempts are rejected and terminated (`ble_gap_terminate(conn_handle, BLE_ERR_REM_USER_CONN_TERM)`).
  - **Bond Lifecycle & FIFO Eviction**: Support up to 4 bonded peer identities in NVS; if a 5th device pairs during an active pairing window, evict the oldest bond automatically (`ble_store_util_delete_oldest_peer()`).
  - **Hardware Bond Factory Reset (`B1 + B4` 5-Second Chord Hold)**: Holding physical buttons **B1 + B4** simultaneously for 5 seconds (`BUTTON_BOND_RESET_MS = 5000`) at power-on or in `STATE_IDLE_RUN` suppresses the 3s single-button pairing trigger, dispatches `CMD_CLEAR_BLE_BONDS`, clears all stored bonds in NVS (`ble_store_clear()`), terminates any active BLE connection, confirms with 3 fast LED flashes (`LED_STATE_INPUT_ERROR`), and automatically re-opens indefinite BLE pairing mode (`LED_STATE_BLE_PAIRING`).
  - **120-Second Pairing Timeout (Multi-Device)**: When $\ge 1$ devices are bonded, if no new device pairs within 120 seconds after a 3s hold, `state_machine_tick()` closes the pairing window and restores `LED_STATE_IDLE`.
- **Standard Device Information Service (DIS `0x180A`)**:
  - Expose read-only Model Number (`0x2A24`: `"Fabrica-DevKit-v1"`), Firmware Revision (`0x2A26`: `"v1.13.0"`), and Manufacturer Name (`0x2A29`: `"Fabrica Robotics"`) characteristics visible natively in nRF Connect and LightBlue.
- **Fabrica Primary GATT Service & Self-Describing Descriptors for Test Apps**:
  - Register custom Primary Service `0000FAB0-0000-1000-8000-00805F9B34FB` with read-only **Characteristic User Description Descriptors (`0x2901`)** on every characteristic so off-the-shelf BLE test apps (nRF Connect / LightBlue on iOS and Android) display human-readable labels instead of `"Unknown Characteristic"`:
    1. **Control Point Characteristic (`FAB1` / `0000FAB1-0000-1000-8000-00805F9B34FB`)**:
       - Properties: `Write` | `Write Without Response` (`BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_WRITE_NO_RSP`).
       - User Description (`0x2901`): `"Fabrica Control Point (FAB1)"`.
       - Dual-Mode Write Support: Accepts both `Write Without Response` (for `<50ms` real-time `CMD_EMERGENCY_STOP`, `CMD_STOP_SEQUENCE`, `CMD_JOG_MOTOR_ANGLE`) and `Write With Response` (for verified sequence execution, NVS saves, and configuration commands), allowing manual testers in nRF Connect / LightBlue to use either write mode.
       - Packed Binary Wire Protocol: Standardized `[1B Opcode][Payload]` framing ($1\text{B}$ to $55\text{B}$, Little-Endian) plus **compact variable-length routine payload support** ($4\text{B}$ to $51\text{B}$) for effortless hex entry in test apps.
    2. **Sequence Progress & Motor Telemetry Characteristic (`FAB2` / `0000FAB2-0000-1000-8000-00805F9B34FB`)**:
       - Properties: `Read` | `Notify` (`BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY`).
       - Descriptors: Standard CCCD (`0x2902`) + User Description (`0x2901`: `"Fabrica Status & Telemetry (FAB2)"`).
       - Broadcasts and returns packed 31-byte binary telemetry frames (`telemetry_packet_t`, Little-Endian) with adaptive streaming (10 Hz in motion/calibration, 1 Hz when idle).
    3. **Button Sequence Configuration Characteristic (`FAB3` / `0000FAB3-0000-1000-8000-00805F9B34FB`)**:
       - Properties: `Read` | `Write` | `Notify` (`BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY`).
       - Descriptors: Standard CCCD (`0x2902`) + User Description (`0x2901`: `"Fabrica Button Sequences 1-4 (FAB3)"`).
       - **Strict Binary Struct Packing**: Apply `__attribute__((packed))` to `fold_step_t` (3 bytes: 1B `motor_count` + 2B `motor_ids`) and `fold_routine_t` (53 bytes: 1B `step_count` + 48B `steps` + 4B Little-Endian `checksum`) in `main/command.h` with zero compiler padding.
       - **GATT Read**: Returns the complete 212-byte table ($4 \times 53\text{ bytes}$) of all 4 button sequences (supporting offset-sliced Long Reads).
       - **GATT Write (Full & Compact Formats)**: Accepts a 212-byte full 4-button table, a 54-byte single-button struct (`[1B preset_id (1-4)][53B fold_routine_t]`), OR a **compact variable-length single-button payload** (`[1B preset_id (1-4)][1B step_count (1-16)][3B * step_count steps]`, 5 to 50 bytes) for rapid manual entry in nRF Connect / LightBlue.
       - **Active Motion Write Lock**: Strictly rejects GATT writes to `FAB3` while `motion_is_busy()` / `STATE_RUNNING_MOTION` with `CMD_STATUS_ERR_BUSY`.
       - **Auto-CRC Calculation & Zero-Padding**: Automatically zero-pads unused step slots ($k \ge \text{step\_count}$) and computes IEEE 802.3 CRC32 across all 49 bytes preceding `checksum` whenever `checksum == 0` (or when using compact format); if a non-zero `checksum` is provided, validates and rejects corrupted payloads with `CMD_STATUS_ERR_CRC_MISMATCH`.
       - **GATT Notify**: Pushes the updated 212-byte table to subscribed centrals whenever any button sequence changes in NVS.
- **Visual Feedback & Device Identification Engine (`led.h`, `led.c`)**:
  - Add `LED_STATE_BLE_CONNECTED` (1.0s solid ON confirmation pulse) and `LED_STATE_IDENTIFY` (3 fast double-blinks over 3.0s for `CMD_IDENTIFY_ROBOT`).
  - **Strict LED Preemption Hierarchy**: Transient states (`LED_STATE_BLE_CONNECTED`, `LED_STATE_SAVE_SUCCESS`, `LED_STATE_IDENTIFY`, `LED_STATE_INPUT_ERROR`) preserve and restore the underlying persistent base state (`return_to_prior_base = true`).
- **Validation**:
  - Verified with host unit test suite (`make test`, 115/115 checks pass in `test_ble_transport.c`, 681/681 total checks pass across all 8 test suites) and clean ESP-IDF v6.0.2 target build (`idf.py build`, `fabrica_firmware.bin` 493 KB with 52% app partition free).
  - Ready for live hardware verification on ESP32 using **nRF Connect** and **LightBlue** on iOS and Android.

---

## Phase 9 — BLE Command Dispatch, Remote Execution & Servo Calibration (`remote_cmd.c`, `command.h`, `state_machine.c`) ✅
- **Remote Sequence Execution & Preemption Engine**:
  - **Start Preset Routine (`CMD_RUN_PRESET`, Opcode `0x00`)**: Wirelessly trigger saved Button 1–4 routines (`[0x00][preset_id (1-4)]`).
  - **Ingress Re-Entrancy & Busy Guard**: If `CMD_RUN_PRESET` or `CMD_RUN_RAW_SEQUENCE` arrives over BLE while motion is active (`motion_is_busy()` / `STATE_RUNNING_MOTION`), reject immediately at ingress on Core 1 and report `CMD_STATUS_ERR_BUSY` in telemetry without queueing behind or interrupting the active fold cycle.
  - **Empty Preset Validation**: If targeted preset has `step_count == 0`, immediately reject execution with `CMD_STATUS_ERR_INVALID_STEP` and flash `LED_STATE_INPUT_ERROR`.
  - **Execution Completion Notification**: At final step completion, emit a dedicated telemetry frame with `step_progress_pct = 100` and `last_cmd_status = CMD_STATUS_OK` before transitioning cleanly to `STATE_IDLE_RUN`.
  - **Stateless Raw Sequence Execution (`CMD_RUN_RAW_SEQUENCE`, Opcode `0x01`)**:
    - Execute unsaved sequence payloads directly over BLE without modifying NVS presets, accepting either the full 54-byte frame (`[0x01][53B fold_routine_t]`) or the compact variable-length frame (`[0x01][step_count (1-16)][3B * step_count steps]`, 5 to 50 bytes) for easy testing in nRF Connect / LightBlue.
    - Pre-validate routine before execution: Enforce $1 \le \text{step\_count} \le 16$, $1 \le \text{motor\_count} \le 2$, and valid channel indices ($0 \le \text{id} \le 15$); reject invalid payloads with `CMD_STATUS_ERR_INVALID_STEP` or `CMD_STATUS_ERR_MOTOR_BOUNDS`.
    - Report `active_button_id = 0` in telemetry during raw sequence execution to distinguish from stored Presets 1–4.
  - **Clean Stop (`CMD_STOP_SEQUENCE`, Opcode `0x02`) & Wireless Emergency Stop (`CMD_EMERGENCY_STOP`, Opcode `0x03`)**:
    - Core 1 BLE ingress fast-path immediately invokes `motion_emergency_stop()` (setting `MOTION_EVENT_ESTOP_BIT` on `xSystemEventGroup`) when `0x02` or `0x03` is received during active motion, guaranteeing `<50ms` preemption latency without waiting behind Core 0 queue execution.
    - `CMD_EMERGENCY_STOP` (`0x03`) immediately halts PWM pulses, commands all 16 channels to $0^\circ$, flashes `LED_STATE_ESTOP` (5 rapid flashes), and latches `STATE_ESTOP`.
    - `CMD_STOP_SEQUENCE` (`0x02`) cleanly stops active motion or calibration, homes all 16 flaps to $0^\circ$, and clears `STATE_ESTOP` back to `STATE_IDLE_RUN` (physical button tap in `STATE_ESTOP` also clears `STATE_ESTOP` to `STATE_IDLE_RUN`).
- **Wireless Preset Slot Management & Factory Reset**:
  - **Direct Button Sequence Save (`CMD_SET_BUTTON_SEQUENCE`, Opcode `0x0A` / `FAB3` Write)**: Overwrite Preset 1–4 in NVS with strict $1 \le \text{preset\_id} \le 4$ validation, supporting both full 55-byte frames and compact variable-length step payloads ($6$ to $51$ bytes) with automatic zero-padding and CRC32 calculation.
  - **Active Motion Write Lock**: Reject `CMD_SET_BUTTON_SEQUENCE`, `CMD_RESTORE_FACTORY_PRESETS`, and `FAB3` writes with `CMD_STATUS_ERR_BUSY` whenever `motion_is_busy()` is true.
  - **Factory Default Reset (`CMD_RESTORE_FACTORY_PRESETS`, Opcode `0x0C`)**: Restore Presets 1–4 to hardcoded factory default folding routines in NVS, home all servos, flash `LED_STATE_SAVE_SUCCESS` (2.0s solid ON), and emit a `FAB3` notification.
  - **Immediate Command Status Reporting**: Every BLE command execution or validation result (`CMD_STATUS_OK`, `CMD_STATUS_ERR_BUSY`, `CMD_STATUS_ERR_INVALID_STEP`, `CMD_STATUS_ERR_MOTOR_BOUNDS`, `CMD_STATUS_ERR_ROUTINE_FULL`, `CMD_STATUS_ERR_CRC_MISMATCH`, `CMD_STATUS_ERR_INVALID_ARG`) updates `last_cmd_status` and triggers an immediate telemetry notification on `FAB2`.
- **Live Servo Jog, Calibration Mode & Thermal Protection (`CMD_JOG_MOTOR_ANGLE`, Opcode `0x0D`)**:
  - Accept 3-byte integer position jog commands (`[0x0D][channel (0-15)][angle_deg (0-180)]`) over `FAB1` for interactive flap identification and mechanical angle verification from any BLE test app.
  - **State Transition**: Sending `CMD_JOG_MOTOR_ANGLE` from `STATE_IDLE_RUN` transitions the state machine to `STATE_CALIBRATING`.
  - **Motion & E-Stop Safety Interlock**: Strictly reject `CMD_JOG_MOTOR_ANGLE` with `CMD_STATUS_ERR_BUSY` if `system_state == STATE_RUNNING_MOTION` or `STATE_ESTOP`, or with `CMD_STATUS_ERR_MOTOR_BOUNDS` if `channel > 15` or `angle_deg > 180`.
  - **Thermal Safety Cutoff (10s)**: Stationary servos in `STATE_CALIBRATING` automatically de-energize (`pca9685_sleep()` or PWM off) after 10 seconds of jog inactivity (`CALIBRATION_THERMAL_TIMEOUT_MS = 10000`) to prevent servo coil overheating.
  - **Auto-Home & Inactivity Exit (15s)**: A 15-second inactivity watchdog (`CALIBRATION_INACTIVITY_TIMEOUT_MS = 15000`) or sending `CMD_STOP_SEQUENCE` (`0x02`) automatically wakes/homes all 16 channels back to $0^\circ$ and returns the state machine to `STATE_IDLE_RUN`.
- **Validation**:
  - Verified with host unit test suite (`make test`, 82/82 checks pass in `test_remote_cmd.c`, 763/763 total checks pass across all 9 test suites with `-Wall -Wextra -Werror`) and clean ESP-IDF v6.0.2 target build (`idf.py build`, `fabrica_firmware.bin` `0x7c130` bytes / 496 KB with 52% app partition free).

---

## Phase 10 — Real-Time Telemetry & Button Configuration Sync (`telemetry.c`) ✅
- **Adaptive Telemetry Streaming Engine (`app_telem_task`, Core 1, Priority 3)**:
  - **Adaptive Streaming Rate**:
    - **High-Rate (10 Hz / 100ms)**: Automatically streamed to subscribed `FAB2` centrals when active motion is running (`STATE_RUNNING_MOTION`) or live servo jogging is active (`STATE_CALIBRATING`).
    - **Low-Rate (1 Hz / 1000ms)**: Automatically throttled during `STATE_IDLE_RUN`, `STATE_ESTOP`, or `STATE_ERROR` to conserve central battery and prevent iOS `CoreBluetooth` background notification throttling.
    - **Stream Control (`CMD_SET_TELEMETRY_STREAM`, Opcode `0x11` & `CMD_GET_TELEMETRY`, Opcode `0x10`)**: Allow BLE centrals to pause/resume periodic streaming (`0x11 00` / `0x11 01`) or request an on-demand single-shot 31-byte telemetry frame (`0x10`).
  - **Packed 31-Byte Binary Telemetry Frame (`telemetry_packet_t`, `__attribute__((packed))`)**:
    - `system_state` (`uint8_t`): `0 = STATE_IDLE_RUN`, `1 = STATE_RUNNING_MOTION`, `2 = STATE_ESTOP`, `3 = STATE_ERROR`, `4 = STATE_CALIBRATING`.
    - `led_state` (`uint8_t`): Active `led_state_t` (`0 = IDLE`, `1 = RUNNING`, `2 = SAVE_SUCCESS`, `3 = INPUT_ERROR`, `4 = ESTOP`, `5 = BLE_PAIRING`, `6 = BLE_CONNECTED`, `7 = IDENTIFY`).
    - `active_button_id` (`uint8_t`): Currently executing preset slot (`1–4`), or `0` during raw sequence preview / idle.
    - `current_step_idx` (`uint8_t`): Active step index (`0–15`).
    - `total_steps` (`uint8_t`): Total steps in active routine (`0–16`).
    - `step_progress_pct` (`uint8_t`): Current step completion percentage (`0–100%`).
    - `elapsed_step_time_ms` (`uint16_t`, Little-Endian): Elapsed time in active step (ms).
    - `channel_angles[16]` (`uint8_t[16]`): Live commanded angles ($0^\circ \text{ to } 180^\circ$) for all 16 PCA9685 servo channels, tracked automatically via `pca9685.c` and `motion.c`.
    - `last_cmd_status` (`uint8_t`): Result of last processed command (`0 = OK`, `1 = ERR_BUSY`, `2 = ERR_INVALID_STEP`, `3 = ERR_MOTOR_BOUNDS`, `4 = ERR_ROUTINE_FULL`, `5 = ERR_CRC_MISMATCH`, `6 = ERR_INVALID_ARG`).
    - `free_heap_kb` (`uint16_t`, Little-Endian): Current free internal SRAM in KB.
    - `ble_rssi_dbm` (`int8_t`): Connected central RSSI in dBm via `ble_gap_conn_rssi()` (`-128` when disconnected).
    - `error_code` (`uint8_t`): Hardware/system fault bitmask (`BIT0 = I2C_FAULT`, `BIT1 = NVS_FAULT`, `BIT2 = ESTOP_ACTIVE`).
    - `sequence_counter` (`uint16_t`, Little-Endian): Monotonically increasing packet counter for drop detection.
  - **Strict Little-Endian Wire Serialization**:
    - All multi-byte fields (`elapsed_step_time_ms`, `free_heap_kb`, `sequence_counter`, and `fold_routine_t.checksum`) are serialized in Little-Endian byte order (`sizeof(telemetry_packet_t) == 31`).
  - **Event-Driven Immediate Push Notifications**:
    - Immediately push a `FAB2` notification upon any state transition, command rejection/completion, step boundary, 100% routine finish, or E-Stop trigger without waiting for the next periodic timer tick.
- **Button Configuration Synchronization (`FAB3`, `0000FAB3-...`)**:
  - Automatically push a `FAB3` GATT notification containing the 212-byte 4-button table whenever any preset sequence is modified in NVS (`CMD_SET_BUTTON_SEQUENCE`, `FAB3` write, or `CMD_RESTORE_FACTORY_PRESETS`).
  - Support on-demand `FAB3` notification trigger via `CMD_GET_BUTTON_CONFIG` (Opcode `0x0B`) in addition to direct GATT Read on `FAB3`.
- **Validation**:
  - Host unit test suite (`test/test_telemetry.c`, 70/70 checks pass, 833/833 total checks pass across all 10 test suites with `-Wall -Wextra -Werror`) verifying exact 31-byte struct packing and field offsets, Little-Endian multi-byte encoding, live servo angle tracking across all 16 channels, mid-sweep progress percentage and elapsed time calculation, adaptive 10 Hz vs 1 Hz rate switching, stream pause/resume via Opcode `0x11`, disconnect safety mute, and `FAB3` 212-byte synchronization notifications.
  - Clean ESP-IDF v6.0.2 target build (`idf.py build`, `fabrica_firmware.bin` `0x7c690` bytes / 498 KB with 51% app partition free).

---

## Phase 11 — End-to-End Firmware BLE Validation & App Store Test App Playbook (`test_ble_integration.c`, `README.md`) ✅
- **Automated Host C End-to-End BLE Central Simulation Suite (`test/test_ble_integration.c`)**:
  - C mock BLE central harness simulating iOS `CoreBluetooth` and Android `BluetoothGatt` stack interactions against the full firmware pipeline (NimBLE GATT Server $\to$ Remote Command Ingress $\to$ State Machine $\to$ Motion Engine $\to$ PCA9685 & NVS $\to$ Telemetry Streamer):
    1. Verify GAP primary advertisement ($\le 31\text{B}$ with `0000FAB0-...` UUID) and scan response (`Fabrica-XXXX` name) payloads, plus DIS (`0x180A`) and GATT Service Changed (`0x1801` / `0x2A05`) registration.
    2. Verify ATT MTU negotiation for both iOS central-initiated exchange and Android peripheral-initiated `ble_gattc_exchange_mtu(512)`, plus offset-sliced GATT Long Read (`ATT_READ_BLOB_REQ`) fallback at 23-byte MTU.
    3. Verify sequential CCCD (`0x2902`) subscription on `FAB2` and `FAB3` and read-only User Description (`0x2901`) descriptors on `FAB1`, `FAB2`, and `FAB3`.
    4. Verify peripheral-initiated connection parameter update compliance with Apple Accessory Guidelines (`15.0ms–30.0ms` interval, `0` latency, `4000ms` supervision timeout).
    5. Verify Hold-to-Pair security: confirm zero-bond initial boot auto-starts indefinite pairing mode; confirm unbonded connection attempts outside the pairing window are terminated; confirm 3s physical button hold (`CMD_ENTER_BLE_PAIRING`) opens a 120s window (`LED_STATE_BLE_PAIRING`) for additional devices, initiates SMP security (`ble_gap_security_initiate`), bonds peer LTK/IRK in NVS, and reconnects seamlessly across simulated 15-minute RPA MAC rotations.
    6. Verify 4-bond NVS capacity limit (5th device FIFO eviction) and `B1 + B4` 5-second simultaneous hold hardware bond reset (`CMD_CLEAR_BLE_BONDS`) with single-button 3s hold suppression and automatic re-opening of indefinite BLE pairing mode.
    7. Verify `CMD_IDENTIFY_ROBOT` (`0x0E`) 3.0s LED pulse confirmation restoring prior persistent base state.
    8. Read the 212-byte 4-button configuration table from `FAB3` and verify factory default routines and CRC32 checksums.
    9. Write custom sequences to Button 1 using both the full 54-byte/55-byte struct and the compact variable-length payload on `FAB3` and `FAB1` (`0x0A`), verifying auto-zero-padding, auto-CRC32 computation, NVS persistence, and `FAB3` notify push.
    10. Execute stateless raw sequence preview (`CMD_RUN_RAW_SEQUENCE`, `0x01`) using both full and compact payloads without modifying NVS, verifying `active_button_id == 0` in `FAB2` telemetry.
    11. Verify empty preset guard (`step_count == 0` rejected with `CMD_STATUS_ERR_INVALID_STEP`) and out-of-bounds motor/step rejection (`CMD_STATUS_ERR_MOTOR_BOUNDS`).
    12. Start Preset 1 over BLE (`0x00 01`); inject concurrent `CMD_RUN_PRESET`, `CMD_RUN_RAW_SEQUENCE`, and `FAB3` writes mid-motion and verify immediate ingress rejection with `CMD_STATUS_ERR_BUSY`.
    13. Verify real-time `FAB2` 31-byte telemetry streaming during motion (10 Hz rate, live `channel_angles[16]`, step progress $0\% \to 100\%$, final completion packet with `last_cmd_status = CMD_STATUS_OK`, and return to 1 Hz idle rate).
    14. Test `CMD_JOG_MOTOR_ANGLE` (`0x0D`) via `Write Without Response`: verify `STATE_CALIBRATING` transition, live angle updates, rejection during active motion/E-Stop (`CMD_STATUS_ERR_BUSY`), 10s stationary thermal de-energize cutoff, and 15s inactivity auto-home back to `STATE_IDLE_RUN`.
    15. Trigger wireless `CMD_EMERGENCY_STOP` (`0x03`) and `CMD_STOP_SEQUENCE` (`0x02`) mid-sweep and verify `<50ms` Core 1 fast-path preemption, immediate 16-channel homing to $0^\circ$, `STATE_ESTOP` latching, and BLE recovery via `0x02`.
    16. Trigger execution via physical button tap (`B1–B4`) and verify connected BLE central receives live 10 Hz `FAB2` telemetry notifications.
    17. Execute `CMD_RESTORE_FACTORY_PRESETS` (`0x0C`) and verify all 4 NVS slots reset to factory defaults with `FAB3` notification.
- **Multi-Source Concurrency, Disconnect Safety & Endurance Stress**:
  - Verify arbitration between simultaneous physical button presses and BLE GATT writes.
  - Verify abrupt BLE disconnect safety: disconnecting during active folding motion allows the current routine to finish safely and return to `STATE_IDLE_RUN`; disconnecting during `STATE_CALIBRATING` safely homes all jogged servos via the inactivity watchdog.
  - 200-cycle continuous endurance run with active BLE telemetry streaming and periodic `FAB3` sequence updates verifying zero FreeRTOS heap leaks, zero stack overflows, and minimum free internal SRAM $>190\text{ KB}$.
- **Off-the-Shelf App Store BLE Test App Verification Guide (`firmware/README.md`)**:
  - Document step-by-step hardware verification procedures and ready-to-paste hex payloads for testing all firmware features on **iOS** and **Android** using **nRF Connect for Mobile** and **LightBlue** (covering pairing/bonding, `FAB1` command opcodes `0x00–0x11`, compact custom sequence programming, `FAB2` 31-byte telemetry decoding, and `FAB3` read/write/notify).
- **Validation**:
  - Host integration test suite (`test/test_ble_integration.c`, 78/78 checks pass, 911/911 total checks pass across all 11 test suites with `-Wall -Wextra -Werror`).
  - Clean ESP-IDF v6.0.2 target build (`idf.py build`, `fabrica_firmware.bin` `0x7c6c0` bytes / 498 KB with 51% app partition free).
  - Comprehensive App Store BLE test app playbook documented in `firmware/README.md`.





