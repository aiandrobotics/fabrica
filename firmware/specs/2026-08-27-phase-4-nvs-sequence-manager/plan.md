# Plan — Phase 4: Non-Volatile Storage (NVS) Sequence Manager

## Overview

Phase 4 implements the persistent storage subsystem for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. This subsystem manages the non-volatile storage and retrieval of multi-step folding routines for Presets 1–4 (`main/storage.h`, `main/storage.c`), providing CRC32 data integrity verification, power-loss resilience, and automatic seeding of factory default routines for standard garments (T-Shirt, Long-Sleeve Shirt, Trousers/Jeans, Towel/Linen).

---

## Task Group 1: NVS Initialization, Namespace Management & CRC32 Integrity Engine (`main/storage.h`, `main/storage.c`)
1. Create `firmware/main/storage.h`:
   - Declare storage constants:
     - `STORAGE_NVS_NAMESPACE` (`"fabrica"`)
     - `STORAGE_INIT_KEY` (`"preset_init"`)
     - `STORAGE_PRESET_KEY_PREFIX` (`"preset_"`)
   - Declare CRC32 helper:
     - `uint32_t storage_compute_crc32(const fold_routine_t *routine)`
   - Declare NVS subsystem initialization:
     - `esp_err_t storage_init(void)`
2. Implement NVS initialization & CRC32 logic in `firmware/main/storage.c`:
   - Implement IEEE 802.3 standard CRC32 algorithm using polynomial `0xEDB88320` covering `offsetof(fold_routine_t, checksum)` bytes (`step_count` + `steps` array).
   - Implement `storage_init()`:
     - Call `nvs_flash_init()`.
     - Check for `ESP_ERR_NVS_NO_FREE_PAGES` or `ESP_ERR_NVS_NEW_VERSION_FOUND`; if encountered, call `nvs_flash_erase()` and re-initialize with `nvs_flash_init()`.
     - Check `"preset_init"` flag; if uninitialized or not present, invoke `storage_init_factory_defaults()` to seed initial routines.

---

## Task Group 2: Binary Routine Serialization & CRUD API Implementation (`main/storage.h`, `main/storage.c`)
1. Extend `firmware/main/storage.h`:
   - Declare CRUD functions:
     - `esp_err_t storage_save_routine(uint8_t preset_id, const fold_routine_t *routine)`
     - `esp_err_t storage_load_routine(uint8_t preset_id, fold_routine_t *routine)`
     - `esp_err_t storage_erase_routine(uint8_t preset_id)`
2. Implement CRUD routines in `firmware/main/storage.c`:
   - Enforce preset ID validation ($1 \le \text{preset\_id} \le 4$), returning `ESP_ERR_INVALID_ARG` for invalid IDs.
   - Enforce input pointer validation (`routine != NULL`), returning `ESP_ERR_INVALID_ARG` for NULL pointers.
   - Implement `storage_save_routine()`:
     - Create copy of routine or calculate CRC32 of payload and update `checksum` field.
     - Open NVS handle (`nvs_open(STORAGE_NVS_NAMESPACE, NVS_READWRITE, &handle)`).
     - Write blob (`nvs_set_blob(handle, key, routine, sizeof(fold_routine_t))`).
     - Commit transaction (`nvs_commit(handle)`).
     - Close NVS handle (`nvs_close(handle)`).
   - Implement `storage_load_routine()`:
     - Open NVS handle (`nvs_open(STORAGE_NVS_NAMESPACE, NVS_READONLY, &handle)`).
     - Read blob (`nvs_get_blob(handle, key, routine, &size)`).
     - If blob does not exist (`ESP_ERR_NVS_NOT_FOUND`), fall back to `storage_get_default_routine(preset_id, routine)`.
     - Calculate CRC32 of loaded payload; if mismatch detected, log error, load factory default routine, and return `ESP_ERR_INVALID_CRC`.
     - Close NVS handle.
   - Implement `storage_erase_routine()`:
     - Open NVS handle with `NVS_READWRITE`.
     - Call `nvs_erase_key(handle, key)` and `nvs_commit(handle)`.
     - Close NVS handle.

---

## Task Group 3: Factory Default Sequences & Boot-Time Seeding Logic (`main/storage.h`, `main/storage.c`)
1. Extend `firmware/main/storage.h`:
   - Declare factory preset API:
     - `esp_err_t storage_init_factory_defaults(void)`
     - `esp_err_t storage_get_default_routine(uint8_t preset_id, fold_routine_t *routine)`
2. Implement factory default routines in `firmware/main/storage.c`:
   - Define static hardcoded structures:
     - **Preset 1 (Adult T-Shirt, 3 steps)**:
       - Step 1: 1 motor $\to$ channel 0 (Left fold)
       - Step 2: 1 motor $\to$ channel 1 (Right fold)
       - Step 3: 1 motor $\to$ channel 2 (Bottom fold)
     - **Preset 2 (Long-Sleeve Shirt, 3 steps)**:
       - Step 1: 2 motors $\to$ channels 0 & 1 (Parallel sleeves)
       - Step 2: 1 motor $\to$ channel 2 (Left body)
       - Step 3: 1 motor $\to$ channel 3 (Right body)
     - **Preset 3 (Trousers / Jeans, 2 steps)**:
       - Step 1: 1 motor $\to$ channel 0 (Vertical fold)
       - Step 2: 1 motor $\to$ channel 1 (Horizontal bottom fold)
     - **Preset 4 (Towel / Linen, 3 steps)**:
       - Step 1: 1 motor $\to$ channel 0 (Half fold)
       - Step 2: 1 motor $\to$ channel 1 (Quarter fold)
       - Step 3: 1 motor $\to$ channel 2 (Final press fold)
   - Implement `storage_init_factory_defaults()`:
     - Save all 4 default routines via `storage_save_routine()`.
     - Set `"preset_init"` flag to `1` in NVS to prevent overwriting user modifications on subsequent boots.

---

## Task Group 4: Host Verification Harness, Mock NVS Storage & Integrated Test Suite (`test/test_storage.c`, `Makefile`, `main.c`, `CMakeLists.txt`)
1. Create `firmware/test/test_storage.c`:
   - Implement a host-compilable C test harness with simulated in-memory NVS key-value store:
     - Validate `storage_compute_crc32()` correctness against known test vectors.
     - Validate bit-mutation sensitivity (flipping any single bit in `steps` or `step_count` alters the computed CRC32).
     - Validate full round-trip `storage_save_routine()` and `storage_load_routine()` for Presets 1–4.
     - Validate CRC mismatch detection and fallback to factory defaults when simulated storage blob is corrupted.
     - Validate boundary checks (preset IDs $<1$ or $>4$, NULL pointers).
     - Validate `storage_erase_routine()` removing keys and subsequent load falling back to defaults.
     - Validate `storage_init_factory_defaults()` and first-boot `"preset_init"` detection.
2. Update `firmware/Makefile`:
   - Add `test_storage` target to `make test` recipe.
3. Update `firmware/main/CMakeLists.txt`:
   - Register `storage.c` in component sources (`SRCS`) and include `nvs_flash` in component dependencies (`REQUIRES`).
4. Update `firmware/main/main.c`:
   - Call `storage_init()` during startup bootstrap.
   - Log loaded preset status and step counts via `ESP_LOGI`.
5. Validate ESP-IDF build:
   - Run `idf.py build` to ensure clean compilation with 0 warnings and 0 errors.
