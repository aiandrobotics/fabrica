# Validation: Phase 10 — Real-Time Telemetry & Button Configuration Sync

## Required Checks

### 1. Automated Host Unit Tests (`test/test_telemetry.c`)
- **Binary Struct Packing & Offsets**:
  - `sizeof(telemetry_packet_t) == 31`.
  - Assert exact byte offset of all 13 fields within `telemetry_packet_t`.
  - Assert Little-Endian representation of multi-byte integers (`elapsed_step_time_ms`, `free_heap_kb`, `sequence_counter`).
- **Adaptive Rate Adaptation**:
  - Verify streaming interval returns 100ms when system state is `STATE_RUNNING_MOTION` or `STATE_CALIBRATING`.
  - Verify streaming interval returns 1000ms when system state is `STATE_IDLE_RUN`, `STATE_ESTOP`, or `STATE_ERROR`.
- **Streaming Enable & Disconnect Gating**:
  - Verify periodic notifications are suppressed when `stream_enabled == false`.
  - Verify periodic notifications are suppressed when central is not connected or CCCD is not subscribed.
  - Verify periodic notifications resume when CCCD is subscribed and `stream_enabled == true`.
  - Verify `CMD_SET_TELEMETRY_STREAM` opcode (`0x11 00` / `0x11 01`) correctly flips stream state.
- **Sequence Counter Monotonicity**:
  - Verify successive telemetry emissions increment `sequence_counter` by 1.
- **Mid-Sweep Progress & Angle Tracking**:
  - Verify `elapsed_step_time_ms` and `step_progress_pct` accurately calculate elapsed time and percentage through mock motion steps.
  - Verify live 16-channel `channel_angles` array correctly reflects `pca9685_get_channel_angle()` values.
- **Button Sync (`FAB3`) Notification**:
  - Verify `ble_transport_notify_fab3()` triggers a 212-byte table notification whenever sequence modifications occur.

### 2. Host Build & Regression Suite
- Run `make test` from `firmware/` and verify all checks pass across all unit test suites (all 10 suites including `test_telemetry.c`) with `-Wall -Wextra -Werror`.

### 3. ESP-IDF Target Compilation
- Execute `idf.py build` targeting ESP32 Dev Board v1.
- Assert 0 compilation errors and 0 compiler warnings.
- Confirm binary footprint remains well within partition limits ($\ge 50\%$ flash free).

## Manual Review

1. **BLE Scanner / nRF Connect Verification**:
   - Connect to `Fabrica-XXXX` in nRF Connect on iOS or Android.
   - Subscribe to notifications on `FAB2` (`0000FAB2-0000-1000-8000-00805F9B34FB`).
   - Observe 1 Hz baseline telemetry stream while idle (`system_state = 0`).
   - Trigger Preset 1 (`0x00 01` on `FAB1`) and observe telemetry rate adaptively increase to 10 Hz with live `elapsed_step_time_ms`, `step_progress_pct`, and rotating servo angles.
   - Observe immediate return to 1 Hz upon completion packet (`step_progress_pct = 100`, `last_cmd_status = OK`).
   - Write `0x11 00` to `FAB1` and verify periodic streaming stops.
   - Write `0x11 01` to `FAB1` and verify periodic streaming resumes.
   - Trigger E-Stop (`0x03` on `FAB1`) and observe immediate `STATE_ESTOP` notification with error bitmask `BIT2` active.

## Merge Criteria
- All 10 host unit test suites pass (`make test`).
- Clean `idf.py build` with zero warnings and zero errors.
- All tasks in `plan.md` checked off.
- Feature branch `feature/phase-10-real-time-telemetry-sync` pushed and cleanly merged into `main`.
