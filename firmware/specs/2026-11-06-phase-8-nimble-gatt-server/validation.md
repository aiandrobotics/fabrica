# Validation — Phase 8: Wireless Transport: NimBLE GATT Server & iOS/Android Interop

## Required Checks

Phase 8 must be validated through automated host unit tests (`make test`), ESP-IDF target compilation (`idf.py build`), and live BLE verification on iOS and Android using off-the-shelf App Store BLE scanner apps (**nRF Connect for Mobile** or **LightBlue**).

### 1. Automated Host Unit Tests (`test/test_ble_transport.c`)

| Test Case | Description | Pass Criteria |
|---|---|---|
| **Packed Wire Struct Sizes** | Verify `sizeof(fold_step_t)`, `sizeof(fold_routine_t)`, and `sizeof(telemetry_packet_t)`. | Exact byte sizes: `3` bytes, `53` bytes (`4 * 53 = 212` bytes), and `31` bytes with zero compiler padding. |
| **GAP Split Advertisement Payloads** | Build primary advertisement and scan response packets and inspect byte layouts. | Primary advertisement is `21` bytes ($\le 31\text{B}$) containing Flags (`0x06`) and 128-bit UUID `0000FAB0-...`; scan response is `17` bytes ($\le 31\text{B}$) containing `"Fabrica-XXXX"` and Tx Power. |
| **GATT Service & `0x2901` / `0x2902` Descriptors** | Inspect registered GATT table for DIS (`0x180A`), GATT (`0x1801`), and Fabrica (`0000FAB0-...`). | Model (`"Fabrica-DevKit-v1"`), Firmware Rev (`"v1.13.0"`), Manufacturer (`"Fabrica Robotics"`), CCCDs (`0x2902`), and User Descriptions (`0x2901`) on `FAB1`, `FAB2`, and `FAB3` resolve accurately. |
| **Peripheral-Initiated MTU & Connection Params** | Simulate iOS central-initiated MTU exchange and Android default 23B connection. | Firmware negotiates up to 512B MTU, initiates peripheral MTU exchange for Android, and requests `15.0ms–30.0ms` interval, `0` latency, `4000ms` timeout. |
| **Unbonded Rejection Outside Pairing Window** | Simulate unbonded central connection when `state_machine_is_ble_pairing() == false`. | Connection is immediately rejected and terminated (`ble_gap_terminate`); LED does not pulse connected. |
| **3s Hold-to-Pair & SMP IRK Bonding** | Dispatch `CMD_ENTER_BLE_PAIRING`, connect unbonded central, complete SMP encryption. | `LED_STATE_BLE_PAIRING` activates on 3s hold; peripheral initiates SMP security; bond is stored in NVS; pairing window closes; `LED_STATE_BLE_CONNECTED` pulses for 1.0s. |
| **RPA Rotation Auto-Reconnect** | Reconnect bonded peer with a rotated Resolvable Private Address (RPA) outside pairing window. | Peer IRK resolves rotated RPA to existing bond; connection succeeds without button hold; `LED_STATE_BLE_CONNECTED` pulses. |
| **4-Bond Capacity & FIFO Eviction** | Pair 5 distinct centrals sequentially across pairing windows. | NVS bond store caps at 4 devices; 1st (oldest) bond is evicted when 5th device pairs; devices 2–5 remain bonded. |
| **`B1 + B4` 5s Hardware Bond Reset** | Hold `B1` and `B4` simultaneously for `5000ms` in `buttons_update_channel` / chord tracker. | Single-button 3s `CMD_ENTER_BLE_PAIRING` is suppressed; `CMD_CLEAR_BLE_BONDS` fires at 5000ms; all NVS bonds are erased; `LED_STATE_INPUT_ERROR` (3 fast flashes) triggers. |
| **`FAB3` Read & Offset-Sliced Long Read** | Read `FAB3` with `MTU = 512` (single read) and `MTU = 23` (chunked `ATT_READ_BLOB_REQ` offsets). | Both return the exact 212-byte ($4 \times 53\text{B}$) preset table matching NVS storage. |
| **`FAB3` Write (Full, Compact & Auto-CRC)** | Write 212B table, 54B single-button (`checksum == 0`), and compact payload (`01 02 01 00 00 01 01 00`). | Unused steps are zero-padded, IEEE 802.3 CRC32 is auto-computed, NVS updates, `LED_STATE_SAVE_SUCCESS` triggers, and `FAB3` notify is emitted. Corrupted non-zero CRC is rejected with `CMD_STATUS_ERR_CRC_MISMATCH`. |
| **`FAB3` Active Motion Write Lock** | Attempt `FAB3` write while `STATE_RUNNING_MOTION` / `motion_is_busy()` is active. | Write is rejected with `CMD_STATUS_ERR_BUSY`; NVS preset remains unmodified. |
| **`FAB1` Command Ingress & Identify** | Write `FAB1` opcodes (`0x00`, `0x02`, `0x03`, `0x0A`, `0x0C`, `0x0D`, `0x0E`, `0x10`) and step LED patterns. | Commands enqueue with `SOURCE_BLE`; `0x0E` pulses `LED_STATE_IDENTIFY` (3 double-blinks restoring prior base); unknown opcode (`0x0F`) rejected with `CMD_STATUS_ERR_INVALID_ARG`. |
| **Full Regression Suite** | Run `make test` across all 8 test suites. | 100% pass rate across `test_headers`, `test_ui_subsystem`, `test_pca9685`, `test_storage`, `test_motion`, `test_state_machine`, `test_e2e_stress`, and `test_ble_transport`. |

### 2. ESP-IDF Target Compilation Check

```bash
cd firmware
idf.py build
```
- **Pass Criteria**:
  - Clean compilation with zero errors and zero warnings (`-Wall -Wextra -Werror`).
  - NimBLE host and GATT server linked cleanly with free internal SRAM $\ge 190\text{ KB}$ at runtime.

---

## Manual Review & Live Hardware Verification (nRF Connect / LightBlue on iOS & Android)

After flashing the ESP32 Dev Board (`idf.py -p /dev/cu.usbserial-* flash monitor`):

1. **Discovery & Unbonded Protection Check**:
   - Open **nRF Connect** or **LightBlue** on iOS and Android.
   - Verify `"Fabrica-XXXX"` appears with primary Service UUID `0000FAB0-0000-1000-8000-00805F9B34FB`.
   - Tap **Connect** without holding any button on the robot $\rightarrow$ verify the ESP32 rejects/terminates the unbonded connection immediately.
2. **3-Second Hold-to-Pair & Bonding Check**:
   - Hold **B1** on the robot for **3 seconds** $\rightarrow$ verify Status LED enters fast double-blink (`LED_STATE_BLE_PAIRING`).
   - Tap **Connect** in nRF Connect / LightBlue $\rightarrow$ accept the native iOS/Android Bluetooth pairing prompt; verify Status LED pulses solid ON for 1.0s (`LED_STATE_BLE_CONNECTED`) and disconnects/reconnects thereafter succeed automatically without holding a button.
3. **Descriptor & Characteristic Verification**:
   - Verify Device Information Service (`0x180A`) reads `"Fabrica-DevKit-v1"`, `"v1.13.0"`, and `"Fabrica Robotics"`.
   - Verify `FAB1`, `FAB2`, and `FAB3` display their `0x2901` User Description names (`"Fabrica Control Point (FAB1)"`, `"Fabrica Status & Telemetry (FAB2)"`, `"Fabrica Button Sequences 1-4 (FAB3)"`).
4. **Control Point (`FAB1`) & Button Config (`FAB3`) Hex Checks**:
   - Write hex `0E` to `FAB1` $\rightarrow$ verify Status LED performs 3 fast double-blinks (`LED_STATE_IDENTIFY`).
   - Write hex `00 01` to `FAB1` $\rightarrow$ verify Preset 1 executes on the robot.
   - Subscribe to notifications on `FAB3` and write compact hex `01 02 01 00 00 01 01 00` to `FAB3` $\rightarrow$ verify Status LED illuminates solid ON for 2.0s (`LED_STATE_SAVE_SUCCESS`) and `FAB3` emits the updated 212-byte notification.
   - Hold **B1 + B4** simultaneously for **5 seconds** $\rightarrow$ verify Status LED flashes 3 times (`LED_STATE_INPUT_ERROR`) and stored BLE bonds are cleared.

---

## Merge Criteria

- [x] All 3 feature spec files (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-11-06-phase-8-nimble-gatt-server/`.
- [x] Task groups in `plan.md` are numbered and ordered from configuration/headers to subsystem extensions, NimBLE GATT server implementation, and verification.
- [x] Working branch `feature/phase-8-nimble-gatt-server` is active.
- [x] Host unit test suite (`make test`) passes 100% across all 8 suites (`681 / 681` checks, including `115 / 115` in `test_ble_transport.c`).
- [x] ESP-IDF target build (`idf.py build`) compiles and links cleanly with zero warnings or errors (`fabrica_firmware.bin` = `0x7b420` bytes, 52% partition free).
- [x] `specs/roadmap.md` Phase 8 marked complete (`✅`).
