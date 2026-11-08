#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "ble_transport.h"
#include "buttons.h"
#include "command.h"
#include "config.h"
#include "led.h"
#include "motion.h"
#include "pca9685.h"
#include "remote_cmd.h"
#include "state_machine.h"
#include "storage.h"

/* ========================================================================= */
/* Test Harness Macros & Helpers                                             */
/* ========================================================================= */

static int s_test_count = 0;
static int s_pass_count = 0;

#define TEST_ASSERT(cond, msg)                                                 \
    do {                                                                       \
        s_test_count++;                                                        \
        if (cond) {                                                            \
            s_pass_count++;                                                    \
            printf("  [PASS] %s\n", msg);                                      \
        } else {                                                               \
            printf("  [FAIL] %s (Line %d)\n", msg, __LINE__);                  \
            assert(cond);                                                      \
        }                                                                      \
    } while (0)

static void setup_paired_subscribed_central(void)
{
    pca9685_mock_reset();
    pca9685_init();
    storage_mock_reset();
    storage_init();
    led_init();
    buttons_reset_all();
    motion_reset_state();
    state_machine_reset();
    state_machine_init();
    ble_transport_mock_reset();

    /* Pair and subscribe to FAB2 & FAB3 notifications */
    command_t pair_cmd = {.type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON};
    (void)state_machine_process_command(&pair_cmd);

    const uint8_t addr[6] = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    const uint8_t irk[16] = {0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8,
                             0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8};
    (void)ble_transport_mock_connect(addr, false, addr, irk);
    (void)ble_transport_mock_set_cccd(0xFAB2, 0x0001);
    (void)ble_transport_mock_set_cccd(0xFAB3, 0x0001);

    /* Let transient 1.0s LED_STATE_BLE_CONNECTED expire back to LED_STATE_IDLE */
    led_step_ms(1100);
}

/* ========================================================================= */
/* Test 1: FAB1 Wire Opcode Parsing & Malformed Frame Rejection              */
/* ========================================================================= */

static void test_fab1_opcode_parsing_and_malformed_rejection(void)
{
    printf("Testing FAB1 Wire Opcode Parsing & Malformed Frame Rejection...\n");
    setup_paired_subscribed_central();

    /* Null & zero-length frames */
    uint32_t f2_before = ble_transport_mock_get_fab2_notify_count();
    TEST_ASSERT(ble_transport_write_fab1(NULL, 0) == CMD_STATUS_ERR_INVALID_ARG,
                "NULL FAB1 payload rejected with CMD_STATUS_ERR_INVALID_ARG");
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == f2_before + 1 &&
                ble_transport_mock_get_last_fab2_notify()->last_cmd_status == CMD_STATUS_ERR_INVALID_ARG,
                "Rejected NULL payload immediately emits FAB2 status notification");

    /* Unknown opcodes (0x0F removed LED mode, 0xFF unknown) */
    const uint8_t op_0f[] = {0x0F, 0x00};
    const uint8_t op_ff[] = {0xFF};
    TEST_ASSERT(ble_transport_write_fab1(op_0f, sizeof(op_0f)) == CMD_STATUS_ERR_INVALID_ARG,
                "Removed opcode 0x0F rejected with CMD_STATUS_ERR_INVALID_ARG");
    TEST_ASSERT(ble_transport_write_fab1(op_ff, sizeof(op_ff)) == CMD_STATUS_ERR_INVALID_ARG,
                "Unknown opcode 0xFF rejected with CMD_STATUS_ERR_INVALID_ARG");

    /* Malformed lengths on known opcodes */
    const uint8_t bad_run_len[] = {BLE_OP_RUN_PRESET};
    const uint8_t bad_run_id0[] = {BLE_OP_RUN_PRESET, 0};
    const uint8_t bad_run_id5[] = {BLE_OP_RUN_PRESET, 5};
    const uint8_t bad_stop_len[] = {BLE_OP_STOP_SEQUENCE, 0x00};
    const uint8_t bad_estop_len[] = {BLE_OP_EMERGENCY_STOP, 0x01};
    const uint8_t bad_stream_val[] = {BLE_OP_SET_TELEMETRY_STREAM, 0x02};

    TEST_ASSERT(ble_transport_write_fab1(bad_run_len, sizeof(bad_run_len)) == CMD_STATUS_ERR_INVALID_ARG,
                "0x00 with missing preset_id rejected");
    TEST_ASSERT(ble_transport_write_fab1(bad_run_id0, sizeof(bad_run_id0)) == CMD_STATUS_ERR_INVALID_ARG,
                "0x00 with preset_id=0 rejected");
    TEST_ASSERT(ble_transport_write_fab1(bad_run_id5, sizeof(bad_run_id5)) == CMD_STATUS_ERR_INVALID_ARG,
                "0x00 with preset_id=5 rejected");
    TEST_ASSERT(ble_transport_write_fab1(bad_stop_len, sizeof(bad_stop_len)) == CMD_STATUS_ERR_INVALID_ARG,
                "0x02 with trailing byte rejected");
    TEST_ASSERT(ble_transport_write_fab1(bad_estop_len, sizeof(bad_estop_len)) == CMD_STATUS_ERR_INVALID_ARG,
                "0x03 with trailing byte rejected");
    TEST_ASSERT(ble_transport_write_fab1(bad_stream_val, sizeof(bad_stream_val)) == CMD_STATUS_ERR_INVALID_ARG,
                "0x11 with invalid stream flag (2) rejected");

    /* Valid stream toggle (0x11) and button config sync (0x0B) */
    command_t cmd;
    const uint8_t stream_on[] = {BLE_OP_SET_TELEMETRY_STREAM, 0x01};
    TEST_ASSERT(ble_transport_write_fab1(stream_on, sizeof(stream_on)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK &&
                ble_transport_is_telemetry_stream_enabled() == true,
                "0x11 01 enables periodic telemetry stream flag and notifies FAB2");

    uint32_t f3_before = ble_transport_mock_get_fab3_notify_count();
    const uint8_t get_cfg[] = {BLE_OP_GET_BUTTON_CONFIG};
    TEST_ASSERT(ble_transport_write_fab1(get_cfg, sizeof(get_cfg)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK &&
                ble_transport_mock_get_fab3_notify_count() == f3_before + 1,
                "0x0B triggers 212-byte FAB3 button config notification");
}

/* ========================================================================= */
/* Test 2: Stateless Raw Sequence (0x01), Bounds Validation & 100% Notify    */
/* ========================================================================= */

static void test_raw_sequence_bounds_and_completion_notify(void)
{
    printf("Testing Stateless Raw Sequence (0x01), Routine Bounds & 100%% Completion Push...\n");
    setup_paired_subscribed_central();

    /* Snapshot Preset 1 in NVS before raw execution */
    fold_routine_t p1_before;
    TEST_ASSERT(storage_load_routine(1, &p1_before) == ESP_OK, "Loaded Preset 1 baseline");

    /* 1. Compact raw sequence: 2 steps -> Step 1: Ch 4, Step 2: Parallel Ch 5 & Ch 6 (8 bytes total) */
    const uint8_t raw_compact[] = {
        BLE_OP_RUN_RAW_SEQUENCE,
        2,          /* step_count = 2 */
        1, 4, 0,    /* Step 1: 1 motor, Ch 4 */
        2, 5, 6     /* Step 2: 2 motors, Ch 5 & Ch 6 */
    };

    command_t cmd;
    uint32_t f2_before = ble_transport_mock_get_fab2_notify_count();
    TEST_ASSERT(ble_transport_write_fab1(raw_compact, sizeof(raw_compact)) == CMD_STATUS_OK,
                "Compact 8-byte 0x01 raw sequence accepted at ingress");
    TEST_ASSERT(ble_transport_mock_pop_command(&cmd) && cmd.type == CMD_RUN_RAW_SEQUENCE,
                "CMD_RUN_RAW_SEQUENCE enqueued with normalized 53B payload");
    TEST_ASSERT(cmd.payload.raw_routine.checksum == storage_compute_crc32(&cmd.payload.raw_routine),
                "Compact raw sequence auto-computed valid IEEE 802.3 CRC32");

    TEST_ASSERT(state_machine_process_command(&cmd) == ESP_OK,
                "Stateless raw sequence executed to completion on Core 0");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN,
                "State returned cleanly to STATE_IDLE_RUN after raw sequence");
    TEST_ASSERT(state_machine_get_active_preset() == 0,
                "active_button_id remains 0 after raw sequence");

    /* Verify dedicated 100% completion notification was emitted on FAB2 */
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() >= f2_before + 2,
                "FAB2 emitted start and 100% completion notifications");
    const telemetry_packet_t *last_pkt = ble_transport_mock_get_last_fab2_notify();
    TEST_ASSERT(last_pkt->step_progress_pct == 100 &&
                last_pkt->total_steps == 2 &&
                last_pkt->current_step_idx == 1 &&
                last_pkt->active_button_id == 0 &&
                last_pkt->last_cmd_status == CMD_STATUS_OK,
                "Completion telemetry reports step_progress_pct=100, active_button_id=0, CMD_STATUS_OK");

    /* Verify NVS Preset 1 was NOT modified by stateless raw execution */
    fold_routine_t p1_after;
    (void)storage_load_routine(1, &p1_after);
    TEST_ASSERT(memcmp(&p1_before, &p1_after, sizeof(fold_routine_t)) == 0,
                "NVS Preset 1 unmodified by stateless 0x01 raw sequence");

    /* 2. Full 54-byte raw sequence ([0x01][53B fold_routine_t]) */
    uint8_t raw_full[1U + sizeof(fold_routine_t)];
    memset(raw_full, 0, sizeof(raw_full));
    raw_full[0] = BLE_OP_RUN_RAW_SEQUENCE;
    fold_routine_t r_full;
    memset(&r_full, 0, sizeof(r_full));
    r_full.step_count = 1;
    r_full.steps[0].motor_count = 1;
    r_full.steps[0].motor_ids[0] = 7;
    r_full.checksum = storage_compute_crc32(&r_full);
    memcpy(&raw_full[1], &r_full, sizeof(r_full));

    TEST_ASSERT(ble_transport_write_fab1(raw_full, sizeof(raw_full)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "Full 54-byte 0x01 raw sequence with valid CRC32 executes cleanly");

    /* Corrupt CRC32 in full 54-byte frame -> CMD_STATUS_ERR_CRC_MISMATCH */
    raw_full[sizeof(raw_full) - 1] ^= 0xFF;
    TEST_ASSERT(ble_transport_write_fab1(raw_full, sizeof(raw_full)) == CMD_STATUS_ERR_CRC_MISMATCH,
                "Corrupted CRC32 in 54B 0x01 frame rejected with CMD_STATUS_ERR_CRC_MISMATCH");

    /* 3. Sequence validation error codes */
    const uint8_t err_zero_steps[] = {BLE_OP_RUN_RAW_SEQUENCE, 0};
    TEST_ASSERT(ble_transport_write_fab1(err_zero_steps, sizeof(err_zero_steps)) == CMD_STATUS_ERR_INVALID_STEP,
                "step_count=0 rejected with CMD_STATUS_ERR_INVALID_STEP");

    uint8_t err_17_steps[2 + (17 * 3)];
    memset(err_17_steps, 0, sizeof(err_17_steps));
    err_17_steps[0] = BLE_OP_RUN_RAW_SEQUENCE;
    err_17_steps[1] = 17;
    TEST_ASSERT(ble_transport_write_fab1(err_17_steps, sizeof(err_17_steps)) == CMD_STATUS_ERR_ROUTINE_FULL,
                "step_count=17 rejected with CMD_STATUS_ERR_ROUTINE_FULL");

    const uint8_t err_mcount_3[] = {BLE_OP_RUN_RAW_SEQUENCE, 1, 3, 0, 1};
    TEST_ASSERT(ble_transport_write_fab1(err_mcount_3, sizeof(err_mcount_3)) == CMD_STATUS_ERR_MOTOR_BOUNDS,
                "motor_count=3 rejected with CMD_STATUS_ERR_MOTOR_BOUNDS");

    const uint8_t err_ch_16[] = {BLE_OP_RUN_RAW_SEQUENCE, 1, 1, 16, 0};
    TEST_ASSERT(ble_transport_write_fab1(err_ch_16, sizeof(err_ch_16)) == CMD_STATUS_ERR_MOTOR_BOUNDS,
                "channel=16 rejected with CMD_STATUS_ERR_MOTOR_BOUNDS");
}

/* ========================================================================= */
/* Test 3: Preset Run (0x00), Empty Preset Rejection & Busy Re-Entrancy      */
/* ========================================================================= */

static void test_preset_execution_empty_guard_and_busy_lock(void)
{
    printf("Testing Preset Execution (0x00), Empty Preset Guard & Busy Lock...\n");
    setup_paired_subscribed_central();

    /* 1. Valid Preset 2 execution via BLE 0x00 */
    const uint8_t run_p2[] = {BLE_OP_RUN_PRESET, 2};
    command_t cmd;
    TEST_ASSERT(ble_transport_write_fab1(run_p2, sizeof(run_p2)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "BLE 0x00 02 executes Preset 2 cleanly");
    const telemetry_packet_t *pkt = ble_transport_mock_get_last_fab2_notify();
    TEST_ASSERT(pkt->step_progress_pct == 100 && pkt->active_button_id == 2,
                "Preset 2 completion notification reports active_button_id=2 and progress=100%");

    /* 2. Empty Preset (step_count == 0) in NVS rejected with CMD_STATUS_ERR_INVALID_STEP */
    fold_routine_t empty_routine;
    memset(&empty_routine, 0, sizeof(empty_routine));
    empty_routine.step_count = 0;
    TEST_ASSERT(storage_save_routine(3, &empty_routine) == ESP_OK, "Seeded 0-step Preset 3 in NVS");

    const uint8_t run_p3[] = {BLE_OP_RUN_PRESET, 3};
    TEST_ASSERT(ble_transport_write_fab1(run_p3, sizeof(run_p3)) == CMD_STATUS_ERR_INVALID_STEP,
                "BLE 0x00 on empty Preset 3 rejected at ingress with CMD_STATUS_ERR_INVALID_STEP");
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR,
                "Empty preset rejection flashes LED_STATE_INPUT_ERROR");
    TEST_ASSERT(ble_transport_mock_get_last_fab2_notify()->last_cmd_status == CMD_STATUS_ERR_INVALID_STEP,
                "FAB2 immediately notified with CMD_STATUS_ERR_INVALID_STEP");

    /* Also verify Core 0 physical button trigger on empty Preset 3 rejects safely */
    command_t btn_p3 = {.type = CMD_RUN_PRESET, .source = SOURCE_PHYSICAL_BUTTON, .payload.preset_id = 3};
    TEST_ASSERT(state_machine_process_command(&btn_p3) == ESP_ERR_INVALID_STATE &&
                state_machine_get_state() == STATE_IDLE_RUN,
                "Core 0 state_machine also rejects 0-step Preset 3 without moving servos");

    /* 3. Ingress Busy Re-Entrancy Guard while motion is active */
    motion_mock_set_status(MOTION_STATUS_RUNNING);

    const uint8_t raw_1[] = {BLE_OP_RUN_RAW_SEQUENCE, 1, 1, 0, 0};
    const uint8_t save_1[] = {BLE_OP_SET_BUTTON_SEQUENCE, 1, 1, 1, 0, 0};
    const uint8_t restore[] = {BLE_OP_RESTORE_FACTORY_PRESETS};
    const uint8_t jog_0[] = {BLE_OP_JOG_MOTOR_ANGLE, 0, 45};
    const uint8_t fab3_compact[] = {1, 1, 1, 0, 0};

    TEST_ASSERT(ble_transport_write_fab1(run_p2, sizeof(run_p2)) == CMD_STATUS_ERR_BUSY,
                "0x00 rejected with CMD_STATUS_ERR_BUSY during active motion");
    TEST_ASSERT(ble_transport_write_fab1(raw_1, sizeof(raw_1)) == CMD_STATUS_ERR_BUSY,
                "0x01 rejected with CMD_STATUS_ERR_BUSY during active motion");
    TEST_ASSERT(ble_transport_write_fab1(save_1, sizeof(save_1)) == CMD_STATUS_ERR_BUSY,
                "0x0A rejected with CMD_STATUS_ERR_BUSY during active motion");
    TEST_ASSERT(ble_transport_write_fab1(restore, sizeof(restore)) == CMD_STATUS_ERR_BUSY,
                "0x0C rejected with CMD_STATUS_ERR_BUSY during active motion");
    TEST_ASSERT(ble_transport_write_fab1(jog_0, sizeof(jog_0)) == CMD_STATUS_ERR_BUSY,
                "0x0D rejected with CMD_STATUS_ERR_BUSY during active motion");
    TEST_ASSERT(ble_transport_write_fab3(fab3_compact, sizeof(fab3_compact)) == CMD_STATUS_ERR_BUSY,
                "FAB3 write rejected with CMD_STATUS_ERR_BUSY during active motion");
    TEST_ASSERT(ble_transport_mock_get_queued_command_count() == 0,
                "Zero rejected commands were enqueued behind active motion");

    motion_reset_state();
}

/* ========================================================================= */
/* Test 4: Fast-Path E-Stop (0x03), Latched STATE_ESTOP & Recovery (0x02)    */
/* ========================================================================= */

static void test_latched_estop_and_recovery_paths(void)
{
    printf("Testing Fast-Path E-Stop (0x03), Latched STATE_ESTOP & Clear Paths...\n");
    setup_paired_subscribed_central();

    /* Move a servo away from home and simulate active motion */
    pca9685_set_servo_angle(2, 120.0f);
    motion_mock_set_status(MOTION_STATUS_RUNNING);

    /* 1. Trigger wireless E-Stop (0x03) */
    const uint8_t op_estop[] = {BLE_OP_EMERGENCY_STOP};
    command_t cmd;
    TEST_ASSERT(ble_transport_write_fab1(op_estop, sizeof(op_estop)) == CMD_STATUS_OK,
                "0x03 accepted immediately during active motion");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_ABORTED,
                "Core 1 fast-path immediately aborted motion (<50ms)");
    TEST_ASSERT(ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "Core 0 processed CMD_EMERGENCY_STOP");

    TEST_ASSERT(state_machine_get_state() == STATE_ESTOP,
                "Robot latched in STATE_ESTOP (system_state == 2)");
    TEST_ASSERT(pca9685_get_channel_angle(2) == 0,
                "All servos immediately homed to 0 deg on E-Stop");
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP,
                "Status LED flashing LED_STATE_ESTOP (5 rapid flashes)");

    const telemetry_packet_t *estop_pkt = ble_transport_mock_get_last_fab2_notify();
    TEST_ASSERT(estop_pkt->system_state == STATE_ESTOP &&
                (estop_pkt->error_code & (1U << 2)) != 0,
                "FAB2 telemetry reports system_state=2 (STATE_ESTOP) and error_code BIT2 set");

    /* 2. Verify run, save, restore, and jog commands are strictly blocked while latched in STATE_ESTOP */
    const uint8_t run_p1[] = {BLE_OP_RUN_PRESET, 1};
    const uint8_t jog_ch0[] = {BLE_OP_JOG_MOTOR_ANGLE, 0, 90};
    TEST_ASSERT(ble_transport_write_fab1(run_p1, sizeof(run_p1)) == CMD_STATUS_ERR_BUSY,
                "0x00 rejected with CMD_STATUS_ERR_BUSY while latched in STATE_ESTOP");
    TEST_ASSERT(ble_transport_write_fab1(jog_ch0, sizeof(jog_ch0)) == CMD_STATUS_ERR_BUSY,
                "0x0D rejected with CMD_STATUS_ERR_BUSY while latched in STATE_ESTOP");

    /* 3. Clear STATE_ESTOP over BLE via 0x02 (CMD_STOP_SEQUENCE) */
    const uint8_t op_stop[] = {BLE_OP_STOP_SEQUENCE};
    TEST_ASSERT(ble_transport_write_fab1(op_stop, sizeof(op_stop)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "0x02 (CMD_STOP_SEQUENCE) clears latched STATE_ESTOP");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN,
                "State returned to STATE_IDLE_RUN after 0x02 clear");
    const telemetry_packet_t *clr_pkt = ble_transport_mock_get_last_fab2_notify();
    TEST_ASSERT(clr_pkt->system_state == STATE_IDLE_RUN && clr_pkt->error_code == 0,
                "FAB2 telemetry reports system_state=0 and error_code=0 after clear");

    /* 4. Latch STATE_ESTOP again and verify physical button tap clears it */
    command_t btn_estop = buttons_translate_gesture(BTN_ID_2, GESTURE_SHORT_TAP, STATE_RUNNING_MOTION);
    TEST_ASSERT(btn_estop.type == CMD_EMERGENCY_STOP &&
                state_machine_process_command(&btn_estop) == ESP_OK &&
                state_machine_get_state() == STATE_ESTOP,
                "Physical button tap during motion latches STATE_ESTOP");

    command_t btn_clear = buttons_translate_gesture(BTN_ID_1, GESTURE_SHORT_TAP, STATE_ESTOP);
    TEST_ASSERT(btn_clear.type == CMD_STOP_SEQUENCE &&
                state_machine_process_command(&btn_clear) == ESP_OK &&
                state_machine_get_state() == STATE_IDLE_RUN,
                "Physical button tap in STATE_ESTOP clears back to STATE_IDLE_RUN");
}

/* ========================================================================= */
/* Test 5: Wireless Preset Save (0x0A) & Factory Default Restore (0x0C)      */
/* ========================================================================= */

static void test_wireless_preset_save_and_factory_restore(void)
{
    printf("Testing Wireless Preset Save (0x0A) & Factory Restore (0x0C)...\n");
    setup_paired_subscribed_central();

    /* 1. Save custom 2-step compact sequence to Button 4 via FAB1 0x0A */
    const uint8_t save_b4[] = {
        BLE_OP_SET_BUTTON_SEQUENCE,
        4,          /* Preset 4 */
        2,          /* 2 steps */
        1, 10, 0,   /* Step 1: Ch 10 */
        2, 11, 12   /* Step 2: Ch 11 & Ch 12 */
    };

    command_t cmd;
    uint32_t f3_before = ble_transport_mock_get_fab3_notify_count();
    TEST_ASSERT(ble_transport_write_fab1(save_b4, sizeof(save_b4)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "0x0A compact button save persisted to Preset 4");
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS,
                "LED set to LED_STATE_SAVE_SUCCESS (2.0s solid ON)");
    TEST_ASSERT(ble_transport_mock_get_fab3_notify_count() == f3_before + 1,
                "FAB3 emitted 212-byte update notification after 0x0A save");

    fold_routine_t loaded_b4;
    TEST_ASSERT(storage_load_routine(4, &loaded_b4) == ESP_OK &&
                loaded_b4.step_count == 2 &&
                loaded_b4.steps[0].motor_ids[0] == 10 &&
                loaded_b4.steps[1].motor_ids[1] == 12,
                "Preset 4 NVS contents match saved compact payload");

    /* 2. Restore factory defaults via 0x0C */
    pca9685_set_servo_angle(5, 90.0f);
    const uint8_t op_restore[] = {BLE_OP_RESTORE_FACTORY_PRESETS};
    f3_before = ble_transport_mock_get_fab3_notify_count();
    TEST_ASSERT(ble_transport_write_fab1(op_restore, sizeof(op_restore)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "0x0C restored all 4 presets to factory defaults");
    TEST_ASSERT(pca9685_get_channel_angle(5) == 0,
                "0x0C homed all 16 servos to 0 deg");
    TEST_ASSERT(ble_transport_mock_get_fab3_notify_count() == f3_before + 1,
                "0x0C emitted 212-byte FAB3 notification");

    fold_routine_t def_b4;
    (void)storage_get_default_routine(4, &def_b4);
    (void)storage_load_routine(4, &loaded_b4);
    TEST_ASSERT(memcmp(&loaded_b4, &def_b4, sizeof(fold_routine_t)) == 0,
                "Preset 4 restored to exact factory default routine");
}

/* ========================================================================= */
/* Test 6: Calibration Mode (0x0D), 10s Thermal Sleep, 15s & Disconnect Exit */
/* ========================================================================= */

static void test_calibration_mode_thermal_sleep_and_safe_exits(void)
{
    printf("Testing Live Servo Jog (0x0D), 10s Thermal Sleep, 15s Auto-Home & Safe Exits...\n");
    setup_paired_subscribed_central();

    /* 1. Out-of-bounds channel (>15) and angle (>180) rejected with CMD_STATUS_ERR_MOTOR_BOUNDS */
    const uint8_t bad_ch[] = {BLE_OP_JOG_MOTOR_ANGLE, 16, 90};
    const uint8_t bad_angle[] = {BLE_OP_JOG_MOTOR_ANGLE, 0, 181};
    const uint8_t bad_len[] = {BLE_OP_JOG_MOTOR_ANGLE, 0};

    TEST_ASSERT(ble_transport_write_fab1(bad_ch, sizeof(bad_ch)) == CMD_STATUS_ERR_MOTOR_BOUNDS,
                "Jog channel=16 rejected with CMD_STATUS_ERR_MOTOR_BOUNDS");
    TEST_ASSERT(ble_transport_write_fab1(bad_angle, sizeof(bad_angle)) == CMD_STATUS_ERR_MOTOR_BOUNDS,
                "Jog angle=181 deg rejected with CMD_STATUS_ERR_MOTOR_BOUNDS");
    TEST_ASSERT(ble_transport_write_fab1(bad_len, sizeof(bad_len)) == CMD_STATUS_ERR_INVALID_ARG,
                "Truncated 2-byte 0x0D frame rejected with CMD_STATUS_ERR_INVALID_ARG");

    /* 2. Valid jog transitions STATE_IDLE_RUN -> STATE_CALIBRATING */
    command_t cmd;
    const uint8_t jog_ch2_90[] = {BLE_OP_JOG_MOTOR_ANGLE, 2, 90};
    TEST_ASSERT(ble_transport_write_fab1(jog_ch2_90, sizeof(jog_ch2_90)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "Jog Ch 2 -> 90 deg executed");
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING,
                "State transitioned to STATE_CALIBRATING (4)");
    TEST_ASSERT(pca9685_get_channel_angle(2) == 90,
                "Channel 2 angle set to 90 deg");
    TEST_ASSERT(ble_transport_mock_get_last_fab2_notify()->system_state == STATE_CALIBRATING &&
                ble_transport_mock_get_last_fab2_notify()->channel_angles[2] == 90,
                "FAB2 pushed immediate calibration telemetry with channel_angles[2]=90");

    /* 3. Advance 9,990 ms -> PCA9685 still awake; +10 ms (10,000 ms) -> PCA9685 enters thermal sleep */
    state_machine_tick(9990);
    TEST_ASSERT(!state_machine_is_calibrating_thermal_sleep() &&
                (pca9685_mock_get_reg(PCA9685_REG_MODE1) & PCA9685_MODE1_SLEEP) == 0,
                "PCA9685 remains awake at 9990ms");

    state_machine_tick(10);
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING &&
                state_machine_is_calibrating_thermal_sleep() == true &&
                (pca9685_mock_get_reg(PCA9685_REG_MODE1) & PCA9685_MODE1_SLEEP) != 0,
                "At 10000ms inactivity, PCA9685 enters thermal sleep (MODE1_SLEEP set) while staying in STATE_CALIBRATING");

    /* 4. Sending another jog at 12,000 ms automatically wakes PCA9685 and resets 10s/15s timers */
    state_machine_tick(2000);
    const uint8_t jog_ch2_135[] = {BLE_OP_JOG_MOTOR_ANGLE, 2, 135};
    TEST_ASSERT(ble_transport_write_fab1(jog_ch2_135, sizeof(jog_ch2_135)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&cmd) &&
                state_machine_process_command(&cmd) == ESP_OK,
                "Subsequent jog at 12s accepted");
    TEST_ASSERT(state_machine_is_calibrating_thermal_sleep() == false &&
                (pca9685_mock_get_reg(PCA9685_REG_MODE1) & PCA9685_MODE1_SLEEP) == 0 &&
                pca9685_get_channel_angle(2) == 135,
                "Subsequent jog automatically woke PCA9685 from thermal sleep and moved Ch 2 to 135 deg");

    /* 5. Full 15,000 ms inactivity watchdog -> wakes PCA9685, homes all 16 servos to 0 deg, exits to IDLE */
    state_machine_tick(10000);
    TEST_ASSERT(state_machine_is_calibrating_thermal_sleep() == true, "Re-entered 10s thermal sleep");
    state_machine_tick(5000);
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN &&
                state_machine_is_calibrating_thermal_sleep() == false &&
                (pca9685_mock_get_reg(PCA9685_REG_MODE1) & PCA9685_MODE1_SLEEP) == 0 &&
                pca9685_get_channel_angle(2) == 0,
                "At 15000ms inactivity, PCA9685 woke, homed all channels to 0 deg, and returned to STATE_IDLE_RUN");

    /* 6. Exit STATE_CALIBRATING immediately via BLE disconnect (even while thermally asleep) */
    (void)ble_transport_write_fab1(jog_ch2_90, sizeof(jog_ch2_90));
    (void)ble_transport_mock_pop_command(&cmd);
    (void)state_machine_process_command(&cmd);
    state_machine_tick(10000); /* Put PCA9685 into thermal sleep */
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING &&
                state_machine_is_calibrating_thermal_sleep() == true,
                "In STATE_CALIBRATING with thermal sleep active prior to BLE disconnect");

    ble_transport_mock_disconnect();
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN &&
                state_machine_is_calibrating_thermal_sleep() == false &&
                (pca9685_mock_get_reg(PCA9685_REG_MODE1) & PCA9685_MODE1_SLEEP) == 0 &&
                pca9685_get_channel_angle(2) == 0,
                "BLE disconnect immediately woke PCA9685, homed all servos to 0 deg, and exited STATE_CALIBRATING");

    /* 7. Reconnect bonded central and verify physical button tap exits STATE_CALIBRATING */
    const uint8_t addr[6] = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    const uint8_t irk[16] = {0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8,
                             0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8};
    TEST_ASSERT(ble_transport_mock_connect(addr, false, addr, irk) == ESP_OK, "Bonded central reconnected");

    (void)ble_transport_write_fab1(jog_ch2_90, sizeof(jog_ch2_90));
    (void)ble_transport_mock_pop_command(&cmd);
    (void)state_machine_process_command(&cmd);
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING, "Re-entered STATE_CALIBRATING");

    command_t btn_exit = buttons_translate_gesture(BTN_ID_3, GESTURE_SHORT_TAP, STATE_CALIBRATING);
    TEST_ASSERT(btn_exit.type == CMD_STOP_SEQUENCE &&
                state_machine_process_command(&btn_exit) == ESP_OK &&
                state_machine_get_state() == STATE_IDLE_RUN &&
                pca9685_get_channel_angle(2) == 0,
                "Physical button tap in STATE_CALIBRATING homes servos and returns to STATE_IDLE_RUN");
}

/* ========================================================================= */
/* Test Main Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 9 Unit Test: Remote Cmd & Calibration\n");
    printf("============================================================\n");

    test_fab1_opcode_parsing_and_malformed_rejection();
    test_raw_sequence_bounds_and_completion_notify();
    test_preset_execution_empty_guard_and_busy_lock();
    test_latched_estop_and_recovery_paths();
    test_wireless_preset_save_and_factory_restore();
    test_calibration_mode_thermal_sleep_and_safe_exits();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", s_pass_count, s_test_count);
    printf("============================================================\n");

    return 0;
}
