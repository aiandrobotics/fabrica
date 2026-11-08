# Plan: Phase 11 — End-to-End Firmware BLE Validation & App Store Test App Playbook

## Task Group 1: Mock BLE Central Integration Suite (`test/test_ble_integration.c`)
1. **Dual-OS Mock Central Test Harness**:
   - Construct simulated mobile OS BLE client models:
     - **iOS (`CoreBluetooth`)**: Initiates ATT MTU exchange up to 185B, relies on peripheral security request (`ble_gap_security_initiate`) for SMP pairing, and resolves RPAs.
     - **Android (`BluetoothGatt`)**: Starts at 23B MTU, accepts peripheral-initiated MTU exchange up to 512B, and exercises offset-sliced GATT Long Reads (`ATT_READ_BLOB_REQ`).
2. **Implement 17 End-to-End Protocol Test Cases**:
   - Verify GAP primary advertisement payload ($\le 31\text{B}$ legacy limit with 128-bit `0000FAB0-...` Service UUID) and scan response (`Fabrica-XXXX` name).
   - Verify Device Information Service (`0x180A`) and Generic Attribute Service Changed (`0x1801` / `0x2A05`) discovery.
   - Verify peripheral-initiated connection parameter update compliance (`15ms–30ms` interval, `0` latency, `4000ms` supervision).
   - Verify Hold-to-Pair security: unbonded rejection outside window, 3s button hold (`CMD_ENTER_BLE_PAIRING`) opening 120s window, SMP bonding, RPA resolution across simulated 15-minute rotations, 4-device FIFO eviction, and `B1 + B4` 5s bond factory reset (`CMD_CLEAR_BLE_BONDS`).
   - Verify `CMD_IDENTIFY_ROBOT` (`0x0E`) 3.0s LED pulse train restoring base state.
   - Verify reading the 212-byte 4-button configuration table from `FAB3` and validating factory defaults and CRC32 checksums.
   - Verify writing custom sequences to Button 1 using full 54B/55B and compact variable-length payloads on `FAB3` and `FAB1` (`0x0A`), verifying auto-zero-padding, CRC32 computation, NVS persistence, and `FAB3` notify push.
   - Verify stateless raw routine execution (`CMD_RUN_RAW_SEQUENCE`, `0x01`) without modifying NVS presets (`active_button_id == 0`).
   - Verify empty preset protection (`step_count == 0` rejected with `CMD_STATUS_ERR_INVALID_STEP`) and out-of-bounds motor/channel rejection (`CMD_STATUS_ERR_MOTOR_BOUNDS`).
   - Verify mid-motion concurrent command rejection (`CMD_STATUS_ERR_BUSY`) at ingress on Core 1 without queueing.
   - Verify real-time `FAB2` 31-byte telemetry streaming during motion (10 Hz rate, live `channel_angles[16]`, step progress $0\% \to 100\%$, final completion packet with `CMD_STATUS_OK`, and return to 1 Hz idle rate).
   - Verify `CMD_JOG_MOTOR_ANGLE` (`0x0D`) via `Write Without Response`: `STATE_CALIBRATING` transition, live angle updates, busy rejection during motion/E-stop, 10s thermal de-energize cutoff, and 15s inactivity auto-home to `STATE_IDLE_RUN`.
   - Verify wireless `CMD_EMERGENCY_STOP` (`0x03`) and `CMD_STOP_SEQUENCE` (`0x02`) mid-sweep: `<50ms` Core 1 fast-path preemption, immediate 16-channel homing to $0^\circ$, `STATE_ESTOP` latching, and recovery via `0x02`.
   - Verify physical button tap (`B1–B4`) triggers execution and connected central receives live 10 Hz `FAB2` telemetry notifications.
   - Verify `CMD_RESTORE_FACTORY_PRESETS` (`0x0C`) resets all 4 slots in NVS with `FAB3` notification.

## Task Group 2: Concurrency, Disconnect Safety & 200-Cycle Endurance Stress Test
1. **Multi-Source Concurrency Arbitration**:
   - Simulate simultaneous physical button presses and BLE GATT writes, verifying that the motion engine processes commands deterministically without race conditions or memory corruption.
2. **Abrupt Disconnect Safety**:
   - Verify disconnecting BLE central mid-fold allows the active sequence to finish safely and return cleanly to `STATE_IDLE_RUN`.
   - Verify disconnecting BLE central during `STATE_CALIBRATING` immediately de-energizes/homes all jogged channels back to $0^\circ$ and exits calibration mode without waiting for timeouts.
3. **200-Cycle Continuous Endurance Run**:
   - Execute 200 consecutive automated fold routines with active 10 Hz telemetry streaming, periodic `FAB3` configuration updates, and simulated RPA reconnections.
   - Assert zero memory leaks, zero state machine invariant violations, and zero stuck states.

## Task Group 3: App Store Test App Playbook & Build Integration
1. **Off-the-Shelf App Store Test App Playbook (`firmware/README.md`)**:
   - Document complete hardware testing cheat sheet for **nRF Connect for Mobile** and **LightBlue** on iOS and Android.
   - Provide visual GATT hierarchy and UUID reference table.
   - Provide copy-paste hexadecimal command strings for all opcodes (`0x00–0x11`) in both full and compact formats.
   - Document step-by-step pairing procedure, custom sequence programming recipe, calibration jog walkthrough, and 31-byte telemetry decoding table.
2. **Build and Test Automation**:
   - Update `firmware/Makefile` with the new `test_ble_integration` target.
   - Run `make test` across all 11 test suites and assert 100% pass rate.
   - Run `idf.py build` to confirm clean compilation and zero warnings.
