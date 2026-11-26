# Plan — Phase 2: UI Subsystem (4-Button Debouncer & Non-Blocking LED Pattern Engine)

## Overview

Phase 2 implements the front-panel User Interface (UI) subsystem for the **Fabrica Cloth Folding Robot** on Core 1 of the **ESP32-S3-DevKitC-1**. This subsystem encompasses two key modules:
1. **Status LED Pattern Engine (`main/led.h`, `main/led.c`)**: A non-blocking, spinlock-protected visual feedback engine driving 8 distinct operational and error blink patterns on `GPIO 15`.
2. **4-Button Debouncer & Gesture Recognizer (`main/buttons.h`, `main/buttons.c`)**: A 50ms low-pass sampling scanner on `GPIO 4` (B1), `GPIO 5` (B2), `GPIO 6` (B3), and `GPIO 7` (B4) that differentiates Short Taps (<500ms), Single-Button Long Presses (≥3000ms), `B1+B4` Bond Reset Holds (≥5000ms), and `B1+B3+B4` Full Factory Reset Holds (≥10000ms), dispatching standardized `command_t` messages to `xCommandQueue`.

---

## Task Group 1: Status LED Pattern Engine (`main/led.h`, `main/led.c`)
1. Create `firmware/main/led.h`:
   - Define `led_state_t` enumeration representing the 8 visual feedback patterns:
     - `LED_STATE_IDLE`: Soft heartbeat pulse (100ms ON / 1900ms OFF / 0.5 Hz).
     - `LED_STATE_RUNNING`: Solid ON continuous throughout folding routine execution.
     - `LED_STATE_SAVE_SUCCESS`: Solid ON for 2.0 seconds, then return to IDLE.
     - `LED_STATE_INPUT_ERROR`: 3 fast flashes (60ms ON / 60ms OFF), then return to prior base state.
     - `LED_STATE_ESTOP`: 5 rapid flashes (50ms ON / 50ms OFF), then return to IDLE.
     - `LED_STATE_BLE_PAIRING`: Fast double-blink (100ms ON / 100ms OFF / 100ms ON / 500ms OFF).
     - `LED_STATE_BLE_CONNECTED`: Solid ON for 1.0 second, then return to prior base state.
     - `LED_STATE_IDENTIFY`: 3 fast double-blinks (3.0s total), then return to prior base state.
   - Declare public API:
     - `esp_err_t led_init(void)`: Configure `STATUS_LED_GPIO` (GPIO 15) as push-pull output and spawn `app_led_task`.
     - `void led_set_state(led_state_t state)`: Thread-safe (`portMUX_TYPE` spinlock) state update function.
     - `led_state_t led_get_state(void)`: Query current active LED state.
2. Implement `firmware/main/led.c`:
   - Initialize `STATUS_LED_GPIO` using ESP-IDF `driver/gpio.h`.
   - Implement `app_led_task` pinned to Core 1 (Priority 3, Stack: 2048 bytes).
   - Implement non-blocking state machine / timing sequencer using `ulTaskNotifyTake()` woken immediately by `xTaskNotifyGive()` on state change.
   - Support transient patterns (`SAVE_SUCCESS`, `INPUT_ERROR`, `ESTOP`, `BLE_CONNECTED`, `IDENTIFY`) that automatically revert to the underlying base state (`IDLE`, `RUNNING`, or `BLE_PAIRING`) upon completion.

---

## Task Group 2: 4-Button Debouncing & Gesture Recognition (`main/buttons.h`, `main/buttons.c`)
1. Create `firmware/main/buttons.h`:
   - Define button identifiers `button_id_t` (`BTN_ID_1`, `BTN_ID_2`, `BTN_ID_3`, `BTN_ID_4`).
   - Define gesture types `button_gesture_t` (`GESTURE_NONE`, `GESTURE_SHORT_TAP`, `GESTURE_LONG_PRESS`, `GESTURE_BOND_RESET`, `GESTURE_FACTORY_RESET`).
   - Declare public API:
     - `esp_err_t buttons_init(void)`: Configure GPIOs (4, 5, 6, 7) with internal pull-ups (`GPIO_PULLUP_ONLY`) and spawn `app_ui_task`.
     - `void buttons_process_tick(uint32_t elapsed_ms)`: Single sampling tick for debouncing and chord tracking.
2. Implement `firmware/main/buttons.c`:
   - Configure input GPIOs with `gpio_config_t` using `GPIO_MODE_INPUT` and `GPIO_PULLUP_ENABLE`.
   - Implement per-button debouncing state tracking (50ms low-pass filter window).
   - Implement gesture classification:
     - **Short Tap**: Button pressed and released in $< 500\text{ms}$ (`BUTTON_SHORT_PRESS_MAX_MS`).
     - **Long Press**: Single button continuously held down for $\ge 3000\text{ms}$ (`BUTTON_LONG_PRESS_MS`). Triggers once immediately at 3000ms without waiting for release; subsequent release does not re-trigger a tap.
     - **Chord Resets**: `B1+B4` held $\ge 5000\text{ms}$ (`GESTURE_BOND_RESET`) and `B1+B3+B4` held $\ge 10000\text{ms}$ (`GESTURE_FACTORY_RESET`), suppressing single-button 3s holds while active.
   - Implement `command_t` dispatching:
     - B1–B4 Short Tap (Idle) $\rightarrow$ `CMD_RUN_PRESET` (`preset_id = 1..4`), (Running) $\rightarrow$ `CMD_EMERGENCY_STOP`, (E-Stop / Calibrating) $\rightarrow$ `CMD_STOP_SEQUENCE`.
     - B1–B4 Long Press $\rightarrow$ `CMD_ENTER_BLE_PAIRING`.
     - `B1+B4` 5s Chord $\rightarrow$ `CMD_CLEAR_BLE_BONDS`; `B1+B3+B4` 10s Chord $\rightarrow$ `CMD_FACTORY_RESET_ALL`.
   - Implement `app_ui_task` pinned to Core 1 (Priority 5, Stack: 3072 bytes, period: 10ms sampling tick).

---

## Task Group 3: Build Registration & System Integration (`main.c`, `CMakeLists.txt`)
1. Update `firmware/main/CMakeLists.txt`:
   - Add `led.c` and `buttons.c` to `SRCS` registration list.
2. Update `firmware/main/main.c`:
   - In `app_main()`:
     - Call `led_init()` and verify status LED starts in `LED_STATE_IDLE`.
     - Call `buttons_init()` to launch the button scanner on Core 1.
     - Implement command queue processing loop to receive `command_t` items from `xCommandQueue`, log receipt via `ESP_LOGI`, and trigger visual LED pattern responses for verification.

---

## Task Group 4: Host Verification Test Harness & ESP-IDF Build Validation
1. Create `firmware/test/test_ui_subsystem.c`:
   - Host-compilable unit test harness (with mocked GPIO and FreeRTOS tick timer) verifying:
     - 50ms low-pass debounce filter suppresses glitches under 50ms.
     - Press-and-release within 200ms correctly generates `GESTURE_SHORT_TAP` and `CMD_RUN_PRESET`.
     - Continuous hold for 3000ms correctly generates `GESTURE_LONG_PRESS` and `CMD_ENTER_BLE_PAIRING`.
     - Releasing after a long press produces no extraneous tap commands.
     - All 8 LED pattern sequences execute correct ON/OFF timing transitions and transient return-to-base behaviors.
2. Update `firmware/Makefile`:
   - Add target `make test` to compile and run both `test_headers` and `test_ui_subsystem` under GCC / Clang with `-Wall -Wextra -Werror`.
3. Validate ESP-IDF compilation:
   - Run `idf.py build` to confirm 0 compiler warnings and 0 errors.
