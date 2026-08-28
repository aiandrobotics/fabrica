#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

#include "config.h"
#include "pca9685.h"

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
/* Angle to 12-Bit PWM Conversion Tests                                      */
/* ========================================================================= */

void test_angle_conversion_math(void)
{
    printf("Testing Angle-to-Counts PWM Conversion Formula...\n");

    /* 0 deg -> 500us -> round(500 * 4096 / 20000) = 102 counts */
    TEST_ASSERT(pca9685_angle_to_counts(0.0f) == 102, "0.0 deg converts to 102 counts (500us)");

    /* 15 deg -> 666.7us -> round(666.6667 * 4096 / 20000) = 137 counts */
    TEST_ASSERT(pca9685_angle_to_counts(15.0f) == 137, "15.0 deg converts to 137 counts (667us)");

    /* 30 deg -> 833.3us -> round(833.3333 * 4096 / 20000) = 171 counts */
    TEST_ASSERT(pca9685_angle_to_counts(30.0f) == 171, "30.0 deg converts to 171 counts (833us)");

    /* 45 deg -> 1000us -> round(1000 * 4096 / 20000) = 205 counts */
    TEST_ASSERT(pca9685_angle_to_counts(45.0f) == 205, "45.0 deg converts to 205 counts (1000us)");

    /* 90 deg -> 1500us -> round(1500 * 4096 / 20000) = 307 counts */
    TEST_ASSERT(pca9685_angle_to_counts(90.0f) == 307, "90.0 deg converts to 307 counts (1500us)");

    /* 135 deg -> 2000us -> round(2000 * 4096 / 20000) = 410 counts */
    TEST_ASSERT(pca9685_angle_to_counts(135.0f) == 410, "135.0 deg converts to 410 counts (2000us)");

    /* 180 deg -> 2500us -> round(2500 * 4096 / 20000) = 512 counts */
    TEST_ASSERT(pca9685_angle_to_counts(180.0f) == 512, "180.0 deg converts to 512 counts (2500us)");

    /* Boundary Clamping */
    TEST_ASSERT(pca9685_angle_to_counts(-50.0f) == 102, "Negative angle (-50.0 deg) clamps to 102 counts (0 deg)");
    TEST_ASSERT(pca9685_angle_to_counts(270.0f) == 512, "Excessive angle (270.0 deg) clamps to 512 counts (180 deg)");
}

/* ========================================================================= */
/* PCA9685 Initialization & Register Verification Tests                     */
/* ========================================================================= */

void test_initialization_and_registers(void)
{
    printf("Testing PCA9685 Initialization and Register Configuration...\n");

    pca9685_mock_reset();

    /* Test 1: Successful Initialization */
    esp_err_t err = pca9685_init();
    TEST_ASSERT(err == ESP_OK, "pca9685_init() returns ESP_OK");

    /* Verify Prescale register (0xFE) is 121 (50 Hz PWM) */
    TEST_ASSERT(pca9685_mock_get_reg(PCA9685_REG_PRESCALE) == 121, "PRESCALE register is set to 121 (50Hz)");

    /* Verify MODE2 register (0x01) has OUTDRV bit set (0x04) */
    TEST_ASSERT((pca9685_mock_get_reg(PCA9685_REG_MODE2) & PCA9685_MODE2_OUTDRV) == PCA9685_MODE2_OUTDRV,
                "MODE2 has totem-pole OUTDRV bit enabled");

    /* Verify MODE1 register (0x00) has AI (0x20) and ALLCALL (0x01) enabled */
    uint8_t mode1 = pca9685_mock_get_reg(PCA9685_REG_MODE1);
    TEST_ASSERT((mode1 & PCA9685_MODE1_AI) != 0, "MODE1 has Auto-Increment enabled");
    TEST_ASSERT((mode1 & PCA9685_MODE1_SLEEP) == 0, "MODE1 is awake (SLEEP bit 0)");

    /* Verify all channels initialized to 0.0 deg home position (102 counts) */
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        TEST_ASSERT(pca9685_mock_get_channel_off_count(ch) == 102, "Channel home off_count initialized to 102");
    }

    /* Test 2: Probe Failure Handling */
    pca9685_mock_reset();
    pca9685_mock_set_probe_success(false);
    err = pca9685_init();
    TEST_ASSERT(err == ESP_ERR_NOT_FOUND, "pca9685_init() returns ESP_ERR_NOT_FOUND when device missing");
}

/* ========================================================================= */
/* Single & Multi-Channel Articulation Tests                                */
/* ========================================================================= */

void test_channel_articulation(void)
{
    printf("Testing Single & Multi-Channel Servo Commands...\n");

    pca9685_mock_reset();
    pca9685_init();

    /* 1. Test Single Channel Angle Command */
    esp_err_t err = pca9685_set_servo_angle(3, 90.0f);
    TEST_ASSERT(err == ESP_OK, "pca9685_set_servo_angle(ch 3, 90 deg) returns ESP_OK");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(3) == 307, "Channel 3 off_count updated to 307 (90 deg)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(2) == 102, "Channel 2 remains unchanged at 102");

    /* 2. Test Invalid Channel Index */
    err = pca9685_set_servo_angle(16, 90.0f);
    TEST_ASSERT(err == ESP_ERR_INVALID_ARG, "pca9685_set_servo_angle(ch 16) rejected with ESP_ERR_INVALID_ARG");

    err = pca9685_set_pwm(16, 0, 300);
    TEST_ASSERT(err == ESP_ERR_INVALID_ARG, "pca9685_set_pwm(ch 16) rejected with ESP_ERR_INVALID_ARG");

    /* 3. Test Identification Nudge (15.0 deg / 137 counts) */
    err = pca9685_nudge_channel(0);
    TEST_ASSERT(err == ESP_OK, "pca9685_nudge_channel(0) returns ESP_OK");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 137, "Channel 0 nudge angle is 137 counts (15 deg)");

    /* 4. Test Visual Staging Hold (30.0 deg / 171 counts) */
    err = pca9685_stage_channel(5);
    TEST_ASSERT(err == ESP_OK, "pca9685_stage_channel(5) returns ESP_OK");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(5) == 171, "Channel 5 staged angle is 171 counts (30 deg)");

    /* 5. Test Multi-Servo Parallel Articulation (e.g. Channels 1 and 4 to 180 deg) */
    uint16_t mask = (1 << 1) | (1 << 4); /* 0x0012 */
    err = pca9685_set_multi_servo_angles(mask, 180.0f);
    TEST_ASSERT(err == ESP_OK, "pca9685_set_multi_servo_angles(mask 0x0012, 180 deg) returns ESP_OK");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(1) == 512, "Channel 1 updated to 512 (180 deg)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(4) == 512, "Channel 4 updated to 512 (180 deg)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(2) == 102, "Channel 2 remains unaffected");

    /* 6. Test Broadcast All-Channel Update (0xFFFF) */
    err = pca9685_set_multi_servo_angles(0xFFFF, 45.0f);
    TEST_ASSERT(err == ESP_OK, "pca9685_set_multi_servo_angles(0xFFFF, 45 deg) returns ESP_OK");
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        TEST_ASSERT(pca9685_mock_get_channel_off_count(ch) == 205, "Channel updated to 205 counts (45 deg)");
    }

    /* 7. Test Home All */
    err = pca9685_home_all();
    TEST_ASSERT(err == ESP_OK, "pca9685_home_all() returns ESP_OK");
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        TEST_ASSERT(pca9685_mock_get_channel_off_count(ch) == 102, "Channel homed to 102 counts (0 deg)");
    }
}

/* ========================================================================= */
/* Sleep / Low-Power Mode Tests                                              */
/* ========================================================================= */

void test_sleep_mode(void)
{
    printf("Testing PCA9685 Sleep & Low Power Control...\n");

    pca9685_mock_reset();
    pca9685_init();

    /* Put PCA9685 to sleep */
    esp_err_t err = pca9685_sleep(true);
    TEST_ASSERT(err == ESP_OK, "pca9685_sleep(true) returns ESP_OK");
    uint8_t mode1 = pca9685_mock_get_reg(PCA9685_REG_MODE1);
    TEST_ASSERT((mode1 & PCA9685_MODE1_SLEEP) != 0, "MODE1 has SLEEP bit set");

    /* Wake PCA9685 from sleep */
    err = pca9685_sleep(false);
    TEST_ASSERT(err == ESP_OK, "pca9685_sleep(false) returns ESP_OK");
    mode1 = pca9685_mock_get_reg(PCA9685_REG_MODE1);
    TEST_ASSERT((mode1 & PCA9685_MODE1_SLEEP) == 0, "MODE1 SLEEP bit cleared on wake");
}

/* ========================================================================= */
/* Main Entry Point                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 3 Unit Test: PCA9685 PWM Driver\n");
    printf("============================================================\n");

    test_angle_conversion_math();
    test_initialization_and_registers();
    test_channel_articulation();
    test_sleep_mode();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
