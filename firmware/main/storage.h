#pragma once
#ifndef FABRICA_STORAGE_H
#define FABRICA_STORAGE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef ESP_PLATFORM
#include "esp_err.h"
#else
/* Standard error codes for host testing harness */
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK                  0
#endif
#ifndef ESP_FAIL
#define ESP_FAIL                -1
#endif
#ifndef ESP_ERR_NO_MEM
#define ESP_ERR_NO_MEM          0x101
#endif
#ifndef ESP_ERR_INVALID_ARG
#define ESP_ERR_INVALID_ARG     0x102
#endif
#ifndef ESP_ERR_INVALID_STATE
#define ESP_ERR_INVALID_STATE   0x103
#endif
#ifndef ESP_ERR_INVALID_SIZE
#define ESP_ERR_INVALID_SIZE    0x104
#endif
#ifndef ESP_ERR_NOT_FOUND
#define ESP_ERR_NOT_FOUND       0x105
#endif
#ifndef ESP_ERR_INVALID_CRC
#define ESP_ERR_INVALID_CRC     0x109
#endif
#ifndef ESP_ERR_NVS_NO_FREE_PAGES
#define ESP_ERR_NVS_NO_FREE_PAGES 0x110d
#endif
#ifndef ESP_ERR_NVS_NEW_VERSION_FOUND
#define ESP_ERR_NVS_NEW_VERSION_FOUND 0x1110
#endif
#ifndef ESP_ERR_NVS_NOT_FOUND
#define ESP_ERR_NVS_NOT_FOUND   0x1102
#endif
#endif

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
 *
 * @return ESP_OK on success, or ESP-IDF error code.
 */
esp_err_t storage_init(void);

/**
 * @brief Save a folding routine to NVS flash for the given preset ID (1 to 4).
 *        Calculates and updates the CRC32 checksum before writing.
 *
 * @param preset_id Preset slot index (1 to 4).
 * @param routine Pointer to routine structure to save.
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if preset_id or routine invalid.
 */
esp_err_t storage_save_routine(uint8_t preset_id, const fold_routine_t *routine);

/**
 * @brief Load a folding routine from NVS flash for the given preset ID (1 to 4).
 *        Verifies CRC32 integrity checksum. Falls back to factory default if invalid.
 *
 * @param preset_id Preset slot index (1 to 4).
 * @param routine Pointer to routine structure to populate.
 * @return ESP_OK on success, ESP_ERR_INVALID_CRC if checksum fails (fallback loaded).
 */
esp_err_t storage_load_routine(uint8_t preset_id, fold_routine_t *routine);

/**
 * @brief Erase a specific preset routine from NVS flash.
 *
 * @param preset_id Preset slot index (1 to 4).
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG on bad index.
 */
esp_err_t storage_erase_routine(uint8_t preset_id);

/**
 * @brief Initialize or re-seed all 4 presets with default factory sequences.
 *
 * @return ESP_OK on success.
 */
esp_err_t storage_init_factory_defaults(void);

/**
 * @brief Populate a routine structure with hardcoded factory default sequence.
 *
 * @param preset_id Preset slot index (1 to 4).
 * @param routine Pointer to routine structure to populate.
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG on bad index.
 */
esp_err_t storage_get_default_routine(uint8_t preset_id, fold_routine_t *routine);

/**
 * @brief Calculate standard IEEE 802.3 CRC32 checksum over routine payload.
 *
 * @param routine Pointer to routine structure.
 * @return 32-bit CRC checksum.
 */
uint32_t storage_compute_crc32(const fold_routine_t *routine);

/* ========================================================================= */
/* Test Harness Mock Helper Functions (Host-Only)                            */
/* ========================================================================= */
#ifndef ESP_PLATFORM
void storage_mock_reset(void);
void storage_mock_corrupt_key(const char *key, size_t byte_offset);
bool storage_mock_key_exists(const char *key);
#endif

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_STORAGE_H */
