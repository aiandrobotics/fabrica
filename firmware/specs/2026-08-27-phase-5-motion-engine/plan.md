# Plan — Phase 5: Motion Engine & Daily Run Mode Execution

## Overview

Phase 5 implements the real-time Motion Engine and Daily Run Mode execution subsystem for the **Fabrica Cloth Folding Robot** on the **ESP32-S3-DevKitC-1**. This subsystem runs a dedicated high-priority FreeRTOS task pinned to Core 0 (`main/motion.h`, `main/motion.c`) that consumes folding routines from NVS storage or direct command payloads, orchestrates deterministic single and parallel dual-servo sweep trajectories ($0^\circ \to 150^\circ \to 0^\circ$), manages fold dwell and inter-step settling delays, coordinates status LED feedback, and enforces instantaneous Emergency Stop (E-Stop) preemption (<50ms response, all 16 channels homed flat to $0^\circ$).

---

## Task Group 1: Core 0 Motion Task Architecture & IPC Primitives (`main/motion.h`, `main/motion.c`)
1. Create `firmware/main/motion.h`:
   - Declare motion task configuration constants:
     - `MOTION_TASK_STACK_SIZE` (4096 bytes)
     - `MOTION_TASK_PRIORITY` (Priority 10, Core ID 0)
   - Declare motion state and event flags:
     - `motion_status_t` (`MOTION_STATUS_IDLE`, `MOTION_STATUS_RUNNING`, `MOTION_STATUS_STOPPING`, `MOTION_STATUS_ABORTED`)
     - Event group bits: `MOTION_EVENT_START_BIT`, `MOTION_EVENT_ESTOP_BIT`, `MOTION_EVENT_COMPLETE_BIT`
   - Declare motion subsystem lifecycle API:
     - `esp_err_t motion_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group)`
     - `motion_status_t motion_get_status(void)`
     - `bool motion_is_busy(void)`
2. Implement Core 0 motion task bootstrap in `firmware/main/motion.c`:
   - Store global IPC queue and event group handles.
   - Implement `app_motion_task` pinned to Core 0 using `xTaskCreatePinnedToCore()`.
   - Implement task loop waiting on motion commands/signals and monitoring system event group flags.

---

## Task Group 2: Sequence Execution Engine & Servo Trajectory Coordination (`main/motion.h`, `main/motion.c`)
1. Extend `firmware/main/motion.h`:
   - Declare routine execution functions:
     - `esp_err_t motion_execute_routine(const fold_routine_t *routine)`
     - `esp_err_t motion_execute_step(const fold_step_t *step)`
2. Implement trajectory execution in `firmware/main/motion.c`:
   - Implement single-motor 5-phase balance-point braked S-curve sweep ($0^\circ \to 150^\circ \to 0^\circ$):
     - Phase 1 (Soft Start Coupler Take-Up): Ramp $0^\circ \to 24^\circ$ (8 frames @ `SCURVE_FRAME_MS` = 200ms).
     - Phase 2 (Controlled Climb): Step $28^\circ \to 84^\circ$ by $+4^\circ$ (`SCURVE_CRUISE_STEP_DEG`) @ 25ms (375ms, $160^\circ\text{/s}$).
     - Phase 3 (Early Balance-Point Flip & Top Gravity Brake): Brake $87^\circ \to 150^\circ$ (`FOLD_TARGET_ANGLE_DEG`) by $+3^\circ$ @ `SCURVE_BRAKE_FRAME_MS` (25ms, $120^\circ\text{/s}$) and hold `FOLD_TOP_HOLD_MS` (250ms). (`FOLD_DWELL_TIME_MS` = 1350ms).
     - Phase 4 (Return Coupler Take-Up & Climb): Ease $148^\circ \to 136^\circ$ (6 frames @ 25ms = 150ms), then climb $132^\circ \to 80^\circ$ by $-4^\circ$ @ 25ms (350ms).
     - Phase 5 (Early Gravity-Braked Descent & Landing): Brake $78^\circ \to 20^\circ$ by $-2^\circ$ @ 25ms (750ms, $80^\circ\text{/s}$), then touch down $16^\circ \to 0^\circ$ (`HOME_ANGLE_DEG`, 8 frames @ 25ms = 200ms). (`LANDING_APPROACH_MS` = 1450ms).
   - Implement parallel dual-motor S-curve sweep:
     - Generate multi-channel bitmask from `step->motor_ids[0]` and `step->motor_ids[1]`.
     - Command both channels synchronously through the identical balance-point braked S-curve trajectory ($0^\circ \to 150^\circ \to 0^\circ$) via `pca9685_set_multi_servo_angles()`.
   - Implement inter-step settling delay:
     - Wait for `INTER_STEP_DELAY_MS` (10ms) between consecutive steps.
   - Bind visual LED status:
     - Set `led_set_state(LED_STATE_RUNNING)` when motion begins.
     - Set `led_set_state(LED_STATE_IDLE)` upon clean completion of all steps.

---

## Task Group 3: Daily Run Mode Dispatcher, Empty Preset Protection & E-Stop Abort Handler (`main/motion.h`, `main/motion.c`)
1. Extend `firmware/main/motion.h`:
   - Declare execution trigger and E-Stop APIs:
     - `esp_err_t motion_trigger_preset(uint8_t preset_id)`
     - `esp_err_t motion_emergency_stop(void)`
2. Implement Daily Run Mode trigger handling in `firmware/main/motion.c`:
   - Implement `motion_trigger_preset(preset_id)`:
     - Validate preset ID ($1 \le \text{preset\_id} \le 4$).
     - Load routine from NVS storage using `storage_load_routine(preset_id, &routine)`.
     - **Empty Preset Protection**: If `routine.step_count == 0`, immediately signal error with `led_set_state(LED_STATE_INPUT_ERROR)` (3 fast flashes) and return `ESP_ERR_INVALID_STATE` without commanding motors.
     - If valid steps exist, dispatch routine to Core 0 motion task for execution.
3. Implement Low-Latency Emergency Stop (E-Stop):
   - Set `MOTION_EVENT_ESTOP_BIT` in `xSystemEventGroup`.
   - Update motion status to `MOTION_STATUS_ABORTED`.
   - Immediately command all 16 channels to $0^\circ$ via `pca9685_home_all()`.
   - Trigger `led_set_state(LED_STATE_ESTOP)` (5 rapid flashes).
   - Ensure step execution loop terminates within $<50\text{ms}$ upon detecting abort flag.

---

## Task Group 4: Host Verification Harness, Mock Motion Suite & ESP-IDF Integration (`test/test_motion.c`, `Makefile`, `main/main.c`, `main/CMakeLists.txt`)
1. Create `firmware/test/test_motion.c`:
   - Implement host test harness with simulated PCA9685, LED, and NVS subsystems:
     - Test single-motor sweep trajectory ($0^\circ \to 150^\circ \to 0^\circ$) and timing parameters.
     - Test synchronized parallel dual-motor sweep execution.
     - Test multi-step routine sequencing (Step 1 to $N$) and 10ms inter-step delay.
     - Test empty preset safeguard (0 steps triggers `LED_STATE_INPUT_ERROR`).
     - Test invalid preset ID rejection ($<1$ or $>4$).
     - Test instant Emergency Stop preemption during active sweep, verifying abort latency $<50\text{ms}$, all channels homed, and `LED_STATE_ESTOP` triggered.
     - Test re-entrancy / busy protection when a new run command arrives during active motion.
2. Update `firmware/Makefile`:
   - Add `test_motion` compilation and execution target to `make test`.
3. Update `firmware/main/CMakeLists.txt`:
   - Register `motion.c` in component sources (`SRCS`).
4. Update `firmware/main/main.c`:
   - Call `motion_init(xCommandQueue, xSystemEventGroup)` during bootstrap.
   - Update command loop to route `CMD_RUN_PRESET`, `CMD_RUN_RAW_SEQUENCE`, and `CMD_EMERGENCY_STOP` to the motion engine.
5. Verify ESP-IDF compilation:
   - Run `idf.py build` to ensure clean build with 0 compiler warnings.
