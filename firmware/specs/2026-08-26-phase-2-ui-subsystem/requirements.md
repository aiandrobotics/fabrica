# Requirements — Phase 2: UI Subsystem (4-Button Debouncer & Non-Blocking LED Pattern Engine)

## Scope

Phase 2 delivers the physical User Interface (UI) front-panel subsystem for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. It encompasses:
1. **Status LED Pattern Engine (`main/led.h`, `main/led.c`)**: Non-blocking driver generating 7 standardized visual pulse patterns on `GPIO 2`.
2. **4-Button Debouncing & Gesture Recognizer (`main/buttons.h`, `main/buttons.c`)**: Active-low button scanner with 50ms low-pass debounce sampling on `GPIO 4`, `GPIO 16`, `GPIO 17`, and `GPIO 5`, discriminating Short Tap (<500ms) and Long Press (≥3000ms) gestures.
3. **Unified Command Queue Dispatch**: Direct translation of button gestures into source-agnostic `command_t` objects (`SOURCE_PHYSICAL_BUTTON`) posted to `xCommandQueue`.
4. **FreeRTOS Dual-Core UI Scheduling**: Dedicated Core 1 tasks (`app_ui_task` at Priority 5, `app_led_task` at Priority 3) ensuring zero blocking on Core 0 motion timing.
5. **Host Unit Test Harness (`test/test_ui_subsystem.c`)**: C unit test harness validating debounce filtering, gesture timing, and LED pattern transitions under simulated clock ticks.

---

## Decisions & Technical Specifications

### 1. FreeRTOS Task Allocation on Core 1

| Task Name | Priority | Core ID | Stack Size | Period / Wakeup | Description |
|---|---|---|---|---|---|
| `app_ui_task` | `5` | `1` | `3072` bytes | `10` ms periodic tick | Samples 4 GPIO buttons, runs 50ms low-pass debounce filter, tracks hold duration, dispatches commands |
| `app_led_task` | `3` | `1` | `2048` bytes | Event / Delay driven | Non-blocking pattern sequencer cycling `STATUS_LED_GPIO` according to active `led_state_t` |

### 2. GPIO Pin Configuration (Sequential Physical Board Order)

| Signal Name | ESP32 GPIO | Direction | Pull Mode | Active Level | Assigned Function | Physical Header Order |
|---|---|---|---|---|---|---|
| `STATUS_LED_GPIO` | `GPIO_NUM_2` | Output | None (Push-Pull) | High (1 = LED ON) | Built-in DevKit Status Indicator | Pin 1 (D2) |
| `BTN1_GPIO` | `GPIO_NUM_4` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0 = Pressed) | Button 1 (Preset 1 / Cycle & Nudge) | Pin 2 (D4) |
| `BTN2_GPIO` | `GPIO_NUM_16` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0 = Pressed) | Button 2 (Preset 2 / Stage & Toggle) | Pin 3 (D16) |
| `BTN3_GPIO` | `GPIO_NUM_17` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0 = Pressed) | Button 3 (Preset 3 / Lock Step) | Pin 4 (D17) |
| `BTN4_GPIO` | `GPIO_NUM_5` | Input | Internal Pull-Up (`GPIO_PULLUP_ONLY`) | Low (0 = Pressed) | Button 4 (Preset 4 / Save & Exit) | Pin 5 (D5) |

### 3. LED Pattern Specifications (`main/led.h`)

| State Enum | Pattern Description | Timing Details | Priority / Mode | Revert Target |
|---|---|---|---|---|
| `LED_STATE_IDLE` | Soft Heartbeat (10% duty cycle @ 0.5 Hz) | 100ms ON, 1900ms OFF (repeating) | Continuous Base | — |
| `LED_STATE_RUNNING` | Solid Continuous ON | 100% ON throughout folding motion | Continuous Base | — |
| `LED_STATE_PROGRAMMING` | Slow Blink (0.5 Hz) | 1000ms ON, 1000ms OFF (repeating) | Continuous Base | — |
| `LED_STATE_STEP_LOCKED` | 2 Fast Flashes | 2 cycles of (80ms ON, 80ms OFF) | Transient Overlay | Returns to prior Base |
| `LED_STATE_SAVE_SUCCESS` | Solid Confirmation Hold | Solid ON for 2000ms, then OFF | Transient Overlay | Returns to `IDLE` |
| `LED_STATE_INPUT_ERROR` | 3 Fast Flashes | 3 cycles of (60ms ON, 60ms OFF) | Transient Overlay | Returns to prior Base |
| `LED_STATE_ESTOP` | 5 Rapid Flashes | 5 cycles of (50ms ON, 50ms OFF) | High Priority Transient | Returns to `IDLE` |

### 4. Button Gesture Recognition & Command Mapping (`main/buttons.h`)

- **Debounce Filter**: Consecutive sampled state must remain stable for $\ge 50\text{ms}$ (`BUTTON_DEBOUNCE_MS`) before registering a valid edge transition.
- **Short Tap Detection**:
  - Registered when a stable press is released within $< 500\text{ms}$ (`BUTTON_SHORT_PRESS_MAX_MS`).
  - Action: Dispatches `command_t` to `xCommandQueue`:
    - `type = CMD_RUN_PRESET`
    - `source = SOURCE_PHYSICAL_BUTTON`
    - `payload.preset_id = button_index + 1` (1 for B1, 2 for B2, 3 for B3, 4 for B4).
- **Long Press Detection**:
  - Registered when a button is held continuously for $\ge 3000\text{ms}$ (`BUTTON_LONG_PRESS_MS`).
  - Triggers immediately at the 3000ms mark (does not wait for button release).
  - Subsequent release is consumed and does not trigger an extra Short Tap.
  - Action: Dispatches `command_t` to `xCommandQueue`:
    - `type = CMD_ENTER_PROGRAM_MODE`
    - `source = SOURCE_PHYSICAL_BUTTON`
    - `payload.preset_id = button_index + 1` (1 for B1, 2 for B2, 3 for B3, 4 for B4).

---

## Constraints

- **Core 1 Isolation**: All UI debounce scanning and LED blinking must execute strictly on Core 1, preventing any CPU contention with Core 0 real-time I2C servo actuation.
- **Non-Blocking Operation**: The LED engine and button scanner must not invoke blocking `vTaskDelay()` calls longer than their fundamental step ticks (10ms for UI scanner, dynamic slice for LED task).
- **Thread Safety**: State transitions in `led_set_state()` and queue posts in `buttons.c` must use FreeRTOS thread-safe queue and mutex/atomic primitives.
- **Host Testability**: Core logic algorithms (debounce state machine, gesture duration math, LED step sequencers) must be decoupled from ESP-IDF hardware macros to enable host compilation under GCC/Clang.

---

## Non-Goals

- I2C communication with PCA9685 PWM driver (Phase 3).
- NVS flash read/write operations (Phase 4).
- Core 0 motion trajectory generation (Phase 5).
- Full multi-step Visual Staging programming workflow (Phase 6).
- Wireless BLE/Wi-Fi event reception (Phase 8).

---

## Context

Phase 2 builds upon the project skeleton, GPIO configuration, and command structures established in Phase 1 (`config.h`, `command.h`, `main.c`). It connects physical inputs (push buttons) and visual feedback (LED) to the unified command architecture, establishing the interactive front-panel interface for all future operating modes.
