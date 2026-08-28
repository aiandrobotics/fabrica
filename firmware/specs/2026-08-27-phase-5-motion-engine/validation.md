# Validation — Phase 5: Motion Engine & Daily Run Mode Execution

## Required Checks

The implementation of Phase 5 must be validated against automated host test suites and ESP-IDF compilation checks.

### 1. Automated Host Unit Tests (`firmware/test/test_motion.c`)

| Test Case | Description | Pass Criteria |
|---|---|---|
| **Single Motor Step Execution** | Execute a single-motor step (`ch 2`). | Verify `pca9685_set_servo_angle(2, 180.0f)` called, followed by 300ms dwell, return to `0.0f`, and LED state set to `LED_STATE_RUNNING`. |
| **Parallel Dual-Motor Step Execution** | Execute a 2-motor step (`ch 0` and `ch 1`). | Verify `pca9685_set_multi_servo_angles(0x0003, 180.0f)` called synchronously, followed by 300ms dwell and return to `0.0f`. |
| **Multi-Step Routine Sequencing** | Execute 3-step routine (e.g. Preset 1). | Verify steps execute sequentially with 200ms `INTER_STEP_DELAY_MS` between steps and `pca9685_home_all()` on completion. |
| **Empty Preset Protection** | Trigger preset with 0 steps. | Verify `motion_trigger_preset()` returns `ESP_ERR_INVALID_STATE`, zero servo commands issued, and `led_set_state(LED_STATE_INPUT_ERROR)` triggered. |
| **Invalid Preset Bounds** | Trigger preset 0 or preset 5. | Verify rejection with `ESP_ERR_INVALID_ARG`. |
| **Emergency Stop Preemption** | Trigger E-Stop during active 300ms fold dwell. | Verify sequence immediately halts within $<50\text{ms}$, all channels homed to `0.0f`, and `led_set_state(LED_STATE_ESTOP)` triggered. |
| **Re-Entrancy & Busy Guard** | Trigger new run command while motion is running. | Verify second command rejected or queued safely without corrupting active trajectory. |
| **Full Regression Suite** | Run all unit tests (`make test`). | All test suites (`test_headers`, `test_ui_subsystem`, `test_pca9685`, `test_storage`, `test_motion`) pass with 100% success. |

### 2. ESP-IDF Build Verification

```bash
cd firmware
idf.py build
```
- **Pass Criteria**: Zero compilation errors, zero warnings (`-Wall -Wextra -Werror` clean), SRAM and Flash footprint within budget.

---

## Manual Review & Live Hardware Verification

When flashing firmware to live hardware (`/dev/cu.usbserial-0001`):

1. **Preset Execution Visual Verification**:
   - Tap **B1**: Status LED turns solid ON, Servo 0 sweeps $0^\circ \to 180^\circ \to 0^\circ$, Servo 1 sweeps $0^\circ \to 180^\circ \to 0^\circ$, Servo 2 sweeps $0^\circ \to 180^\circ \to 0^\circ$, then LED returns to soft heartbeat (IDLE).
   - Tap **B2**: Servo 0 and Servo 1 sweep synchronously to $180^\circ$, hold for 300ms, return to $0^\circ$, followed by Servo 2 then Servo 3.
2. **Emergency Stop (E-Stop) Latency Verification**:
   - While a multi-step routine is running, tap any button (B1–B4).
   - Servos must immediately stop forward stroke, return flat to $0^\circ$, and the Status LED must emit 5 rapid flashes (50ms ON / 50ms OFF).
3. **Empty Preset Indication**:
   - Erase a preset slot or configure a 0-step routine, then tap the corresponding button.
   - Status LED must emit 3 fast error flashes (60ms ON / 60ms OFF) with zero servo jitter or movement.

---

## Merge Criteria

- [ ] All 3 feature spec files (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-08-27-phase-5-motion-engine/`.
- [ ] Task groups are numbered, ordered logically, and reflect the roadmap specifications.
- [ ] Implementation branch `feature/phase-5-motion-engine` is created and active.
- [ ] No implementation source files were modified or committed during the spec phase.
- [ ] `specs/roadmap.md` status remains unchanged until phase completion.
