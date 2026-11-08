# Validation: Phase 11 — End-to-End Firmware BLE Validation & App Store Test App Playbook

## Required Checks

### 1. Automated Host Integration Suite (`test/test_ble_integration.c`)
- **Dual-OS Simulation**:
  - Simulate iOS `CoreBluetooth` client connecting with 185B MTU, handling peripheral security request, and reconnecting across 15-minute RPA rotations.
  - Simulate Android `BluetoothGatt` client connecting with 23B MTU, performing peripheral-initiated MTU exchange (512B), and reading the 212-byte `FAB3` table via offset-sliced GATT Long Reads (`ATT_READ_BLOB_REQ`).
- **All 17 Integration Protocol Vectors**:
  - Vectors 1–17 defined in `requirements.md` must all execute and pass.
- **200-Cycle Endurance Stress Test**:
  - Continuous execution of 200 fold cycles with active 10 Hz telemetry streaming, periodic `FAB3` sequence updates, and simulated RPA reconnections.
  - Assert zero memory leaks and state invariants preserved.

### 2. Host Build & Regression Suite
- Run `make test` from `firmware/` and assert all 11 test suites pass with 100% success rate under `-Wall -Wextra -Werror`:
  1. `test_headers`
  2. `test_ui_subsystem`
  3. `test_pca9685`
  4. `test_storage`
  5. `test_motion`
  6. `test_state_machine`
  7. `test_e2e_stress`
  8. `test_ble_transport`
  9. `test_remote_cmd`
  10. `test_telemetry`
  11. `test_ble_integration`

### 3. ESP-IDF Target Compilation
- Execute `idf.py build` targeting ESP32 Dev Board v1.
- Assert 0 compilation errors and 0 compiler warnings.
- Confirm binary footprint remains well within partition limits ($\ge 50\%$ flash free).

## Manual Review

1. **Hardware Validation with nRF Connect for Mobile (iOS & Android)**:
   - Follow the step-by-step playbook in `firmware/README.md`.
   - Hold physical Button 1 for 3 seconds to enter pairing mode (`LED_STATE_BLE_PAIRING`).
   - Connect from nRF Connect; verify bond prompt and bond persistence.
   - Subscribe to notifications on `FAB2` and `FAB3`.
   - Send `0x0E` on `FAB1` to visually identify the robot (3-second locator pulse train).
   - Read the 212-byte 4-button table from `FAB3` and verify factory defaults.
   - Write a custom compact sequence to Button 1 (`[0x01][0x02][0x01 0x00 0x00][0x01 0x01 0x00]`).
   - Trigger Preset 1 (`0x00 01`) and observe live 10 Hz telemetry updates on `FAB2`.
   - Trigger Emergency Stop (`0x03`) and verify immediate halt and homing within $<50\text{ms}$.
   - Clear E-Stop using `0x02` or physical button tap.
   - Jog servo Channel 0 to $45^\circ$ (`0x0D 00 2D`) and verify live movement.
   - Trigger Factory Reset (`0x0C`) and confirm all presets return to factory defaults.

## Merge Criteria
- All 11 host unit and integration test suites pass (`make test`).
- Clean `idf.py build` with zero warnings and zero errors.
- Comprehensive hardware playbook added to `firmware/README.md`.
- All tasks in `plan.md` checked off.
- Feature branch `feature/phase-11-e2e-ble-validation-playbook` pushed and cleanly merged into `main`.
