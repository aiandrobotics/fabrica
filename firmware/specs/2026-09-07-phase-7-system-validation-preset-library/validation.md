# Validation — Phase 7: End-to-End System Validation, Stress Testing & Preset Library

## Required Checks

The implementation of Phase 7 must be validated through automated host stress tests, full regression suites, and ESP-IDF target compilation.

### 1. Automated Host Unit & Stress Tests (`test/test_e2e_stress.c`)

| Test Suite / Case | Description | Pass Criteria |
|---|---|---|
| **Factory Preset Verification** | Load and inspect all 4 factory presets from `storage.c`. | Presets 1–4 match exact garment sequences (T-Shirt, Long-Sleeve Shirt, Trousers, Towel), step counts (3, 4, 2, 3), and CRC32 validity. |
| **100-Cycle Endurance Test** | Execute 100 consecutive fold sequences cycling through Presets 1–4. | All 100 routines execute to completion without state machine desync, timeout faults, or memory leaks (heap delta = 0 bytes). |
| **Mid-Sweep E-Stop (Outward Sweep)** | Inject `CMD_EMERGENCY_STOP` while servo is sweeping $0^\circ \to 180^\circ$. | Motion halts immediately, all 16 channels drop to $0^\circ$, `LED_STATE_ESTOP` triggered, abort latency $<50\text{ms}$. |
| **Mid-Sweep E-Stop (Fold Dwell)** | Inject `CMD_EMERGENCY_STOP` while servo is dwelling at $180^\circ$ (300ms hold). | Motion halts immediately, flap returns to $0^\circ$, routine aborted. |
| **Mid-Sweep E-Stop (Return Sweep)** | Inject `CMD_EMERGENCY_STOP` while servo is sweeping $180^\circ \to 0^\circ$. | PWM pulses reset, all channels homed flat to $0^\circ$. |
| **Mid-Sweep E-Stop (Inter-Step Delay)** | Inject `CMD_EMERGENCY_STOP` during the 200ms inter-step settling delay. | Next step is canceled, robot aborts immediately to `STATE_IDLE_RUN`. |
| **NVS Single-Bit Bit-Rot Recovery** | Invert single byte in stored NVS preset blob. | `storage_load_routine()` detects CRC32 mismatch (`ESP_ERR_INVALID_CRC`), prevents corrupted playback, and reloads default factory preset. |
| **NVS Partial Write Truncation** | Simulate size truncation of NVS preset blob. | Read returns `ESP_ERR_INVALID_SIZE`, reloads clean default routine. |
| **Rapid Mode Invariant Stress** | Rapidly toggle Run Mode, Programming Mode, and E-Stop over 50 iterations. | System never deadlocks, state transitions remain deterministic, all servos remain flat ($0^\circ$) when idle. |
| **Full Regression Suite** | Execute `make test` across all 7 test suites. | `test_headers`, `test_ui_subsystem`, `test_pca9685`, `test_storage`, `test_motion`, `test_state_machine`, and `test_e2e_stress` pass with 100% success. |

### 2. ESP-IDF Target Compilation Check

```bash
cd firmware
idf.py build
```
- **Pass Criteria**:
  - Zero compilation errors.
  - Zero compiler warnings (`-Wall -Wextra -Werror` clean).
  - Internal DRAM free $\ge 120\text{ KB}$ for future Phase 8 wireless connectivity.

---

## Manual Review & Live Hardware Verification

When flashing firmware to live hardware (`/dev/cu.usbserial-0001`):

1. **Factory Preset Execution Verification**:
   - Tap **B1** $\rightarrow$ Robot executes Preset 1 (Adult T-Shirt): Left Flap (Ch 0) $180^\circ$ fold, Right Flap (Ch 1) $180^\circ$ fold, Bottom Flap (Ch 2) $180^\circ$ fold.
   - Tap **B2** $\rightarrow$ Robot executes Preset 2 (Long-Sleeve Shirt): Parallel sleeve fold (Ch 0 & Ch 1 simultaneously), then body folds.
   - Tap **B3** $\rightarrow$ Robot executes Preset 3 (Trousers / Jeans): Vertical fold (Ch 0) then bottom fold (Ch 2).
   - Tap **B4** $\rightarrow$ Robot executes Preset 4 (Towel / Linen): Quarter fold sequence.
2. **Physical E-Stop Preemption**:
   - Trigger Preset 2. While flaps are actively lifting mid-air, press any of the 4 buttons.
   - **Pass Criteria**: Servos immediately drop flat to table ($0^\circ$), motion terminates within $<50\text{ms}$, and Status LED delivers 5 rapid flashes (`LED_STATE_ESTOP`).
3. **Power Loss & Flash Persistence**:
   - Power-cycle the unit during operation. Verify on reboot that system boots to `STATE_IDLE_RUN` with soft heartbeat and factory presets fully functional.
4. **Documentation Audit**:
   - Verify `firmware/README.md` includes accurate GPIO pin assignments, I2C addresses, power supply specifications, and step-by-step operating instructions.

---

## Merge Criteria

- [ ] All 3 feature spec files (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-09-07-phase-7-system-validation-preset-library/`.
- [ ] Task groups are numbered, ordered logically, and reflect roadmap specifications.
- [ ] Working branch `feature/phase-7-system-validation-preset-library` is active.
- [ ] No implementation code was modified during spec creation.
- [ ] `specs/roadmap.md` status remains unchanged until phase implementation is completed.
