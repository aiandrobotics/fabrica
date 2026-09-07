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
- **Validation**: Verified with host unit tests (`make test`, 50/50 pass), ESP-IDF build compilation, and live hardware flash/monitor on ESP32 (`/dev/cu.usbserial-0001`).

---

## Phase 2 — UI Subsystem: 4-Button Debouncer & Non-Blocking LED Pattern Engine (`buttons.c`, `led.c`) ✅
- **Status LED Pattern Engine** (`main/led.h`, `main/led.c`):
  - Implement non-blocking FreeRTOS software timer / task driving 7 visual state feedback patterns:
    1. `LED_STATE_IDLE`: Soft heartbeat (10% duty cycle / 0.5 Hz) or OFF awaiting input.
    2. `LED_STATE_RUNNING`: Solid ON continuous throughout routine execution.
    3. `LED_STATE_PROGRAMMING`: Slow blink (1.0s ON / 1.0s OFF / 0.5 Hz).
    4. `LED_STATE_STEP_LOCKED`: 2 fast flashes (80ms ON / 80ms OFF).
    5. `LED_STATE_SAVE_SUCCESS`: Solid ON for 2.0 seconds then OFF.
    6. `LED_STATE_INPUT_ERROR`: 3 fast flashes (60ms ON / 60ms OFF).
    7. `LED_STATE_ESTOP`: 5 rapid flashes (50ms ON / 50ms OFF).
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

## Phase 6 — Visual Staging Programming Mode & State Machine Integration (`state_machine.c`) ✅
- **Mode Transition & Staging Coordinator** (`main/state_machine.h`, `main/state_machine.c`):
  - Hold B1–B4 for 3 seconds $\rightarrow$ Enter Programming Mode for that preset; set LED to Slow Blink (0.5 Hz).
- **Physical Staging Workflow**:
  - **B1 (CYCLE / NUDGE)**: Increment target servo index (0–15) and trigger $15^\circ$ physical nudge for quick identification.
  - **B2 (STAGE / TOGGLE)**: Lift identified flap to $30^\circ$ and hold in position. Tapping B2 on an already-staged flap drops it to $0^\circ$. Support up to 2 simultaneously staged flaps.
  - **B3 (NEXT STEP)**: Lock staged flap(s) into step buffer, flash LED 2 times rapidly, drop flaps flat to $0^\circ$, increment step buffer index.
  - **B4 (SAVE & EXIT)**: Commit sequence buffer to NVS flash, turn LED Solid ON for 2.0 seconds, and return to Daily Run Mode.
- **Programming Safeguards & Failsafes**:
  - **2-Motor Limit**: Staging a 3rd motor in 1 step is rejected with 3 fast flashes.
  - **Empty Step Skip**: Pressing B3 with no staged flaps is ignored.
  - **Inactivity Timeout**: 20 seconds with no button presses drops all flaps to $0^\circ$, discards buffer, and safely exits to Run Mode.
  - **16-Step Cap**: Reaching 16 steps automatically saves sequence to NVS and exits.
- **Validation**: Verified with host unit test suite (`make test`, 161/161 checks pass, 503/503 total across all test suites) covering state machine lifecycle, button gesture translation matrix across all states, channel cycling/nudge, staging toggles, 2-motor limit enforcement, step locking, empty step rejection, NVS save/playback, 16-step auto-commit, 20s inactivity watchdog timeout, and Emergency Stop in all states.

---

## Phase 7 — End-to-End System Validation, Stress Testing & Preset Library ✅
- **Factory Preset Library**:
  - Preset 1: Standard Adult T-Shirt (Left fold $\to$ Right fold $\to$ Bottom fold: Ch 0 $\to$ Ch 1 $\to$ Ch 2).
  - Preset 2: Long-Sleeve Shirt (Parallel dual-sleeve fold $\to$ Left body $\to$ Right body $\to$ Bottom fold).
  - Preset 3: Trousers / Jeans (Vertical half fold $\to$ Bottom fold: Ch 0 $\to$ Ch 2).
  - Preset 4: Towel / Linen (Left half fold $\to$ Right quarter fold $\to$ Bottom fold: Ch 0 $\to$ Ch 1 $\to$ Ch 2).
  - Standardized named channel aliases (`SERVO_FLAP_LEFT`, `SERVO_FLAP_RIGHT`, `SERVO_FLAP_BOTTOM`, `SERVO_FLAP_TOP`) in `main/config.h`.
- **Stress & Endurance Testing**:
  - 100-cycle continuous run test verifying zero heap memory leaks and long-term state stability.
  - Stress testing E-Stop triggers under active mid-sweep conditions (<50ms abort latency, immediate 16-channel homing).
  - Automated verification of power loss and bit-rot resilience during NVS write operations (`ESP_ERR_INVALID_CRC` fallback).
  - 50-cycle rapid mode-switching stress test verifying state machine invariant stability.
- **System Documentation**: Comprehensive `firmware/README.md` with electrical wiring diagrams, PCA9685 power isolation, dual-core FreeRTOS architecture, full operator manual, and test instructions.
- **Validation**: Verified with host unit test suite (`make test`, 60/60 checks pass in `test_e2e_stress.c`, 553/553 total checks pass across all 7 test suites).

---

## Phase 8 — Wireless Transport: NimBLE GATT Server (`ble_transport.c`, `nimble`)
- **NimBLE Stack Initialization & Task Allocation**:
  - Initialize Apache NimBLE stack on Core 1 (`app_ble_task`, Priority 4, 4KB stack) to maintain zero jitter on Core 0 real-time motion.
  - Implement BLE GAP advertising engine broadcasting service UUID `0000FAB0-0000-1000-8000-00805F9B34FB` with human-readable device name (`Fabrica-XXXX` from last 2 MAC bytes).
  - Configure low-latency connection parameters (connection interval: 7.5ms–15ms, slave latency: 0, supervision timeout: 4000ms).
  - Enforce mandatory ATT MTU exchange immediately upon connection ($\ge 247$ bytes, up to 512 bytes) to guarantee single-packet transfers for telemetry and sequence tables.
  - Implement single active central connection policy (`max_connections = 1`; stops advertising while connected).
  - Implement automatic advertising restart on mobile app disconnect and connection watchdog.
- **Proof-of-Presence BLE Security & Bonding Engine**:
  - When an unbonded mobile central connects, trigger a 30-second Physical Authorization Window.
  - Command status LED to `LED_STATE_BLE_PAIRING` (fast double-blink).
  - Require physical button press on robot (B1–B4) to authorize pairing and store bonding keys in NVS (`"ble_bonds"`, up to 4 trusted devices).
  - **Motion Suppression during Pairing**: While the 30-second authorization window is active, the first physical button press strictly authorizes the BLE bond and suppresses triggering routine execution.
  - **Bond Lifecycle & Eviction**: Support up to 4 bonded devices; if a 5th mobile device pairs, the oldest bond is evicted automatically (FIFO/LRU).
  - **Hardware Bond Reset**: Holding physical buttons B1 + B4 simultaneously for 5 seconds at power-on or in idle clears all stored bonds in `"ble_bonds"` and confirms with 3 fast LED flashes.
  - Command status LED to `LED_STATE_BLE_CONNECTED` (solid 1.0s confirmation pulse) upon successful authorization or auto-reconnect.
  - If no physical button is pressed within 30 seconds, automatically terminate the connection (`ble_gap_terminate`).
  - Seamless auto-reconnect for previously bonded mobile devices without requiring a physical button press.
- **Standard Device Information Service (DIS `0x180A`)**:
  - Expose Model Number (`0x2A24`: `"Fabrica-DevKit-v1"`), Firmware Revision (`0x2A26`: `"v1.13.0"`), and Manufacturer (`0x2A29`: `"Fabrica Robotics"`) for mobile app version handshakes.
- **Fabrica Primary GATT Service Architecture**:
  - Register custom Primary Service `0000FAB0-0000-1000-8000-00805F9B34FB`:
    1. **Control Point Characteristic (`FAB1` / `0000FAB1-0000-1000-8000-00805F9B34FB`)**:
       - Permissions: Write / Write Without Response.
       - Packed Binary Wire Protocol: Implements standardized `[1B Opcode][Payload]` framing ($1\text{B}$ to $55\text{B}$) with zero compiler struct padding across iOS / Android / Flutter.
       - Ingests binary command packets (Start/Stop, Raw Preview, Staging, Step Editing, Integer Motor Jog, E-Stop, Factory Reset, Identify, LED Mode) and dispatches to `xCommandQueue` with `SOURCE_BLE`.
    2. **Sequence Progress & Motor Telemetry Characteristic (`FAB2` / `0000FAB2-0000-1000-8000-00805F9B34FB`)**:
       - Permissions: Notify / Read.
       - Streams 10 Hz packed binary telemetry frames (`telemetry_packet_t`, 30 bytes) containing real-time system state, visual LED state mirroring, sequence progress, all 16 motor positions, and last command status (no hardware current sensing needed).
    3. **Button Sequence Configuration Characteristic (`FAB3` / `0000FAB3-0000-1000-8000-00805F9B34FB`)**:
       - Permissions: Read / Write / Notify.
       - **Canonical Transport**: Primary GATT interface for all button sequence reads and writes.
       - **Strict Binary Struct Packing**: Uses `__attribute__((packed))` for `fold_step_t` (3 bytes: 1B count + 2B motor IDs) and `fold_routine_t` (53 bytes: 1B step_count + 48B steps + 4B CRC32) with zero internal padding.
       - GATT Read returns the complete 212-byte table ($4 \times 53\text{ bytes}$) of all 4 button sequences in a single transfer.
       - GATT Write accepts either a 54-byte single button update (1-byte button ID + 53-byte `fold_routine_t`) or the full 212-byte table.
       - **Active Motion Write Lock**: Strictly rejects GATT writes to `FAB3` while `system_state == STATE_RUNNING_MOTION` with `ERR_BUSY`.
       - **Auto-CRC Calculation & Zero-Padding**: Computes IEEE 802.3 CRC32 across all 49 bytes preceding checksum with zero-padded unused slots; if `checksum == 0`, firmware auto-computes valid CRC before NVS commit; if non-zero, validates and rejects corrupted payloads with `ERR_CRC_MISMATCH`.
       - GATT Notify automatically alerts mobile clients whenever button sequences change on-device.
- **Visual Feedback & Device Identification Engine**:
  - Expose `CMD_IDENTIFY_ROBOT` command to pulse status LED for 3.0 seconds (3 fast double-blinks) to visually locate unit during BLE scanning.
  - Expose `CMD_SET_LED_MODE` to allow mobile app to configure visual mode: `0 = Auto` (State-driven), `1 = Manual Pattern Override` (`led_state_t`), `2 = Stealth/Night Mode` (suppresses idle heartbeat).
  - Strict LED Preemption Hierarchy: Transient states (`LED_STATE_BLE_CONNECTED`, `LED_STATE_STEP_LOCKED`, `LED_STATE_SAVE_SUCCESS`, `CMD_IDENTIFY_ROBOT`) preserve and restore underlying base state (`return_to_prior_base = true`) to prevent display glitches across state transitions.
- **Unified Command Queue Ingress**:
  - Translate GATT write events directly into standardized `command_t` instances and inject into `xCommandQueue` without modifying Core 0 motion mechanics.
- **Validation**:
  - Host mock test suite verifying NimBLE GATT table registration, DIS service descriptors, authorization window timing and button suppression, bond eviction and hardware reset, struct packing byte counts, MTU negotiation, command queue injection, and identify LED pulsing.
  - Live hardware verification with nRF Connect / LightBlue on iOS/Android over `/dev/cu.usbserial-0001`.

---

## Phase 9 — Mobile Configuration & Remote Execution (`remote_cmd.c`, `command.h`, `state_machine.c`)
- **Start / Stop Sequence Execution from Mobile App**:
  - Start routine execution: Wirelessly trigger saved Button 1–4 routines (`CMD_RUN_PRESET`).
  - **Re-Entrancy / Busy Guard**: If `CMD_RUN_PRESET` or `CMD_RUN_RAW_SEQUENCE` is received while motion is active (`motion_is_busy()`), command is safely rejected and reports `ERR_BUSY` in telemetry without interrupting active cycle.
  - **Empty Preset Validation**: If targeted preset has `step_count == 0`, immediately reject execution with `ERR_INVALID_STEP`.
  - **Execution Completion Notification**: At final step completion, emit a dedicated telemetry frame with `step_progress_pct = 100` and `last_cmd_status = OK` before transitioning cleanly to `STATE_IDLE_RUN`.
  - **Stateless Raw Routine Execution & Validation**:
    - Execute temporary unsaved sequence payloads directly (`CMD_RUN_RAW_SEQUENCE`) allowing users to preview fold sequences before committing them to a button.
    - Pre-validate routine before execution: Enforce $1 \le \text{step\_count} \le 16$, $1 \le \text{motor\_count} \le 2$, and valid channel indices ($0 \le \text{id} \le 15$); reject invalid payloads with `ERR_INVALID_STEP` or `ERR_MOTOR_BOUNDS`.
    - Telemetry indicator: `active_button_id` reports `0` during raw preview execution to distinguish from stored buttons 1–4.
  - Stop routine execution: Cleanly stop active folding sequence (`CMD_STOP_SEQUENCE`) and return all flaps to $0^\circ$ home.
  - Wireless Emergency Stop: Instant `<50ms` preemptive abort (`CMD_EMERGENCY_STOP`) immediately cutting PWM pulses and homing all 16 panels.
  - **E-Stop Clear & Recovery over BLE**: Sending `CMD_STOP_SEQUENCE` over BLE (or tapping any physical button) resets `STATE_ESTOP` back to `STATE_IDLE_RUN`.
- **Client-Side Garment Profiles (Stateless Execution Model)**:
  - Dynamic garment profile catalog, fabric tags, custom folding routines, and user-to-user sharing (JSON/QR) live 100% on the mobile application.
  - Mobile app can preview and execute any garment profile on the robot without modifying on-device NVS slots (`CMD_RUN_RAW_SEQUENCE`).
  - Mobile app can bind any garment profile to physical Buttons 1–4 via 1-touch sync (`CMD_SET_BUTTON_SEQUENCE` or `FAB3` write), requiring zero firmware updates for new garment profiles.
- **Button Management & Factory Reset**:
  - Direct 4-button sequence overwrite/sync (`CMD_SET_BUTTON_SEQUENCE` / `FAB3`) over BLE with strict $1 \le \text{button\_id} \le 4$ range enforcement.
  - **Write Interlock during Motion**: Reject button sequence writes with `ERR_BUSY` if motion is currently running.
  - Factory Default Reset: `CMD_RESTORE_FACTORY_PRESETS` command restores Buttons 1–4 to hardcoded default folding routines in NVS.
- **Wireless Button Sequence Recording & Editing**:
  - Remotely record, edit, and organize folding sequences per button (Buttons 1–4) over BLE:
    - Remote entry into programming mode for target button (`CMD_ENTER_PROGRAM_MODE`).
    - Remote flap identification: Cycle motor index and trigger $15^\circ$ nudge (`CMD_CYCLE_NUDGE_MOTOR`).
    - Remote flap staging: Toggle flap staged ($30^\circ$) or resting ($0^\circ$) (`CMD_STAGE_TOGGLE_MOTOR`).
    - Remote step locking: Commit staged flaps into routine step buffer (`CMD_LOCK_STEP`).
    - Remote save & exit: Commit accumulated sequence to target button slot in NVS (`CMD_SAVE_EXIT_PROGRAM`).
  - Remote Staging Feedback: Expose 16-bit staged motor bitmask and active cursor channel so the mobile UI mirrors staged flaps in real time.
- **Remote Sequence Editor Backend**:
  - Direct step manipulation API (`CMD_REMOTE_EDIT_STEP`):
    - Insert new step at index $k$.
    - Delete step at index $k$.
    - Update active motor IDs and dwell parameters for step $k$.
    - Reorder step sequence.
  - Routine payload validation: Enforce maximum 16 steps, maximum 2 motors per step, valid channel bounds (0–15), and CRC32 integrity.
  - **Immediate Command Feedback**: Command execution or validation failures (e.g. `ERR_BUSY`, `ERR_INVALID_STEP`, `ERR_MOTOR_BOUNDS`, `ERR_ROUTINE_FULL`, `ERR_CRC_MISMATCH`, `ERR_INVALID_ARG`) update `last_cmd_status` in the telemetry packet for instant mobile UI toast feedback.
- **Live Servo Jog, Calibration Mode & Thermal Protection**:
  - Integer position jog (`CMD_JOG_MOTOR_ANGLE`: `[channel (0-15)][angle_deg (0-180)]`) for interactive visual calibration from mobile app sliders.
  - **State Transition**: Sending jog command from Idle transitions machine to `STATE_CALIBRATING`.
  - **Motion Safety Interlock**: Strictly reject `CMD_JOG_MOTOR_ANGLE` if `system_state == RUNNING_MOTION` or `ESTOP` to prevent mechanical binding and gear stripping.
  - **Auto-Home & Inactivity Exit**: 15-second inactivity watchdog or `CMD_STOP_SEQUENCE` automatically homes all jogged channels back to $0^\circ$ and returns to `STATE_IDLE_RUN`.
  - **Thermal Safety Cutoff**: Stationary servos in calibration mode automatically de-energize after 10 seconds to prevent servo motor coil burnout.
- **Validation**:
  - Host unit tests covering remote start/stop execution triggers, busy re-entrancy rejection, raw sequence validation and preview execution, wireless E-Stop preemption and BLE reset recovery, factory preset restoration, remote staging sequence recording, step insertion/deletion/reordering, error status code reporting, and servo jog safety interlocks.

---

## Phase 10 — Real-Time Telemetry & Button Sync (`telemetry.c`)
- **High-Rate Telemetry Streaming Engine (`app_telemetry_task`, Core 1)**:
  - 10 Hz packed binary telemetry packet (`telemetry_packet_t`, 30 bytes):
    - `system_state`: Current operational state (`IDLE`, `RUNNING`, `PROGRAMMING`, `ESTOP`, `ERROR`, `CALIBRATING`).
    - `led_state`: Current visual feedback pattern (`IDLE`, `RUNNING`, `PROGRAMMING`, `STEP_LOCKED`, `SAVE_SUCCESS`, `INPUT_ERROR`, `ESTOP`, `BLE_PAIRING`, `BLE_CONNECTED`) for 1:1 mobile UI mirroring.
    - `active_button_id`: Currently executing button routine (1 to 4, or 0 if raw preview / idle).
    - `current_step_idx`: Active step number (0-indexed, 0 to 15).
    - `total_steps`: Total steps in active routine.
    - `step_progress_pct`: Current step completion percentage (0-100%).
    - `elapsed_step_time_ms`: Elapsed time in active step (ms).
    - `channel_angles`: Live angular positions for all 16 PCA9685 servo channels ($0^\circ \text{ to } 180^\circ$).
    - `last_cmd_status`: Status code of last received command (`OK`, `ERR_BUSY`, `ERR_INVALID_STEP`, `ERR_MOTOR_BOUNDS`, `ERR_ROUTINE_FULL`, `ERR_CRC_MISMATCH`, `ERR_INVALID_ARG`).
    - `system_health`: Free internal heap (KB), minimum heap watermark, BLE RSSI, sequence counter, error bitmask.
    - Note: Omits hardware current sensing to minimize BOM costs; safety stall prevention is fully addressed via physical clearances and <50ms E-Stop.
  - Event-Driven Push Notifications:
    - Immediate BLE notifications on state transitions (Routine started, Step completed, Routine finished 100%, Sequence stopped, E-Stop triggered, Routine saved).
- **Button Configuration Synchronization**:
  - Automatically notifies subscribed mobile clients via `FAB3` whenever a button sequence is modified (either via physical buttons or over BLE).
  - Allows mobile app to fetch or verify all 4 button sequences on connection (`CMD_GET_BUTTON_CONFIG`) to maintain 100% synchronization.
- **Validation**:
  - Host unit tests verifying packed telemetry serialization, 10 Hz streaming timer determinism, LED state mirroring, command status reflection, event notification triggers, and button configuration sync dispatch.

---

## Phase 11 — End-to-End System Validation & Mobile Integration (`test_mobile_integration.c`)
- **Cross-Platform Mobile App Test Harness**:
  - Automated Python / C mock mobile client simulating mobile app BLE central over GATT.
  - Comprehensive end-to-end integration workflows:
    1. Scan & connect over BLE GAP (`Fabrica-XXXX`) and negotiate ATT MTU $\ge 247$ bytes.
    2. Proof-of-Presence pairing authorization: verify 30s window timeout disconnects unbonded devices; verify physical button press authorizes and bonds while suppressing motion execution; verify subsequent auto-reconnect without button press.
    3. Verify bond capacity limits (5th device FIFO eviction) and manual B1+B4 5-second bond clear reset.
    4. Send `CMD_IDENTIFY_ROBOT` and verify 3.0s LED pulse confirmation.
    5. Test `CMD_SET_LED_MODE`: verify Mode 2 (Stealth/Night) disables idle heartbeat; verify Mode 0 restores normal operation.
    6. Read current 4-button sequence configuration (`FAB3`) in 212-byte packed table transfer.
    7. Remotely edit Button 1 sequence (insert, delete, reorder steps) and commit to NVS over BLE with auto-CRC32 calculation.
    8. Execute stateless client garment profile preview directly without modifying NVS (`CMD_RUN_RAW_SEQUENCE`), verifying `active_button_id == 0`.
    9. Test empty preset execution guard: attempt `CMD_RUN_PRESET` on 0-step sequence and verify rejection with `ERR_INVALID_STEP`.
    10. Start sequence execution from mobile app (`CMD_RUN_PRESET` 1); send concurrent `CMD_RUN_PRESET` 2 mid-execution and verify rejection with `ERR_BUSY`.
    11. Attempt GATT write to `FAB3` during active motion and verify write lock rejection with `ERR_BUSY`.
    12. Stream 10 Hz real-time sequence progress, LED state mirroring, and live motor angles (`FAB2`); verify final completion packet (`progress == 100%`, `status == OK`).
    13. Attempt `CMD_JOG_MOTOR_ANGLE` during active motion and verify safety rejection with `ERR_BUSY`.
    14. From Idle, send `CMD_JOG_MOTOR_ANGLE` and verify transition to `STATE_CALIBRATING`; verify stationary 10s thermal de-energize; verify 15s timeout auto-homes all jogged channels back to $0^\circ$ and returns to `STATE_IDLE_RUN`.
    15. Send stop / emergency stop command from mobile app during mid-sweep and verify $<50\text{ms}$ preemption.
    16. Clear E-Stop lock over BLE via `CMD_STOP_SEQUENCE` and verify return to `STATE_IDLE_RUN`.
    17. Trigger execution via physical button tap and verify mobile app receives real-time sequence progress and button sync notifications.
    18. Execute `CMD_RESTORE_FACTORY_PRESETS` and verify NVS resets to factory defaults.
- **Multi-Source Concurrency & Priority Arbitration**:
  - Concurrent physical button tap vs wireless mobile command arbitration.
  - E-Stop priority enforcement across physical buttons and BLE commands.
  - Mobile disconnect robustness: Abrupt BLE disconnection during active motion allows running fold cycle to finish safely and return to Idle.
- **Endurance & Memory Leak Verification**:
  - 200-cycle continuous run test with active 10 Hz telemetry streaming and periodic button sequence read/writes over BLE.
  - Verification of zero FreeRTOS heap memory leaks, zero stack overflows, and minimum free internal SRAM $>190\text{ KB}$.
- **System Documentation**:
  - Update `firmware/README.md` with BLE GATT UUID tables, packet specifications, button configuration sync flows, and mobile pairing guides.
- **Validation**:
  - Host unit test suite (`make test`) passing 100% of checks across all 11 phases.

---

## Future Roadmap — AI Garment Vision Recognition
- **Mobile Vision Classification Model**:
  - Camera snapshot of garment spread on folding bed captured via mobile application.
  - On-device edge neural network (CoreML / TensorFlow Lite) or cloud inference to classify garment category (t-shirt, collared shirt, trousers, shorts, towel) and detect size/thickness.
  - Automated selection and BLE dispatch of recommended folding sequence and dwell parameters to the robot.
- **Adaptive Closed-Loop Fold Quality Inspection**:
  - Post-fold visual inspection via smartphone camera to verify fold symmetry and squareness.
  - Anomaly detection to flag misfolds, fabric slippage, or fabric bunching with adaptive recovery routines.




