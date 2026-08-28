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
    TEST_ASSERT(state_machine_init(NULL, NULL) == ESP_OK, "state_machine_init() returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Initial state is STATE_IDLE_RUN");

    const staging_context_t *ctx = state_machine_get_context();
    TEST_ASSERT(ctx != NULL, "state_machine_get_context() returns non-null context");
    TEST_ASSERT(ctx->target_preset_id == 0, "Initial target_preset_id is 0");
    TEST_ASSERT(ctx->current_channel_idx == 0, "Initial current_channel_idx is 0");
    TEST_ASSERT(ctx->cursor_active == false, "Initial cursor_active is false");
    TEST_ASSERT(ctx->staged_motor_count == 0, "Initial staged_motor_count is 0");
    TEST_ASSERT(ctx->buffer_routine.step_count == 0, "Initial buffer step_count is 0");

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
/* Test 3: Enter Visual Staging Programming Mode                             */
/* ========================================================================= */

void test_enter_programming_mode(void)
{
    printf("Testing Entry into Visual Staging Programming Mode...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();
    state_machine_reset();

    /* Long press on B2 -> Enter Programming Mode for Preset 2 */
    command_t cmd_prog;
    memset(&cmd_prog, 0, sizeof(cmd_prog));
    cmd_prog.type = CMD_ENTER_PROGRAM_MODE;
    cmd_prog.payload.preset_id = 2;

    esp_err_t err = state_machine_process_command(&cmd_prog);
    TEST_ASSERT(err == ESP_OK, "CMD_ENTER_PROGRAM_MODE (Preset 2) returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_PROGRAMMING, "State transitioned to STATE_PROGRAMMING");
    TEST_ASSERT(led_get_state() == LED_STATE_PROGRAMMING, "LED state transitioned to LED_STATE_PROGRAMMING (slow blink)");

    const staging_context_t *ctx = state_machine_get_context();
    TEST_ASSERT(ctx->target_preset_id == 2, "Target preset ID is set to 2");
    TEST_ASSERT(ctx->current_channel_idx == 0, "Current servo channel cursor reset to 0");
    TEST_ASSERT(ctx->cursor_active == false, "Cursor active is false on entry");
    TEST_ASSERT(ctx->staged_motor_count == 0, "Staged motor count initialized to 0");
    TEST_ASSERT(ctx->buffer_routine.step_count == 0, "Temporary routine step count initialized to 0");

    /* Verify all channels homed to 0 deg */
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        TEST_ASSERT(pca9685_mock_get_channel_off_count(ch) == 102, "Channel homed to 102 counts (0 deg) on mode entry");
    }

    /* Invalid preset ID on entry */
    state_machine_reset();
    cmd_prog.payload.preset_id = 0;
    TEST_ASSERT(state_machine_process_command(&cmd_prog) == ESP_ERR_INVALID_ARG, "Preset 0 programming entry rejected with ESP_ERR_INVALID_ARG");
}

/* ========================================================================= */
/* Test 4: Channel Cycling and 15-degree Nudge (B1)                          */
/* ========================================================================= */

void test_b1_cycle_nudge_channels(void)
{
    printf("Testing B1 (CYCLE / NUDGE) Channel Traversal & Nudge Pulses...\n");

    pca9685_mock_reset();
    pca9685_init();
    state_machine_reset();

    /* Enter Programming Mode for Preset 1 */
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.type = CMD_ENTER_PROGRAM_MODE;
    cmd.payload.preset_id = 1;
    state_machine_process_command(&cmd);

    /* B1 Short Tap: Cycle Nudge Motor */
    command_t cmd_b1;
    memset(&cmd_b1, 0, sizeof(cmd_b1));
    cmd_b1.type = CMD_CYCLE_NUDGE_MOTOR;

    /* First tap: selects Motor 1 (Channel 0) and pulses nudge */
    esp_err_t err = state_machine_process_command(&cmd_b1);
    TEST_ASSERT(err == ESP_OK, "CMD_CYCLE_NUDGE_MOTOR returns ESP_OK");
    const staging_context_t *ctx = state_machine_get_context();
    TEST_ASSERT(ctx->current_channel_idx == 0, "First B1 tap selects Channel 0 (Motor 1)");
    TEST_ASSERT(ctx->cursor_active == true, "Cursor is now active");
    /* Nudge angle 15 deg = ~137 counts */
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 137, "Channel 0 received 15 deg nudge count (137)");

    /* Second tap: advances to Motor 2 (Channel 1) */
    state_machine_process_command(&cmd_b1);
    TEST_ASSERT(ctx->current_channel_idx == 1, "Second B1 tap advanced to Channel 1 (Motor 2)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(1) == 137, "Channel 1 received 15 deg nudge count (137)");

    /* Cycle through remaining channels 2..15 */
    for (uint8_t expected_ch = 2; expected_ch < TOTAL_SERVO_CHANNELS; expected_ch++) {
        state_machine_process_command(&cmd_b1);
        TEST_ASSERT(ctx->current_channel_idx == expected_ch, "Channel cursor advanced sequentially");
        TEST_ASSERT(pca9685_mock_get_channel_off_count(expected_ch) == 137, "Nudge count (137) applied to channel");
    }

    /* Wrap around to channel 0 on 17th tap */
    state_machine_process_command(&cmd_b1);
    TEST_ASSERT(ctx->current_channel_idx == 0, "Channel cursor wrapped around from 15 to 0");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 137, "Channel 0 received 15 deg nudge count (137)");
}

/* ========================================================================= */
/* Test 5: Flap Staging Toggle (B2) and 2-Motor Safeguard                     */
/* ========================================================================= */

void test_b2_staging_toggle_and_limits(void)
{
    printf("Testing B2 (STAGE / TOGGLE) 30-degree Hold and 2-Motor Limit...\n");

    pca9685_mock_reset();
    pca9685_init();
    state_machine_reset();

    /* Enter Programming Mode for Preset 1 */
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.type = CMD_ENTER_PROGRAM_MODE;
    cmd.payload.preset_id = 1;
    state_machine_process_command(&cmd);

    const staging_context_t *ctx = state_machine_get_context();
    command_t cmd_b1 = {.type = CMD_CYCLE_NUDGE_MOTOR};
    command_t cmd_b2 = {.type = CMD_STAGE_TOGGLE_MOTOR};

    /* Channel cursor is currently 0 */
    /* 1. Stage Channel 0 to 30 deg */
    esp_err_t err = state_machine_process_command(&cmd_b2);
    TEST_ASSERT(err == ESP_OK, "CMD_STAGE_TOGGLE_MOTOR (Stage Ch 0) returns ESP_OK");
    TEST_ASSERT(ctx->staged_motor_count == 1, "Staged motor count is 1");
    TEST_ASSERT(ctx->staged_motor_ids[0] == 0, "Staged motor ID is 0");
    /* 30 deg stage count = ~171 counts */
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 171, "Channel 0 lifted to 30 deg stage count (171)");

    /* 2. Toggle OFF (Unstage Channel 0) */
    err = state_machine_process_command(&cmd_b2);
    TEST_ASSERT(err == ESP_OK, "CMD_STAGE_TOGGLE_MOTOR (Unstage Ch 0) returns ESP_OK");
    TEST_ASSERT(ctx->staged_motor_count == 0, "Staged motor count returned to 0");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 102, "Channel 0 returned flat to 0 deg (102 counts)");

    /* 3. Re-stage Channel 0 */
    state_machine_process_command(&cmd_b2);
    TEST_ASSERT(ctx->staged_motor_count == 1, "Channel 0 re-staged");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 171, "Channel 0 at 30 deg");

    /* 4. Advance to Channel 3 and Stage Channel 3 (Parallel 2-motor step) */
    state_machine_process_command(&cmd_b1); /* Ch 1 */
    state_machine_process_command(&cmd_b1); /* Ch 2 */
    state_machine_process_command(&cmd_b1); /* Ch 3 */
    TEST_ASSERT(ctx->current_channel_idx == 3, "Cursor is at Channel 3");

    err = state_machine_process_command(&cmd_b2);
    TEST_ASSERT(err == ESP_OK, "Stage Channel 3 returns ESP_OK");
    TEST_ASSERT(ctx->staged_motor_count == 2, "Staged motor count is 2");
    TEST_ASSERT(ctx->staged_motor_ids[0] == 0 && ctx->staged_motor_ids[1] == 3, "Staged motor IDs are {0, 3}");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 171, "Channel 0 remains at 30 deg");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(3) == 171, "Channel 3 is at 30 deg");

    /* 5. Attempt to Stage a 3rd Motor (Channel 5) -> REJECTION */
    state_machine_process_command(&cmd_b1); /* Ch 4 */
    state_machine_process_command(&cmd_b1); /* Ch 5 */
    TEST_ASSERT(ctx->current_channel_idx == 5, "Cursor is at Channel 5");

    err = state_machine_process_command(&cmd_b2);
    TEST_ASSERT(err == ESP_ERR_INVALID_STATE, "3rd motor stage rejected with ESP_ERR_INVALID_STATE");
    TEST_ASSERT(ctx->staged_motor_count == 2, "Staged motor count remains 2");
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR, "LED state set to LED_STATE_INPUT_ERROR (3 fast flashes)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(5) == 137, "Channel 5 was not lifted to 30 deg (remains at nudge count)");
}

/* ========================================================================= */
/* Test 6: Step Locking (B3) and Empty Step Guard                            */
/* ========================================================================= */

void test_b3_step_locking_and_homing(void)
{
    printf("Testing B3 (NEXT STEP / LOCK) and Step Buffering...\n");

    pca9685_mock_reset();
    pca9685_init();
    state_machine_reset();

    /* Enter Programming Mode */
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.type = CMD_ENTER_PROGRAM_MODE;
    cmd.payload.preset_id = 1;
    state_machine_process_command(&cmd);

    const staging_context_t *ctx = state_machine_get_context();
    command_t cmd_b1 = {.type = CMD_CYCLE_NUDGE_MOTOR};
    command_t cmd_b2 = {.type = CMD_STAGE_TOGGLE_MOTOR};
    command_t cmd_b3 = {.type = CMD_LOCK_STEP};

    /* 1. Empty Step Lock Rejection (0 staged motors) */
    TEST_ASSERT(ctx->staged_motor_count == 0, "No motors currently staged");
    esp_err_t err = state_machine_process_command(&cmd_b3);
    TEST_ASSERT(err == ESP_ERR_INVALID_STATE, "Locking empty step rejected with ESP_ERR_INVALID_STATE");
    TEST_ASSERT(ctx->buffer_routine.step_count == 0, "Buffer step_count remains 0");

    /* 2. Stage Channel 1 and Lock Step 1 */
    state_machine_process_command(&cmd_b1); /* First press -> Ch 0 */
    state_machine_process_command(&cmd_b1); /* Second press -> Ch 1 */
    state_machine_process_command(&cmd_b2); /* Stage Ch 1 */
    TEST_ASSERT(ctx->staged_motor_count == 1, "Channel 1 staged");

    err = state_machine_process_command(&cmd_b3);
    TEST_ASSERT(err == ESP_OK, "CMD_LOCK_STEP for Step 1 returns ESP_OK");
    TEST_ASSERT(ctx->buffer_routine.step_count == 1, "Buffer step_count incremented to 1");
    TEST_ASSERT(ctx->buffer_routine.steps[0].motor_count == 1, "Step 1 has motor_count == 1");
    TEST_ASSERT(ctx->buffer_routine.steps[0].motor_ids[0] == 1, "Step 1 has motor_id == 1");
    TEST_ASSERT(ctx->staged_motor_count == 0, "Staged motor count cleared to 0");
    TEST_ASSERT(ctx->cursor_active == false, "Cursor reset to unselected for next step");
    TEST_ASSERT(led_get_state() == LED_STATE_STEP_LOCKED, "LED state set to LED_STATE_STEP_LOCKED (2 fast flashes)");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(1) == 102, "Channel 1 dropped flat to 0 deg (102 counts)");

    /* 3. Stage Channel 2 & Channel 4 (Parallel) and Lock Step 2 */
    state_machine_process_command(&cmd_b1); /* First press of Step 2 -> Ch 0 */
    state_machine_process_command(&cmd_b1); /* Ch 1 */
    state_machine_process_command(&cmd_b1); /* Ch 2 */
    state_machine_process_command(&cmd_b2); /* Stage Ch 2 */
    state_machine_process_command(&cmd_b1); /* Ch 3 */
    state_machine_process_command(&cmd_b1); /* Ch 4 */
    state_machine_process_command(&cmd_b2); /* Stage Ch 4 */
    TEST_ASSERT(ctx->staged_motor_count == 2, "Channels 2 and 4 staged");

    err = state_machine_process_command(&cmd_b3);
    TEST_ASSERT(err == ESP_OK, "CMD_LOCK_STEP for Step 2 returns ESP_OK");
    TEST_ASSERT(ctx->buffer_routine.step_count == 2, "Buffer step_count incremented to 2");
    TEST_ASSERT(ctx->buffer_routine.steps[1].motor_count == 2, "Step 2 has motor_count == 2");
    TEST_ASSERT(ctx->buffer_routine.steps[1].motor_ids[0] == 2, "Step 2 motor 0 is Ch 2");
    TEST_ASSERT(ctx->buffer_routine.steps[1].motor_ids[1] == 4, "Step 2 motor 1 is Ch 4");
    TEST_ASSERT(ctx->staged_motor_count == 0, "Staged motor count cleared to 0");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(2) == 102, "Channel 2 dropped to 0 deg");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(4) == 102, "Channel 4 dropped to 0 deg");
}

/* ========================================================================= */
/* Test 7: Manual Save & Exit (B4) and Immediate Playback                    */
/* ========================================================================= */

void test_b4_save_exit_and_playback(void)
{
    printf("Testing B4 (SAVE & EXIT), NVS Persistence & Run Mode Playback...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    motion_reset_state();
    state_machine_reset();

    /* Enter Programming Mode for Preset 3 */
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.type = CMD_ENTER_PROGRAM_MODE;
    cmd.payload.preset_id = 3;
    state_machine_process_command(&cmd);

    command_t cmd_b1 = {.type = CMD_CYCLE_NUDGE_MOTOR};
    command_t cmd_b2 = {.type = CMD_STAGE_TOGGLE_MOTOR};
    command_t cmd_b3 = {.type = CMD_LOCK_STEP};
    command_t cmd_b4 = {.type = CMD_SAVE_EXIT_PROGRAM};

    /* Program Step 1: Ch 7 (Press B1 8 times: Ch 0, 1, 2, 3, 4, 5, 6, 7) */
    for (int i = 0; i <= 7; i++) state_machine_process_command(&cmd_b1);
    state_machine_process_command(&cmd_b2); /* Stage Ch 7 */
    state_machine_process_command(&cmd_b3); /* Lock Step 1 */

    /* Program Step 2: Ch 8 & Ch 9 */
    for (int i = 0; i <= 8; i++) state_machine_process_command(&cmd_b1); /* Reaches Ch 8 */
    state_machine_process_command(&cmd_b2); /* Stage Ch 8 */
    state_machine_process_command(&cmd_b1); /* Ch 9 */
    state_machine_process_command(&cmd_b2); /* Stage Ch 9 */
    state_machine_process_command(&cmd_b3); /* Lock Step 2 */

    /* Commit with B4 (SAVE & EXIT) */
    esp_err_t err = state_machine_process_command(&cmd_b4);
    TEST_ASSERT(err == ESP_OK, "CMD_SAVE_EXIT_PROGRAM returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State machine returned to STATE_IDLE_RUN");
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS, "LED state set to LED_STATE_SAVE_SUCCESS (2.0s solid ON)");

    /* Verify stored sequence in NVS */
    fold_routine_t loaded;
    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(3, &loaded);
    TEST_ASSERT(err == ESP_OK, "storage_load_routine(3) loads newly programmed sequence");
    TEST_ASSERT(loaded.step_count == 2, "Loaded routine has 2 steps");
    TEST_ASSERT(loaded.steps[0].motor_count == 1 && loaded.steps[0].motor_ids[0] == 7, "Loaded Step 1 is Ch 7");
    TEST_ASSERT(loaded.steps[1].motor_count == 2 && loaded.steps[1].motor_ids[0] == 8 && loaded.steps[1].motor_ids[1] == 9, "Loaded Step 2 is Ch 8 & 9");

    /* Execute the newly programmed routine in Daily Run Mode */
    command_t cmd_run = {.type = CMD_RUN_PRESET, .payload.preset_id = 3};
    err = state_machine_process_command(&cmd_run);
    TEST_ASSERT(err == ESP_OK, "Newly saved Preset 3 executes cleanly in Daily Run Mode");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Returned to STATE_IDLE_RUN after execution");
}

/* ========================================================================= */
/* Test 8: 16-Step Maximum Cap Auto-Commit                                    */
/* ========================================================================= */

void test_16_step_cap_auto_commit(void)
{
    printf("Testing 16-Step Maximum Cap Auto-Commit to NVS...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    state_machine_reset();

    /* Enter Programming Mode for Preset 4 */
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.type = CMD_ENTER_PROGRAM_MODE;
    cmd.payload.preset_id = 4;
    state_machine_process_command(&cmd);

    command_t cmd_b1 = {.type = CMD_CYCLE_NUDGE_MOTOR};
    command_t cmd_b2 = {.type = CMD_STAGE_TOGGLE_MOTOR};
    command_t cmd_b3 = {.type = CMD_LOCK_STEP};

    /* Lock 16 consecutive steps */
    for (uint8_t step = 0; step < 16; step++) {
        state_machine_process_command(&cmd_b1); /* Selects Ch 0 */
        state_machine_process_command(&cmd_b2); /* Stage Ch 0 */
        state_machine_process_command(&cmd_b3); /* Lock Step */
    }

    /* Verify auto-commit occurred upon locking 16th step */
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "16th step lock automatically returned state to STATE_IDLE_RUN");
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS, "LED state set to LED_STATE_SAVE_SUCCESS");

    /* Verify NVS contains 16 steps */
    fold_routine_t loaded;
    memset(&loaded, 0, sizeof(loaded));
    TEST_ASSERT(storage_load_routine(4, &loaded) == ESP_OK, "Preset 4 loaded from NVS");
    TEST_ASSERT(loaded.step_count == 16, "Preset 4 contains exactly 16 steps");
}

/* ========================================================================= */
/* Test 9: Inactivity Watchdog Timeout (20s) & Timer Reset                   */
/* ========================================================================= */

void test_inactivity_watchdog_timeout(void)
{
    printf("Testing 20-Second Inactivity Watchdog Timeout & Timer Resets...\n");

    pca9685_mock_reset();
    pca9685_init();
    state_machine_reset();

    /* 1. Enter Programming Mode and stage a servo */
    command_t cmd = {.type = CMD_ENTER_PROGRAM_MODE, .payload.preset_id = 1};
    state_machine_process_command(&cmd);
    command_t cmd_b2 = {.type = CMD_STAGE_TOGGLE_MOTOR};
    state_machine_process_command(&cmd_b2); /* Stage Ch 0 to 30 deg */
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 171, "Channel 0 staged at 30 deg");

    /* Advance 10 seconds -> should still be programming */
    state_machine_tick(10000);
    TEST_ASSERT(state_machine_get_state() == STATE_PROGRAMMING, "Still in STATE_PROGRAMMING after 10s");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 171, "Channel 0 still staged at 30 deg after 10s");

    /* Advance another 10 seconds (total 20s) -> timeout triggers! */
    state_machine_tick(10000);
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Inactivity timeout transitioned state to STATE_IDLE_RUN");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED returned to LED_STATE_IDLE");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 102, "Channel 0 homed to 0 deg (102 counts) on timeout");

    /* 2. Test Inactivity Timer Reset on Input */
    state_machine_process_command(&cmd);
    TEST_ASSERT(state_machine_get_state() == STATE_PROGRAMMING, "Re-entered STATE_PROGRAMMING");

    /* Advance 15 seconds */
    state_machine_tick(15000);
    /* Press B1 (CYCLE) -> resets timer */
    command_t cmd_b1 = {.type = CMD_CYCLE_NUDGE_MOTOR};
    state_machine_process_command(&cmd_b1);

    /* Advance 10 seconds more (total 25s elapsed, but only 10s since last input) */
    state_machine_tick(10000);
    TEST_ASSERT(state_machine_get_state() == STATE_PROGRAMMING, "Input at 15s reset watchdog, state remains STATE_PROGRAMMING at 25s total");

    /* Advance 10.1s more -> now 20.1s since input -> triggers timeout */
    state_machine_tick(10100);
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Timeout triggers after 20s of continuous inactivity");
}

/* ========================================================================= */
/* Test 10: Emergency Stop in All States                                     */
/* ========================================================================= */

void test_emergency_stop_in_all_states(void)
{
    printf("Testing Emergency Stop in Programming and Idle States...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();
    state_machine_reset();

    /* 1. E-Stop during STATE_IDLE_RUN */
    command_t cmd_estop = {.type = CMD_EMERGENCY_STOP};
    esp_err_t err = state_machine_process_command(&cmd_estop);
    TEST_ASSERT(err == ESP_OK, "CMD_EMERGENCY_STOP in IDLE returns ESP_OK");
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP, "LED state set to LED_STATE_ESTOP");

    /* 2. E-Stop during STATE_PROGRAMMING */
    command_t cmd_prog = {.type = CMD_ENTER_PROGRAM_MODE, .payload.preset_id = 2};
    state_machine_process_command(&cmd_prog);
    command_t cmd_b2 = {.type = CMD_STAGE_TOGGLE_MOTOR};
    state_machine_process_command(&cmd_b2); /* Stage Ch 0 */
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 171, "Channel 0 at 30 deg");

    err = state_machine_process_command(&cmd_estop);
    TEST_ASSERT(err == ESP_OK, "CMD_EMERGENCY_STOP in PROGRAMMING returns ESP_OK");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State returns to STATE_IDLE_RUN on E-Stop");
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP, "LED state set to LED_STATE_ESTOP");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(0) == 102, "Channel 0 dropped to 0 deg on E-Stop");
}

/* ========================================================================= */
/* Test 11: Button Gesture Translation Matrix                                */
/* ========================================================================= */

void test_button_gesture_translation_matrix(void)
{
    printf("Testing Button Gesture Translation Matrix across All States...\n");

    /* 1. Daily Run Mode (STATE_IDLE_RUN) */
    for (uint8_t i = 0; i < BTN_ID_COUNT; i++) {
        command_t c = buttons_translate_gesture(i, GESTURE_SHORT_TAP, STATE_IDLE_RUN);
        TEST_ASSERT(c.type == CMD_RUN_PRESET && c.payload.preset_id == (i + 1), "Short tap in IDLE produces CMD_RUN_PRESET");

        c = buttons_translate_gesture(i, GESTURE_LONG_PRESS, STATE_IDLE_RUN);
        TEST_ASSERT(c.type == CMD_ENTER_PROGRAM_MODE && c.payload.preset_id == (i + 1), "Long press in IDLE produces CMD_ENTER_PROGRAM_MODE");
    }

    /* 2. Motion Mode (STATE_RUNNING_MOTION) */
    for (uint8_t i = 0; i < BTN_ID_COUNT; i++) {
        command_t c = buttons_translate_gesture(i, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
        TEST_ASSERT(c.type == CMD_EMERGENCY_STOP, "Short tap in RUNNING produces CMD_EMERGENCY_STOP");
    }

    /* 3. Programming Mode (STATE_PROGRAMMING) */
    command_t c1 = buttons_translate_gesture(BTN_ID_1, GESTURE_SHORT_TAP, STATE_PROGRAMMING);
    TEST_ASSERT(c1.type == CMD_CYCLE_NUDGE_MOTOR, "B1 short tap in PROGRAMMING produces CMD_CYCLE_NUDGE_MOTOR");

    command_t c2 = buttons_translate_gesture(BTN_ID_2, GESTURE_SHORT_TAP, STATE_PROGRAMMING);
    TEST_ASSERT(c2.type == CMD_STAGE_TOGGLE_MOTOR, "B2 short tap in PROGRAMMING produces CMD_STAGE_TOGGLE_MOTOR");

    command_t c3 = buttons_translate_gesture(BTN_ID_3, GESTURE_SHORT_TAP, STATE_PROGRAMMING);
    TEST_ASSERT(c3.type == CMD_LOCK_STEP, "B3 short tap in PROGRAMMING produces CMD_LOCK_STEP");

    command_t c4 = buttons_translate_gesture(BTN_ID_4, GESTURE_SHORT_TAP, STATE_PROGRAMMING);
    TEST_ASSERT(c4.type == CMD_SAVE_EXIT_PROGRAM, "B4 short tap in PROGRAMMING produces CMD_SAVE_EXIT_PROGRAM");

    /* Long press ignored in Programming Mode */
    for (uint8_t i = 0; i < BTN_ID_COUNT; i++) {
        command_t c = buttons_translate_gesture(i, GESTURE_LONG_PRESS, STATE_PROGRAMMING);
        TEST_ASSERT(c.type == 0 && c.payload.preset_id == 0, "Long press ignored while in STATE_PROGRAMMING");
    }
}

/* ========================================================================= */
/* Test Main Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 6 Unit Test: State Machine Engine\n");
    printf("============================================================\n");

    test_state_machine_lifecycle_and_boot();
    test_run_mode_dispatch();
    test_enter_programming_mode();
    test_b1_cycle_nudge_channels();
    test_b2_staging_toggle_and_limits();
    test_b3_step_locking_and_homing();
    test_b4_save_exit_and_playback();
    test_16_step_cap_auto_commit();
    test_inactivity_watchdog_timeout();
    test_emergency_stop_in_all_states();
    test_button_gesture_translation_matrix();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
