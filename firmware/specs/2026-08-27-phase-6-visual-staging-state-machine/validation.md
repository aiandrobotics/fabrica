# Validation — Phase 6: Visual Staging Programming Mode & State Machine Integration

## Required Checks

The implementation of Phase 6 must be validated against automated host test suites and ESP-IDF compilation checks.

### 1. Automated Host Unit Tests (`firmware/test/test_state_machine.c`)

| Test Case | Description | Pass Criteria |
|---|---|---|
| **Initial Boot State** | Inspect state machine state on bootstrap. | Verify `state_machine_get_state()` returns `STATE_IDLE_RUN`. |
| **Run Mode Dispatch** | Dispatch short tap on B1–B4 in `STATE_IDLE_RUN`. | Verify `CMD_RUN_PRESET` triggers `motion_trigger_preset()`, transitioning state to `STATE_RUNNING_MOTION`. |
| **Enter Programming Mode** | Dispatch long press (≥3s) on B1–B4. | Verify transition to `STATE_PROGRAMMING`, target preset set (1–4), `led_set_state(LED_STATE_PROGRAMMING)` called, and all flaps homed. |
| **Channel Cycle & Nudge** | Dispatch B1 short tap in Programming Mode. | Verify `current_channel_idx` increments (0 $\to$ 15 with wrap to 0), and `pca9685_nudge_channel()` is triggered with $15^\circ$ angle. |
| **Flap Staging Toggle** | Dispatch B2 short tap on target channel. | Verify first tap stages channel at $30^\circ$ (`staged_motor_count == 1`), second tap on same channel drops it to $0^\circ$ (`staged_motor_count == 0`). |
| **Parallel 2-Motor Staging** | Stage channel 0 then stage channel 1. | Verify both channels held at $30^\circ$ and `staged_motor_count == 2`. |
| **3-Motor Limit Rejection** | Attempt to stage a 3rd channel when 2 are already staged. | Verify rejection, 3rd channel remains at $0^\circ$, `staged_motor_count == 2`, and `led_set_state(LED_STATE_INPUT_ERROR)` triggered (3 fast flashes). |
| **Step Locking** | Dispatch B3 short tap with 1 or 2 staged motors. | Verify step recorded in buffer, `buffer_routine.step_count` incremented, `pca9685_home_all()` called, `led_set_state(LED_STATE_STEP_LOCKED)` triggered, and `staged_motor_count` reset to 0. |
| **Empty Step Rejection** | Dispatch B3 short tap with 0 staged motors. | Verify step is NOT recorded, `buffer_routine.step_count` remains 0. |
| **Manual Save & Exit** | Dispatch B4 short tap with recorded steps. | Verify `storage_save_routine()` called for target preset, CRC32 checksum computed, `led_set_state(LED_STATE_SAVE_SUCCESS)` triggered (2.0s solid), and state returns to `STATE_IDLE_RUN`. |
| **16-Step Auto-Commit** | Lock 16 consecutive steps in Programming Mode. | Verify automatic commit to NVS upon locking the 16th step, `LED_STATE_SAVE_SUCCESS` triggered, and transition to `STATE_IDLE_RUN`. |
| **Inactivity Timeout Watchdog** | Advance simulated time by 20,000ms with no button input. | Verify timeout triggers, all flaps homed to $0^\circ$, uncommitted buffer discarded, and state machine resets to `STATE_IDLE_RUN`. |
| **Inactivity Timer Reset on Input** | Advance time by 15,000ms, press B1, then advance 10,000ms. | Verify state remains in `STATE_PROGRAMMING` (timer was reset at 15s). |
| **Post-Programming Playback** | Program a custom sequence in Preset 2, exit, and execute Preset 2 in Daily Run Mode. | Verify the newly saved sequence is loaded from NVS and correctly executed by the motion engine. |
| **Full Regression Suite** | Run all unit tests (`make test`). | All test suites (`test_headers`, `test_ui_subsystem`, `test_pca9685`, `test_storage`, `test_motion`, `test_state_machine`) pass with 100% success. |

### 2. ESP-IDF Build Verification

```bash
cd firmware
idf.py build
```
- **Pass Criteria**: Zero compilation errors, zero warnings (`-Wall -Wextra -Werror` clean), SRAM and Flash footprint within budget.

---

## Manual Review & Live Hardware Verification

When flashing firmware to live hardware (`/dev/cu.usbserial-0001`):

1. **Visual Staging Flow Verification**:
   - Hold **B1** for 3 seconds $\rightarrow$ Status LED starts slow blinking (0.5 Hz).
   - Press **B1** $\rightarrow$ Servo 0 twitches $15^\circ$ and returns. Press B1 again $\rightarrow$ Servo 1 twitches $15^\circ$.
   - Press **B2** $\rightarrow$ Servo 1 raises to $30^\circ$ and holds.
   - Press **B1** $\rightarrow$ Servo 2 twitches $15^\circ$. Press **B2** $\rightarrow$ Servo 2 raises to $30^\circ$ and holds alongside Servo 1.
   - Press **B3** $\rightarrow$ Both Servos 1 and 2 drop flat to $0^\circ$, LED flashes twice quickly (Step 1 locked).
   - Press **B1** twice to reach Servo 4 $\rightarrow$ Press **B2** $\rightarrow$ Servo 4 raises to $30^\circ$.
   - Press **B3** $\rightarrow$ Servo 4 drops flat to $0^\circ$, LED flashes twice quickly (Step 2 locked).
   - Press **B4** $\rightarrow$ LED illuminates solid ON for 2.0 seconds, then returns to Idle heartbeat.
2. **Immediate Routine Recall Verification**:
   - Short tap **B1** $\rightarrow$ LED turns solid ON, robot executes Step 1 (Servos 1 & 2 parallel fold $180^\circ$), dwells 300ms, returns to $0^\circ$, then executes Step 2 (Servo 4 fold $180^\circ$), dwells 300ms, returns to $0^\circ$.
3. **20-Second Timeout Verification**:
   - Hold **B2** for 3 seconds $\rightarrow$ Enters Programming Mode (slow blink). Stage a servo to $30^\circ$.
   - Wait 20 seconds without touching any buttons.
   - Flap must drop flat to $0^\circ$, and LED must return to Idle heartbeat. Short tapping B2 must replay the original sequence, confirming the aborted buffer was not saved.

---

## Merge Criteria

- [ ] All 3 feature spec files (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-08-27-phase-6-visual-staging-state-machine/`.
- [ ] Task groups are numbered, ordered logically, and reflect roadmap specifications.
- [ ] Implementation branch `feature/phase-6-visual-staging-state-machine` is created and active.
- [ ] No implementation source files were modified or committed during the spec creation phase.
- [ ] `specs/roadmap.md` status remains unchanged until phase implementation is completed.
