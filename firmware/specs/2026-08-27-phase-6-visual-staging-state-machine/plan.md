# Plan — Phase 6: State Machine Coordinator & Minimal Physical Button Interface

> [!NOTE]
> **Architecture Update**: On-device multi-button visual staging (`STATE_PROGRAMMING`, `15°` nudge, `30°` stage hold) was retired in favor of the minimal physical 4-button pad + BLE GATT configuration (`FAB1`/`FAB3`) and live servo jog calibration (`0x0D`). This plan reflects the active production state machine in `main/state_machine.h` and `main/state_machine.c`.

## Overview

Phase 6 implements the central **State Machine Coordinator** (`main/state_machine.h`, `main/state_machine.c`) for the **Fabrica Cloth Folding Robot** on the **ESP32-S3-DevKitC-1**. It coordinates operating states (`STATE_IDLE_RUN`, `STATE_RUNNING_MOTION`, `STATE_ESTOP`, `STATE_CALIBRATING = 4`), routes state-aware physical button gestures (`buttons.c`), manages the zero-bond indefinite / 120-second BLE pairing window, enforces latched E-Stop safety and 10s/15s calibration watchdogs, and dispatches sequence execution, NVS saves, and factory resets cleanly across Core 0 and Core 1.

---

## Task Group 1: State Machine Architecture, Operating States & Public API (`main/state_machine.h`, `main/state_machine.c`)
1. Define `system_state_t` in `firmware/main/state_machine.h`:
   - `STATE_IDLE_RUN = 0` (Daily Run Mode awaiting preset trigger or BLE command)
   - `STATE_RUNNING_MOTION = 1` (Core 0 actively executing a folding routine)
   - `STATE_ESTOP = 2` (Latched Emergency Stop, all 16 servos homed; wire byte `3` reserved)
   - `STATE_CALIBRATING = 4` (Live servo jog calibration mode; explicit wire value `4`)
2. Declare lifecycle, pairing, calibration, and command dispatch APIs:
   - `void state_machine_set_command_queue(QueueHandle_t queue)`
   - `esp_err_t state_machine_init(void)`
   - `void state_machine_check_initial_pairing(void)`
   - `system_state_t state_machine_get_state(void)`
   - `uint8_t state_machine_get_active_preset(void)`
   - `bool state_machine_is_ble_pairing(void)`
   - `void state_machine_close_ble_pairing(void)`
   - `bool state_machine_is_calibrating_thermal_sleep(void)`
   - `void state_machine_on_ble_disconnect(void)`
   - `esp_err_t state_machine_process_command(const command_t *cmd)`
   - `void state_machine_tick(uint32_t elapsed_ms)`
   - `void state_machine_reset(void)`

---

## Task Group 2: Command Dispatch, Pairing Lifecycle & Safety Watchdogs (`main/state_machine.c`)
1. Implement command handling in `state_machine_process_command()`:
   - `CMD_RUN_PRESET`: Validate preset ID (1–4) and non-empty routine, track `s_active_preset_id`, invoke `motion_trigger_preset()`, notify 100% completion over `FAB2`, and return to `STATE_IDLE_RUN` (or preserve latched `STATE_ESTOP` on abort).
   - `CMD_RUN_RAW_SEQUENCE`: Execute unsaved routine in RAM with `active_button_id = 0` without altering NVS.
   - `CMD_EMERGENCY_STOP`: Abort motion (`motion_emergency_stop()`), wake PCA9685 if asleep, home all 16 servos, flash `LED_STATE_ESTOP`, latch `STATE_ESTOP`, and notify `FAB2`.
   - `CMD_STOP_SEQUENCE`: Cleanly clear `STATE_ESTOP` or exit `STATE_CALIBRATING` (wake + home all 16 servos) back to `STATE_IDLE_RUN`.
   - `CMD_ENTER_BLE_PAIRING`: Cache `s_ble_pairing_indefinite = (ble_transport_get_bond_count() == 0)`, activate `LED_STATE_BLE_PAIRING`, and call `ble_transport_enter_pairing_mode()`.
   - `CMD_SET_BUTTON_SEQUENCE` & `CMD_RESTORE_FACTORY_PRESETS`: Persist validated routines to NVS, illuminate `LED_STATE_SAVE_SUCCESS`, and push `FAB3` notification.
   - `CMD_JOG_MOTOR_ANGLE`: Transition to `STATE_CALIBRATING`, wake PCA9685 if sleeping, command target channel (`0°..180°`), reset calibration timers, and push `FAB2` update.
   - `CMD_CLEAR_BLE_BONDS` & `CMD_FACTORY_RESET_ALL`: Purge BLE bonds (and presets + home servos on full factory reset) and reopen indefinite pairing mode.
2. Implement periodic watchdog stepping in `state_machine_tick(elapsed_ms)`:
   - Enforce `BLE_PAIRING_TIMEOUT_MS` (120,000ms) when `!s_ble_pairing_indefinite`.
   - Enforce `CALIBRATION_THERMAL_TIMEOUT_MS` (10,000ms -> `CMD_CALIBRATION_THERMAL_SLEEP`) and `CALIBRATION_INACTIVITY_TIMEOUT_MS` (15,000ms -> `CMD_STOP_SEQUENCE`), dispatching through `xCommandQueue` on `ESP_PLATFORM` to serialize Core 0 I2C access.
   - Invoke `telemetry_notify_state_change()` on every `system_state_t` transition.

---

## Task Group 3: State-Aware Button Routing & System Integration (`main/buttons.c`, `main/main.c`, `main/CMakeLists.txt`)
1. Update `firmware/main/buttons.c` gesture routing (`buttons_translate_gesture()`):
   - In `STATE_IDLE_RUN`: Short tap $\to$ `CMD_RUN_PRESET` (1–4); 3s hold $\to$ `CMD_ENTER_BLE_PAIRING`.
   - In `STATE_RUNNING_MOTION`: Any button tap $\to$ `CMD_EMERGENCY_STOP`.
   - In `STATE_ESTOP` / `STATE_CALIBRATING`: Any button tap $\to$ `CMD_STOP_SEQUENCE`.
   - Across non-running states: `B1+B4` 5s chord $\to$ `CMD_CLEAR_BLE_BONDS`; `B1+B3+B4` 10s chord $\to$ `CMD_FACTORY_RESET_ALL`.
2. Update `firmware/main/main.c` and `firmware/main/CMakeLists.txt`:
   - Register `state_machine.c`, bind `s_command_queue`, call `state_machine_init()` and `state_machine_check_initial_pairing()`, and route the Core 0 queue loop to `state_machine_process_command()`.

---

## Task Group 4: Host Verification Harness (`test/test_state_machine.c`, `Makefile`)
1. Implement `firmware/test/test_state_machine.c` verifying boot state, preset dispatch, raw sequence preview, wireless preset save & factory restore, BLE pairing (indefinite vs 120s timeout), bond reset & full factory reset, live servo jog with 10s thermal sleep & 15s auto-home, latched E-Stop & recovery, and state-aware button translation.
2. Register `test_state_machine` in `firmware/Makefile` and verify `make test` and ESP-IDF compilation with 0 warnings.
