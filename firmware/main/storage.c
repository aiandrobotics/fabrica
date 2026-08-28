#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stddef.h>

#include "config.h"
#include "command.h"
#include "storage.h"

#ifdef ESP_PLATFORM
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_STORAGE";
#else
/* Host testing mock storage */
typedef struct {
    char key[32];
    uint8_t data[256];
    size_t size;
    bool exists;
} mock_nvs_entry_t;

#define MOCK_NVS_MAX_ENTRIES 16
static mock_nvs_entry_t s_mock_nvs[MOCK_NVS_MAX_ENTRIES];
#endif

/* ========================================================================= */
/* CRC32 Integrity Checksum Engine (IEEE 802.3 Standard)                     */
/* ========================================================================= */

/**
 * @brief Calculate standard IEEE 802.3 32-bit CRC.
 *        Polynomial: 0xEDB88320 (reversed 0x04C11DB7)
 */
static uint32_t crc32_ieee(const uint8_t *data, size_t len)
{
    uint32_t crc = 0xFFFFFFFFU;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1U) {
                crc = (crc >> 1) ^ 0xEDB88320U;
            } else {
                crc = crc >> 1;
            }
        }
    }
    return ~crc;
}

uint32_t storage_compute_crc32(const fold_routine_t *routine)
{
    if (routine == NULL) {
        return 0;
    }
    /* Calculate CRC over all struct bytes preceding the checksum field */
    size_t payload_len = offsetof(fold_routine_t, checksum);
    return crc32_ieee((const uint8_t *)routine, payload_len);
}

/* ========================================================================= */
/* Helper Functions                                                          */
/* ========================================================================= */

static esp_err_t get_preset_key(uint8_t preset_id, char *key_buf, size_t max_len)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT || key_buf == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    snprintf(key_buf, max_len, "%s%u", STORAGE_PRESET_KEY_PREFIX, (unsigned int)preset_id);
    return ESP_OK;
}

/* ========================================================================= */
/* Factory Default Folding Sequences                                         */
/* ========================================================================= */

esp_err_t storage_get_default_routine(uint8_t preset_id, fold_routine_t *routine)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT || routine == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    memset(routine, 0, sizeof(fold_routine_t));

    switch (preset_id) {
        case 1:
            /* Preset 1: Adult T-Shirt (3 Steps) */
            routine->step_count = 3;
            /* Step 1: Left fold (Servo 0) */
            routine->steps[0].motor_count = 1;
            routine->steps[0].motor_ids[0] = 0;
            /* Step 2: Right fold (Servo 1) */
            routine->steps[1].motor_count = 1;
            routine->steps[1].motor_ids[0] = 1;
            /* Step 3: Bottom fold (Servo 2) */
            routine->steps[2].motor_count = 1;
            routine->steps[2].motor_ids[0] = 2;
            break;

        case 2:
            /* Preset 2: Long-Sleeve Shirt (3 Steps) */
            routine->step_count = 3;
            /* Step 1: Parallel sleeve folds (Servo 0 and Servo 1 synchronously) */
            routine->steps[0].motor_count = 2;
            routine->steps[0].motor_ids[0] = 0;
            routine->steps[0].motor_ids[1] = 1;
            /* Step 2: Left body fold (Servo 2) */
            routine->steps[1].motor_count = 1;
            routine->steps[1].motor_ids[0] = 2;
            /* Step 3: Right body fold (Servo 3) */
            routine->steps[2].motor_count = 1;
            routine->steps[2].motor_ids[0] = 3;
            break;

        case 3:
            /* Preset 3: Trousers / Jeans (2 Steps) */
            routine->step_count = 2;
            /* Step 1: Vertical fold (Servo 0) */
            routine->steps[0].motor_count = 1;
            routine->steps[0].motor_ids[0] = 0;
            /* Step 2: Horizontal bottom fold (Servo 1) */
            routine->steps[1].motor_count = 1;
            routine->steps[1].motor_ids[0] = 1;
            break;

        case 4:
            /* Preset 4: Towel / Linen (3 Steps) */
            routine->step_count = 3;
            /* Step 1: Half fold (Servo 0) */
            routine->steps[0].motor_count = 1;
            routine->steps[0].motor_ids[0] = 0;
            /* Step 2: Quarter fold (Servo 1) */
            routine->steps[1].motor_count = 1;
            routine->steps[1].motor_ids[0] = 1;
            /* Step 3: Final press fold (Servo 2) */
            routine->steps[2].motor_count = 1;
            routine->steps[2].motor_ids[0] = 2;
            break;

        default:
            return ESP_ERR_INVALID_ARG;
    }

    /* Compute CRC for default routine */
    routine->checksum = storage_compute_crc32(routine);
    return ESP_OK;
}

/* ========================================================================= */
/* NVS CRUD Storage Operations                                               */
/* ========================================================================= */

esp_err_t storage_save_routine(uint8_t preset_id, const fold_routine_t *routine)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT || routine == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (routine->step_count > MAX_STEPS_PER_ROUTINE) {
        return ESP_ERR_INVALID_ARG;
    }

    char key[16];
    esp_err_t err = get_preset_key(preset_id, key, sizeof(key));
    if (err != ESP_OK) {
        return err;
    }

    /* Create copy to update checksum */
    fold_routine_t to_save = *routine;
    to_save.checksum = storage_compute_crc32(&to_save);

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    err = nvs_open(STORAGE_NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS namespace '%s' for writing: %s",
                 STORAGE_NVS_NAMESPACE, esp_err_to_name(err));
        return err;
    }

    err = nvs_set_blob(handle, key, &to_save, sizeof(fold_routine_t));
    if (err == ESP_OK) {
        err = nvs_commit(handle);
    }
    nvs_close(handle);

    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Saved Preset %d to NVS (Steps: %d, CRC: 0x%08" PRIX32 ")",
                 preset_id, to_save.step_count, to_save.checksum);
    } else {
        ESP_LOGE(TAG, "Failed to commit Preset %d blob to NVS: %s",
                 preset_id, esp_err_to_name(err));
    }
    return err;
#else
    /* Host Mock Implementation */
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (s_mock_nvs[i].exists && strcmp(s_mock_nvs[i].key, key) == 0) {
            memcpy(s_mock_nvs[i].data, &to_save, sizeof(fold_routine_t));
            s_mock_nvs[i].size = sizeof(fold_routine_t);
            return ESP_OK;
        }
    }
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (!s_mock_nvs[i].exists) {
            strncpy(s_mock_nvs[i].key, key, sizeof(s_mock_nvs[i].key) - 1);
            memcpy(s_mock_nvs[i].data, &to_save, sizeof(fold_routine_t));
            s_mock_nvs[i].size = sizeof(fold_routine_t);
            s_mock_nvs[i].exists = true;
            return ESP_OK;
        }
    }
    return ESP_ERR_NO_MEM;
#endif
}

esp_err_t storage_load_routine(uint8_t preset_id, fold_routine_t *routine)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT || routine == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    char key[16];
    esp_err_t err = get_preset_key(preset_id, key, sizeof(key));
    if (err != ESP_OK) {
        return err;
    }

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    err = nvs_open(STORAGE_NVS_NAMESPACE, NVS_READONLY, &handle);
    if (err != ESP_OK) {
        /* If namespace doesn't exist yet, fall back to safe default */
        storage_get_default_routine(preset_id, routine);
        return err;
    }

    size_t required_size = sizeof(fold_routine_t);
    err = nvs_get_blob(handle, key, routine, &required_size);
    nvs_close(handle);

    if (err != ESP_OK || required_size != sizeof(fold_routine_t)) {
        ESP_LOGW(TAG, "Preset %d not found in NVS (or size mismatch), loading factory default...", preset_id);
        storage_get_default_routine(preset_id, routine);
        return (err == ESP_ERR_NVS_NOT_FOUND) ? ESP_OK : err;
    }
#else
    /* Host Mock Implementation */
    bool found = false;
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (s_mock_nvs[i].exists && strcmp(s_mock_nvs[i].key, key) == 0) {
            if (s_mock_nvs[i].size != sizeof(fold_routine_t)) {
                storage_get_default_routine(preset_id, routine);
                return ESP_ERR_INVALID_SIZE;
            }
            memcpy(routine, s_mock_nvs[i].data, sizeof(fold_routine_t));
            found = true;
            break;
        }
    }
    if (!found) {
        storage_get_default_routine(preset_id, routine);
        return ESP_OK;
    }
#endif

    /* Verify CRC32 Integrity */
    uint32_t computed_crc = storage_compute_crc32(routine);
    if (computed_crc != routine->checksum) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "CRC error on Preset %d! Expected 0x%08" PRIX32 ", Got 0x%08" PRIX32 ". Restoring default...",
                 preset_id, routine->checksum, computed_crc);
#endif
        /* Fall back to safe default routine on corrupted flash data */
        storage_get_default_routine(preset_id, routine);
        return ESP_ERR_INVALID_CRC;
    }

    return ESP_OK;
}

esp_err_t storage_erase_routine(uint8_t preset_id)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }

    char key[16];
    esp_err_t err = get_preset_key(preset_id, key, sizeof(key));
    if (err != ESP_OK) {
        return err;
    }

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    err = nvs_open(STORAGE_NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (err != ESP_OK) {
        return err;
    }

    err = nvs_erase_key(handle, key);
    if (err == ESP_OK) {
        err = nvs_commit(handle);
    }
    nvs_close(handle);
    return err;
#else
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (s_mock_nvs[i].exists && strcmp(s_mock_nvs[i].key, key) == 0) {
            s_mock_nvs[i].exists = false;
            memset(s_mock_nvs[i].data, 0, sizeof(s_mock_nvs[i].data));
            return ESP_OK;
        }
    }
    return ESP_OK;
#endif
}

/* ========================================================================= */
/* Factory Defaults Seeding & Initialization                                 */
/* ========================================================================= */

esp_err_t storage_init_factory_defaults(void)
{
#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Seeding factory default folding presets into NVS...");
#endif

    for (uint8_t id = 1; id <= TOTAL_PRESET_COUNT; id++) {
        fold_routine_t def_routine;
        esp_err_t err = storage_get_default_routine(id, &def_routine);
        if (err != ESP_OK) {
            return err;
        }
        err = storage_save_routine(id, &def_routine);
        if (err != ESP_OK) {
            return err;
        }
    }

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    esp_err_t err = nvs_open(STORAGE_NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (err == ESP_OK) {
        uint8_t init_val = 1;
        nvs_set_u8(handle, STORAGE_INIT_KEY, init_val);
        nvs_commit(handle);
        nvs_close(handle);
    }
#else
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (s_mock_nvs[i].exists && strcmp(s_mock_nvs[i].key, STORAGE_INIT_KEY) == 0) {
            s_mock_nvs[i].data[0] = 1;
            s_mock_nvs[i].size = 1;
            return ESP_OK;
        }
    }
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (!s_mock_nvs[i].exists) {
            strncpy(s_mock_nvs[i].key, STORAGE_INIT_KEY, sizeof(s_mock_nvs[i].key) - 1);
            s_mock_nvs[i].data[0] = 1;
            s_mock_nvs[i].size = 1;
            s_mock_nvs[i].exists = true;
            return ESP_OK;
        }
    }
#endif

    return ESP_OK;
}

esp_err_t storage_init(void)
{
#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Initializing ESP-IDF NVS Flash subsystem...");

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS partition truncated or version updated. Erasing and re-initializing...");
        err = nvs_flash_erase();
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to erase NVS partition: %s", esp_err_to_name(err));
            return err;
        }
        err = nvs_flash_init();
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to initialize NVS flash after erase: %s", esp_err_to_name(err));
            return err;
        }
    } else if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS Flash initialization failed: %s", esp_err_to_name(err));
        return err;
    }

    /* Check if factory defaults have been seeded */
    nvs_handle_t handle;
    err = nvs_open(STORAGE_NVS_NAMESPACE, NVS_READONLY, &handle);
    bool need_seed = false;
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        need_seed = true;
    } else if (err == ESP_OK) {
        uint8_t init_val = 0;
        err = nvs_get_u8(handle, STORAGE_INIT_KEY, &init_val);
        if (err != ESP_OK || init_val != 1) {
            need_seed = true;
        }
        nvs_close(handle);
    } else {
        need_seed = true;
    }

    if (need_seed) {
        ESP_LOGI(TAG, "First boot detected (NVS uninitialized). Seeding factory presets...");
        err = storage_init_factory_defaults();
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to seed factory defaults: %s", esp_err_to_name(err));
            return err;
        }
    }

    ESP_LOGI(TAG, "Storage Subsystem initialized successfully.");
    return ESP_OK;
#else
    /* Host Mock Initialization */
    bool need_seed = !storage_mock_key_exists(STORAGE_INIT_KEY);
    if (need_seed) {
        return storage_init_factory_defaults();
    }
    return ESP_OK;
#endif
}

/* ========================================================================= */
/* Test Harness Mock Helper Functions (Host-Only)                            */
/* ========================================================================= */
#ifndef ESP_PLATFORM
void storage_mock_reset(void)
{
    memset(s_mock_nvs, 0, sizeof(s_mock_nvs));
}

void storage_mock_corrupt_key(const char *key, size_t byte_offset)
{
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (s_mock_nvs[i].exists && strcmp(s_mock_nvs[i].key, key) == 0) {
            if (byte_offset < s_mock_nvs[i].size) {
                s_mock_nvs[i].data[byte_offset] ^= 0xFF; /* Invert byte to corrupt */
            }
            return;
        }
    }
}

bool storage_mock_key_exists(const char *key)
{
    for (int i = 0; i < MOCK_NVS_MAX_ENTRIES; i++) {
        if (s_mock_nvs[i].exists && strcmp(s_mock_nvs[i].key, key) == 0) {
            return true;
        }
    }
    return false;
}
#endif
