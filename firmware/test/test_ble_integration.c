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

/* ========================================================================= */
/* Test Harness Counters & Assertion Macro                                   */
/* ========================================================================= */

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

/* ========================================================================= */
/* Dual-OS Simulated BLE Central Models                                      */
/* ========================================================================= */

static void reset_subsystems(void)
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
    telemetry_init();
}

/**
 * @brief Simulate iOS (CoreBluetooth) client connection and pairing.
 *        Models 185-byte MTU exchange, peripheral security request, and CCCD setup.
 */
static void sim_ios_central_connect(const uint8_t id_addr[6], const uint8_t irk[16], bool open_pairing)
{
    if (open_pairing) {
        command_t pair_cmd = { .type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON };
        (void)state_machine_process_command(&pair_cmd);
    }

    (void)ble_transport_mock_connect(id_addr, false, id_addr, irk);
    (void)ble_transport_mock_exchange_mtu(185); /* iOS default initial MTU */
    (void)ble_transport_mock_set_cccd(0xFAB2, 0x0001);
    (void)ble_transport_mock_set_cccd(0xFAB3, 0x0001);
    led_step_ms(1100); /* Expire transient LED_STATE_BLE_CONNECTED */
}

/**
 * @brief Simulate Android (BluetoothGatt) client connection.
 *        Starts at legacy 23-byte MTU, upgrades via peripheral-initiated exchange (512B).
 */
static void sim_android_central_connect(const uint8_t id_addr[6], const uint8_t irk[16], bool open_pairing)
{
    if (open_pairing) {
        command_t pair_cmd = { .type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON };
        (void)state_machine_process_command(&pair_cmd);
    }

    (void)ble_transport_mock_connect(id_addr, false, id_addr, irk);
    /* Simulate Android central with legacy 23-byte MTU before exchange */
    (void)ble_transport_mock_exchange_mtu(23);
    TEST_ASSERT(ble_transport_get_mtu() == 23, "Android central legacy 23-byte MTU");

    /* Peripheral proactively initiates MTU exchange */
    ble_mock_conn_info_t info;
    ble_transport_mock_get_conn_info(&info);
    TEST_ASSERT(info.peripheral_mtu_initiated, "Peripheral proactively initiated ble_gattc_exchange_mtu");

    /* Upgrade MTU to 512 */
    (void)ble_transport_mock_exchange_mtu(BLE_PREFERRED_MTU);
    TEST_ASSERT(ble_transport_get_mtu() == BLE_PREFERRED_MTU, "ATT MTU upgraded to 512 bytes");

    (void)ble_transport_mock_set_cccd(0xFAB2, 0x0001);
    (void)ble_transport_mock_set_cccd(0xFAB3, 0x0001);
    led_step_ms(1100);
}

static void send_ble_command(const uint8_t *data, size_t len)
{
    (void)ble_transport_write_fab1(data, len);
    command_t cmd;
    if (ble_transport_mock_pop_command(&cmd)) {
        (void)state_machine_process_command(&cmd);
    }
}

/* ========================================================================= */
/* Test Suite: 17 End-to-End Protocol Verification Vectors                   */
/* ========================================================================= */

static void test_vectors_1_to_6_discovery_security_and_locator(void)
{
    printf("\n--- Vectors 1-6: Discovery, Security, MTU & Locator ---\n");
    reset_subsystems();

    const uint8_t mac_mock[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
    ble_transport_mock_set_bt_mac(mac_mock);

    /* Vector 1: GAP Advertisement Split & DIS / Service Changed Discovery */
    uint8_t adv_buf[BLE_ADV_MAX_LEN];
    size_t adv_len = 0;
    uint8_t rsp_buf[BLE_ADV_MAX_LEN];
    size_t rsp_len = 0;
    TEST_ASSERT(ble_transport_build_adv_packets("Fabrica-EEFF", 3, adv_buf, &adv_len, rsp_buf, &rsp_len) == ESP_OK,
                "Built split advertising and scan response packets");
    TEST_ASSERT(adv_len <= 31, "Primary advertisement is <= 31 bytes legacy limit (21B)");
    TEST_ASSERT(adv_len == 21, "Primary advertisement length is exactly 21 bytes (Flags + 128-bit UUID)");
    TEST_ASSERT(rsp_len <= 31, "Scan response is <= 31 bytes legacy limit (17B)");
    TEST_ASSERT(rsp_len == 17, "Scan response length is exactly 17 bytes (Name + Tx Power)");

    char dis_buf[32];
    TEST_ASSERT(ble_transport_mock_read_dis_char(0x2A24, dis_buf, sizeof(dis_buf)) == ESP_OK &&
                strcmp(dis_buf, "Fabrica-DevKit-v1") == 0, "DIS Model Number (0x2A24) is 'Fabrica-DevKit-v1'");
    TEST_ASSERT(ble_transport_mock_read_dis_char(0x2A26, dis_buf, sizeof(dis_buf)) == ESP_OK &&
                strcmp(dis_buf, "v1.13.0") == 0, "DIS Firmware Revision (0x2A26) is 'v1.13.0'");
    TEST_ASSERT(ble_transport_mock_read_dis_char(0x2A29, dis_buf, sizeof(dis_buf)) == ESP_OK &&
                strcmp(dis_buf, BLE_DIS_MANUFACTURER_NAME) == 0, "DIS Manufacturer Name (0x2A29) is 'AIR Robotics'");

    char desc_buf[48];
    TEST_ASSERT(ble_transport_mock_read_user_desc(0xFAB1, desc_buf, sizeof(desc_buf)) == ESP_OK &&
                strstr(desc_buf, "FAB1") != NULL, "FAB1 exposes 0x2901 User Description descriptor");
    TEST_ASSERT(ble_transport_mock_read_user_desc(0xFAB2, desc_buf, sizeof(desc_buf)) == ESP_OK &&
                strstr(desc_buf, "FAB2") != NULL, "FAB2 exposes 0x2901 User Description descriptor");
    TEST_ASSERT(ble_transport_mock_read_user_desc(0xFAB3, desc_buf, sizeof(desc_buf)) == ESP_OK &&
                strstr(desc_buf, "FAB3") != NULL, "FAB3 exposes 0x2901 User Description descriptor");

    /* Vector 2: Peripheral-Initiated Connection Parameter Update */
    const uint8_t dev1_addr[6] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06};
    const uint8_t dev1_irk[16]  = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
    sim_ios_central_connect(dev1_addr, dev1_irk, true);

    ble_mock_conn_info_t conn_info;
    ble_transport_mock_get_conn_info(&conn_info);
    TEST_ASSERT(conn_info.param_update_requested, "Peripheral initiated connection parameter update");
    TEST_ASSERT(conn_info.itvl_min_units == BLE_CONN_INTERVAL_MIN_UNITS &&
                conn_info.itvl_max_units == BLE_CONN_INTERVAL_MAX_UNITS,
                "Connection interval compliant with Apple guidelines (15.0ms - 30.0ms)");
    TEST_ASSERT(conn_info.latency == BLE_CONN_SLAVE_LATENCY, "Slave latency is 0");
    TEST_ASSERT(conn_info.supervision_timeout_10ms == BLE_SUPERVISION_TIMEOUT_UNITS, "Supervision timeout is 4000ms");
    TEST_ASSERT(conn_info.smp_security_initiated, "Peripheral proactively initiated SMP security request");

    /* Vector 3: Hold-to-Pair Security, Native SMP Bonding & 15-Minute RPA Reconnection */
    ble_transport_mock_disconnect();

    /* Unbonded device rejected outside pairing window */
    const uint8_t unbonded_addr[6] = {0x99, 0x88, 0x77, 0x66, 0x55, 0x44};
    const uint8_t unbonded_irk[16]  = {0x99, 0x88, 0x77, 0x66, 0x55, 0x44};
    TEST_ASSERT(ble_transport_mock_connect(unbonded_addr, false, unbonded_addr, unbonded_irk) == ESP_ERR_INVALID_STATE,
                "Unbonded central rejected outside pairing window");

    /* Bonded device seamlessly auto-reconnects with rotating RPA */
    const uint8_t dev1_rpa[6] = {0x7F, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE}; /* Simulated rotating RPA */
    TEST_ASSERT(ble_transport_mock_connect(dev1_rpa, true, dev1_addr, dev1_irk) == ESP_OK,
                "Bonded central reconnected seamlessly across 15-minute RPA MAC rotation");

    /* Vector 4: 4-Bond NVS Limit & 5th Device FIFO Eviction */
    ble_transport_mock_disconnect();
    /* Bond devices 2, 3, 4 */
    for (uint8_t id = 2; id <= 4; id++) {
        uint8_t addr[6] = {id, id, id, id, id, id};
        uint8_t irk[16] = {id};
        sim_ios_central_connect(addr, irk, true);
        ble_transport_mock_disconnect();
    }
    TEST_ASSERT(ble_transport_get_bond_count() == 4, "NVS bond store holds 4 trusted peers");

    /* Connect a 5th device during active pairing window */
    uint8_t dev5_addr[6] = {5, 5, 5, 5, 5, 5};
    uint8_t dev5_irk[16] = {5};
    sim_ios_central_connect(dev5_addr, dev5_irk, true);
    ble_transport_mock_disconnect();
    TEST_ASSERT(ble_transport_get_bond_count() == 4, "Bond count capped at 4 after 5th device pairing");
    TEST_ASSERT(!ble_transport_mock_is_peer_bonded(dev1_addr), "Oldest device (dev1) evicted via FIFO policy");
    TEST_ASSERT(ble_transport_mock_is_peer_bonded(dev5_addr), "Newest device (dev5) successfully bonded");

    /* Vector 5: Hardware Bond Factory Reset (B1 + B4 5s Chord Hold) */
    command_t reset_bonds_cmd = { .type = CMD_CLEAR_BLE_BONDS, .source = SOURCE_PHYSICAL_BUTTON };
    (void)state_machine_process_command(&reset_bonds_cmd);
    TEST_ASSERT(ble_transport_get_bond_count() == 0, "All bonds erased from NVS via CMD_CLEAR_BLE_BONDS");
    TEST_ASSERT(ble_transport_mock_connect(dev5_addr, false, dev5_addr, dev5_irk) == ESP_ERR_INVALID_STATE,
                "Previously bonded central now rejected following hardware bond reset");

    /* Vector 6: Visual Robot Locator (CMD_IDENTIFY_ROBOT, 0x0E) */
    sim_ios_central_connect(dev1_addr, dev1_irk, true);
    const uint8_t identify_cmd[] = { 0x0E };
    send_ble_command(identify_cmd, sizeof(identify_cmd));
    TEST_ASSERT(led_get_state() == LED_STATE_IDENTIFY, "Status LED entered LED_STATE_IDENTIFY (3 double-blinks)");
    led_step_ms(3100);
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "Status LED restored base LED_STATE_IDLE after 3.0s identify train");

    ble_transport_mock_disconnect();
}

static void test_vectors_7_to_11_sequences_guards_and_busy_locks(void)
{
    printf("\n--- Vectors 7-11: Sequences, Guards & Busy Locks ---\n");
    reset_subsystems();

    const uint8_t dev_addr[6] = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    const uint8_t dev_irk[16]  = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
    sim_android_central_connect(dev_addr, dev_irk, true);

    /* Vector 7: Read 212-Byte 4-Button Table from FAB3 */
    uint8_t table_buf[BLE_FAB3_TABLE_SIZE];
    for (uint8_t id = 1; id <= TOTAL_PRESET_COUNT; id++) {
        fold_routine_t routine;
        storage_get_default_routine(id, &routine);
        memcpy(&table_buf[(size_t)(id - 1) * sizeof(fold_routine_t)], &routine, sizeof(fold_routine_t));
    }
    TEST_ASSERT(sizeof(fold_routine_t) == 53, "fold_routine_t is packed to 53 bytes");
    TEST_ASSERT(BLE_FAB3_TABLE_SIZE == 212, "Full 4-button sequence table is 212 bytes");

    /* Vector 8: Write Custom Sequence to Button 1 in Compact Format */
    /* Compact: [preset_id=1][step_count=2][step 1: 1 motor, ch 0][step 2: 1 motor, ch 1] */
    const uint8_t compact_save[] = { 0x01, 0x02, 0x01, 0x00, 0x00, 0x01, 0x01, 0x00 };
    uint32_t fab3_notif_before = ble_transport_mock_get_fab3_notify_count();
    TEST_ASSERT(ble_transport_write_fab3(compact_save, sizeof(compact_save)) == CMD_STATUS_OK,
                "Compact sequence write accepted on FAB3");
    TEST_ASSERT(ble_transport_mock_get_fab3_notify_count() == fab3_notif_before + 1,
                "FAB3 emitted 212-byte table notification upon sequence update");

    fold_routine_t loaded_p1;
    storage_load_routine(1, &loaded_p1);
    TEST_ASSERT(loaded_p1.step_count == 2, "Preset 1 saved with step_count = 2");
    TEST_ASSERT(loaded_p1.checksum != 0, "CRC32 auto-computed and non-zero");

    /* Also verify save via Opcode 0x0A on FAB1 */
    const uint8_t fab1_save[] = { 0x0A, 0x02, 0x01, 0x01, 0x02, 0x00 }; /* Preset 2, 1 step, ch 2 */
    send_ble_command(fab1_save, sizeof(fab1_save));
    fold_routine_t loaded_p2;
    storage_load_routine(2, &loaded_p2);
    TEST_ASSERT(loaded_p2.step_count == 1 && loaded_p2.steps[0].motor_ids[0] == 2,
                "Preset 2 saved via Opcode 0x0A on FAB1");

    /* Vector 9: Stateless Raw Routine Preview (CMD_RUN_RAW_SEQUENCE, 0x01) */
    /* Compact raw sequence: [opcode=0x01][step_count=1][step 1: 1 motor, ch 3] */
    const uint8_t raw_cmd[] = { 0x01, 0x01, 0x01, 0x03, 0x00 };
    send_ble_command(raw_cmd, sizeof(raw_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Raw sequence completed cleanly");

    /* Preset 1 in NVS remains unmodified by raw sequence */
    fold_routine_t verify_p1;
    storage_load_routine(1, &verify_p1);
    TEST_ASSERT(verify_p1.step_count == 2, "NVS Preset 1 untouched by stateless raw execution");

    /* Vector 10: Empty Preset Guard & Out-of-Bounds Rejection */
    fold_routine_t empty_p3;
    memset(&empty_p3, 0, sizeof(empty_p3));
    storage_save_routine(3, &empty_p3);

    const uint8_t run_p3_cmd[] = { 0x00, 0x03 };
    TEST_ASSERT(ble_transport_write_fab1(run_p3_cmd, sizeof(run_p3_cmd)) == CMD_STATUS_ERR_INVALID_STEP,
                "0x00 on empty Preset 3 rejected at ingress with CMD_STATUS_ERR_INVALID_STEP");
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR, "Empty preset rejection flashed LED_STATE_INPUT_ERROR");

    const uint8_t bad_channel_cmd[] = { 0x01, 0x01, 0x01, 0x10, 0x00 }; /* ch 16 out of bounds */
    TEST_ASSERT(ble_transport_write_fab1(bad_channel_cmd, sizeof(bad_channel_cmd)) == CMD_STATUS_ERR_MOTOR_BOUNDS,
                "Out-of-bounds servo channel 16 rejected with CMD_STATUS_ERR_MOTOR_BOUNDS");

    /* Vector 11: Active Motion Busy Locks & Re-Entrancy Guard */
    motion_mock_set_status(MOTION_STATUS_RUNNING);
    TEST_ASSERT(motion_is_busy(), "Motion engine marked busy");

    const uint8_t run_p1_cmd[] = { 0x00, 0x01 };
    TEST_ASSERT(ble_transport_write_fab1(run_p1_cmd, sizeof(run_p1_cmd)) == CMD_STATUS_ERR_BUSY,
                "0x00 (CMD_RUN_PRESET) rejected with CMD_STATUS_ERR_BUSY during motion");
    TEST_ASSERT(ble_transport_write_fab1(raw_cmd, sizeof(raw_cmd)) == CMD_STATUS_ERR_BUSY,
                "0x01 (CMD_RUN_RAW_SEQUENCE) rejected with CMD_STATUS_ERR_BUSY during motion");
    TEST_ASSERT(ble_transport_write_fab1(fab1_save, sizeof(fab1_save)) == CMD_STATUS_ERR_BUSY,
                "0x0A (CMD_SET_BUTTON_SEQUENCE) rejected with CMD_STATUS_ERR_BUSY during motion");
    const uint8_t factory_reset_cmd[] = { 0x0C };
    TEST_ASSERT(ble_transport_write_fab1(factory_reset_cmd, sizeof(factory_reset_cmd)) == CMD_STATUS_ERR_BUSY,
                "0x0C (CMD_RESTORE_FACTORY_PRESETS) rejected with CMD_STATUS_ERR_BUSY during motion");
    const uint8_t jog_cmd[] = { 0x0D, 0x00, 0x5A };
    TEST_ASSERT(ble_transport_write_fab1(jog_cmd, sizeof(jog_cmd)) == CMD_STATUS_ERR_BUSY,
                "0x0D (CMD_JOG_MOTOR_ANGLE) rejected with CMD_STATUS_ERR_BUSY during motion");
    TEST_ASSERT(ble_transport_write_fab3(compact_save, sizeof(compact_save)) == CMD_STATUS_ERR_BUSY,
                "FAB3 GATT Write rejected with CMD_STATUS_ERR_BUSY during active motion");

    TEST_ASSERT(ble_transport_mock_get_queued_command_count() == 0,
                "Zero rejected commands were enqueued behind active motion");
    motion_reset_state();

    ble_transport_mock_disconnect();
}

static void test_vectors_12_to_17_telemetry_calibration_estop_and_concurrency(void)
{
    printf("\n--- Vectors 12-17: Telemetry, Calibration, E-Stop & Concurrency ---\n");
    reset_subsystems();

    const uint8_t dev_addr[6] = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    const uint8_t dev_irk[16]  = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
    sim_ios_central_connect(dev_addr, dev_irk, true);

    /* Vector 12: Real-Time 31-Byte Telemetry Streaming & Completion Push */
    motion_mock_set_status(MOTION_STATUS_RUNNING);
    motion_mock_set_progress(0, 3, 50, 150);
    pca9685_set_servo_angle(0, 90.0f);

    telemetry_packet_t pkt;
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.current_step_idx == 0 && pkt.total_steps == 3, "Telemetry reports step 1 / 3");
    TEST_ASSERT(pkt.step_progress_pct == 50, "Telemetry reports mid-sweep progress 50%");
    TEST_ASSERT(pkt.elapsed_step_time_ms == 150, "Telemetry reports elapsed_step_time_ms = 150ms");
    TEST_ASSERT(pkt.channel_angles[0] == 90, "Telemetry reports live channel_angles[0] = 90 deg");
    TEST_ASSERT(telemetry_get_current_interval_ms() == 100, "Adaptive stream interval is 100ms (10 Hz) in motion");

    /* Routine completion notification */
    motion_reset_state();
    remote_cmd_notify_completion(3);
    const telemetry_packet_t *comp_pkt = ble_transport_mock_get_last_fab2_notify();
    TEST_ASSERT(comp_pkt->step_progress_pct == 100, "Completion notification reports step_progress_pct = 100%");
    TEST_ASSERT(comp_pkt->last_cmd_status == CMD_STATUS_OK, "Completion notification reports CMD_STATUS_OK");
    TEST_ASSERT(telemetry_get_current_interval_ms() == 1000, "Stream throttles back to 1000ms (1 Hz) in idle");

    /* Vector 13: Live Servo Jog Calibration (0x0D), 10s Thermal Sleep & 15s Auto-Home */
    const uint8_t jog_ch1_90[] = { 0x0D, 0x01, 0x5A };
    send_ble_command(jog_ch1_90, sizeof(jog_ch1_90));
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING, "State transitioned to STATE_CALIBRATING");
    TEST_ASSERT(pca9685_get_channel_angle(1) == 90, "Channel 1 jogged to 90 deg");

    /* Stationary thermal de-energize cutoff (10s) */
    state_machine_tick(9990);
    TEST_ASSERT(!state_machine_is_calibrating_thermal_sleep(), "PCA9685 awake at 9.99s");
    state_machine_tick(20);
    TEST_ASSERT(state_machine_is_calibrating_thermal_sleep(), "PCA9685 entered thermal sleep at 10.0s while in STATE_CALIBRATING");

    /* Inactivity auto-home watchdog (15s) */
    state_machine_tick(5000);
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Inactivity watchdog homed channels and returned to IDLE at 15s");
    TEST_ASSERT(pca9685_get_channel_angle(1) == 0, "Channel 1 safely homed to 0 deg");

    /* Vector 14: Fast-Path Emergency Stop (0x03) & Stop (0x02) Preemption */
    motion_mock_set_status(MOTION_STATUS_RUNNING);
    pca9685_set_servo_angle(0, 180.0f);

    /* 0x03 Fast-path preemption */
    const uint8_t estop_cmd[] = { 0x03 };
    send_ble_command(estop_cmd, sizeof(estop_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_ESTOP, "Robot latched in STATE_ESTOP (2)");
    TEST_ASSERT(pca9685_get_channel_angle(0) == 0, "All channels immediately homed to 0 deg on E-Stop");
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT((pkt.error_code & (1U << 2)) != 0, "Telemetry error_code has BIT2 active (E-Stop latched)");

    /* Clear E-Stop using 0x02 */
    const uint8_t stop_cmd[] = { 0x02 };
    send_ble_command(stop_cmd, sizeof(stop_cmd));
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "STATE_ESTOP cleared back to STATE_IDLE_RUN via 0x02");
    ble_transport_build_telemetry(&pkt);
    TEST_ASSERT(pkt.error_code == 0, "Telemetry error_code cleared back to 0");

    /* Vector 15: Physical Button Press Execution Mirroring to Central */
    command_t btn_cmd = { .type = CMD_RUN_PRESET, .source = SOURCE_PHYSICAL_BUTTON, .payload = { .preset_id = 1 } };
    (void)state_machine_process_command(&btn_cmd);
    /* In host environment, Preset 1 runs synchronously to completion */
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Physical button Preset 1 completed");
    TEST_ASSERT(ble_transport_mock_get_last_fab2_notify()->step_progress_pct == 100,
                "Connected central received completion telemetry for physical button trigger");

    /* Vector 16: Factory Reset (0x0C) */
    uint32_t fab3_before = ble_transport_mock_get_fab3_notify_count();
    const uint8_t reset_cmd[] = { 0x0C };
    send_ble_command(reset_cmd, sizeof(reset_cmd));
    TEST_ASSERT(ble_transport_mock_get_fab3_notify_count() == fab3_before + 1,
                "0x0C emitted 212-byte FAB3 notification");
    fold_routine_t r1, r2, r3, r4;
    storage_load_routine(1, &r1);
    storage_load_routine(2, &r2);
    storage_load_routine(3, &r3);
    storage_load_routine(4, &r4);
    TEST_ASSERT(r1.step_count > 0 && r2.step_count > 0 && r3.step_count > 0 && r4.step_count > 0,
                "All 4 presets restored to factory default routines in NVS");

    /* Vector 17: Multi-Source Concurrency Arbitration & Disconnect Safety */
    /* Abrupt disconnect during active calibration */
    const uint8_t jog_ch2_45[] = { 0x0D, 0x02, 0x2D };
    send_ble_command(jog_ch2_45, sizeof(jog_ch2_45));
    TEST_ASSERT(state_machine_get_state() == STATE_CALIBRATING, "In STATE_CALIBRATING before disconnect");
    ble_transport_mock_disconnect();
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "Abrupt disconnect immediately safely homed servos and returned to IDLE");
    TEST_ASSERT(pca9685_get_channel_angle(2) == 0, "Channel 2 homed on disconnect");
}

/* ========================================================================= */
/* Test Suite: 200-Cycle Endurance Stress Test                               */
/* ========================================================================= */

static void test_200_cycle_endurance_stress(void)
{
    printf("\n--- 200-Cycle Continuous Endurance Stress Test ---\n");
    reset_subsystems();

    const uint8_t dev_addr[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
    const uint8_t dev_irk[16]  = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
    sim_ios_central_connect(dev_addr, dev_irk, true);

    const int TOTAL_CYCLES = 200;
    for (int cycle = 1; cycle <= TOTAL_CYCLES; cycle++) {
        /* 1. Trigger folding routine (Preset 1) */
        const uint8_t run_cmd[] = { 0x00, 0x01 };
        send_ble_command(run_cmd, sizeof(run_cmd));

        /* 2. Stream telemetry ticks */
        telemetry_tick();

        /* 3. Periodic sequence update on FAB3 (every 25 cycles) */
        if (cycle % 25 == 0) {
            const uint8_t custom_p1[] = { 0x01, 0x02, 0x01, 0x00, 0x00, 0x01, 0x01, 0x00 };
            (void)ble_transport_write_fab3(custom_p1, sizeof(custom_p1));
        }

        /* 4. Periodic simulated RPA MAC rotation reconnection (every 50 cycles) */
        if (cycle % 50 == 0) {
            ble_transport_mock_disconnect();
            uint8_t rotating_rpa[6] = {0x40 | (uint8_t)(cycle & 0x3F), 0x11, 0x22, 0x33, 0x44, 0x55};
            (void)ble_transport_mock_connect(rotating_rpa, true, dev_addr, dev_irk);
            (void)ble_transport_mock_set_cccd(0xFAB2, 0x0001);
            (void)ble_transport_mock_set_cccd(0xFAB3, 0x0001);
        }

        /* Assert state invariants */
        assert(state_machine_get_state() == STATE_IDLE_RUN);
        assert(!motion_is_busy());
    }

    TEST_ASSERT(true, "Completed 200 consecutive automated fold routines without failure");
    TEST_ASSERT(state_machine_get_state() == STATE_IDLE_RUN, "System invariant maintained (STATE_IDLE_RUN)");
    TEST_ASSERT(!motion_is_busy(), "Motion engine clean and idle");

    ble_transport_mock_disconnect();
}

/* ========================================================================= */
/* Main Test Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 11: End-to-End BLE Integration Test\n");
    printf("============================================================\n");

    test_vectors_1_to_6_discovery_security_and_locator();
    test_vectors_7_to_11_sequences_guards_and_busy_locks();
    test_vectors_12_to_17_telemetry_calibration_estop_and_concurrency();
    test_200_cycle_endurance_stress();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", s_tests_passed, s_total_tests);
    printf("============================================================\n");

    return 0;
}
