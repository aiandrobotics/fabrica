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

void test_config_constants(void)
{
    printf("Testing config.h GPIO pin allocations...\n");
    TEST_ASSERT(STATUS_LED_GPIO == 2, "STATUS_LED_GPIO is GPIO 2");
    TEST_ASSERT(BTN1_GPIO == 4, "BTN1_GPIO is GPIO 4");
    TEST_ASSERT(BTN2_GPIO == 16, "BTN2_GPIO is GPIO 16");
    TEST_ASSERT(BTN3_GPIO == 17, "BTN3_GPIO is GPIO 17");
    TEST_ASSERT(BTN4_GPIO == 5, "BTN4_GPIO is GPIO 5");
    TEST_ASSERT(I2C_SDA_GPIO == 21, "I2C_SDA_GPIO is GPIO 21");
    TEST_ASSERT(I2C_SCL_GPIO == 22, "I2C_SCL_GPIO is GPIO 22");

    printf("Testing config.h system limits and timing...\n");
    TEST_ASSERT(MAX_STEPS_PER_ROUTINE == 16, "MAX_STEPS_PER_ROUTINE is 16");
    TEST_ASSERT(MAX_MOTORS_PER_STEP == 2, "MAX_MOTORS_PER_STEP is 2");
    TEST_ASSERT(TOTAL_SERVO_CHANNELS == 16, "TOTAL_SERVO_CHANNELS is 16");
    TEST_ASSERT(TOTAL_PRESET_COUNT == 4, "TOTAL_PRESET_COUNT is 4");
    TEST_ASSERT(COMMAND_QUEUE_LENGTH == 16, "COMMAND_QUEUE_LENGTH is 16");
    TEST_ASSERT(BUTTON_DEBOUNCE_MS == 50, "BUTTON_DEBOUNCE_MS is 50ms");
    TEST_ASSERT(BUTTON_SHORT_PRESS_MAX_MS == 500, "BUTTON_SHORT_PRESS_MAX_MS is 500ms");
    TEST_ASSERT(BUTTON_LONG_PRESS_MS == 3000, "BUTTON_LONG_PRESS_MS is 3000ms");
    TEST_ASSERT(PROGRAMMING_TIMEOUT_MS == 20000, "PROGRAMMING_TIMEOUT_MS is 20000ms");
    TEST_ASSERT(FOLD_DWELL_TIME_MS == 300, "FOLD_DWELL_TIME_MS is 300ms");
    TEST_ASSERT(INTER_STEP_DELAY_MS == 200, "INTER_STEP_DELAY_MS is 200ms");

    printf("Testing config.h angles and PCA9685 constants...\n");
    TEST_ASSERT(HOME_ANGLE_DEG == 0.0f, "HOME_ANGLE_DEG is 0.0 deg");
    TEST_ASSERT(NUDGE_ANGLE_DEG == 15.0f, "NUDGE_ANGLE_DEG is 15.0 deg");
    TEST_ASSERT(STAGE_ANGLE_DEG == 30.0f, "STAGE_ANGLE_DEG is 30.0 deg");
    TEST_ASSERT(FOLD_ANGLE_DEG == 180.0f, "FOLD_ANGLE_DEG is 180.0 deg");
    TEST_ASSERT(PCA9685_I2C_ADDR == 0x40, "PCA9685_I2C_ADDR is 0x40");
    TEST_ASSERT(PCA9685_I2C_FREQ_HZ == 100000, "PCA9685_I2C_FREQ_HZ is 100 kHz");
    TEST_ASSERT(PCA9685_PWM_FREQ_HZ == 50, "PCA9685_PWM_FREQ_HZ is 50 Hz");
    TEST_ASSERT(PCA9685_PWM_RES_BITS == 12, "PCA9685_PWM_RES_BITS is 12 bits");
    TEST_ASSERT(PCA9685_PRESCALE_VAL == 121, "PCA9685_PRESCALE_VAL is 121");
    TEST_ASSERT(SERVO_MIN_PULSE_US == 500, "SERVO_MIN_PULSE_US is 500 us");
    TEST_ASSERT(SERVO_MAX_PULSE_US == 2500, "SERVO_MAX_PULSE_US is 2500 us");
}

void test_command_structures(void)
{
    printf("Testing command.h structures and enums...\n");
    TEST_ASSERT(SOURCE_PHYSICAL_BUTTON == 0, "SOURCE_PHYSICAL_BUTTON is 0");
    TEST_ASSERT(SOURCE_BLE == 1, "SOURCE_BLE is 1");
    TEST_ASSERT(SOURCE_WIFI == 2, "SOURCE_WIFI is 2");
    TEST_ASSERT(SOURCE_INTERNAL_TIMER == 3, "SOURCE_INTERNAL_TIMER is 3");

    TEST_ASSERT(CMD_RUN_PRESET == 0, "CMD_RUN_PRESET is 0");
    TEST_ASSERT(CMD_RUN_RAW_SEQUENCE == 1, "CMD_RUN_RAW_SEQUENCE is 1");
    TEST_ASSERT(CMD_EMERGENCY_STOP == 2, "CMD_EMERGENCY_STOP is 2");
    TEST_ASSERT(CMD_ENTER_PROGRAM_MODE == 3, "CMD_ENTER_PROGRAM_MODE is 3");
    TEST_ASSERT(CMD_CYCLE_NUDGE_MOTOR == 4, "CMD_CYCLE_NUDGE_MOTOR is 4");
    TEST_ASSERT(CMD_STAGE_TOGGLE_MOTOR == 5, "CMD_STAGE_TOGGLE_MOTOR is 5");
    TEST_ASSERT(CMD_LOCK_STEP == 6, "CMD_LOCK_STEP is 6");
    TEST_ASSERT(CMD_SAVE_EXIT_PROGRAM == 7, "CMD_SAVE_EXIT_PROGRAM is 7");
    TEST_ASSERT(CMD_JOG_MOTOR_ANGLE == 8, "CMD_JOG_MOTOR_ANGLE is 8");
    TEST_ASSERT(CMD_GET_TELEMETRY == 9, "CMD_GET_TELEMETRY is 9");
    TEST_ASSERT(CMD_SYNC_PRESETS == 10, "CMD_SYNC_PRESETS is 10");

    /* Test fold_step_t sizing and memory layout */
    TEST_ASSERT(sizeof(fold_step_t) >= 3, "fold_step_t has sufficient byte size");
    fold_step_t step;
    step.motor_count = 2;
    step.motor_ids[0] = 3;
    step.motor_ids[1] = 7;
    TEST_ASSERT(step.motor_count == 2 && step.motor_ids[0] == 3 && step.motor_ids[1] == 7,
                "fold_step_t field assignment integrity");

    /* Test fold_routine_t initialization and packing */
    fold_routine_t routine;
    memset(&routine, 0, sizeof(routine));
    routine.step_count = 3;
    routine.steps[0].motor_count = 1;
    routine.steps[0].motor_ids[0] = 0;
    routine.steps[1].motor_count = 2;
    routine.steps[1].motor_ids[0] = 1;
    routine.steps[1].motor_ids[1] = 2;
    routine.checksum = 0xAABBCCDD;
    TEST_ASSERT(routine.step_count == 3 && routine.checksum == 0xAABBCCDD,
                "fold_routine_t field assignment integrity");

    /* Test command_t polymorphic payloads */
    command_t cmd_btn;
    cmd_btn.type = CMD_RUN_PRESET;
    cmd_btn.source = SOURCE_PHYSICAL_BUTTON;
    cmd_btn.payload.preset_id = 1;
    TEST_ASSERT(cmd_btn.type == CMD_RUN_PRESET && cmd_btn.payload.preset_id == 1,
                "command_t preset run assignment");

    command_t cmd_jog;
    cmd_jog.type = CMD_JOG_MOTOR_ANGLE;
    cmd_jog.source = SOURCE_BLE;
    cmd_jog.payload.jog_param.channel = 5;
    cmd_jog.payload.jog_param.angle_deg = 45.0f;
    TEST_ASSERT(cmd_jog.type == CMD_JOG_MOTOR_ANGLE && cmd_jog.payload.jog_param.channel == 5 &&
                cmd_jog.payload.jog_param.angle_deg == 45.0f,
                "command_t jog parameter assignment");

    command_t cmd_estop;
    cmd_estop.type = CMD_EMERGENCY_STOP;
    cmd_estop.source = SOURCE_PHYSICAL_BUTTON;
    TEST_ASSERT(cmd_estop.type == CMD_EMERGENCY_STOP, "command_t E-Stop assignment");
}

void test_storage_headers(void)
{
    printf("Testing storage.h constants and namespaces...\n");
    TEST_ASSERT(strcmp(STORAGE_NVS_NAMESPACE, "fabrica") == 0, "STORAGE_NVS_NAMESPACE is 'fabrica'");
    TEST_ASSERT(strcmp(STORAGE_INIT_KEY, "preset_init") == 0, "STORAGE_INIT_KEY is 'preset_init'");
    TEST_ASSERT(strcmp(STORAGE_PRESET_KEY_PREFIX, "preset_") == 0, "STORAGE_PRESET_KEY_PREFIX is 'preset_'");
}

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 1 Unit Test: Headers & Structures\n");
    printf("============================================================\n");

    test_config_constants();
    test_command_structures();
    test_storage_headers();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
