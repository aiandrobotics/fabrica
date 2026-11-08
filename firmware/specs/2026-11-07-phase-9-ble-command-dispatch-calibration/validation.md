# Validation — Phase 9: BLE Command Dispatch, Remote Execution & Servo Calibration

## Required Checks

Phase 9 requires passing automated host unit tests (`make test` with `-Wall -Wextra -Werror`) across the new `test/test_remote_cmd.c` suite and all 8 existing suites, plus a clean ESP-IDF target firmware build (`idf.py build`). Live hardware verification on ESP32 using **nRF Connect** / **LightBlue** is documented under Manual Review.

### 1. Automated Host Unit Tests (`test/test_remote_cmd.c` & Full Suite)

```bash
cd firmware
make test
```

| Test Case | Description | Pass Criteria |
|---|---|---|
| **`FAB1` Wire Opcode & Malformed Payload Parsing** | Exercise opcodes `0x00–0x03`, `0x0A–0x0E`, `0x10`, `0x11`, unknown opcodes (`0x0F`, `0xFF`), and truncated/oversized frames. | Valid frames dispatch `SOURCE_BLE` commands with `CMD_STATUS_OK`; malformed lengths or unknown opcodes reject immediately with `CMD_STATUS_ERR_INVALID_ARG` and push a `FAB2` status notification. |
| **Stateless Raw Sequence (`0x01`) Full & Compact Unpacking** | Send both 54-byte full `[0x01][53B routine]` and variable-length compact `[0x01][step_count][3B * N]` frames. | Routine executes cleanly in RAM, reports `active_button_id = 0` during motion, auto-computes CRC32 when compact or `checksum == 0`, and leaves NVS Presets 1–4 untouched. |
| **Sequence Bounds & CRC32 Validation** | Test `step_count == 0`, `step_count == 17`, `motor_count == 0`, `motor_count == 3`, `channel == 16`, and corrupted non-zero CRC32. | Returns exact error codes: `CMD_STATUS_ERR_INVALID_STEP` (`0` steps), `CMD_STATUS_ERR_ROUTINE_FULL` (`>16` steps), `CMD_STATUS_ERR_MOTOR_BOUNDS` (bad motor count/channel), and `CMD_STATUS_ERR_CRC_MISMATCH` (bad CRC). |
| **Ingress Busy Re-Entrancy Guard** | Simulate active motion (`STATE_RUNNING_MOTION` / `motion_is_busy()`) and send `0x00`, `0x01`, `0x0A`, `0x0C`, `0x0D`, and `FAB3` writes. | Every mutating/motion command is rejected at Core 1 ingress with `CMD_STATUS_ERR_BUSY` (`FAB2` notified) without queueing or disturbing active motion. |
| **Empty NVS Preset Rejection (`0x00`)** | Attempt `0x00` on an unconfigured/zero-step preset slot (`step_count == 0`). | Rejected with `CMD_STATUS_ERR_INVALID_STEP`, flashes `LED_STATE_INPUT_ERROR`, and remains in `STATE_IDLE_RUN`. |
| **100% Routine Completion Notification** | Subscribe to `FAB2` (`CCCD = 0x0001`) and execute a preset (`0x00`) or raw sequence (`0x01`) to completion. | Emits a `FAB2` notification at final step finish with `step_progress_pct = 100` and `last_cmd_status = CMD_STATUS_OK` before transitioning cleanly to `STATE_IDLE_RUN`. |
| **Fast-Path E-Stop (`0x03`), Latched `STATE_ESTOP` & Recovery** | Trigger `0x03` (or button tap during motion), attempt `0x00`/`0x0D` while latched, then clear via `0x02` and via physical button tap. | `motion_emergency_stop()` fires immediately; all 16 servos home to $0^\circ$; `LED_STATE_ESTOP` flashes; `system_state == STATE_ESTOP` (`2`) and `error_code` `BIT2` latch; `0x00`/`0x0D` reject with `CMD_STATUS_ERR_BUSY`; `0x02` or button tap clears back to `STATE_IDLE_RUN` (`0`). |
| **Wireless Preset Save (`0x0A`) & Factory Reset (`0x0C`)** | Save custom compact/full routine via `0x0A`, verify NVS & `FAB3` notify, then trigger `0x0C`. | `0x0A` updates target slot, flashes `LED_STATE_SAVE_SUCCESS`, and pushes 212B `FAB3` notify; `0x0C` restores all 4 factory defaults in NVS, homes servos, flashes `LED_STATE_SAVE_SUCCESS`, and pushes 212B `FAB3` notify. |
| **Live Servo Jog (`0x0D`) & Bounds Interlock** | Send `0D 02 5A` (`ch 2 -> 90°`), plus out-of-bounds `0D 10 5A` (`ch 16`) and `0D 00 B5` (`181°`). | Valid jog transitions `STATE_IDLE_RUN` $\rightarrow$ `STATE_CALIBRATING` (`4`), sets channel 2 to $90^\circ$, and pushes `FAB2` with `channel_angles[2] == 90`; out-of-bounds channel or angle $>180^\circ$ rejects with `CMD_STATUS_ERR_MOTOR_BOUNDS`. |
| **Calibration 10s Thermal Cutoff & Wake-on-Jog** | Enter `STATE_CALIBRATING`, step `state_machine_tick()` to `10000ms`, then send another `0x0D` jog at `12000ms`. | At `10000ms`, `PCA9685_MODE1_SLEEP` bit is set (`pca9685_sleep(true)`) while staying in `STATE_CALIBRATING`; jog at `12000ms` wakes PCA9685 (`PCA9685_MODE1_SLEEP` cleared), updates servo angle, and resets timers. |
| **Calibration 15s Auto-Home & Disconnect / Button Exit** | Test (a) `15000ms` inactivity timeout, (b) `0x02` Stop command, (c) physical button tap, and (d) BLE central disconnect while in `STATE_CALIBRATING` (including while thermally asleep). | All 4 paths wake PCA9685 if asleep, home all 16 channels to $0^\circ$ (`102` counts), return `system_state` to `STATE_IDLE_RUN`, and emit a `FAB2` notification. |
| **Full Regression Suite (9 Suites)** | Run all host suites (`test_headers`, `test_ui_subsystem`, `test_pca9685`, `test_storage`, `test_motion`, `test_state_machine`, `test_e2e_stress`, `test_ble_transport`, `test_remote_cmd`). | 100% pass rate with zero compiler warnings under `-Wall -Wextra -Werror`. |

### 2. ESP-IDF Target Compilation Check

```bash
# Ensure ESP-IDF environment is activated (e.g., . $IDF_PATH/export.sh)
cd firmware
idf.py build
```

- **Pass Criteria**:
  - Compiles and links `remote_cmd.c`, `ble_transport.c`, `state_machine.c`, `buttons.c`, and all ESP-IDF components with **0 errors and 0 warnings**.
  - Flash binary size remains well within partition limits with $\ge 190\text{ KB}$ free internal SRAM.

---

## Manual Review & Optional Live Hardware Verification (ESP32 + nRF Connect)

After flashing the ESP32 (`idf.py -p <PORT> flash monitor`) and connecting with **nRF Connect** (subscribed to `FAB2` and `FAB3` notifications):

1. **Stateless Raw Sequence (`0x01`) & 100% Completion Push**:
   - Write compact hex `01 02 01 00 00 01 01 00` to `FAB1` (`0000FAB1-...` value row, not `0x2901`).
   - Verify Flap 0 then Flap 1 fold without altering saved Button 1–4 presets, and `FAB2` pushes a completion packet with `step_progress_pct = 0x64` (`100%`) and `last_cmd_status = 0x00`.
2. **Latched Wireless E-Stop (`0x03`) & Clear (`0x02` / Button Tap)**:
   - Start Preset 1 (`00 01`), then immediately send `03` to `FAB1`.
   - Verify servos halt and home within `<50ms`, Status LED flashes 5 rapid pulses (`LED_STATE_ESTOP`), and `FAB2` reports `system_state = 0x02` (`STATE_ESTOP`) with `error_code = 0x04` (`BIT2`).
   - Attempt `00 01` while latched $\rightarrow$ verify immediate rejection (`last_cmd_status = 0x01` `ERR_BUSY`).
   - Send `02` (or tap physical Button B1) $\rightarrow$ verify `FAB2` reports `system_state = 0x00` (`STATE_IDLE_RUN`) and `error_code = 0x00`.
3. **Live Servo Calibration (`0x0D`), 10s Thermal Sleep & 15s Auto-Home**:
   - Write `0D 00 5A` to `FAB1` $\rightarrow$ verify Channel 0 moves to $90^\circ$ and `FAB2` reports `system_state = 0x04` (`STATE_CALIBRATING`).
   - Wait 10 seconds $\rightarrow$ verify serial log reports PCA9685 thermal sleep cutoff (`pca9685_sleep(true)`) and servo torque relaxes.
   - Wait 5 more seconds (15s total) or disconnect BLE in nRF Connect $\rightarrow$ verify PCA9685 wakes, Channel 0 returns to $0^\circ$, and state returns to `STATE_IDLE_RUN`.

---

## Merge Criteria

- [x] Dated spec directory `firmware/specs/2026-11-07-phase-9-ble-command-dispatch-calibration/` contains `plan.md`, `requirements.md`, and `validation.md`.
- [x] Working branch `feature/phase-9-ble-command-dispatch-calibration` is active and up to date with `main`.
- [x] `make test` passes 100% across all 9 host unit test suites (`763 / 763` checks total, including `82 / 82` in `test/test_remote_cmd.c`) with `-Wall -Wextra -Werror`.
- [x] `idf.py build` succeeds cleanly with zero warnings or errors (`fabrica_firmware.bin` = `0x7c130` bytes, 52% app partition free).
- [x] `specs/roadmap.md` Phase 9 is marked complete (`✅`) upon implementation completion.
