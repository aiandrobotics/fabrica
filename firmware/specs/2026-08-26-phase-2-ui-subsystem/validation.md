# Validation — Phase 2: UI Subsystem (4-Button Debouncer & Non-Blocking LED Pattern Engine)

## Required Checks

### 1. Host-Based Unit Test Suite (`firmware/test/test_ui_subsystem.c`)
- [ ] Compile and execute host test harness using GCC or Clang:
  ```bash
  gcc -Wall -Wextra -Werror -I./firmware/main -o /tmp/test_ui_subsystem firmware/test/test_ui_subsystem.c && /tmp/test_ui_subsystem
  ```
- [ ] **Debounce Filter Validation**:
  - Verify spurious noise spikes (<50ms) on any button GPIO do not transition button state or dispatch commands.
  - Verify stable low level maintained for ≥50ms transitions state to pressed.
- [ ] **Short Tap Gesture Validation**:
  - Simulate press duration of 150ms on B1 $\rightarrow$ verify exact generation of `CMD_RUN_PRESET` with `preset_id = 1` and `source = SOURCE_PHYSICAL_BUTTON`.
  - Simulate press duration of 250ms on B2, B3, B4 $\rightarrow$ verify exact generation of `CMD_RUN_PRESET` with `preset_id = 2, 3, 4`.
- [ ] **Long Press & Chord Reset Gesture Validation**:
  - Simulate continuous press for 3000ms on B1 $\rightarrow$ verify generation of `CMD_ENTER_BLE_PAIRING` at exactly the 3000ms mark.
  - Simulate simultaneous `B1+B4` press for 5000ms $\rightarrow$ verify `GESTURE_BOND_RESET` (`CMD_CLEAR_BLE_BONDS`) fires while suppressing 3s long press.
  - Simulate simultaneous `B1+B3+B4` press for 10000ms $\rightarrow$ verify `GESTURE_FACTORY_RESET` (`CMD_FACTORY_RESET_ALL`) fires while suppressing 3s/5s gestures.
  - Verify that subsequent button release (e.g. at 3500ms) produces zero extra commands.
- [ ] **LED Pattern Sequencer Validation**:
  - Test `LED_STATE_IDLE`: verifies 100ms ON / 1900ms OFF repeating timing.
  - Test `LED_STATE_RUNNING`: verifies continuous 100% duty cycle ON.
  - Test `LED_STATE_SAVE_SUCCESS`: verifies solid ON for 2000ms, then returns to `LED_STATE_IDLE`.
  - Test `LED_STATE_INPUT_ERROR`: verifies exactly 3 pulses of 60ms ON / 60ms OFF, then returns to previous base state.
  - Test `LED_STATE_ESTOP`: verifies exactly 5 pulses of 50ms ON / 50ms OFF, then returns to `LED_STATE_IDLE`.
  - Test `LED_STATE_BLE_PAIRING`: verifies fast double-blink (100ms ON / 100ms OFF / 100ms ON / 500ms OFF).
  - Test `LED_STATE_BLE_CONNECTED`: verifies solid ON for 1000ms, then restores previous base state.
  - Test `LED_STATE_IDENTIFY`: verifies 3 fast double-blinks (3000ms total), then restores previous base state.

### 2. ESP-IDF Build & Compilation Verification
- [ ] Confirm `CMakeLists.txt` registers `led.c` and `buttons.c`.
- [ ] Execute clean ESP-IDF project compilation:
  ```bash
  idf.py build
  ```
- [ ] Verify compilation completes with **0 warnings** and **0 errors** under `-Wall -Wextra`.
- [ ] Verify binary size and SRAM allocation leave $\ge 120\text{ KB}$ internal DRAM available for future phases.

---

## Manual Review & Hardware Bench Verification

### 1. Serial Monitor Logging Inspection
- [ ] Flash ESP32-S3-DevKitC-1 and connect monitor:
  ```bash
  idf.py flash monitor
  ```
- [ ] Verify boot diagnostics show `app_ui_task` (Core 1, Priority 5) and `app_led_task` (Core 1, Priority 3) running.
- [ ] **Short Tap Test**:
  - Briefly tap B1 $\rightarrow$ verify log: `[BUTTONS] Button B1 Short Tap (<500ms) -> Dispatched CMD_RUN_PRESET (Preset 1)`.
  - Briefly tap B2, B3, B4 $\rightarrow$ verify logs for Presets 2, 3, and 4.
- [ ] **Long Press Test**:
  - Hold B1 for 3 seconds $\rightarrow$ verify log at 3s mark: `[BUTTONS] Button B1 Long Press (>=3000ms) -> Dispatched CMD_ENTER_BLE_PAIRING`.
  - Release B1 after 4s $\rightarrow$ verify no trailing tap message logged.

### 2. Physical Status LED Inspection
- [ ] Observe on-board LED (`GPIO 15`) during idle: soft heartbeat (100ms pulse every 2 seconds).
- [ ] Trigger test states and confirm visual output matches specified blink timings (fast double-blink in BLE pairing mode, rapid 5-flash on E-stop, solid ON for save confirmation).

---

## Merge Criteria

- [ ] All three spec documents (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-08-26-phase-2-ui-subsystem/`.
- [ ] Working branch `feature/phase-2-ui-subsystem` is active.
- [ ] Spec aligns completely with `specs/mission.md`, `specs/tech-stack.md`, and `specs/roadmap.md`.
- [ ] No implementation code was written during the spec authoring stage.
