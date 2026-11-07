# Plan — Phase 8: Wireless Transport: NimBLE GATT Server & iOS/Android Interop

## Overview

Phase 8 implements the dedicated Bluetooth Low Energy (BLE) wireless transport subsystem (`ble_transport.h`, `ble_transport.c`) on **Core 1** using the **Apache NimBLE** stack for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**.

This milestone provides native iOS (`CoreBluetooth`) and Android (`BluetoothGatt`) BLE interoperability directly from the firmware, enabling complete testing and verification with existing App Store BLE scanner apps (**nRF Connect for Mobile** and **LightBlue**) without requiring custom mobile application code.

Key goals include:
1. Configuring ESP-IDF (`sdkconfig.defaults`, `main/CMakeLists.txt`) for Apache NimBLE pinned to Core 1, updating `command.h` with `__attribute__((packed))` wire structures (`3B` step, `53B` routine, `31B` telemetry), and adding BLE timing/security constants in `config.h`.
2. Extending the Status LED engine (`led.h`, `led.c`) with `LED_STATE_BLE_CONNECTED` and `LED_STATE_IDENTIFY`, and extending the 4-button subsystem (`buttons.c`, `state_machine.c`) with the 5-second `B1 + B4` simultaneous chord hold for hardware BLE bond factory reset (`CMD_CLEAR_BLE_BONDS`).
3. Implementing the NimBLE GAP, SMP, and GATT server (`ble_transport.h`, `ble_transport.c`) featuring 31-byte split advertising, peripheral-initiated connection parameter updates (`15.0ms–30.0ms`), peripheral- and central-initiated 512-byte ATT MTU negotiation, Hold-to-Pair 120s authorization window with peripheral-initiated SMP "Just Works" + IRK bonding, Device Information Service (`0x180A`), Generic Attribute Service (`0x1801` / `0x2A05`), and the custom Fabrica GATT Service (`0000FAB0-...` with `FAB1`, `FAB2`, `FAB3` and `0x2901` User Description descriptors).
4. Validating all Phase 8 functionality with a comprehensive host unit test suite (`test/test_ble_transport.c`), clean ESP-IDF compilation (`idf.py build`), and live iOS/Android verification using nRF Connect / LightBlue.

---

## Task Group 1: SDK Configuration, Packed Wire Structures & Command Schema (`sdkconfig.defaults`, `main/CMakeLists.txt`, `main/config.h`, `main/command.h`)
1. Update `firmware/sdkconfig.defaults` to enable Apache NimBLE on Core 1:
   - Enable `CONFIG_BT_ENABLED=y`, `CONFIG_BT_NIMBLE_ENABLED=y`, `CONFIG_BT_NIMBLE_PINNED_TO_CORE_1=y`, and `CONFIG_BT_NIMBLE_HOST_TASK_STACK_SIZE=4096`.
   - Configure `CONFIG_BT_NIMBLE_ATT_PREFERRED_MTU=512`, `CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1`, `CONFIG_BT_NIMBLE_MAX_BONDS=4`, and `CONFIG_BT_NIMBLE_NVS_PERSIST=y`.
   - Enable LE Secure Connections and privacy/RPA resolution: `CONFIG_BT_NIMBLE_SM_LEGACY=y`, `CONFIG_BT_NIMBLE_SM_SC=y`, `CONFIG_BT_NIMBLE_RPA_TIMEOUT=900`.
2. Update `firmware/main/CMakeLists.txt`:
   - Register `ble_transport.c` in `SRCS`.
   - Add `bt` and `nvs_flash` to component requirements (`PRIV_REQUIRES` / `REQUIRES`).
3. Update `firmware/main/config.h` with BLE transport, connection parameter, and bond-reset constants:
   - `BUTTON_BOND_RESET_MS` (`5000` ms for simultaneous `B1 + B4` hold).
   - `BLE_ADV_INTERVAL_MS` (`100` ms fast advertising).
   - `BLE_CONN_INTERVAL_MIN_MS` (`15.0f` ms / `12` units), `BLE_CONN_INTERVAL_MAX_MS` (`30.0f` ms / `24` units), `BLE_CONN_SLAVE_LATENCY` (`0`), `BLE_SUPERVISION_TIMEOUT_MS` (`4000` ms / `400` units).
   - `BLE_PREFERRED_MTU` (`512` bytes) and `BLE_MAX_BONDS` (`4` devices).
4. Update `firmware/main/command.h`:
   - Apply `__attribute__((packed))` to `fold_step_t` (exact 3 bytes: `1B motor_count` + `2B motor_ids`) and `fold_routine_t` (exact 53 bytes: `1B step_count` + `48B steps` + `4B checksum`).
   - Append Phase 8–10 command types to `cmd_type_t` after `CMD_SYNC_PRESETS = 8` (preserving existing enum values `0..8`): `CMD_STOP_SEQUENCE`, `CMD_IDENTIFY_ROBOT`, `CMD_SET_TELEMETRY_STREAM`, `CMD_CLEAR_BLE_BONDS`.
   - Define `cmd_status_t` (`CMD_STATUS_OK = 0`, `CMD_STATUS_ERR_BUSY = 1`, `CMD_STATUS_ERR_INVALID_STEP = 2`, `CMD_STATUS_ERR_MOTOR_BOUNDS = 3`, `CMD_STATUS_ERR_ROUTINE_FULL = 4`, `CMD_STATUS_ERR_CRC_MISMATCH = 5`, `CMD_STATUS_ERR_INVALID_ARG = 6`).
   - Add `stream_enable` field to `cmd_payload_t`.

---

## Task Group 2: Visual Feedback Extensions & Hardware Bond Factory Reset (`main/led.h`, `main/led.c`, `main/buttons.h`, `main/buttons.c`, `main/state_machine.c`)
1. Extend the Status LED pattern engine (`main/led.h`, `main/led.c`):
   - Add `LED_STATE_BLE_CONNECTED` (1.0s solid ON, transient, `return_to_prior_base = true`) and `LED_STATE_IDENTIFY` (3 fast double-blinks: `100ms ON / 100ms OFF / 100ms ON / 700ms OFF` $\times 3 = 3000\text{ms}$, transient, `return_to_prior_base = true`).
2. Implement 5-second `B1 + B4` simultaneous hold chord detection (`main/buttons.h`, `main/buttons.c`):
   - Track simultaneous active-low state on `B1` (index 0) and `B4` (index 3).
   - While both `B1` and `B4` are held together, suppress the 3-second single-button `GESTURE_LONG_PRESS` (`CMD_ENTER_BLE_PAIRING`) on both channels.
   - When `B1 + B4` continuous hold reaches `BUTTON_BOND_RESET_MS` (`5000ms`), trigger `GESTURE_BOND_RESET` once per hold and dispatch `CMD_CLEAR_BLE_BONDS` to `xCommandQueue`.
3. Update `main/state_machine.c` to handle Phase 8 commands:
   - `CMD_ENTER_BLE_PAIRING`: Open the 120-second pairing window, set `LED_STATE_BLE_PAIRING`, and invoke `ble_transport_enter_pairing_mode()` so a 3s physical button hold always takes priority (disconnecting any active central and immediately restarting GAP advertising).
   - `CMD_CLEAR_BLE_BONDS`: Invoke `ble_transport_clear_bonds()`, close any active pairing window, and trigger `LED_STATE_INPUT_ERROR` (3 fast flashes) confirmation.
   - `CMD_IDENTIFY_ROBOT`: Trigger `led_set_state(LED_STATE_IDENTIFY)` (accepted in both `STATE_IDLE_RUN` and `STATE_RUNNING_MOTION` since `LED_STATE_IDENTIFY` restores prior base state).

---

## Task Group 3: NimBLE GAP, SMP Security & GATT Server Implementation (`main/ble_transport.h`, `main/ble_transport.c`, `main/main.c`)
1. Create `main/ble_transport.h` and `main/ble_transport.c` with dual-target support (`#ifdef ESP_PLATFORM` real NimBLE stack and `#else` deterministic host simulation mock for unit tests):
   - **Dynamic Device Name & Advertising Split**:
     - Derive `"Fabrica-XXXX"` from the last 2 bytes of the ESP32 Bluetooth MAC address (`esp_read_mac(..., ESP_MAC_BT)`).
     - Build the 21-byte Primary Advertisement packet: Flags (`0x06`, 3B) + Complete 128-bit Service UUID (`0000FAB0-0000-1000-8000-00805F9B34FB`, 18B) $\le 31\text{B}$ limit for iOS `CoreBluetooth` background/filtered scanning.
     - Build the 17-byte Scan Response packet: Complete Local Name (`"Fabrica-XXXX"`, 14B) + Tx Power Level (3B) for immediate human-readable discovery in nRF Connect and LightBlue on iOS and Android.
     - Configure 100ms fast advertising (`itvl_min = 0x00A0`, `itvl_max = 0x00A0`), stopping advertising while 1 central is connected and automatically restarting advertising upon disconnect.
   - **Firmware-Initiated Connection Parameter & ATT MTU Negotiation**:
     - Configure preferred ATT MTU to 512 bytes (`ble_att_set_preferred_mtu(512)`).
     - Upon `BLE_GAP_EVENT_CONNECT`, proactively call `ble_gattc_exchange_mtu(conn_handle, ...)` so Android devices upgrade from the default 23-byte MTU automatically, while handling iOS central-initiated MTU exchanges cleanly (`BLE_GAP_EVENT_MTU`).
     - Schedule/initiate `ble_gap_update_params(conn_handle, &params)` (after a 1.5s post-connect stabilization delay) requesting `itvl_min = 12` (`15.0ms`), `itvl_max = 24` (`30.0ms`), `latency = 0`, and `supervision_timeout = 400` (`4000ms`).
   - **Hold-to-Pair Security, Native SMP Bonding & RPA Resolution**:
     - Configure NimBLE Security Manager (`ble_hs_cfg`): `sm_io_cap = BLE_HS_IO_NO_INPUT_OUTPUT`, `sm_bonding = 1`, `sm_mitm = 0`, `sm_sc = 1`, `sm_our_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID`, `sm_their_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID`, and initialize NVS bond storage (`ble_store_config_init()`).
     - Upon `BLE_GAP_EVENT_CONNECT`:
       - Check if peer address/IRK matches an existing bond in NVS (`ble_gap_conn_find` + bond store lookup).
       - If bonded: call `ble_gap_security_initiate(conn_handle)` to encrypt the link and pulse `LED_STATE_BLE_CONNECTED`.
       - If unbonded and `state_machine_is_ble_pairing() == true`: allow connection, call `ble_gap_security_initiate(conn_handle)` to trigger the native iOS/Android OS pairing prompt, evict the oldest bond if bond count $\ge 4$ (`ble_store_util_delete_oldest_peer()`), close the pairing window upon `BLE_GAP_EVENT_ENC_CHANGE` success, and pulse `LED_STATE_BLE_CONNECTED`.
       - If unbonded and `state_machine_is_ble_pairing() == false`: immediately reject and terminate the connection (`ble_gap_terminate(conn_handle, BLE_ERR_REM_USER_CONN_TERM)`).
   - **GATT Services, Characteristics & `0x2901` User Descriptors**:
     - Initialize Generic Attribute Service (`0x1801` with Service Changed `0x2A05` via `ble_svc_gatt_init()`) and Generic Access Service (`0x1800` via `ble_svc_gap_init()`).
     - Register Device Information Service (`0x180A`): Model Number (`0x2A24`: `"Fabrica-DevKit-v1"`), Firmware Revision (`0x2A26`: `"v1.13.0"`), and Manufacturer Name (`0x2A29`: `"Fabrica Robotics"`).
     - Register Fabrica Primary Service (`0000FAB0-0000-1000-8000-00805F9B34FB`):
       1. `FAB1` (`0000FAB1-...`): `BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_WRITE_NO_RSP` + `0x2901` User Description (`"Fabrica Control Point (FAB1)"`). Parses wire opcodes (`0x00–0x03`, `0x0A–0x11`), supports both full and compact sequence payloads, invokes `motion_emergency_stop()` on Core 1 fast-path for `0x02`/`0x03`, and dispatches `command_t` (`SOURCE_BLE`) to `xCommandQueue`.
       2. `FAB2` (`0000FAB2-...`): `BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY` + CCCD (`0x2902`) + `0x2901` User Description (`"Fabrica Status & Telemetry (FAB2)"`). Serves 31-byte `telemetry_packet_t` reads (with offset slicing) and notifications.
       3. `FAB3` (`0000FAB3-...`): `BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY` + CCCD (`0x2902`) + `0x2901` User Description (`"Fabrica Button Sequences 1-4 (FAB3)"`).
          - GATT Read returns the 212-byte ($4 \times 53\text{B}$) table of Presets 1–4 from NVS (supporting offset-sliced Long Reads).
          - GATT Write rejects writes during active motion (`motion_is_busy()` / `STATE_RUNNING_MOTION`) with `CMD_STATUS_ERR_BUSY`; accepts 212-byte full table writes, 54-byte single-button writes (`[1B preset_id][53B fold_routine_t]`), and compact variable-length single-button writes (`[1B preset_id][1B step_count][3B * step_count steps]`, 5–50 bytes); auto-zero-pads unused steps, auto-computes IEEE 802.3 CRC32 when `checksum == 0` (or compact format), validates non-zero CRC32 (`CMD_STATUS_ERR_CRC_MISMATCH`), commits to NVS, sets `LED_STATE_SAVE_SUCCESS`, and pushes a `FAB3` notification to subscribed centrals.
2. Integrate `ble_transport_start(s_command_queue)` into `main/main.c` startup sequence on Core 1 (named `ble_transport_start` to avoid colliding with NimBLE's internal `void ble_transport_init(void)` HCI symbol).

---

## Task Group 4: Host Unit Test Suite & Build Verification (`test/test_ble_transport.c`, `Makefile`)
1. Update existing unit tests (`test/test_headers.c`, `test/test_ui_subsystem.c`, `test/test_state_machine.c`) if needed to verify exact packed struct sizes (`sizeof(fold_step_t) == 3`, `sizeof(fold_routine_t) == 53`, `sizeof(telemetry_packet_t) == 31`) while keeping 100% backward compatibility with all 566 existing checks.
2. Create `firmware/test/test_ble_transport.c` exercising:
   - GATT service/characteristic/descriptor (`0x2901`, `0x2902`) registration and DIS (`0x180A`) read responses.
   - Primary advertisement ($\le 31\text{B}$, 21B exact) and scan response (`Fabrica-XXXX` name, 17B exact) packet construction.
   - Peripheral-initiated MTU (`512B`) and Apple-compliant connection parameter (`15.0ms–30.0ms`, `0` latency, `4000ms` timeout) negotiation.
   - Strict Hold-to-Pair enforcement: unbonded connection termination outside the 120s window, 3s button hold opening the 120s pairing window, SMP security initiation + IRK bonding during the window, seamless reconnect of bonded peers across simulated RPA address rotations outside the window, 4-bond capacity with 5th-device FIFO eviction, and `B1 + B4` 5-second chord hold bond factory reset (verifying suppression of the 3s single-button pairing trigger).
   - `FAB3` GATT Read (212-byte table + offset-sliced Long Read at 23B MTU), `FAB3` GATT Write (212B table, 54B single-button with `checksum == 0` auto-CRC and corrupted non-zero CRC rejection, compact variable-length single-button payload expansion), active motion write lock (`CMD_STATUS_ERR_BUSY`), and `FAB3` change notification.
   - `FAB1` command ingestion (`0x00–0x03`, `0x0A–0x0E`, `0x10–0x11`) into `xCommandQueue` with `SOURCE_BLE`, plus `LED_STATE_BLE_CONNECTED` and `LED_STATE_IDENTIFY` verification.
3. Register `test_ble_transport` in `firmware/Makefile` and verify `make test` and `idf.py build` pass with zero warnings or errors.
