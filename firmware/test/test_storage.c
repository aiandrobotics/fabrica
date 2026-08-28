#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "storage.h"

static int test_count = 0;
static int pass_count = 0;

#define TEST_ASSERT(cond, msg) do { \
    test_count++; \
    if (cond) { \
        pass_count++; \
        printf("  [PASS] %s\n", msg); \
    } else { \
        printf("  [FAIL] %s (Line %d)\n", msg, __LINE__); \
        assert(cond); \
    } \
} while(0)

/* ========================================================================= */
/* CRC32 Calculation & Integrity Check Tests                                */
/* ========================================================================= */

void test_crc32_calculation(void)
{
    printf("Testing CRC32 Integrity Checksum Engine...\n");

    fold_routine_t r1;
    memset(&r1, 0, sizeof(r1));
    r1.step_count = 2;
    r1.steps[0].motor_count = 1;
    r1.steps[0].motor_ids[0] = 5;
    r1.steps[1].motor_count = 2;
    r1.steps[1].motor_ids[0] = 6;
    r1.steps[1].motor_ids[1] = 7;

    uint32_t crc1 = storage_compute_crc32(&r1);
    TEST_ASSERT(crc1 != 0, "storage_compute_crc32 returns non-zero checksum for valid routine");

    /* Determinism test */
    fold_routine_t r2 = r1;
    uint32_t crc2 = storage_compute_crc32(&r2);
    TEST_ASSERT(crc1 == crc2, "Identical routine structs produce identical CRC32");

    /* Bit-flip sensitivity in step_count */
    r2.step_count = 3;
    uint32_t crc3 = storage_compute_crc32(&r2);
    TEST_ASSERT(crc1 != crc3, "Altering step_count produces distinct CRC32");

    /* Bit-flip sensitivity in motor_count */
    r2 = r1;
    r2.steps[0].motor_count = 2;
    uint32_t crc4 = storage_compute_crc32(&r2);
    TEST_ASSERT(crc1 != crc4, "Altering motor_count produces distinct CRC32");

    /* Bit-flip sensitivity in motor_ids */
    r2 = r1;
    r2.steps[0].motor_ids[0] = 4;
    uint32_t crc5 = storage_compute_crc32(&r2);
    TEST_ASSERT(crc1 != crc5, "Altering motor_ids produces distinct CRC32");

    /* Null pointer safety */
    TEST_ASSERT(storage_compute_crc32(NULL) == 0, "NULL routine pointer returns 0 checksum");
}

/* ========================================================================= */
/* Factory Default Presets Verification Tests                                */
/* ========================================================================= */

void test_factory_defaults(void)
{
    printf("Testing Factory Default Folding Sequences...\n");

    fold_routine_t routine;

    /* Preset 1: Adult T-Shirt */
    esp_err_t err = storage_get_default_routine(1, &routine);
    TEST_ASSERT(err == ESP_OK, "storage_get_default_routine(1) returns ESP_OK");
    TEST_ASSERT(routine.step_count == 3, "Preset 1 has 3 steps");
    TEST_ASSERT(routine.steps[0].motor_count == 1 && routine.steps[0].motor_ids[0] == 0, "Preset 1 Step 1 is Left fold (Ch 0)");
    TEST_ASSERT(routine.steps[1].motor_count == 1 && routine.steps[1].motor_ids[0] == 1, "Preset 1 Step 2 is Right fold (Ch 1)");
    TEST_ASSERT(routine.steps[2].motor_count == 1 && routine.steps[2].motor_ids[0] == 2, "Preset 1 Step 3 is Bottom fold (Ch 2)");
    TEST_ASSERT(routine.checksum == storage_compute_crc32(&routine), "Preset 1 checksum is valid");

    /* Preset 2: Long-Sleeve Shirt */
    err = storage_get_default_routine(2, &routine);
    TEST_ASSERT(err == ESP_OK, "storage_get_default_routine(2) returns ESP_OK");
    TEST_ASSERT(routine.step_count == 3, "Preset 2 has 3 steps");
    TEST_ASSERT(routine.steps[0].motor_count == 2 && routine.steps[0].motor_ids[0] == 0 && routine.steps[0].motor_ids[1] == 1,
                "Preset 2 Step 1 is Parallel sleeve folds (Ch 0 + Ch 1)");
    TEST_ASSERT(routine.steps[1].motor_count == 1 && routine.steps[1].motor_ids[0] == 2, "Preset 2 Step 2 is Left body fold (Ch 2)");
    TEST_ASSERT(routine.steps[2].motor_count == 1 && routine.steps[2].motor_ids[0] == 3, "Preset 2 Step 3 is Right body fold (Ch 3)");
    TEST_ASSERT(routine.checksum == storage_compute_crc32(&routine), "Preset 2 checksum is valid");

    /* Preset 3: Trousers / Jeans */
    err = storage_get_default_routine(3, &routine);
    TEST_ASSERT(err == ESP_OK, "storage_get_default_routine(3) returns ESP_OK");
    TEST_ASSERT(routine.step_count == 2, "Preset 3 has 2 steps");
    TEST_ASSERT(routine.steps[0].motor_count == 1 && routine.steps[0].motor_ids[0] == 0, "Preset 3 Step 1 is Vertical fold (Ch 0)");
    TEST_ASSERT(routine.steps[1].motor_count == 1 && routine.steps[1].motor_ids[0] == 1, "Preset 3 Step 2 is Bottom fold (Ch 1)");
    TEST_ASSERT(routine.checksum == storage_compute_crc32(&routine), "Preset 3 checksum is valid");

    /* Preset 4: Towel / Linen */
    err = storage_get_default_routine(4, &routine);
    TEST_ASSERT(err == ESP_OK, "storage_get_default_routine(4) returns ESP_OK");
    TEST_ASSERT(routine.step_count == 3, "Preset 4 has 3 steps");
    TEST_ASSERT(routine.steps[0].motor_count == 1 && routine.steps[0].motor_ids[0] == 0, "Preset 4 Step 1 is Half fold (Ch 0)");
    TEST_ASSERT(routine.steps[1].motor_count == 1 && routine.steps[1].motor_ids[0] == 1, "Preset 4 Step 2 is Quarter fold (Ch 1)");
    TEST_ASSERT(routine.steps[2].motor_count == 1 && routine.steps[2].motor_ids[0] == 2, "Preset 4 Step 3 is Press fold (Ch 2)");
    TEST_ASSERT(routine.checksum == storage_compute_crc32(&routine), "Preset 4 checksum is valid");

    /* Invalid Preset ID checks */
    TEST_ASSERT(storage_get_default_routine(0, &routine) == ESP_ERR_INVALID_ARG, "Preset 0 rejected");
    TEST_ASSERT(storage_get_default_routine(5, &routine) == ESP_ERR_INVALID_ARG, "Preset 5 rejected");
    TEST_ASSERT(storage_get_default_routine(1, NULL) == ESP_ERR_INVALID_ARG, "NULL destination rejected");
}

/* ========================================================================= */
/* Storage CRUD & Flash Persistence Tests                                    */
/* ========================================================================= */

void test_storage_crud_operations(void)
{
    printf("Testing Storage Initialization and CRUD Operations...\n");

    storage_mock_reset();

    /* 1. Initial boot: storage_init() seeds factory defaults */
    esp_err_t err = storage_init();
    TEST_ASSERT(err == ESP_OK, "storage_init() initializes and seeds factory defaults");
    TEST_ASSERT(storage_mock_key_exists(STORAGE_INIT_KEY), "STORAGE_INIT_KEY set in NVS");
    TEST_ASSERT(storage_mock_key_exists("preset_1"), "preset_1 exists in NVS");
    TEST_ASSERT(storage_mock_key_exists("preset_2"), "preset_2 exists in NVS");
    TEST_ASSERT(storage_mock_key_exists("preset_3"), "preset_3 exists in NVS");
    TEST_ASSERT(storage_mock_key_exists("preset_4"), "preset_4 exists in NVS");

    /* 2. Load Preset 1 and verify */
    fold_routine_t loaded;
    err = storage_load_routine(1, &loaded);
    TEST_ASSERT(err == ESP_OK, "storage_load_routine(1) returns ESP_OK");
    TEST_ASSERT(loaded.step_count == 3, "Loaded Preset 1 has 3 steps");
    TEST_ASSERT(loaded.steps[0].motor_ids[0] == 0, "Loaded Preset 1 Step 1 motor ID is 0");

    /* 3. Save a Custom Routine to Preset 2 */
    fold_routine_t custom;
    memset(&custom, 0, sizeof(custom));
    custom.step_count = 4;
    custom.steps[0].motor_count = 1; custom.steps[0].motor_ids[0] = 7;
    custom.steps[1].motor_count = 2; custom.steps[1].motor_ids[0] = 8; custom.steps[1].motor_ids[1] = 9;
    custom.steps[2].motor_count = 1; custom.steps[2].motor_ids[0] = 10;
    custom.steps[3].motor_count = 1; custom.steps[3].motor_ids[0] = 11;

    err = storage_save_routine(2, &custom);
    TEST_ASSERT(err == ESP_OK, "storage_save_routine(2, custom) returns ESP_OK");

    /* 4. Load Preset 2 and verify custom contents */
    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(2, &loaded);
    TEST_ASSERT(err == ESP_OK, "storage_load_routine(2) returns ESP_OK");
    TEST_ASSERT(loaded.step_count == 4, "Loaded Preset 2 has 4 steps");
    TEST_ASSERT(loaded.steps[0].motor_ids[0] == 7, "Loaded custom Step 1 motor ID is 7");
    TEST_ASSERT(loaded.steps[1].motor_ids[0] == 8 && loaded.steps[1].motor_ids[1] == 9, "Loaded custom Step 2 has motors 8 and 9");
    TEST_ASSERT(loaded.checksum == storage_compute_crc32(&loaded), "Loaded custom routine has valid calculated checksum");

    /* 5. Erase Preset 2 */
    err = storage_erase_routine(2);
    TEST_ASSERT(err == ESP_OK, "storage_erase_routine(2) returns ESP_OK");
    TEST_ASSERT(!storage_mock_key_exists("preset_2"), "preset_2 key deleted from NVS");

    /* 6. Load Erased Preset 2 -> Falls back gracefully to factory default */
    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(2, &loaded);
    TEST_ASSERT(err == ESP_OK, "storage_load_routine(2) on erased key falls back to factory default with ESP_OK");
    TEST_ASSERT(loaded.step_count == 3, "Fallback Preset 2 has default 3 steps");
    TEST_ASSERT(loaded.steps[0].motor_count == 2, "Fallback Preset 2 Step 1 has default 2 motors");
}

/* ========================================================================= */
/* Corruption Recovery & Error Handling Tests                                */
/* ========================================================================= */

void test_corruption_and_boundary_handling(void)
{
    printf("Testing Corruption Recovery, CRC Mismatch & Boundary Cases...\n");

    storage_mock_reset();
    storage_init();

    /* 1. Inject bit corruption into preset_1 storage blob */
    storage_mock_corrupt_key("preset_1", 0); /* Corrupt step_count byte */

    fold_routine_t loaded;
    esp_err_t err = storage_load_routine(1, &loaded);
    TEST_ASSERT(err == ESP_ERR_INVALID_CRC, "Corrupted blob detected and returns ESP_ERR_INVALID_CRC");
    TEST_ASSERT(loaded.step_count == 3, "Corrupted load falls back to default factory routine (3 steps)");
    TEST_ASSERT(loaded.steps[0].motor_ids[0] == 0, "Corrupted load fallback has correct factory motor ID (0)");
    TEST_ASSERT(loaded.checksum == storage_compute_crc32(&loaded), "Fallback routine has valid recalculated CRC");

    /* 2. Boundary Parameter Validation */
    fold_routine_t dummy;
    memset(&dummy, 0, sizeof(dummy));

    TEST_ASSERT(storage_save_routine(0, &dummy) == ESP_ERR_INVALID_ARG, "storage_save_routine(0) returns ESP_ERR_INVALID_ARG");
    TEST_ASSERT(storage_save_routine(5, &dummy) == ESP_ERR_INVALID_ARG, "storage_save_routine(5) returns ESP_ERR_INVALID_ARG");
    TEST_ASSERT(storage_save_routine(1, NULL) == ESP_ERR_INVALID_ARG, "storage_save_routine(NULL) returns ESP_ERR_INVALID_ARG");

    dummy.step_count = MAX_STEPS_PER_ROUTINE + 1;
    TEST_ASSERT(storage_save_routine(1, &dummy) == ESP_ERR_INVALID_ARG, "storage_save_routine with step_count > 16 rejected");

    TEST_ASSERT(storage_load_routine(0, &dummy) == ESP_ERR_INVALID_ARG, "storage_load_routine(0) returns ESP_ERR_INVALID_ARG");
    TEST_ASSERT(storage_load_routine(5, &dummy) == ESP_ERR_INVALID_ARG, "storage_load_routine(5) returns ESP_ERR_INVALID_ARG");
    TEST_ASSERT(storage_load_routine(1, NULL) == ESP_ERR_INVALID_ARG, "storage_load_routine(NULL) returns ESP_ERR_INVALID_ARG");

    TEST_ASSERT(storage_erase_routine(0) == ESP_ERR_INVALID_ARG, "storage_erase_routine(0) returns ESP_ERR_INVALID_ARG");
    TEST_ASSERT(storage_erase_routine(5) == ESP_ERR_INVALID_ARG, "storage_erase_routine(5) returns ESP_ERR_INVALID_ARG");
}

/* ========================================================================= */
/* Main Entry Point                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 4 Unit Test: NVS Storage Manager\n");
    printf("============================================================\n");

    test_crc32_calculation();
    test_factory_defaults();
    test_storage_crud_operations();
    test_corruption_and_boundary_handling();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
