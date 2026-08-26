# Validation — Phase 1: Project Skeleton, Hardware Configuration & Diagnostics

## Required Checks

### 1. Host-Based Header & Structure Validation (`test/test_headers.c`)
- [ ] Compile host test harness using standard C compiler:
  ```bash
  gcc -Wall -Wextra -Werror -I./main -o /tmp/test_headers firmware/test/test_headers.c && /tmp/test_headers
  ```
- [ ] Verify all constants in `main/config.h`:
  - `STATUS_LED_GPIO == 2`
  - `BTN1_GPIO == 0`, `BTN2_GPIO == 4`, `BTN3_GPIO == 16`, `BTN4_GPIO == 17`
  - `I2C_SDA_GPIO == 21`, `I2C_SCL_GPIO == 22`
  - `MAX_STEPS_PER_ROUTINE == 16`
  - `MAX_MOTORS_PER_STEP == 2`
  - `TOTAL_SERVO_CHANNELS == 16`
  - `BUTTON_DEBOUNCE_MS == 50`
  - `BUTTON_LONG_PRESS_MS == 3000`
- [ ] Verify data structure sizing and alignment in `main/command.h`:
  - `sizeof(fold_step_t)` and struct packing.
  - `sizeof(fold_routine_t)` and struct packing.
  - `sizeof(command_t)` validation.
  - `cmd_source_t` and `cmd_type_t` enumeration coverage.

### 2. ESP-IDF Build & Compilation Verification
- [ ] Ensure `firmware/CMakeLists.txt` and `firmware/main/CMakeLists.txt` conform to ESP-IDF v5.x / v6.x build standards.
- [ ] Execute clean ESP-IDF project build:
  ```bash
  idf.py build
  ```
- [ ] Confirm build completes with **0 compilation errors** and **0 compiler warnings** under `-Wall -Wextra`.
- [ ] Verify binary artifacts (`fabrica_firmware.bin`, `bootloader.bin`, `partition-table.bin`) are generated in the `build/` directory.

### 3. Flash Size & Heap Telemetry Validation
- [ ] Verify `main/main.c` contains diagnostic queries for:
  - `esp_chip_info()`
  - `esp_flash_get_size()`
  - `esp_get_minimum_free_heap_size()`
- [ ] Verify FreeRTOS queue allocation check (`xCommandQueue != NULL`) with appropriate error handling on allocation failure.

---

## Manual Review Steps

### 1. UART Boot Log Output Inspection
- [ ] Connect ESP32 Dev Board over USB serial (`idf.py monitor` @ 115200 bps).
- [ ] Verify console output displays structured diagnostic startup banner:
  ```text
  ============================================================
   Fabrica Cloth Folding Robot - ESP32 Firmware
   Version: 1.0.0 (Phase 1 Skeleton)
  ============================================================
  [INFO] Silicon: ESP32 Rev 3 (2 CPU cores, WiFi/BT BLE)
  [INFO] Flash Size: 4 MB
  [INFO] Initial Free Heap: ~295 KB (Min Free: ~295 KB)
  [INFO] Unified Command Queue Initialized (Depth: 16)
  [INFO] System Ready. Awaiting Subsystem Initialization...
  ```
- [ ] Verify no watchdog timeouts or crash panics during boot.

---

## Merge Criteria

- [ ] All three spec documents (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-08-26-phase-1-project-skeleton/`.
- [ ] The working branch `feature/phase-1-firmware-skeleton` is active and clean.
- [ ] The spec accurately matches the roadmap phase requirements from `firmware/specs/roadmap.md` and user preferences.
- [ ] No implementation code was written during the spec authoring stage.
