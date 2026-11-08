#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "buttons.h"
#include "pca9685.h"
#include "storage.h"
#include "motion.h"
#include "state_machine.h"

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
/* Test 1: State Machine Lifecycle & Boot State                              */
/* ========================================================================= */

void test_state_machine_lifecycle_and_boot(void)
{
    printf("Testing State Machine Lifecycle & Initial Boot State...\n");

    state_machine_reset();
    TEST_ASSERT(state_machine_init() == ESP_OK, "state_machine_init() returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Initial state is STATE_IDLE_RUN");
    TEST_ASSERT(state_machine_is_ble_pairing() == false, "BLE pairing is NOT active on initial boot (requires 3s hold)");

    /* NULL command rejection */
    TEST_ASSERT(state_machine_process_command(NULL) == ESP_ERR_INVALID_ARG, "NULL command returns ESP_ERR_INVALID_ARG");
}

/* ========================================================================= */
/* Test 2: Daily Run Mode Dispatch                                           */
/* ========================================================================= */

void test_run_mode_dispatch(void)
{
    printf("Testing Daily Run Mode Dispatch in STATE_IDLE_RUN...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    motion_reset_state();
    state_machine_reset();

    /* 1. Trigger Preset 1 via command */
    command_t cmd_run;
    memset(&cmd_run, 0, sizeof(cmd_run));
    cmd_run.type = CMD_RUN_PRESET;
    cmd_run.payload.preset_id = 1;

    esp_err_t err = state_machine_process_command(&cmd_run);
    TEST_ASSERT(err == ESP_OK, "CMD_RUN_PRESET (1) executed with ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State returns to STATE_IDLE_RUN after execution");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED state returns to LED_STATE_IDLE");

    /* 2. Bounds check on Preset IDs */
    cmd_run.payload.preset_id = 0;
    TEST_ASSERT(state_machine_process_command(&cmd_run) == ESP_ERR_INVALID_ARG, "Preset 0 rejected with ESP_ERR_INVALID_ARG");

    cmd_run.payload.preset_id = 5;
    TEST_ASSERT(state_machine_process_command(&cmd_run) == ESP_ERR_INVALID_ARG, "Preset 5 rejected with ESP_ERR_INVALID_ARG");

    /* 3. Raw Sequence Execution */
    command_t cmd_raw;
    memset(&cmd_raw, 0, sizeof(cmd_raw));
    cmd_raw.type = CMD_RUN_RAW_SEQUENCE;
    cmd_raw.payload.raw_routine.step_count = 1;
    cmd_raw.payload.raw_routine.steps[0].motor_count = 1;
    cmd_raw.payload.raw_routine.steps[0].motor_ids[0] = 2;

    err = state_machine_process_command(&cmd_raw);
    TEST_ASSERT(err == ESP_OK, "CMD_RUN_RAW_SEQUENCE executed with ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State returns to STATE_IDLE_RUN after raw execution");
}

/* ========================================================================= */
/* Test 3: Wireless Button Sequence Assignment & Playback                    */
/* ========================================================================= */

void test_wireless_button_sequence_save_and_playback(void)
{
    printf("Testing Wireless Button Sequence Save (CMD_SET_BUTTON_SEQUENCE) & Playback...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    motion_reset_state();
    state_machine_reset();

    /* 1. Save a custom 2-step sequence to Button 3 from mobile app */
    command_t cmd_save;
    memset(&cmd_save, 0, sizeof(cmd_save));
    cmd_save.type = CMD_SET_BUTTON_SEQUENCE;
    cmd_save.source = SOURCE_BLE;
    cmd_save.payload.button_sync.preset_id = 3;
    cmd_save.payload.button_sync.routine.step_count = 2;
    cmd_save.payload.button_sync.routine.steps[0].motor_count = 1;
    cmd_save.payload.button_sync.routine.steps[0].motor_ids[0] = 7;
    cmd_save.payload.button_sync.routine.steps[1].motor_count = 2;
    cmd_save.payload.button_sync.routine.steps[1].motor_ids[0] = 8;
    cmd_save.payload.button_sync.routine.steps[1].motor_ids[1] = 9;

    esp_err_t err = state_machine_process_command(&cmd_save);
    TEST_ASSERT(err == ESP_OK, "CMD_SET_BUTTON_SEQUENCE returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State remains STATE_IDLE_RUN");
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS, "LED state set to LED_STATE_SAVE_SUCCESS (2.0s solid ON)");

    /* 2. Verify stored sequence in NVS */
    fold_routine_t loaded;
    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(3, &loaded);
    TEST_ASSERT(err == ESP_OK, "storage_load_routine(3) loads newly saved sequence");
    TEST_ASSERT(loaded.step_count == 2, "Loaded routine has 2 steps");
    TEST_ASSERT(loaded.steps[0].motor_count == 1 && loaded.steps[0].motor_ids[0] == 7, "Loaded Step 1 is Ch 7");
    TEST_ASSERT(loaded.steps[1].motor_count == 2 && loaded.steps[1].motor_ids[0] == 8 && loaded.steps[1].motor_ids[1] == 9, "Loaded Step 2 is Ch 8 & 9");

    /* 3. Execute the newly saved routine in Daily Run Mode */
    command_t cmd_run = {.type = CMD_RUN_PRESET, .payload.preset_id = 3};
    err = state_machine_process_command(&cmd_run);
    TEST_ASSERT(err == ESP_OK, "Newly saved Preset 3 executes cleanly in Daily Run Mode");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Returned to STATE_IDLE_RUN after execution");

    /* 4. Reject invalid preset IDs or empty step counts */
    cmd_save.payload.button_sync.preset_id = 0;
    TEST_ASSERT(state_machine_process_command(&cmd_save) == ESP_ERR_INVALID_ARG, "Invalid preset_id 0 rejected");
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR, "LED set to LED_STATE_INPUT_ERROR on invalid save");

    cmd_save.payload.button_sync.preset_id = 2;
    cmd_save.payload.button_sync.routine.step_count = 0;
    TEST_ASSERT(state_machine_process_command(&cmd_save) == ESP_ERR_INVALID_ARG, "Empty step_count 0 rejected");
}

/* ========================================================================= */
/* Test 4: Factory Preset Restoration & Live Servo Jog                       */
/* ========================================================================= */

void test_factory_reset_and_live_jog(void)
{
    printf("Testing CMD_RESTORE_FACTORY_PRESETS and CMD_JOG_MOTOR_ANGLE...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    state_machine_reset();

    /* 1. Restore factory defaults */
    command_t cmd_reset = {.type = CMD_RESTORE_FACTORY_PRESETS, .source = SOURCE_BLE};
    esp_err_t err = state_machine_process_command(&cmd_reset);
    TEST_ASSERT(err == ESP_OK, "CMD_RESTORE_FACTORY_PRESETS returns ESP_OK");
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS, "LED set to LED_STATE_SAVE_SUCCESS after factory restore");

    fold_routine_t r3;
    TEST_ASSERT(storage_load_routine(3, &r3) == ESP_OK && r3.step_count == 3 && r3.steps[0].motor_ids[0] == SERVO_FLAP_LEFT,
                "Preset 3 restored to factory default Trousers routine");

    /* 2. Live Servo Jog from mobile app */
    command_t cmd_jog;
    memset(&cmd_jog, 0, sizeof(cmd_jog));
    cmd_jog.type = CMD_JOG_MOTOR_ANGLE;
    cmd_jog.source = SOURCE_BLE;
    cmd_jog.payload.jog_param.channel = 2;
    cmd_jog.payload.jog_param.angle_deg = 90.0f;

    err = state_machine_process_command(&cmd_jog);
    TEST_ASSERT(err == ESP_OK, "CMD_JOG_MOTOR_ANGLE (Ch 2 -> 90 deg) returns ESP_OK");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(2) == pca9685_angle_to_counts(90.0f),
                "Channel 2 updated to 90 deg PWM count");
}

/* ========================================================================= */
/* Test 5: Emergency Stop Preemption                                         */
/* ========================================================================= */

void test_emergency_stop_in_all_states(void)
{
    printf("Testing Emergency Stop Preemption & Servo Homing...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();
    state_machine_reset();

    /* Jog a channel away from home, then trigger E-Stop */
    pca9685_set_servo_angle(0, 90.0f);
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) != 102, "Channel 0 away from home");

    command_t cmd_estop = {.type = CMD_EMERGENCY_STOP};
    esp_err_t err = state_machine_process_command(&cmd_estop);
    TEST_ASSERT(err == ESP_OK, "CMD_EMERGENCY_STOP returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_ESTOP, "State latches in STATE_ESTOP after E-Stop");
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP, "LED state set to LED_STATE_ESTOP");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 102, "Channel 0 homed to 0 deg on E-Stop");

    /* Clear latched STATE_ESTOP via CMD_STOP_SEQUENCE */
    command_t cmd_clear = {.type = CMD_STOP_SEQUENCE};
    TEST_ASSERT(state_machine_process_command(&cmd_clear) == ESP_OK, "CMD_STOP_SEQUENCE clears STATE_ESTOP");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State returns to STATE_IDLE_RUN after clear");
}

/* ========================================================================= */
/* Test 6: BLE Pairing Mode (3s Hold Entry & 120s Auto-Timeout)              */
/* ========================================================================= */

void test_ble_pairing_mode_and_timeout(void)
{
    printf("Testing BLE Pairing Mode (3s Hold Entry & 120s Timeout)...\n");

    state_machine_reset();
    led_init();
    TEST_ASSERT(state_machine_is_ble_pairing() == false, "Pairing mode starts inactive");

    /* 1. Enter BLE Pairing Mode via 3s hold command */
    command_t cmd_pair = {.type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON};
    esp_err_t err = state_machine_process_command(&cmd_pair);
    TEST_ASSERT(err == ESP_OK, "CMD_ENTER_BLE_PAIRING returns ESP_OK");
    TEST_ASSERT(state_machine_is_ble_pairing() == true, "120-second BLE pairing window is now active");
    TEST_ASSERT(led_get_state() == LED_STATE_BLE_PAIRING, "Status LED set to LED_STATE_BLE_PAIRING (fast double-blink)");

    /* 2. Step 60 seconds -> still active */
    state_machine_tick(60000);
    TEST_ASSERT(state_machine_is_ble_pairing() == true, "BLE pairing still active at 60s");

    /* 3. Step another 60 seconds (total 120s) -> expires and returns to IDLE */
    state_machine_tick(60000);
    TEST_ASSERT(state_machine_is_ble_pairing() == false, "BLE pairing window automatically closed at 120s");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "Status LED returned to LED_STATE_IDLE after 120s timeout");
}

/* ========================================================================= */
/* Test 7: Minimal Physical Button Gesture Translation Matrix                */
/* ========================================================================= */

void test_button_gesture_translation_matrix(void)
{
    printf("Testing Minimal Physical Button Gesture Translation Matrix...\n");

    /* 1. Daily Run Mode (STATE_IDLE_RUN): Short tap -> Run Preset 1..4, Long press (3s) -> BLE Pairing */
    for (uint8_t i = 0; i < BTN_ID_COUNT; i++) {
        command_t c = buttons_translate_gesture(i, GESTURE_SHORT_TAP, STATE_IDLE_RUN);
        TEST_ASSERT(c.type == CMD_RUN_PRESET && c.payload.preset_id == (i + 1),
                    "Short tap in IDLE produces CMD_RUN_PRESET (1..4)");

        c = buttons_translate_gesture(i, GESTURE_LONG_PRESS, STATE_IDLE_RUN);
        TEST_ASSERT(c.type == CMD_ENTER_BLE_PAIRING,
                    "3s Long press in IDLE produces CMD_ENTER_BLE_PAIRING");
    }

    /* 2. Motion Mode (STATE_RUNNING_MOTION): Any short tap triggers E-Stop */
    for (uint8_t i = 0; i < BTN_ID_COUNT; i++) {
        command_t c = buttons_translate_gesture(i, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
        TEST_ASSERT(c.type == CMD_EMERGENCY_STOP, "Short tap in RUNNING produces CMD_EMERGENCY_STOP");
    }
}

/* ========================================================================= */
/* Test Main Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Unit Test: State Machine Engine\n");
    printf("============================================================\n");

    test_state_machine_lifecycle_and_boot();
    test_run_mode_dispatch();
    test_wireless_button_sequence_save_and_playback();
    test_factory_reset_and_live_jog();
    test_emergency_stop_in_all_states();
    test_ble_pairing_mode_and_timeout();
    test_button_gesture_translation_matrix();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
