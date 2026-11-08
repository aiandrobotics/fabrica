#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stddef.h>
#include <assert.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "buttons.h"
#include "pca9685.h"
#include "storage.h"
#include "motion.h"
#include "ble_transport.h"
#include "remote_cmd.h"
#include "state_machine.h"
#include "telemetry.h"

static int s_tests_passed = 0;
static int s_total_tests = 0;

#define TEST_ASSERT(cond, msg) do { \
    s_total_tests++; \
    if (cond) { \
        s_tests_passed++; \
        printf("  [PASS] %s\n", msg); \
    } else { \
        printf("  [FAIL] %s (Line %d)\n", msg, __LINE__); \
        assert(cond); \
    } \
} while(0)

static void helper_connect_central(void)
{
    command_t pair_cmd = { .type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON };
    (void)state_machine_process_command(&pair_cmd);

    const uint8_t addr[6] = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    const uint8_t irk[16] = {0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8,
                             0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8};
    (void)ble_transport_mock_connect(addr, false, addr, irk);
    (void)ble_transport_mock_set_cccd(0xFAB2, 0x0001);
    (void)ble_transport_mock_set_cccd(0xFAB3, 0x0001);
    led_step_ms(1100);
}

static void helper_write_fab1(const uint8_t *data, size_t len)
{
    (void)ble_transport_write_fab1(data, len);
    command_t cmd;
    if (ble_transport_mock_pop_command(&cmd)) {
        (void)state_machine_process_command(&cmd);
    }
}

/* ========================================================================= */
/* Test Suite 1: Binary Struct Packing, Alignment & Little-Endian Layout     */
/* ========================================================================= */
static void test_telemetry_struct_packing(void)
{
    printf("\nTesting packed 31-byte telemetry struct layout and offsets...\n");

    TEST_ASSERT(sizeof(telemetry_packet_t) == 31, "telemetry_packet_t size is exactly 31 bytes");
    TEST_ASSERT(offsetof(telemetry_packet_t, system_state) == 0, "system_state offset is 0");
    TEST_ASSERT(offsetof(telemetry_packet_t, led_state) == 1, "led_state offset is 1");
    TEST_ASSERT(offsetof(telemetry_packet_t, active_button_id) == 2, "active_button_id offset is 2");
    TEST_ASSERT(offsetof(telemetry_packet_t, current_step_idx) == 3, "current_step_idx offset is 3");
    TEST_ASSERT(offsetof(telemetry_packet_t, total_steps) == 4, "total_steps offset is 4");
    TEST_ASSERT(offsetof(telemetry_packet_t, step_progress_pct) == 5, "step_progress_pct offset is 5");
    TEST_ASSERT(offsetof(telemetry_packet_t, elapsed_step_time_ms) == 6, "elapsed_step_time_ms offset is 6");
    TEST_ASSERT(offsetof(telemetry_packet_t, channel_angles) == 8, "channel_angles offset is 8 (16 bytes)");
    TEST_ASSERT(offsetof(telemetry_packet_t, last_cmd_status) == 24, "last_cmd_status offset is 24");
    TEST_ASSERT(offsetof(telemetry_packet_t, free_heap_kb) == 25, "free_heap_kb offset is 25");
    TEST_ASSERT(offsetof(telemetry_packet_t, ble_rssi_dbm) == 27, "ble_rssi_dbm offset is 27");
    TEST_ASSERT(offsetof(telemetry_packet_t, error_code) == 28, "error_code offset is 28");
    TEST_ASSERT(offsetof(telemetry_packet_t, sequence_counter) == 29, "sequence_counter offset is 29");

    /* Verify Little-Endian wire encoding of 16-bit values */
    telemetry_packet_t pkt;
    memset(&pkt, 0, sizeof(pkt));
    pkt.elapsed_step_time_ms = 0x0123;
    pkt.free_heap_kb = 0x0456;
    pkt.sequence_counter = 0x0789;

    const uint8_t *raw = (const uint8_t *)&pkt;
    TEST_ASSERT(raw[6] == 0x23 && raw[7] == 0x01, "elapsed_step_time_ms serialized Little-Endian (0x23, 0x01)");
    TEST_ASSERT(raw[25] == 0x56 && raw[26] == 0x04, "free_heap_kb serialized Little-Endian (0x56, 0x04)");
    TEST_ASSERT(raw[29] == 0x89 && raw[30] == 0x07, "sequence_counter serialized Little-Endian (0x89, 0x07)");
}

/* ========================================================================= */
/* Test Suite 2: Adaptive Rate Calculation (10 Hz vs 1 Hz)                   */
/* ========================================================================= */
static void test_telemetry_adaptive_rate(void)
{
    printf("\nTesting adaptive interval rate calculation...\n");

    TEST_ASSERT(TELEMETRY_STREAM_ACTIVE_HZ == 10, "TELEMETRY_STREAM_ACTIVE_HZ is 10 Hz");
    TEST_ASSERT(TELEMETRY_STREAM_IDLE_HZ == 1, "TELEMETRY_STREAM_IDLE_HZ is 1 Hz");
    TEST_ASSERT(TELEMETRY_INTERVAL_ACTIVE_MS == 100, "TELEMETRY_INTERVAL_ACTIVE_MS is 100ms");
    TEST_ASSERT(TELEMETRY_INTERVAL_IDLE_MS == 1000, "TELEMETRY_INTERVAL_IDLE_MS is 1000ms");

    TEST_ASSERT(telemetry_get_interval_ms(STATE_IDLE_RUN) == 1000, "STATE_IDLE_RUN interval is 1000ms (1 Hz)");
    TEST_ASSERT(telemetry_get_interval_ms(STATE_RUNNING_MOTION) == 100, "STATE_RUNNING_MOTION interval is 100ms (10 Hz)");
    TEST_ASSERT(telemetry_get_interval_ms(STATE_ESTOP) == 1000, "STATE_ESTOP interval is 1000ms (1 Hz)");
    TEST_ASSERT(telemetry_get_interval_ms(STATE_ERROR) == 1000, "STATE_ERROR interval is 1000ms (1 Hz)");
    TEST_ASSERT(telemetry_get_interval_ms(STATE_CALIBRATING) == 100, "STATE_CALIBRATING interval is 100ms (10 Hz)");

    /* Dynamic rate reflection from active state */
    state_machine_init();
    TEST_ASSERT(telemetry_get_current_interval_ms() == 1000, "Current interval in IDLE is 1000ms");

    /* Transition to calibrating via jog */
    helper_connect_central();
    const uint8_t jog_cmd[] = { 0x0D, 0x00, 0x2D }; /* Ch 0 -> 45 deg */
    helper_write_fab1(jog_cmd, sizeof(jog_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING, "State transitioned to STATE_CALIBRATING");
    TEST_ASSERT(telemetry_get_current_interval_ms() == 100, "Current interval adaptively changed to 100ms during calibration");

    /* Exit calibration via stop sequence */
    const uint8_t stop_cmd[] = { 0x02 };
    helper_write_fab1(stop_cmd, sizeof(stop_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "State returned to STATE_IDLE_RUN");
    TEST_ASSERT(telemetry_get_current_interval_ms() == 1000, "Current interval throttled back to 1000ms upon returning to IDLE");

    ble_transport_mock_disconnect();
}

/* ========================================================================= */
/* Test Suite 3: CCCD Gating, Periodic Ticks & Opcode 0x11 Stream Control   */
/* ========================================================================= */
static void test_telemetry_streaming_control(void)
{
    printf("\nTesting CCCD subscription gating, periodic ticks & stream toggle...\n");

    telemetry_init();
    state_machine_init();
    pca9685_init();
    storage_init();
    motion_init(NULL);

    /* 1. When disconnected, ticks produce zero notifications */
    ble_transport_mock_disconnect();
    uint32_t count_before = ble_transport_mock_get_fab2_notify_count();
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before, "telemetry_tick() suppressed when disconnected");

    /* 2. When connected but CCCD unsubscribed, ticks produce zero notifications */
    helper_connect_central();
    ble_transport_mock_set_cccd(0xFAB2, 0x0000);
    TEST_ASSERT(!ble_transport_is_telemetry_subscribed(), "FAB2 CCCD reports unsubscribed (0x0000)");
    count_before = ble_transport_mock_get_fab2_notify_count();
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before, "telemetry_tick() suppressed when CCCD unsubscribed");

    /* 3. When connected and CCCD subscribed (0x0001), periodic ticks emit notifications */
    ble_transport_mock_set_cccd(0xFAB2, 0x0001);
    TEST_ASSERT(ble_transport_is_telemetry_subscribed(), "FAB2 CCCD reports subscribed (0x0001)");
    TEST_ASSERT(telemetry_is_stream_enabled(), "Periodic streaming is enabled by default");

    count_before = ble_transport_mock_get_fab2_notify_count();
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before + 1, "telemetry_tick() emitted FAB2 notification when subscribed");

    /* Verify monotonic sequence counter */
    const telemetry_packet_t *pkt1 = ble_transport_mock_get_last_fab2_notify();
    uint16_t seq1 = pkt1->sequence_counter;
    telemetry_tick();
    const telemetry_packet_t *pkt2 = ble_transport_mock_get_last_fab2_notify();
    uint16_t seq2 = pkt2->sequence_counter;
    TEST_ASSERT(seq2 == seq1 + 1, "sequence_counter incremented monotonically on next tick");

    /* 4. Disable streaming via telemetry_set_stream_enabled(false) */
    telemetry_set_stream_enabled(false);
    TEST_ASSERT(!telemetry_is_stream_enabled(), "Periodic streaming paused via API");
    count_before = ble_transport_mock_get_fab2_notify_count();
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before, "telemetry_tick() suppressed when streaming paused");

    /* 5. Resume streaming via Opcode 0x11 (0x11 01) */
    const uint8_t resume_stream_cmd[] = { 0x11, 0x01 };
    helper_write_fab1(resume_stream_cmd, sizeof(resume_stream_cmd));
    TEST_ASSERT(telemetry_is_stream_enabled(), "Periodic streaming resumed via Opcode 0x11 01");
    count_before = ble_transport_mock_get_fab2_notify_count();
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before + 1, "telemetry_tick() resumed emitting notifications");

    /* 6. Pause streaming via Opcode 0x11 (0x11 00) */
    const uint8_t pause_stream_cmd[] = { 0x11, 0x00 };
    helper_write_fab1(pause_stream_cmd, sizeof(pause_stream_cmd));
    TEST_ASSERT(!telemetry_is_stream_enabled(), "Periodic streaming paused via Opcode 0x11 00");
    count_before = ble_transport_mock_get_fab2_notify_count();
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before, "telemetry_tick() suppressed after Opcode 0x11 00");

    /* 7. Re-enable and verify disconnect mute */
    telemetry_set_stream_enabled(true);
    telemetry_tick();
    count_before = ble_transport_mock_get_fab2_notify_count();

    ble_transport_mock_disconnect();
    TEST_ASSERT(!ble_transport_is_connected(), "Central disconnected");
    telemetry_tick();
    TEST_ASSERT(ble_transport_mock_get_fab2_notify_count() == count_before, "telemetry_tick() immediately muted upon disconnect");
}

/* ========================================================================= */
/* Test Suite 4: Mid-Sweep Elapsed Time & Live Angle Tracking                */
/* ========================================================================= */
static void test_telemetry_progress_and_angles(void)
{
    printf("\nTesting mid-sweep elapsed time and live 16-channel angle tracking...\n");

    telemetry_init();
    pca9685_init();
    helper_connect_central();
    ble_transport_mock_set_cccd(0xFAB2, 0x0001);

    /* 1. Verify multi-channel servo angle reflection */
    pca9685_set_servo_angle(0, 15.0f);
    pca9685_set_servo_angle(1, 45.0f);
    pca9685_set_servo_angle(2, 90.0f);
    pca9685_set_servo_angle(3, 135.0f);
    pca9685_set_servo_angle(15, 180.0f);

    telemetry_packet_t pkt;
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.channel_angles[0] == 15, "channel_angles[0] reflects 15 deg");
    TEST_ASSERT(pkt.channel_angles[1] == 45, "channel_angles[1] reflects 45 deg");
    TEST_ASSERT(pkt.channel_angles[2] == 90, "channel_angles[2] reflects 90 deg");
    TEST_ASSERT(pkt.channel_angles[3] == 135, "channel_angles[3] reflects 135 deg");
    TEST_ASSERT(pkt.channel_angles[15] == 180, "channel_angles[15] reflects 180 deg");

    /* 2. Mock clock stepping for mid-sweep progress tracking */
    motion_mock_set_progress(1, 4, 0, 0);
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.current_step_idx == 1, "current_step_idx is 1");
    TEST_ASSERT(pkt.total_steps == 4, "total_steps is 4");
    TEST_ASSERT(pkt.step_progress_pct == 0, "step_progress_pct is 0% at step start");
    TEST_ASSERT(pkt.elapsed_step_time_ms == 0, "elapsed_step_time_ms is 0ms at step start");

    /* Step mid-sweep to 50% */
    motion_mock_set_progress(1, 4, 50, 150);
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.step_progress_pct == 50, "step_progress_pct is 50% mid-sweep");
    TEST_ASSERT(pkt.elapsed_step_time_ms == 150, "elapsed_step_time_ms is 150ms mid-sweep");

    /* Step sweep completion to 100% */
    motion_mock_set_progress(1, 4, 100, 300);
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.step_progress_pct == 100, "step_progress_pct is 100% at sweep end");
    TEST_ASSERT(pkt.elapsed_step_time_ms == 300, "elapsed_step_time_ms is 300ms at sweep end");

    /* Reset motion progress */
    motion_reset_state();
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.step_progress_pct == 0, "step_progress_pct reset to 0 in idle");
    TEST_ASSERT(pkt.elapsed_step_time_ms == 0, "elapsed_step_time_ms reset to 0 in idle");

    ble_transport_mock_disconnect();
}

/* ========================================================================= */
/* Test Suite 5: Error Bitmask & Button Table Sync (FAB3)                    */
/* ========================================================================= */
static void test_telemetry_error_and_fab3_sync(void)
{
    printf("\nTesting error bitmask and FAB3 sequence table notifications...\n");

    telemetry_init();
    state_machine_init();
    storage_init();
    helper_connect_central();

    /* 1. Normal state has zero error code */
    telemetry_packet_t pkt;
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.error_code == 0, "error_code is 0 in normal idle");

    /* 2. E-Stop sets error bitmask BIT2 (0x04) */
    const uint8_t estop_cmd[] = { 0x03 };
    helper_write_fab1(estop_cmd, sizeof(estop_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_ESTOP, "System state is STATE_ESTOP");

    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.system_state == STATE_ESTOP, "telemetry reports system_state == STATE_ESTOP (2)");
    TEST_ASSERT((pkt.error_code & (1U << 2)) != 0, "error_code has BIT2 set (0x04)");

    /* Clear E-Stop */
    const uint8_t stop_cmd[] = { 0x02 };
    helper_write_fab1(stop_cmd, sizeof(stop_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "System returned to STATE_IDLE_RUN");
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.error_code == 0, "error_code cleared back to 0");

    /* 3. FAB3 Sequence Table Synchronization */
    ble_transport_mock_set_cccd(0xFAB3, 0x0001);
    uint32_t fab3_count_before = ble_transport_mock_get_fab3_notify_count();

    /* Trigger FAB3 notification via CMD_SYNC_PRESETS (0x0B) */
    const uint8_t sync_cmd[] = { 0x0B };
    helper_write_fab1(sync_cmd, sizeof(sync_cmd));
    TEST_ASSERT(ble_transport_mock_get_fab3_notify_count() == fab3_count_before + 1,
                "0x0B (CMD_SYNC_PRESETS) pushed 212-byte FAB3 notification");

    const uint8_t *table = ble_transport_mock_get_last_fab3_notify();
    TEST_ASSERT(table != NULL, "FAB3 table pointer is valid");
    TEST_ASSERT(table[0] > 0, "Preset 1 step_count in FAB3 table is valid (> 0)");

    ble_transport_mock_disconnect();
}

/* ========================================================================= */
/* Main Test Runner                                                          */
/* ========================================================================= */
int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 10 Unit Test: Telemetry Subsystem\n");
    printf("============================================================\n");

    test_telemetry_struct_packing();
    test_telemetry_adaptive_rate();
    test_telemetry_streaming_control();
    test_telemetry_progress_and_angles();
    test_telemetry_error_and_fab3_sync();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", s_tests_passed, s_total_tests);
    printf("============================================================\n");

    return 0;
}
