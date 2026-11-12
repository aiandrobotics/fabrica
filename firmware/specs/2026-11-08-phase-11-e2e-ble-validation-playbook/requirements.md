# Requirements: Phase 11 — End-to-End Firmware BLE Validation & App Store Test App Playbook

## Scope
Phase 11 delivers the complete system-level integration test suite (`test/test_ble_integration.c`) simulating the entire mobile BLE client lifecycle across iOS (`CoreBluetooth`) and Android (`BluetoothGatt`), stress-tests multi-source concurrency and endurance over 200 cycles, and documents an exhaustive hardware validation playbook in `firmware/README.md` enabling immediate testing using off-the-shelf App Store tools (**nRF Connect** and **LightBlue**).

## Decisions

### 1. Dual-OS BLE Central Simulation Architecture
- **iOS (`CoreBluetooth`) Simulation**:
  - Model strict 185-byte ATT MTU exchange.
  - Model iOS behavior of never initiating link security; rely entirely on peripheral security request (`ble_gap_security_initiate`) to trigger SMP pairing.
  - Model 15-minute Resolvable Private Address (RPA) rotation, confirming seamless reconnection via stored IRKs in NVS.
- **Android (`BluetoothGatt`) Simulation**:
  - Model default 23-byte ATT MTU on initial connection.
  - Verify peripheral-initiated MTU exchange (`ble_gattc_exchange_mtu(512)`).
  - Verify fallback to offset-sliced GATT Long Reads (`ATT_READ_BLOB_REQ`) for full 212-byte `FAB3` table access if MTU negotiation were constrained.

### 2. Protocol Integration Coverage (17 Test Vectors)
1. Split GAP advertisement compliance ($\le 31\text{B}$ primary with `0000FAB0-...` Service UUID + `Fabrica-XXXX` scan response).
2. DIS (`0x180A`) and Service Changed (`0x1801` / `0x2A05`) attribute presence.
3. Apple-compliant peripheral connection parameter negotiation (15ms–30ms interval, 0 latency, 4000ms supervision timeout).
4. Hold-to-Pair security: zero-bond boot indefinite auto-pairing, unbonded rejection outside pairing window, 3s button hold entry (120s timed window for multi-device pairing), SMP bonding, RPA resolution across 15-minute rotation, 4-device FIFO eviction, and 5s `B1 + B4` chord hold bond reset with automatic indefinite pairing re-opening.
5. Visual robot locator (`CMD_IDENTIFY_ROBOT`, `0x0E`) 3.0s LED pulse train.
6. Reading the 212-byte 4-button configuration table from `FAB3` (verifying factory defaults & CRC32).
7. Custom sequence programming on `FAB3` and `FAB1` (`0x0A`) in full and compact formats with auto-zero-padding, CRC32 recalculation, and `FAB3` notification.
8. Stateless raw routine preview (`0x01`) in full and compact formats without modifying NVS presets (`active_button_id == 0`).
9. Safety guards: empty preset rejection (`CMD_STATUS_ERR_INVALID_STEP`) and out-of-bounds motor/channel rejection (`CMD_STATUS_ERR_MOTOR_BOUNDS`).
10. Active motion busy locks: ingress rejection of concurrent commands with `CMD_STATUS_ERR_BUSY`.
11. Real-time 31-byte telemetry streaming (`FAB2`, 10 Hz in motion, 1 Hz idle, completion packet with `CMD_STATUS_OK`).
12. Live servo jog calibration (`0x0D`): `STATE_CALIBRATING` transition, live angles, busy rejection during motion, 10s thermal cutoff, 15s inactivity auto-home.
13. Wireless Emergency Stop (`0x03`) and Stop (`0x02`): $<50\text{ms}$ Core 1 fast-path preemption, immediate 16-channel homing, latched `STATE_ESTOP`, and clear via `0x02`.
14. Physical button press execution mirroring to connected central.
15. Factory reset (`0x0C`) resetting all 4 slots with `FAB3` notification.
16. Multi-source concurrency arbitration (simultaneous button presses and BLE writes).
17. Abrupt disconnect safety (finishes motion safely, homes jogged servos immediately).
18. Full factory reset (`0x1F` / B1+B3+B4 10s chord hold) wiping both presets and BLE bonds, disconnecting central, and restarting indefinite pairing mode.

### 3. Endurance & Stability Stress Criteria
- 200 consecutive automated fold cycles with active 10 Hz telemetry streaming and periodic `FAB3` sequence updates.
- Zero FreeRTOS heap memory leaks and zero stack overflows.
- State invariants preserved throughout all transitions.

### 4. Hardware Verification Playbook Format (`firmware/README.md`)
- Ready-to-paste hexadecimal strings for all opcodes (`0x00–0x11`) in both full and compact formats.
- Complete characteristic reference (`FAB1`, `FAB2`, `FAB3`) with UUIDs, descriptors, and write modes (`Write Without Response` vs `Write With Response`).
- Step-by-step pairing walkthrough for **nRF Connect for Mobile** and **LightBlue** on iOS and Android.
- 31-byte telemetry packet byte-by-byte decoder cheat sheet.

## Constraints
1. **Zero External Dependencies**: Host integration test suite must compile cleanly with native `gcc` using standard C libraries (`-Wall -Wextra -Werror`).
2. **Deterministic Execution**: All 17 integration vectors and the 200-cycle endurance test must complete in $<5$ seconds on the host test runner.
3. **Firmware Scope**: All code changes remain within `firmware/` and root documentation (`CHANGELOG.md`, `README.md`).

## Non-goals
- Building native iOS/Android mobile application source code (that belongs in mobile app repositories).
- Cloud / MQTT / Wi-Fi integration.
