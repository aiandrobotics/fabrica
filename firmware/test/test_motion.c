#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "pca9685.h"
#include "storage.h"
#include "motion.h"

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
/* Motion Engine Lifecycle & Status Tests                                    */
/* ========================================================================= */

void test_motion_lifecycle(void)
{
    printf("Testing Motion Engine Lifecycle & Status APIs...\n");

    motion_reset_state();
    TEST_ASSERT(motion_init(NULL, NULL) == ESP_OK, "motion_init() returns ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Initial status is MOTION_STATUS_IDLE");
    TEST_ASSERT(motion_is_busy() == false, "Initial motion_is_busy() returns false");

    /* Reset state helper */
    motion_reset_state();
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "motion_reset_state() restores MOTION_STATUS_IDLE");
    TEST_ASSERT(motion_is_busy() == false, "motion_is_busy() is false after reset");
}

/* ========================================================================= */
/* Single & Parallel Step Execution Tests                                    */
/* ========================================================================= */

void test_single_and_parallel_steps(void)
{
    printf("Testing Single & Parallel Step Execution...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();

    /* 1. Single Motor Step */
    fold_step_t step_single;
    memset(&step_single, 0, sizeof(step_single));
    step_single.motor_count = 1;
    step_single.motor_ids[0] = 3; /* Channel 3 */

    esp_err_t err = motion_execute_step(&step_single);
    TEST_ASSERT(err == ESP_OK, "motion_execute_step(single motor) returns ESP_OK");
    /* Verify channel 3 finished at home count (102 = 0 deg) */
    TEST_ASSERT(pca9685_mock_get_channel_off_count(3) == 102, "Channel 3 returned to 0 deg home count (102)");

    /* 2. Parallel Dual-Motor Step */
    fold_step_t step_parallel;
    memset(&step_parallel, 0, sizeof(step_parallel));
    step_parallel.motor_count = 2;
    step_parallel.motor_ids[0] = 0; /* Channel 0 */
    step_parallel.motor_ids[1] = 1; /* Channel 1 */

    err = motion_execute_step(&step_parallel);
    TEST_ASSERT(err == ESP_OK, "motion_execute_step(parallel dual motors) returns ESP_OK");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 102, "Channel 0 returned to 0 deg home count (102)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(1) == 102, "Channel 1 returned to 0 deg home count (102)");

    /* 3. Parameter Validation Boundaries */
    TEST_ASSERT(motion_execute_step(NULL) == ESP_ERR_INVALID_ARG, "NULL step pointer rejected with ESP_ERR_INVALID_ARG");

    step_single.motor_count = 0;
    TEST_ASSERT(motion_execute_step(&step_single) == ESP_ERR_INVALID_ARG, "Zero motor count rejected with ESP_ERR_INVALID_ARG");

    step_single.motor_count = 3;
    TEST_ASSERT(motion_execute_step(&step_single) == ESP_ERR_INVALID_ARG, "Motor count > 2 rejected with ESP_ERR_INVALID_ARG");

    step_single.motor_count = 1;
    step_single.motor_ids[0] = 16; /* Channel 16 out of bounds */
    TEST_ASSERT(motion_execute_step(&step_single) == ESP_ERR_INVALID_ARG, "Channel 16 rejected with ESP_ERR_INVALID_ARG");

    step_parallel.motor_count = 2;
    step_parallel.motor_ids[0] = 0;
    step_parallel.motor_ids[1] = 20; /* Channel 20 out of bounds */
    TEST_ASSERT(motion_execute_step(&step_parallel) == ESP_ERR_INVALID_ARG, "2nd channel > 15 rejected with ESP_ERR_INVALID_ARG");
}

/* ========================================================================= */
/* Multi-Step Routine Sequencing & LED Coordination Tests                   */
/* ========================================================================= */

void test_routine_sequencing_and_led(void)
{
    printf("Testing Multi-Step Routine Sequencing & LED Feedback...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();

    /* Build 3-step test routine */
    fold_routine_t routine;
    memset(&routine, 0, sizeof(routine));
    routine.step_count = 3;

    /* Step 1: Ch 0 (Left fold) */
    routine.steps[0].motor_count = 1;
    routine.steps[0].motor_ids[0] = 0;

    /* Step 2: Ch 1 (Right fold) */
    routine.steps[1].motor_count = 1;
    routine.steps[1].motor_ids[0] = 1;

    /* Step 3: Ch 2 & Ch 3 (Parallel bottom fold) */
    routine.steps[2].motor_count = 2;
    routine.steps[2].motor_ids[0] = 2;
    routine.steps[2].motor_ids[1] = 3;

    esp_err_t err = motion_execute_routine(&routine);
    TEST_ASSERT(err == ESP_OK, "motion_execute_routine() returns ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Status returns to MOTION_STATUS_IDLE after completion");
    TEST_ASSERT(motion_is_busy() == false, "motion_is_busy() is false after completion");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED state returns to LED_STATE_IDLE after routine completion");

    /* Verify all channels homed */
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        TEST_ASSERT(pca9685_mock_get_channel_off_count(ch) == 102, "Channel homed to 102 counts (0 deg)");
    }
}

/* ========================================================================= */
/* Empty Routine Protection & Boundary Rejection Tests                       */
/* ========================================================================= */

void test_empty_and_boundary_rejection(void)
{
    printf("Testing Empty Preset & Boundary Case Rejection...\n");

    motion_reset_state();

    /* 1. NULL pointer */
    TEST_ASSERT(motion_execute_routine(NULL) == ESP_ERR_INVALID_ARG, "NULL routine returns ESP_ERR_INVALID_ARG");

    /* 2. Empty routine (0 steps) */
    fold_routine_t empty_routine;
    memset(&empty_routine, 0, sizeof(empty_routine));
    empty_routine.step_count = 0;

    esp_err_t err = motion_execute_routine(&empty_routine);
    TEST_ASSERT(err == ESP_ERR_INVALID_STATE, "Empty routine (0 steps) returns ESP_ERR_INVALID_STATE");
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR, "Empty routine sets LED_STATE_INPUT_ERROR");

    /* 3. Excessive step count (>16) */
    fold_routine_t huge_routine;
    memset(&huge_routine, 0, sizeof(huge_routine));
    huge_routine.step_count = 17;
    TEST_ASSERT(motion_execute_routine(&huge_routine) == ESP_ERR_INVALID_ARG, "Routine with 17 steps returns ESP_ERR_INVALID_ARG");

    /* 4. Invalid Preset IDs */
    TEST_ASSERT(motion_trigger_preset(0) == ESP_ERR_INVALID_ARG, "motion_trigger_preset(0) rejected with ESP_ERR_INVALID_ARG");
    TEST_ASSERT(motion_trigger_preset(5) == ESP_ERR_INVALID_ARG, "motion_trigger_preset(5) rejected with ESP_ERR_INVALID_ARG");
}

/* ========================================================================= */
/* Daily Run Mode Factory Presets 1 to 4 Execution Tests                     */
/* ========================================================================= */

void test_daily_run_presets(void)
{
    printf("Testing Daily Run Mode Factory Presets 1–4 Execution...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    motion_reset_state();

    /* Trigger Preset 1: Adult T-Shirt (3 steps) */
    TEST_ASSERT(motion_trigger_preset(1) == ESP_OK, "Preset 1 (Adult T-Shirt) executes with ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Status returns to IDLE after Preset 1");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED returns to IDLE after Preset 1");

    /* Trigger Preset 2: Long-Sleeve Shirt (3 steps: parallel sleeves + 2 body folds) */
    TEST_ASSERT(motion_trigger_preset(2) == ESP_OK, "Preset 2 (Long-Sleeve Shirt) executes with ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Status returns to IDLE after Preset 2");

    /* Trigger Preset 3: Trousers / Jeans (2 steps) */
    TEST_ASSERT(motion_trigger_preset(3) == ESP_OK, "Preset 3 (Trousers/Jeans) executes with ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Status returns to IDLE after Preset 3");

    /* Trigger Preset 4: Towel / Linen (3 steps) */
    TEST_ASSERT(motion_trigger_preset(4) == ESP_OK, "Preset 4 (Towel/Linen) executes with ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Status returns to IDLE after Preset 4");
}

/* ========================================================================= */
/* Emergency Stop (E-Stop) Preemption Tests                                  */
/* ========================================================================= */

void test_emergency_stop_preemption(void)
{
    printf("Testing Emergency Stop (E-Stop) Abort Preemption...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();

    /* Articulate some servos to non-zero angles */
    pca9685_set_servo_angle(0, 180.0f);
    pca9685_set_servo_angle(1, 90.0f);
    pca9685_set_servo_angle(2, 45.0f);
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 512, "Channel 0 set to 180 deg");

    /* Trigger E-Stop */
    esp_err_t err = motion_emergency_stop();
    TEST_ASSERT(err == ESP_OK, "motion_emergency_stop() returns ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_ABORTED, "Motion status transitioned to MOTION_STATUS_ABORTED");
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP, "LED state set to LED_STATE_ESTOP (5 rapid flashes)");

    /* Verify all channels homed to 0 deg */
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        TEST_ASSERT(pca9685_mock_get_channel_off_count(ch) == 102, "Channel instantly homed to 102 counts (0 deg) on E-Stop");
    }

    /* Verify that new step attempts are aborted while E-Stop condition is active */
    fold_step_t step;
    memset(&step, 0, sizeof(step));
    step.motor_count = 1;
    step.motor_ids[0] = 0;
    TEST_ASSERT(motion_execute_step(&step) == ESP_ERR_TIMEOUT, "motion_execute_step() immediately returns ESP_ERR_TIMEOUT while aborted");

    /* Verify that a new routine execution automatically clears E-Stop abort state */
    err = motion_trigger_preset(1);
    TEST_ASSERT(err == ESP_OK, "motion_trigger_preset(1) automatically clears E-Stop and executes with ESP_OK");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Status returns to IDLE after recovery execution");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED returns to IDLE after recovery execution");
}

/* ========================================================================= */
/* Test Main Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 5 Unit Test: Motion Engine\n");
    printf("============================================================\n");

    test_motion_lifecycle();
    test_single_and_parallel_steps();
    test_routine_sequencing_and_led();
    test_empty_and_boundary_rejection();
    test_daily_run_presets();
    test_emergency_stop_preemption();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
