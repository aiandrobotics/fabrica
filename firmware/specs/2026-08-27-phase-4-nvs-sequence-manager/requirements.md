# Requirements — Phase 4: Non-Volatile Storage (NVS) Sequence Manager

## Scope

Phase 4 implements the persistent storage subsystem for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. It provides reliable, power-loss tolerant non-volatile storage and retrieval of multi-step folding sequences for Presets 1 through 4 (`main/storage.h`, `main/storage.c`).

Key deliverables include:
1. **NVS Partition Initialization & Management**: Initialization of the ESP-IDF Non-Volatile Storage (NVS) flash subsystem (`nvs_flash_init()`) with automatic recovery and partition erasure when encountering corrupted partitions or version upgrades (`ESP_ERR_NVS_NO_FREE_PAGES` / `ESP_ERR_NVS_NEW_VERSION_FOUND`).
2. **CRC32 Integrity Validation Engine**: Standard IEEE 802.3 CRC32 checksum calculation over sequence payloads to detect flash corruption, incomplete writes, or bit-rot before dispatching sequences to the motion engine.
3. **Sequence CRUD APIs**: Robust routines for saving (`storage_save_routine`), loading (`storage_load_routine`), and erasing (`storage_erase_routine`) serialized `fold_routine_t` structures with CRC verification and graceful fallbacks.
4. **Factory Preset Seeding**: Seeding standard factory folding routines (Adult T-Shirt, Long-Sleeve Shirt, Trousers/Jeans, Towel/Linen) on initial first boot or explicit factory reset.
5. **Host-Based Unit Test Suite & Mock Flash Harness (`test/test_storage.c`)**: Mocked NVS storage verifying CRC32 calculations, serialization round-trips, bit-corruption detection, and boundary conditions under host GCC/Clang builds.

---

## Decisions & Technical Specifications

### 1. NVS Namespace & Key Architecture

| Parameter | Value | Description |
|---|---|---|
| **NVS Namespace** | `"fabrica"` | Dedicated NVS namespace for Fabrica sequence profiles (max 15 chars) |
| **Preset 1 Key** | `"preset_1"` | NVS blob key for Preset 1 folding routine |
| **Preset 2 Key** | `"preset_2"` | NVS blob key for Preset 2 folding routine |
| **Preset 3 Key** | `"preset_3"` | NVS blob key for Preset 3 folding routine |
| **Preset 4 Key** | `"preset_4"` | NVS blob key for Preset 4 folding routine |
| **Init Flag Key** | `"preset_init"` | `uint8_t` flag (`0x01` = initialized) to track factory seeding |

### 2. Sequence Binary Serialization Schema (`command.h`)

The storage module serializes and deserializes the fixed-size `fold_routine_t` binary structure defined in `main/command.h`:

```c
typedef struct {
    uint8_t motor_count;                     /* Number of active motors (1 or 2) */
    uint8_t motor_ids[MAX_MOTORS_PER_STEP];  /* Zero-indexed servo IDs (0 to 15) */
} fold_step_t;

typedef struct {
    uint8_t step_count;                       /* Number of steps (1 to 16) */
    fold_step_t steps[MAX_STEPS_PER_ROUTINE]; /* Array of sequence steps */
    uint32_t checksum;                        /* CRC32 integrity checksum */
} fold_routine_t;
```

#### Memory Layout & Size:
- `fold_step_t`: $1 \text{ byte (motor\_count)} + 2 \times 1 \text{ byte (motor\_ids)} = 3 \text{ bytes}$.
- `fold_routine_t`: $1 \text{ byte (step\_count)} + 16 \times 3 \text{ bytes (steps)} + 4 \text{ bytes (checksum)} = 53 \text{ bytes}$ (or struct-padded to 56 bytes depending on 32-bit alignment).
- Storage blob size: `sizeof(fold_routine_t)`.

### 3. CRC32 Checksum Calculation (IEEE 802.3)

- **Polynomial**: `0xEDB88320` (reversed representation of standard polynomial `0x04C11DB7`).
- **Data Range Covered**: Calculated over all bytes of `fold_routine_t` excluding the `checksum` field itself (`offsetof(fold_routine_t, checksum)` bytes: `step_count` + `steps` array).
- **Validation Rule**:
  1. On save: Compute CRC32 of routine payload $\to$ store in `routine->checksum` $\to$ write blob to NVS.
  2. On load: Read blob from NVS $\to$ compute CRC32 of loaded payload $\to$ compare against stored `routine->checksum`.
  3. If computed CRC does not match stored CRC, load fails (`ESP_ERR_INVALID_CRC`) and falls back to default factory routine.

### 4. Factory Default Routines

On first boot (when `"preset_init"` is not present or set to 0), the system seeds the following 4 presets into NVS:

| Preset Slot | Garment Profile | Step Count | Step Details |
|---|---|---|---|
| **Preset 1** | Adult T-Shirt | 3 Steps | **Step 1**: Left fold (Servo 0)<br/>**Step 2**: Right fold (Servo 1)<br/>**Step 3**: Bottom fold (Servo 2) |
| **Preset 2** | Long-Sleeve Shirt | 3 Steps | **Step 1**: Parallel sleeves (Servo 0 & Servo 1 synchronously)<br/>**Step 2**: Left body fold (Servo 2)<br/>**Step 3**: Right body fold (Servo 3) |
| **Preset 3** | Trousers / Jeans | 2 Steps | **Step 1**: Vertical fold (Servo 0)<br/>**Step 2**: Horizontal bottom fold (Servo 1) |
| **Preset 4** | Towel / Linen | 3 Steps | **Step 1**: Half fold (Servo 0)<br/>**Step 2**: Quarter fold (Servo 1)<br/>**Step 3**: Final press fold (Servo 2) |

### 5. API Function Signatures (`main/storage.h`)

```c
#pragma once
#ifndef FABRICA_STORAGE_H
#define FABRICA_STORAGE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"
#include "config.h"
#include "command.h"

#ifdef __cplusplus
extern "C" {
#endif

#define STORAGE_NVS_NAMESPACE        "fabrica"
#define STORAGE_INIT_KEY             "preset_init"
#define STORAGE_PRESET_KEY_PREFIX    "preset_"

/**
 * @brief Initialize the NVS flash subsystem and storage manager.
 *        Automatically recovers and formats if partition is truncated/corrupted.
 *        Seeds factory defaults if first boot is detected.
 * @return ESP_OK on success, or appropriate error code.
 */
esp_err_t storage_init(void);

/**
 * @brief Save a folding routine to NVS flash for the given preset ID (1 to 4).
 *        Calculates and updates the CRC32 checksum before writing.
 * @param preset_id Preset slot index (1 to 4).
 * @param routine Pointer to routine structure to save.
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if preset_id or routine invalid.
 */
esp_err_t storage_save_routine(uint8_t preset_id, const fold_routine_t *routine);

/**
 * @brief Load a folding routine from NVS flash for the given preset ID (1 to 4).
 *        Verifies CRC32 integrity checksum. Falls back to factory default if invalid.
 * @param preset_id Preset slot index (1 to 4).
 * @param routine Pointer to routine structure to populate.
 * @return ESP_OK on success, ESP_ERR_INVALID_CRC if checksum fails (fallback loaded).
 */
esp_err_t storage_load_routine(uint8_t preset_id, fold_routine_t *routine);

/**
 * @brief Erase a specific preset routine from NVS flash.
 * @param preset_id Preset slot index (1 to 4).
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG on bad index.
 */
esp_err_t storage_erase_routine(uint8_t preset_id);

/**
 * @brief Initialize or re-seed all 4 presets with default factory sequences.
 * @return ESP_OK on success.
 */
esp_err_t storage_init_factory_defaults(void);

/**
 * @brief Populate a routine structure with hardcoded factory default sequence.
 * @param preset_id Preset slot index (1 to 4).
 * @param routine Pointer to routine structure to populate.
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG on bad index.
 */
esp_err_t storage_get_default_routine(uint8_t preset_id, fold_routine_t *routine);

/**
 * @brief Calculate standard IEEE 802.3 CRC32 checksum over routine payload.
 * @param routine Pointer to routine structure.
 * @return 32-bit CRC checksum.
 */
uint32_t storage_compute_crc32(const fold_routine_t *routine);

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_STORAGE_H */
```

---

## Constraints

- **Thread-Safety & Handle Management**: NVS handle opened and closed per transaction or protected with FreeRTOS mutex to avoid race conditions between UI tasks (Core 1) and potential background wireless synchronization.
- **Strict Preset ID Validation**: Only preset IDs $1 \le \text{preset\_id} \le 4$ are permitted. Any index $<1$ or $>4$ must immediately return `ESP_ERR_INVALID_ARG`.
- **Validation Before Execution**: `storage_load_routine` must never return uninitialized memory or corrupted data. In the event of CRC failure or unprogrammed slot, it must fall back to the safe factory default.
- **Power-Loss Tolerance**: Writes use atomic NVS blob set & commit operations (`nvs_set_blob` followed by `nvs_commit`).
- **Host Testability**: CRC32 calculation, validation logic, and storage CRUD abstraction must compile and execute cleanly under host GCC/Clang test runners without hardware ESP-IDF dependencies via mock implementations.

---

## Non-Goals

- Direct servo actuation or I2C communication (Phase 3 PCA9685 Driver & Phase 5 Motion Engine).
- Button scanning or debouncing (Phase 2 UI Subsystem).
- Live trajectory sequencing or dwell execution (Phase 5 Motion Engine).
- Wireless preset synchronization over BLE/Wi-Fi (Phase 8 Mobile App Integration).

---

## Context

Phase 4 establishes the persistent data layer connecting the visual staging workflow of Phase 6 (which creates and saves custom folding sequences) with the daily run execution of Phase 5 (which reads and plays back saved presets on 1-touch button taps).
