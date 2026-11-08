# Plan — Phase 9: BLE Command Dispatch, Remote Execution & Servo Calibration

## Overview

Phase 9 completes the stateful remote command execution, fast-path preemption, latched Emergency Stop recovery, immediate `FAB2` command status reporting, and thermal-safe interactive servo calibration subsystem (`remote_cmd.h`, `remote_cmd.c`, `command.h`, `state_machine.h`, `state_machine.c`, `buttons.c`, `ble_transport.c`) for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**.

Building on the Phase 8 Apache NimBLE GATT server (`ble_transport.c`), Phase 9 extracts the `FAB1` / `FAB3` wire protocol parser, compact routine unpacker, Core 1 fast-path preemption guards, and `cmd_status_t` tracking into a dedicated `main/remote_cmd.c` module (matching `specs/tech-stack.md` and `specs/roadmap.md`), extends `system_state_t` with `STATE_ESTOP`, `STATE_ERROR`, and `STATE_CALIBRATING`, and enforces the 10-second PCA9685 thermal sleep cutoff and 15-second inactivity auto-home safety timers during live servo jogging.

---

## Task Group 1: Configuration Constants, System State Enumerations & Build Registration (`main/config.h`, `main/state_machine.h`, `main/CMakeLists.txt`, `Makefile`)
1. Update `firmware/main/config.h` with calibration safety timer thresholds:
   - `CALIBRATION_THERMAL_TIMEOUT_MS` (`10000` ms — stationary servo PCA9685 oscillator sleep cutoff in `STATE_CALIBRATING`).
   - `CALIBRATION_INACTIVITY_TIMEOUT_MS` (`15000` ms — inactivity watchdog waking/homing all 16 servos to $0^\circ$ and returning to `STATE_IDLE_RUN`).
2. Extend `system_state_t` in `firmware/main/state_machine.h` to match the 31-byte `telemetry_packet_t` specification in `specs/tech-stack.md`:
   - `STATE_IDLE_RUN = 0` (Daily Run Mode, awaiting preset trigger or BLE command).
   - `STATE_RUNNING_MOTION = 1` (Active folding trajectory on Core 0).
   - `STATE_ESTOP = 2` (Latched Emergency Stop, all 16 servos homed to $0^\circ$, `error_code` `BIT2` active).
   - `STATE_ERROR = 3` (Hardware / I2C / storage fault state).
   - `STATE_CALIBRATING = 4` (Interactive live servo position jog mode via `0x0D`).
3. Declare Phase 9 state machine inspection & lifecycle hooks in `firmware/main/state_machine.h`:
   - `bool state_machine_is_calibrating_thermal_sleep(void)` (queries whether the 10s thermal sleep cutoff is currently active).
   - `void state_machine_on_ble_disconnect(void)` (handles immediate calibration exit and servo homing upon BLE link loss).
4. Register `remote_cmd.c` in `firmware/main/CMakeLists.txt` (`SRCS`) and add `remote_cmd.c` + `test/test_remote_cmd.c` build rules in `firmware/Makefile`.

---

## Task Group 2: Dedicated BLE Command Parser, Fast-Path Guards & Status Reporting (`main/remote_cmd.h`, `main/remote_cmd.c`, `main/ble_transport.c`)
1. Create `firmware/main/remote_cmd.h` and `firmware/main/remote_cmd.c` owning BLE wire command validation, routine normalization, fast-path preemption, and `last_cmd_status` state:
   - Extract `remote_cmd_validate_routine()` supporting both fixed 53-byte `fold_routine_t` payloads (with strict IEEE 802.3 CRC32 verification when `checksum != 0` and auto-CRC32 when `checksum == 0`) and compact variable-length step payloads (`[1B step_count][3B * step_count]`, $4$ to $49$ routine bytes) with automatic trailing step zero-padding and CRC32 calculation:
     - Enforce `step_count == 0` $\rightarrow$ `CMD_STATUS_ERR_INVALID_STEP`.
     - Enforce `step_count > 16` $\rightarrow$ `CMD_STATUS_ERR_ROUTINE_FULL`.
     - Enforce `motor_count < 1 || motor_count > 2` or `motor_ids[m] > 15` $\rightarrow$ `CMD_STATUS_ERR_MOTOR_BOUNDS`.
   - Implement `remote_cmd_handle_fab1_write(const uint8_t *data, size_t len)` covering all `FAB1` opcodes (`0x00–0x03`, `0x0A–0x0E`, `0x10`, `0x11`):
     - **Ingress Re-Entrancy & Busy Guard**: Reject `0x00` (`CMD_RUN_PRESET`), `0x01` (`CMD_RUN_RAW_SEQUENCE`), `0x0A` (`CMD_SET_BUTTON_SEQUENCE`), `0x0C` (`CMD_RESTORE_FACTORY_PRESETS`), and `0x0D` (`CMD_JOG_MOTOR_ANGLE`) immediately on Core 1 with `CMD_STATUS_ERR_BUSY` whenever `motion_is_busy()`, `system_state == STATE_RUNNING_MOTION`, or `system_state == STATE_ESTOP`.
     - **Empty Preset Pre-Check (`0x00`)**: Validate $1 \le \text{preset\_id} \le 4$ (`CMD_STATUS_ERR_INVALID_ARG` otherwise) and verify the target NVS preset has `step_count >= 1` (if empty or `step_count == 0`, reject with `CMD_STATUS_ERR_INVALID_STEP` and flash `LED_STATE_INPUT_ERROR`).
     - **Core 1 Fast-Path Preemption (`0x02` & `0x03`)**: Immediately invoke `motion_emergency_stop()` (setting `MOTION_EVENT_ESTOP_BIT` on `xSystemEventGroup` for $<50\text{ms}$ preemption latency) before enqueuing `CMD_STOP_SEQUENCE` (`0x02`) or `CMD_EMERGENCY_STOP` (`0x03`) to `xCommandQueue`.
     - **Servo Jog Bounds Check (`0x0D`)**: Validate exact 3-byte length (`[0x0D][channel][angle_deg]`); reject `channel > 15` or `angle_deg > 180` with `CMD_STATUS_ERR_MOTOR_BOUNDS` (flashing `LED_STATE_INPUT_ERROR`).
   - Implement `remote_cmd_handle_fab3_write(const uint8_t *data, size_t len)` supporting 212-byte full table writes, 54-byte single-button writes, and 5–50-byte compact single-button writes, rejecting writes with `CMD_STATUS_ERR_BUSY` during active motion or `STATE_ESTOP`.
   - Implement `remote_cmd_set_status(cmd_status_t status, bool notify_fab2)` and `remote_cmd_get_last_status(void)` so every command acceptance, ingress rejection, or Core 0 completion updates `last_cmd_status` and immediately pushes an event-driven 31-byte `FAB2` GATT notification when subscribed.
2. Refactor `firmware/main/ble_transport.c` to delegate `ble_transport_write_fab1()`, `ble_transport_write_fab3()`, and `ble_transport_get_last_cmd_status()` to `remote_cmd.c` while preserving 100% API compatibility with existing callers and `test_ble_transport.c`:
   - Update `ble_transport_build_telemetry()` to set `error_code` `BIT2` (`ESTOP_ACTIVE`) whenever `state_machine_get_state() == STATE_ESTOP || motion_get_status() == MOTION_STATUS_ABORTED`, and populate final completion progress (`step_progress_pct = 100` on routine finish notification).
   - Invoke `state_machine_on_ble_disconnect()` from the NimBLE disconnect handler (and `ble_transport_mock_disconnect()` in host builds) so losing the BLE link during `STATE_CALIBRATING` immediately wakes/homes all servos and returns to `STATE_IDLE_RUN`.

---

## Task Group 3: Latched E-Stop, Execution Completion & Calibration Watchdogs (`main/state_machine.c`, `main/buttons.c`)
1. Implement **Latched `STATE_ESTOP` & Recovery** in `firmware/main/state_machine.c` and `firmware/main/buttons.c`:
   - `CMD_EMERGENCY_STOP` (`0x03` over BLE or physical button short tap during active motion):
     - Immediately abort active motion (`motion_emergency_stop()`), wake PCA9685 if sleeping (`pca9685_sleep(false)`), command all 16 channels to $0^\circ$ (`pca9685_home_all()`), flash `LED_STATE_ESTOP` (5 rapid flashes), clear `s_active_preset_id = 0`, latch `s_system_state = STATE_ESTOP`, set `last_cmd_status = CMD_STATUS_OK`, and push an immediate `FAB2` telemetry notification (`system_state = 2`, `error_code` `BIT2` set).
   - While in `STATE_ESTOP`:
     - Reject motion, preset save, factory reset, and calibration jog commands (`ESP_ERR_INVALID_STATE` / `CMD_STATUS_ERR_BUSY`).
     - `CMD_STOP_SEQUENCE` (`0x02` over BLE or physical button short tap) wakes/homes all 16 servos, clears `STATE_ESTOP` back to `STATE_IDLE_RUN`, restores `LED_STATE_IDLE` (preserving `LED_STATE_BLE_PAIRING` if pairing window is open), updates `last_cmd_status = CMD_STATUS_OK`, and pushes an immediate `FAB2` telemetry notification.
   - Update `buttons_translate_gesture()` and `dispatch_button_command()` in `firmware/main/buttons.c`:
     - Map `GESTURE_SHORT_TAP` in `STATE_ESTOP` or `STATE_CALIBRATING` to `CMD_STOP_SEQUENCE` (`SOURCE_PHYSICAL_BUTTON`) so tapping any physical button (`B1–B4`) cleanly clears `STATE_ESTOP` or exits `STATE_CALIBRATING` to `STATE_IDLE_RUN`.
     - Preserve 3-second hold (`GESTURE_LONG_PRESS` $\rightarrow$ `CMD_ENTER_BLE_PAIRING`) priority across non-running states (`STATE_IDLE_RUN`, `STATE_ESTOP`, `STATE_CALIBRATING`).
2. Implement **Routine Execution Validation & 100% Completion Notification** in `firmware/main/state_machine.c`:
   - On `CMD_RUN_PRESET`, load/check the routine from `storage_load_routine()`; if `step_count == 0`, flash `LED_STATE_INPUT_ERROR`, report `CMD_STATUS_ERR_INVALID_STEP` (`FAB2` notify), and return `ESP_ERR_INVALID_ARG` without entering `STATE_RUNNING_MOTION`.
   - During `CMD_RUN_PRESET` (`active_button_id = 1..4`) and `CMD_RUN_RAW_SEQUENCE` (`active_button_id = 0`), if `motion_trigger_preset()` / `motion_execute_routine()` completes cleanly (`ESP_OK`), emit a dedicated completion `FAB2` telemetry frame with `step_progress_pct = 100` and `last_cmd_status = CMD_STATUS_OK` before resetting `s_active_preset_id = 0` and transitioning to `STATE_IDLE_RUN` (followed by the idle transition telemetry push). If aborted via E-Stop while running on Core 0, preserve the latched `STATE_ESTOP` transition.
3. Implement **Live Servo Calibration (`STATE_CALIBRATING`) & 10s / 15s Safety Watchdogs** in `firmware/main/state_machine.c`:
   - Sending `CMD_JOG_MOTOR_ANGLE` (`0x0D`) in `STATE_IDLE_RUN` or `STATE_CALIBRATING`:
     - Reset calibration inactivity timer (`s_calib_inactivity_ms = 0`).
     - If `s_calib_thermal_sleep == true`, wake the PCA9685 oscillator (`pca9685_sleep(false)`) and clear `s_calib_thermal_sleep = false`.
     - Command target servo channel via `pca9685_set_servo_angle(channel, angle_deg)`, transition `s_system_state = STATE_CALIBRATING`, update `last_cmd_status = CMD_STATUS_OK`, and emit an immediate `FAB2` telemetry notification reflecting the updated `channel_angles[channel]`.
   - Step calibration timers inside `state_machine_tick(uint32_t elapsed_ms)`:
     - **10s Thermal Safety Cutoff (`CALIBRATION_THERMAL_TIMEOUT_MS = 10000`)**: When `s_calib_inactivity_ms >= 10000` and `!s_calib_thermal_sleep`, set `s_calib_thermal_sleep = true` and de-energize stationary servos via `pca9685_sleep(true)` (thread-safely dispatched to Core 0 on `ESP_PLATFORM` or invoked directly in host builds).
     - **15s Inactivity Auto-Home (`CALIBRATION_INACTIVITY_TIMEOUT_MS = 15000`)**: When `s_calib_inactivity_ms >= 15000`, wake PCA9685 (`pca9685_sleep(false)`), home all 16 channels to $0^\circ$ (`pca9685_home_all()`), exit `STATE_CALIBRATING` $\rightarrow$ `STATE_IDLE_RUN`, and emit a `FAB2` telemetry notification.
   - Exit `STATE_CALIBRATING` immediately (waking PCA9685 if asleep, homing all 16 servos to $0^\circ$, returning to `STATE_IDLE_RUN`, and notifying `FAB2`) upon `CMD_STOP_SEQUENCE` (`0x02`), any physical button tap, or BLE central disconnect (`state_machine_on_ble_disconnect()`).

---

## Task Group 4: Host Unit Test Suite & Target Build Verification (`test/test_remote_cmd.c`, `test/test_state_machine.c`, `test/test_e2e_stress.c`, `Makefile`)
1. Update existing unit tests (`test/test_state_machine.c`, `test/test_e2e_stress.c`, `test/test_ble_transport.c`) where assertions previously expected `CMD_EMERGENCY_STOP` to auto-return immediately to `STATE_IDLE_RUN`, verifying the new latched `STATE_ESTOP` state and subsequent clear via `CMD_STOP_SEQUENCE` / button tap while keeping all prior checks green.
2. Create `firmware/test/test_remote_cmd.c` covering all Phase 9 requirements:
   - `FAB1` wire opcode parsing (`0x00–0x03`, `0x0A–0x0E`, `0x10`, `0x11`) and unknown/malformed opcode rejection (`CMD_STATUS_ERR_INVALID_ARG`).
   - Full 54-byte and compact variable-length (`5..50B`) `CMD_RUN_RAW_SEQUENCE` (`0x01`) unpacking, zero-padding, CRC32 verification/auto-computation, `active_button_id = 0` tracking, and NVS non-modification check.
   - Routine bounds rejection: `step_count == 0` (`CMD_STATUS_ERR_INVALID_STEP`), `step_count > 16` (`CMD_STATUS_ERR_ROUTINE_FULL`), `motor_count == 0` or `> 2` (`CMD_STATUS_ERR_MOTOR_BOUNDS`), `channel > 15` (`CMD_STATUS_ERR_MOTOR_BOUNDS`), and corrupted CRC32 (`CMD_STATUS_ERR_CRC_MISMATCH`).
   - Ingress busy guard during `STATE_RUNNING_MOTION`: rejecting `0x00`, `0x01`, `0x0A`, `0x0C`, `0x0D`, and `FAB3` writes with `CMD_STATUS_ERR_BUSY` without interrupting active motion.
   - Empty NVS preset (`step_count == 0`) rejection on `0x00` with `CMD_STATUS_ERR_INVALID_STEP` and `LED_STATE_INPUT_ERROR`.
   - 100% routine completion `FAB2` telemetry notification (`step_progress_pct = 100`, `last_cmd_status = CMD_STATUS_OK`) before returning to `STATE_IDLE_RUN`.
   - Core 1 fast-path preemption on `0x02` (`CMD_STOP_SEQUENCE`) and `0x03` (`CMD_EMERGENCY_STOP`), latched `STATE_ESTOP` (`system_state = 2`, `error_code` `BIT2` set), rejection of run/jog commands while latched in `STATE_ESTOP`, and recovery to `STATE_IDLE_RUN` via `0x02` over BLE or physical button tap.
   - Wireless preset save (`0x0A` full & compact), factory preset restore (`0x0C` homing servos + `LED_STATE_SAVE_SUCCESS` + `FAB3` notify), and immediate `FAB2` status push on every command outcome.
   - Live servo calibration (`0x0D`): transition `STATE_IDLE_RUN` $\rightarrow$ `STATE_CALIBRATING`, bounds rejection (`channel > 15` or `angle_deg > 180` $\rightarrow$ `CMD_STATUS_ERR_MOTOR_BOUNDS`), 10-second PCA9685 sleep thermal cutoff (`PCA9685_MODE1_SLEEP` bit set at `10000ms`), automatic wake on subsequent jog between `10s` and `15s`, 15-second auto-home exit to `STATE_IDLE_RUN`, and immediate wake/home exit on `0x02`, physical button tap, or BLE disconnect.
3. Run `make test` (all 9 host test suites with `-Wall -Wextra -Werror`) and `idf.py build` to confirm zero warnings and zero errors.
