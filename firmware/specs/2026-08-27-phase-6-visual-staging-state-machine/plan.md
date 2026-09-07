# Plan — Phase 6: Visual Staging Programming Mode & State Machine Integration

## Overview

Phase 6 implements the **Visual Staging Programming Mode & State Machine Integration** for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. This subsystem introduces a dedicated state machine engine (`main/state_machine.h`, `main/state_machine.c`) that coordinates operating modes (**Daily Run Mode**, **Visual Staging Programming Mode**, and **Motion Execution**), manages the physical button mapping based on system state, coordinates visual flap staging using PCA9685 servo positions ($15^\circ$ nudge for identification, $30^\circ$ hold for staging), accumulates folding steps into a temporary sequence buffer, enforces safety constraints (max 2 motors per step, empty step rejection, 20s inactivity watchdog timeout, 16-step automatic commit), and commits completed sequences to Non-Volatile Storage (NVS) flash with instant playback availability.

---

## Task Group 1: State Machine Architecture, Data Types & IPC Primitives (`main/state_machine.h`, `main/state_machine.c`)
1. Create `firmware/main/state_machine.h`:
   - Declare system operating states:
     - `system_state_t` (`STATE_IDLE_RUN`, `STATE_RUNNING_MOTION`, `STATE_PROGRAMMING`)
   - Declare visual staging context data structure (`staging_context_t`):
     - `uint8_t target_preset_id` (1 to 4)
     - `uint8_t current_channel_idx` (0 to 15)
     - `uint8_t staged_motor_count` (0 to 2)
     - `uint8_t staged_motor_ids[MAX_MOTORS_PER_STEP]` (0 to 15)
     - `fold_routine_t buffer_routine` (temporary sequence buffer, up to 16 steps)
     - `uint32_t inactivity_timer_ms` (20,000ms countdown watchdog)
   - Declare state machine lifecycle and event handling API:
     - `esp_err_t state_machine_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group)`
     - `system_state_t state_machine_get_state(void)`
     - `const staging_context_t* state_machine_get_context(void)`
     - `esp_err_t state_machine_process_command(const command_t *cmd)`
     - `void state_machine_tick(uint32_t elapsed_ms)`
2. Implement core state transition engine in `firmware/main/state_machine.c`:
   - Store global IPC queue, event group handles, and internal `staging_context_t`.
   - Implement state transition guards:
     - Allow `CMD_RUN_PRESET` only when in `STATE_IDLE_RUN`.
     - Transition to `STATE_RUNNING_MOTION` during motion execution.
     - Transition to `STATE_PROGRAMMING` on `CMD_ENTER_PROGRAM_MODE` (long press ≥3s).
     - Return to `STATE_IDLE_RUN` on motion complete, E-Stop, manual save & exit, or inactivity timeout.

---

## Task Group 2: Physical Visual Staging Engine & Flap Articulation (`main/state_machine.c`)
1. Implement Button 1 (CYCLE / NUDGE) handler in `firmware/main/state_machine.c`:
   - Increment `current_channel_idx` (0 $\to$ 15, wrapping back to 0).
   - If the newly selected channel is not already staged at $30^\circ$, issue a brief identification nudge ($15^\circ$ via `pca9685_nudge_channel()`).
2. Implement Button 2 (STAGE / TOGGLE) handler in `firmware/main/state_machine.c`:
   - Check if `current_channel_idx` is currently in `staged_motor_ids`:
     - **Toggle OFF (Unstage)**: If already staged, remove from `staged_motor_ids`, decrement `staged_motor_count`, and return servo to $0^\circ$ (`HOME_ANGLE_DEG`).
     - **Toggle ON (Stage)**: If not staged and `staged_motor_count < 2`, add to `staged_motor_ids`, increment `staged_motor_count`, and command servo to $30^\circ$ (`STAGE_ANGLE_DEG`).
     - **3rd Motor Safeguard**: If `staged_motor_count == 2` and user attempts to stage a 3rd motor, reject with `led_set_state(LED_STATE_INPUT_ERROR)` (3 fast flashes) and leave flap at $0^\circ`.
3. Implement Button 3 (NEXT STEP / LOCK) handler in `firmware/main/state_machine.c`:
   - **Empty Step Safeguard**: If `staged_motor_count == 0`, ignore press or trigger error feedback without recording an empty step.
   - If `staged_motor_count > 0`:
     - Record current staged motors into `buffer_routine.steps[buffer_routine.step_count]`.
     - Increment `buffer_routine.step_count`.
     - Drop all staged flaps flat to $0^\circ$ via `pca9685_home_all()`.
     - Trigger `led_set_state(LED_STATE_STEP_LOCKED)` (2 fast flashes: 80ms ON / 80ms OFF).
     - Clear staged motor tracking (`staged_motor_count = 0`).
     - **16-Step Auto-Commit**: If `buffer_routine.step_count == MAX_STEPS_PER_ROUTINE` (16 steps), automatically trigger save to NVS flash and exit to `STATE_IDLE_RUN`.
4. Implement Button 4 (SAVE & EXIT) handler in `firmware/main/state_machine.c`:
   - If `buffer_routine.step_count > 0`:
     - Commit `buffer_routine` to NVS storage slot `target_preset_id` via `storage_save_routine()`.
     - Drop all servos flat to $0^\circ$.
     - Trigger `led_set_state(LED_STATE_SAVE_SUCCESS)` (Solid ON for 2.0s).
   - If `buffer_routine.step_count == 0`:
     - Drop all servos to $0^\circ and exit without modifying existing NVS preset.
   - Transition state machine back to `STATE_IDLE_RUN`.

---

## Task Group 3: Inactivity Watchdog, Button Routing & Dispatch Integration (`main/buttons.c`, `main/state_machine.c`, `main/main.c`)
1. Implement Inactivity Watchdog Timer:
   - In `state_machine_tick(elapsed_ms)`:
     - When in `STATE_PROGRAMMING`, accumulate elapsed time in `inactivity_timer_ms`.
     - Reset `inactivity_timer_ms = 0` on any valid button press or command.
     - If `inactivity_timer_ms >= PROGRAMMING_TIMEOUT_MS` (20,000ms):
       - Drop all servos flat to $0^\circ$ (`pca9685_home_all()`).
       - Discard temporary sequence buffer.
       - Set `led_set_state(LED_STATE_IDLE)`.
       - Transition back to `STATE_IDLE_RUN`.
2. Update `firmware/main/buttons.c` gesture routing:
   - Query `state_machine_get_state()` on button tap:
     - In `STATE_IDLE_RUN`: B1–B4 short tap dispatches `CMD_RUN_PRESET` (Preset 1–4); long press dispatches `CMD_ENTER_PROGRAM_MODE`.
     - In `STATE_RUNNING_MOTION`: Any button tap dispatches `CMD_EMERGENCY_STOP`.
     - In `STATE_PROGRAMMING`:
       - B1 short tap $\to$ `CMD_CYCLE_NUDGE_MOTOR`
       - B2 short tap $\to$ `CMD_STAGE_TOGGLE_MOTOR`
       - B3 short tap $\to$ `CMD_LOCK_STEP`
       - B4 short tap $\to$ `CMD_SAVE_EXIT_PROGRAM`
       - Long press ignored while already in Programming Mode.
3. Update `firmware/main/main.c`:
   - Initialize state machine during system startup via `state_machine_init()`.
   - Update main command processing loop to delegate events to `state_machine_process_command()`.

---

## Task Group 4: Host Verification Harness, Mock State Machine Suite & ESP-IDF Integration (`test/test_state_machine.c`, `Makefile`, `main/CMakeLists.txt`)
1. Create `firmware/test/test_state_machine.c`:
   - Implement comprehensive host test harness with simulated PCA9685, LED, Buttons, Storage, and Motion modules:
     - Test initial state on boot (`STATE_IDLE_RUN`).
     - Test transition from Run Mode to Programming Mode on 3-second long press on B1–B4.
     - Test B1 motor cycling (channels 0 through 15 wrap-around) and $15^\circ$ nudge pulse verification.
     - Test B2 staging ($30^\circ$ hold) and unstaging toggle ($0^\circ$ rest).
     - Test 2-motor per step limit enforcement (3rd motor attempt triggers `LED_STATE_INPUT_ERROR`).
     - Test B3 step locking (staged servos drop to $0^\circ$, `LED_STATE_STEP_LOCKED` 2-flash trigger, buffer step increment).
     - Test empty step locking rejection (B3 pressed with 0 staged motors).
     - Test B4 manual save & exit (NVS flash write, `LED_STATE_SAVE_SUCCESS` 2s solid ON, return to `STATE_IDLE_RUN`).
     - Test 16-step buffer limit auto-save and exit.
     - Test 20-second inactivity timeout (all flaps homed, buffer discarded, return to `STATE_IDLE_RUN`).
     - Test Emergency Stop preemption during motion vs programming.
     - Test subsequent Run Mode playback of newly programmed sequence from NVS.
2. Update `firmware/Makefile`:
   - Add `test_state_machine` target and link to `make test`.
3. Update `firmware/main/CMakeLists.txt`:
   - Register `state_machine.c` in component sources (`SRCS`).
4. Verify ESP-IDF compilation:
   - Run `idf.py build` ensuring clean compilation with zero warnings and verify memory headroom.
