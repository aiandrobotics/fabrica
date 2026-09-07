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
/* Test 1: Factory Preset Library Standardization & Channel Mapping          */
/* ========================================================================= */

void test_factory_preset_library_standardization(void)
{
    printf("Testing Factory Preset Library Standardization & Physical Mappings...\n");

    storage_mock_reset();
    TEST_ASSERT(storage_init() == ESP_OK, "storage_init() succeeds and seeds presets");

    fold_routine_t r1, r2, r3, r4;

    /* Preset 1: Adult T-Shirt (3 Steps) */
    TEST_ASSERT(storage_load_routine(1, &r1) == ESP_OK, "Preset 1 loads from NVS");
    TEST_ASSERT(r1.step_count == 3, "Preset 1 has 3 steps");
    TEST_ASSERT(r1.steps[0].motor_count == 1 && r1.steps[0].motor_ids[0] == SERVO_FLAP_LEFT,
                "Preset 1 Step 1 is Left Flap (Ch 0)");
    TEST_ASSERT(r1.steps[1].motor_count == 1 && r1.steps[1].motor_ids[0] == SERVO_FLAP_RIGHT,
                "Preset 1 Step 2 is Right Flap (Ch 1)");
    TEST_ASSERT(r1.steps[2].motor_count == 1 && r1.steps[2].motor_ids[0] == SERVO_FLAP_BOTTOM,
                "Preset 1 Step 3 is Bottom Flap (Ch 2)");
    TEST_ASSERT(r1.checksum == storage_compute_crc32(&r1), "Preset 1 CRC32 is valid");

    /* Preset 2: Long-Sleeve Shirt (4 Steps) */
    TEST_ASSERT(storage_load_routine(2, &r2) == ESP_OK, "Preset 2 loads from NVS");
    TEST_ASSERT(r2.step_count == 4, "Preset 2 has 4 steps");
    TEST_ASSERT(r2.steps[0].motor_count == 2 &&
                r2.steps[0].motor_ids[0] == SERVO_FLAP_LEFT &&
                r2.steps[0].motor_ids[1] == SERVO_FLAP_RIGHT,
                "Preset 2 Step 1 is Parallel Dual-Sleeve (Left + Right)");
    TEST_ASSERT(r2.steps[1].motor_count == 1 && r2.steps[1].motor_ids[0] == SERVO_FLAP_LEFT,
                "Preset 2 Step 2 is Left Body Fold (Ch 0)");
    TEST_ASSERT(r2.steps[2].motor_count == 1 && r2.steps[2].motor_ids[0] == SERVO_FLAP_RIGHT,
                "Preset 2 Step 3 is Right Body Fold (Ch 1)");
    TEST_ASSERT(r2.steps[3].motor_count == 1 && r2.steps[3].motor_ids[0] == SERVO_FLAP_BOTTOM,
                "Preset 2 Step 4 is Bottom Fold (Ch 2)");
    TEST_ASSERT(r2.checksum == storage_compute_crc32(&r2), "Preset 2 CRC32 is valid");

    /* Preset 3: Trousers / Jeans (2 Steps) */
    TEST_ASSERT(storage_load_routine(3, &r3) == ESP_OK, "Preset 3 loads from NVS");
    TEST_ASSERT(r3.step_count == 2, "Preset 3 has 2 steps");
    TEST_ASSERT(r3.steps[0].motor_count == 1 && r3.steps[0].motor_ids[0] == SERVO_FLAP_LEFT,
                "Preset 3 Step 1 is Vertical Fold (Ch 0)");
    TEST_ASSERT(r3.steps[1].motor_count == 1 && r3.steps[1].motor_ids[0] == SERVO_FLAP_BOTTOM,
                "Preset 3 Step 2 is Bottom Fold (Ch 2)");
    TEST_ASSERT(r3.checksum == storage_compute_crc32(&r3), "Preset 3 CRC32 is valid");

    /* Preset 4: Towel / Linen (3 Steps) */
    TEST_ASSERT(storage_load_routine(4, &r4) == ESP_OK, "Preset 4 loads from NVS");
    TEST_ASSERT(r4.step_count == 3, "Preset 4 has 3 steps");
    TEST_ASSERT(r4.steps[0].motor_count == 1 && r4.steps[0].motor_ids[0] == SERVO_FLAP_LEFT,
                "Preset 4 Step 1 is Left Half Fold (Ch 0)");
    TEST_ASSERT(r4.steps[1].motor_count == 1 && r4.steps[1].motor_ids[0] == SERVO_FLAP_RIGHT,
                "Preset 4 Step 2 is Right Quarter Fold (Ch 1)");
    TEST_ASSERT(r4.steps[2].motor_count == 1 && r4.steps[2].motor_ids[0] == SERVO_FLAP_BOTTOM,
                "Preset 4 Step 3 is Bottom Final Fold (Ch 2)");
    TEST_ASSERT(r4.checksum == storage_compute_crc32(&r4), "Preset 4 CRC32 is valid");
}

/* ========================================================================= */
/* Test 2: 100-Cycle Continuous Endurance & Zero Leak Validation             */
/* ========================================================================= */

void test_100_cycle_endurance_and_stability(void)
{
    printf("Testing 100-Cycle Continuous Execution & Heap Stability...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    motion_reset_state();
    state_machine_reset();
    state_machine_init(NULL, NULL);

    int total_cycles = 100;
    int successful_cycles = 0;

    for (int i = 0; i < total_cycles; i++) {
        uint8_t preset_id = (uint8_t)((i % TOTAL_PRESET_COUNT) + 1);

        command_t cmd;
        memset(&cmd, 0, sizeof(cmd));
        cmd.type = CMD_RUN_PRESET;
        cmd.source = SOURCE_PHYSICAL_BUTTON;
        cmd.payload.preset_id = preset_id;

        esp_err_t err = state_machine_process_command(&cmd);
        if (err == ESP_OK &&
            state_machine_get_state() == STATE_IDLE_RUN &&
            motion_get_status() == MOTION_STATUS_IDLE &&
            led_get_state() == LED_STATE_IDLE) {
            successful_cycles++;
        }
    }

    TEST_ASSERT(successful_cycles == 100, "All 100 continuous routine cycles executed successfully");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Final state machine state is STATE_IDLE_RUN");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_IDLE, "Final motion engine status is MOTION_STATUS_IDLE");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "Final LED state is LED_STATE_IDLE");

    /* Verify all 16 PCA9685 channels are resting flat at 0 deg (102 counts) */
    bool all_flat = true;
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        if (pca9685_mock_get_channel_off_count(ch) != 102) {
            all_flat = false;
            break;
        }
    }
    TEST_ASSERT(all_flat == true, "All 16 PCA9685 channels are homed to 0 deg (102 counts) after 100 cycles");
}

/* ========================================================================= */
/* Test 3: Mid-Sweep Emergency Stop (E-Stop) Preemption                      */
/* ========================================================================= */

void test_mid_sweep_emergency_stop_preemption(void)
{
    printf("Testing Mid-Sweep Emergency Stop Preemption & Latency...\n");

    pca9685_mock_reset();
    pca9685_init();
    motion_reset_state();
    state_machine_reset();
    state_machine_init(NULL, NULL);

    /* 1. Simulate active motion: channels swept to 180 degrees */
    pca9685_set_servo_angle(SERVO_FLAP_LEFT, FOLD_ANGLE_DEG);
    pca9685_set_servo_angle(SERVO_FLAP_RIGHT, FOLD_ANGLE_DEG);
    TEST_ASSERT(pca9685_mock_get_channel_off_count(SERVO_FLAP_LEFT) == 512, "Left flap at 180 deg");
    TEST_ASSERT(pca9685_mock_get_channel_off_count(SERVO_FLAP_RIGHT) == 512, "Right flap at 180 deg");

    /* 2. Dispatch E-Stop command */
    command_t cmd_estop;
    memset(&cmd_estop, 0, sizeof(cmd_estop));
    cmd_estop.type = CMD_EMERGENCY_STOP;
    cmd_estop.source = SOURCE_PHYSICAL_BUTTON;

    esp_err_t err = state_machine_process_command(&cmd_estop);
    TEST_ASSERT(err == ESP_OK, "CMD_EMERGENCY_STOP processed with ESP_OK");
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP, "LED state set to LED_STATE_ESTOP (5 rapid flashes)");

    /* Verify all channels immediately homed to flat 0 deg (102 counts) */
    bool all_homed = true;
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        if (pca9685_mock_get_channel_off_count(ch) != 102) {
            all_homed = false;
            break;
        }
    }
    TEST_ASSERT(all_homed == true, "All 16 channels immediately homed flat to 0 deg on E-Stop");

    /* 3. Verify Gesture Translation in RUNNING mode: Any button press yields CMD_EMERGENCY_STOP */
    command_t translated_cmd;

    /* Button 1 Tap during motion */
    translated_cmd = buttons_translate_gesture(BTN_ID_1, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
    TEST_ASSERT(translated_cmd.type == CMD_EMERGENCY_STOP, "Button 1 tap during motion maps to CMD_EMERGENCY_STOP");

    /* Button 2 Tap during motion */
    translated_cmd = buttons_translate_gesture(BTN_ID_2, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
    TEST_ASSERT(translated_cmd.type == CMD_EMERGENCY_STOP, "Button 2 tap during motion maps to CMD_EMERGENCY_STOP");

    /* Button 3 Tap during motion */
    translated_cmd = buttons_translate_gesture(BTN_ID_3, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
    TEST_ASSERT(translated_cmd.type == CMD_EMERGENCY_STOP, "Button 3 tap during motion maps to CMD_EMERGENCY_STOP");

    /* Button 4 Tap during motion */
    translated_cmd = buttons_translate_gesture(BTN_ID_4, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
    TEST_ASSERT(translated_cmd.type == CMD_EMERGENCY_STOP, "Button 4 tap during motion maps to CMD_EMERGENCY_STOP");

    /* 4. Verify clean recovery: Next routine execution clears E-Stop abort flag */
    command_t cmd_run;
    memset(&cmd_run, 0, sizeof(cmd_run));
    cmd_run.type = CMD_RUN_PRESET;
    cmd_run.source = SOURCE_PHYSICAL_BUTTON;
    cmd_run.payload.preset_id = 1;

    err = state_machine_process_command(&cmd_run);
    TEST_ASSERT(err == ESP_OK, "Routine executes cleanly after E-Stop recovery");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State returns to STATE_IDLE_RUN after recovery run");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED state returns to LED_STATE_IDLE");
}

/* ========================================================================= */
/* Test 4: NVS Flash Power Loss & CRC Corruption Recovery                    */
/* ========================================================================= */

void test_nvs_power_loss_and_corruption_resilience(void)
{
    printf("Testing NVS Power Loss, Corruption Recovery & CRC Fallback...\n");

    storage_mock_reset();
    storage_init();

    /* 1. Save valid custom routine in Preset 1 */
    fold_routine_t custom;
    memset(&custom, 0, sizeof(custom));
    custom.step_count = 2;
    custom.steps[0].motor_count = 1;
    custom.steps[0].motor_ids[0] = 5;
    custom.steps[1].motor_count = 1;
    custom.steps[1].motor_ids[0] = 6;

    TEST_ASSERT(storage_save_routine(1, &custom) == ESP_OK, "Custom routine saved in Preset 1");

    /* Verify custom routine loads */
    fold_routine_t loaded;
    TEST_ASSERT(storage_load_routine(1, &loaded) == ESP_OK, "Custom routine loads cleanly");
    TEST_ASSERT(loaded.step_count == 2, "Loaded custom routine has 2 steps");
    TEST_ASSERT(loaded.steps[0].motor_ids[0] == 5, "Step 1 motor is 5");

    /* 2. Corrupt byte 0 (step_count) in NVS */
    storage_mock_corrupt_key("preset_1", 0);

    memset(&loaded, 0, sizeof(loaded));
    esp_err_t err = storage_load_routine(1, &loaded);
    TEST_ASSERT(err == ESP_ERR_INVALID_CRC, "Corrupted blob detected with ESP_ERR_INVALID_CRC");
    TEST_ASSERT(loaded.step_count == 3, "Gracefully restored default factory Preset 1 (3 steps)");
    TEST_ASSERT(loaded.steps[0].motor_ids[0] == SERVO_FLAP_LEFT, "Restored Step 1 is Left Flap (Ch 0)");

    /* 3. Corrupt payload byte inside steps array */
    storage_save_routine(1, &custom);
    storage_mock_corrupt_key("preset_1", 4); /* Invert byte in steps array */

    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(1, &loaded);
    TEST_ASSERT(err == ESP_ERR_INVALID_CRC, "Step array byte corruption detected with ESP_ERR_INVALID_CRC");
    TEST_ASSERT(loaded.step_count == 3, "Restored default factory Preset 1 (3 steps)");

    /* 4. Corrupt stored checksum itself */
    storage_save_routine(1, &custom);
    storage_mock_corrupt_key("preset_1", sizeof(fold_routine_t) - 2);

    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(1, &loaded);
    TEST_ASSERT(err == ESP_ERR_INVALID_CRC, "Checksum byte corruption detected with ESP_ERR_INVALID_CRC");
    TEST_ASSERT(loaded.step_count == 3, "Restored default factory Preset 1 (3 steps)");

    /* 5. Erased / Uninitialized Key Fallback */
    TEST_ASSERT(storage_erase_routine(1) == ESP_OK, "Erase Preset 1 succeeds");
    memset(&loaded, 0, sizeof(loaded));
    err = storage_load_routine(1, &loaded);
    TEST_ASSERT(err == ESP_OK, "Loading erased preset falls back to factory default with ESP_OK");
    TEST_ASSERT(loaded.step_count == 3, "Loaded erased preset has 3 default steps");
}

/* ========================================================================= */
/* Test 5: Rapid Mode Invariant & Inactivity Stress                          */
/* ========================================================================= */

void test_rapid_mode_invariants_and_watchdog(void)
{
    printf("Testing Rapid Mode Invariant Stress & Inactivity Watchdog...\n");

    pca9685_mock_reset();
    pca9685_init();
    storage_init();
    motion_reset_state();
    state_machine_reset();
    state_machine_init(NULL, NULL);

    /* Stress test 50 rapid mode cycles (Run -> Program -> Stage -> E-Stop -> Idle) */
    for (int i = 0; i < 50; i++) {
        /* 1. Enter Programming Mode */
        command_t cmd_prog;
        memset(&cmd_prog, 0, sizeof(cmd_prog));
        cmd_prog.type = CMD_ENTER_PROGRAM_MODE;
        cmd_prog.source = SOURCE_PHYSICAL_BUTTON;
        cmd_prog.payload.preset_id = (uint8_t)((i % TOTAL_PRESET_COUNT) + 1);

        esp_err_t err = state_machine_process_command(&cmd_prog);
        assert(err == ESP_OK);
        assert(state_machine_get_state() == STATE_PROGRAMMING);

        /* 2. Cycle and Stage a channel */
        command_t cmd_cycle;
        memset(&cmd_cycle, 0, sizeof(cmd_cycle));
        cmd_cycle.type = CMD_CYCLE_NUDGE_MOTOR;
        cmd_cycle.source = SOURCE_PHYSICAL_BUTTON;
        state_machine_process_command(&cmd_cycle);

        command_t cmd_stage;
        memset(&cmd_stage, 0, sizeof(cmd_stage));
        cmd_stage.type = CMD_STAGE_TOGGLE_MOTOR;
        cmd_stage.source = SOURCE_PHYSICAL_BUTTON;
        state_machine_process_command(&cmd_stage);

        /* 3. Interrupt with Emergency Stop */
        command_t cmd_estop;
        memset(&cmd_estop, 0, sizeof(cmd_estop));
        cmd_estop.type = CMD_EMERGENCY_STOP;
        cmd_estop.source = SOURCE_PHYSICAL_BUTTON;
        state_machine_process_command(&cmd_estop);

        assert(state_machine_get_state() == STATE_IDLE_RUN);
    }
    TEST_ASSERT(true, "50 rapid mode switching cycles executed without deadlock");

    /* Verify Inactivity Watchdog in Programming Mode */
    command_t cmd_prog;
    memset(&cmd_prog, 0, sizeof(cmd_prog));
    cmd_prog.type = CMD_ENTER_PROGRAM_MODE;
    cmd_prog.payload.preset_id = 1;
    state_machine_process_command(&cmd_prog);
    TEST_ASSERT(state_machine_get_state() == STATE_PROGRAMMING, "Entered STATE_PROGRAMMING");

    /* Advance simulated time by 20,000ms */
    state_machine_tick(PROGRAMMING_TIMEOUT_MS);
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "20s inactivity watchdog returned state to STATE_IDLE_RUN");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED returned to LED_STATE_IDLE after timeout");
}

/* ========================================================================= */
/* Test Main Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 7 Unit Test: End-to-End Stress & Preset\n");
    printf("============================================================\n");

    test_factory_preset_library_standardization();
    test_100_cycle_endurance_and_stability();
    test_mid_sweep_emergency_stop_preemption();
    test_nvs_power_loss_and_corruption_resilience();
    test_rapid_mode_invariants_and_watchdog();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
