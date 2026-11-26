# Validation — Phase 6: State Machine Coordinator & Minimal Physical Button Interface

> [!NOTE]
> **Architecture Update**: Updated from legacy on-device visual staging checks to match the active production minimal physical UI + BLE configuration state machine in `main/state_machine.c` and `test/test_state_machine.c`.

## Required Checks

The implementation of Phase 6 is validated through automated host unit tests (`make test`) and ESP-IDF target compilation checks.

### 1. Automated Host Unit Tests (`firmware/test/test_state_machine.c`)

| Test Case | Description | Pass Criteria |
|---|---|---|
| **Initial Boot State** | Inspect state machine state on bootstrap. | `state_machine_get_state()` returns `STATE_IDLE_RUN` (`0`) and `active_preset == 0`. |
| **Run Mode Dispatch** | Dispatch short tap on B1–B4 in `STATE_IDLE_RUN`. | `CMD_RUN_PRESET` triggers `motion_trigger_preset()` (`0° -> 165° -> 30° -> 0°`, `900/600/500ms`) and returns cleanly to `STATE_IDLE_RUN`. |
| **Latched E-Stop & Recovery** | Dispatch `CMD_EMERGENCY_STOP` during motion or idle, then clear with `CMD_STOP_SEQUENCE` / button tap. | All 16 servos home to $0^\circ$, `LED_STATE_ESTOP` triggers, `STATE_ESTOP` (`2`) latches, and `CMD_STOP_SEQUENCE` clears back to `STATE_IDLE_RUN`. |
| **Zero-Bond Auto-Pairing & 120s Window** | Test `state_machine_check_initial_pairing()` with 0 bonds vs $\ge 1$ bonds + 3s `CMD_ENTER_BLE_PAIRING`. | 0 bonds keeps pairing open indefinitely (`LED_STATE_BLE_PAIRING`); bonded device opens 120,000ms window and auto-closes upon timeout or bond completion. |
| **Wireless Sequence Save & Restore** | Dispatch `CMD_SET_BUTTON_SEQUENCE` and `CMD_RESTORE_FACTORY_PRESETS`. | Routine persists in NVS with valid CRC32, `LED_STATE_SAVE_SUCCESS` triggers, and `FAB3` notification emits. |
| **Stateless Raw Sequence Preview** | Dispatch `CMD_RUN_RAW_SEQUENCE`. | Executes routine in RAM with `active_preset == 0` without modifying stored NVS presets. |
| **Live Calibration & Watchdogs** | Dispatch `CMD_JOG_MOTOR_ANGLE`, advance ticks to 10s and 15s, and test BLE disconnect / button tap exit. | Transitions to `STATE_CALIBRATING` (`4`), triggers `pca9685_sleep(true)` at 10,000ms, wakes and homes all 16 channels to $0^\circ$ at 15,000ms (or immediately on `0x02` / button tap / BLE disconnect). |
| **Chord Resets (`B1+B4` & `B1+B3+B4`)** | Dispatch `CMD_CLEAR_BLE_BONDS` and `CMD_FACTORY_RESET_ALL`. | Clears NVS bonds (and restores all 4 factory presets + homes servos on full reset) and re-opens indefinite pairing mode. |
| **Full Regression Suite** | Run all unit tests (`make test`). | All 11 test suites (`880 / 880` checks) pass with 100% success under `-Wall -Wextra -Werror`. |

### 2. ESP-IDF Build Verification

```bash
cd firmware
idf.py build
```
- **Pass Criteria**: Zero compilation errors, zero warnings (`-Wall -Wextra -Werror` clean), SRAM and Flash footprint within budget.

---

## Manual Review & Live Hardware Verification

When flashing firmware to live hardware (`idf.py -p <PORT> flash monitor`):

1. **Daily Run Execution**:
   - Short tap **B1** $\rightarrow$ LED turns solid ON, Preset 1 executes all 4 flaps sequentially ($0^\circ \to 165^\circ$ in `900ms`, return & brake at $30^\circ$ in `600ms`, linear soft-landing to $0^\circ$ in `500ms`), then LED returns to soft heartbeat (`LED_STATE_IDLE`).
2. **Physical E-Stop & Clear**:
   - Tap any button mid-fold $\rightarrow$ Flaps abort and home to $0^\circ$ in $<50\text{ms}$, LED flashes 5 rapid pulses (`LED_STATE_ESTOP`), and `STATE_ESTOP` latches until any button is tapped (or BLE `0x02` is sent).
3. **Pairing & Hardware Reset Chords**:
   - Hold any button for **3 seconds** $\rightarrow$ Enters BLE Pairing Mode (`LED_STATE_BLE_PAIRING`).
   - Hold **B1 + B4** for **5 seconds** $\rightarrow$ Clears BLE bonds and re-opens indefinite pairing mode.
   - Hold **B1 + B3 + B4** for **10 seconds** $\rightarrow$ Restores factory presets, clears BLE bonds, homes all 16 servos, and re-opens indefinite pairing mode.
