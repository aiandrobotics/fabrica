# Validation — Phase 4: Non-Volatile Storage (NVS) Sequence Manager

## Required Checks

### 1. Host-Based Unit Test Suite (`firmware/test/test_storage.c`)
- [ ] Compile and execute host test harness using GCC or Clang:
  ```bash
  gcc -Wall -Wextra -Werror -I./firmware/main -o /tmp/test_storage firmware/main/storage.c firmware/test/test_storage.c && /tmp/test_storage
  ```
- [ ] **CRC32 Calculation & Integrity Verification**:
  - Test CRC32 calculation against known baseline vectors.
  - Verify deterministic CRC generation across identical structs.
  - Verify bit-flip sensitivity: flipping any single bit in `step_count`, `motor_count`, or `motor_ids` produces a distinct CRC32.
- [ ] **Preset CRUD Operations**:
  - Test `storage_save_routine()` successfully serializes and computes CRC for Presets 1, 2, 3, and 4.
  - Test `storage_load_routine()` retrieves exact matching step configurations and valid checksums.
  - Test `storage_erase_routine()` deletes the target key and subsequent load safely falls back to factory defaults.
- [ ] **Corrupt Data & Error Fallbacks**:
  - Test CRC mismatch detection: injecting simulated bit errors into stored NVS blobs triggers `ESP_ERR_INVALID_CRC` and falls back to default factory routine.
  - Test invalid parameter rejection: preset ID $0$ or $>4$ returns `ESP_ERR_INVALID_ARG`.
  - Test NULL pointer rejection: `storage_save_routine(1, NULL)` and `storage_load_routine(1, NULL)` return `ESP_ERR_INVALID_ARG`.
- [ ] **Factory Preset Seeding & Defaults**:
  - Test `storage_get_default_routine()` returns valid configurations for all 4 presets:
    - Preset 1: Adult T-Shirt (3 steps: ch 0, ch 1, ch 2).
    - Preset 2: Long-Sleeve Shirt (3 steps: ch 0+1, ch 2, ch 3).
    - Preset 3: Trousers / Jeans (2 steps: ch 0, ch 1).
    - Preset 4: Towel / Linen (3 steps: ch 0, ch 1, ch 2).
  - Test initial boot seeding sets `"preset_init"` flag to prevent re-seeding over modified user sequences.

### 2. ESP-IDF Build & Compilation Verification
- [ ] Confirm `firmware/main/CMakeLists.txt` registers `storage.c` and includes `nvs_flash` in component requirements.
- [ ] Execute clean ESP-IDF project compilation:
  ```bash
  idf.py build
  ```
- [ ] Verify compilation completes with **0 warnings** and **0 errors** under `-Wall -Wextra`.
- [ ] Confirm memory usage maintains $\ge 120\text{ KB}$ free heap headroom for future wireless networking.

### 3. Integrated Makefile Test Suite
- [ ] Run automated host test suite across all modules:
  ```bash
  make test
  ```
- [ ] Confirm `test_headers`, `test_ui_subsystem`, `test_pca9685`, and `test_storage` all pass with 100% success rate.

---

## Manual Review & Hardware Bench Verification

### 1. Serial Monitor Startup Diagnostics & Preset Loading
- [ ] Flash ESP32 Dev Board and open serial monitor:
  ```bash
  idf.py flash monitor
  ```
- [ ] Verify serial startup logs confirm successful NVS initialization and preset loading:
  ```text
  [STORAGE] NVS flash initialized successfully
  [STORAGE] Factory presets seeded on first boot
  [STORAGE] Preset 1 loaded: Adult T-Shirt (3 steps, CRC: 0x...)
  [STORAGE] Preset 2 loaded: Long-Sleeve Shirt (3 steps, CRC: 0x...)
  [STORAGE] Preset 3 loaded: Trousers / Jeans (2 steps, CRC: 0x...)
  [STORAGE] Preset 4 loaded: Towel / Linen (3 steps, CRC: 0x...)
  ```

### 2. Persistence & Power-Cut Recovery Verification
- [ ] Save a modified folding sequence to Preset 1.
- [ ] Perform hard reset or power cycle of the ESP32.
- [ ] Confirm on boot that the custom Preset 1 sequence is restored identically with valid CRC.

---

## Merge Criteria

- [ ] All three spec documents (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-08-27-phase-4-nvs-sequence-manager/`.
- [ ] Active working branch is `feature/phase-4-nvs-sequence-manager`.
- [ ] Specs align with `firmware/specs/mission.md`, `firmware/specs/tech-stack.md`, and `firmware/specs/roadmap.md`.
- [ ] No implementation code was written during spec creation.
