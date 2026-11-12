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
#include "ble_transport.h"

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

static void reset_full_ble_test_env(void)
{
    led_init();
    buttons_init();
    pca9685_mock_reset();
    pca9685_init();
    storage_mock_reset();
    storage_init();
    motion_reset_state();
    state_machine_reset();
    ble_transport_start(NULL);
}

/* ========================================================================= */
/* Test 1: Packed Wire Struct Sizes & Phase 8 Command Schema                 */
/* ========================================================================= */

static void test_packed_wire_struct_sizes(void)
{
    printf("Testing Packed Wire Struct Sizes & Command Schema...\n");

    TEST_ASSERT(sizeof(fold_step_t) == 3, "sizeof(fold_step_t) == 3 bytes exact (zero padding)");
    TEST_ASSERT(sizeof(fold_routine_t) == 53, "sizeof(fold_routine_t) == 53 bytes exact (zero padding)");
    TEST_ASSERT(BLE_FAB3_TABLE_SIZE == 212, "BLE_FAB3_TABLE_SIZE == 212 bytes (4 x 53B)");
    TEST_ASSERT(sizeof(button_sync_param_t) == 54, "sizeof(button_sync_param_t) == 54 bytes exact");
    TEST_ASSERT(sizeof(telemetry_packet_t) == 31, "sizeof(telemetry_packet_t) == 31 bytes exact");

    /* Backward compatibility of original 0..8 command enums + Phase 8 additions */
    TEST_ASSERT(CMD_RUN_PRESET == 0 && CMD_SYNC_PRESETS == 8, "Existing cmd_type_t 0..8 preserved");
    TEST_ASSERT(CMD_STOP_SEQUENCE == 9, "CMD_STOP_SEQUENCE == 9");
    TEST_ASSERT(CMD_IDENTIFY_ROBOT == 10, "CMD_IDENTIFY_ROBOT == 10");
    TEST_ASSERT(CMD_SET_TELEMETRY_STREAM == 11, "CMD_SET_TELEMETRY_STREAM == 11");
    TEST_ASSERT(CMD_CLEAR_BLE_BONDS == 12, "CMD_CLEAR_BLE_BONDS == 12");
    TEST_ASSERT(CMD_FACTORY_RESET_ALL == 14, "CMD_FACTORY_RESET_ALL == 14");
    TEST_ASSERT(BLE_OP_FACTORY_RESET_ALL == 0x1F, "BLE_OP_FACTORY_RESET_ALL == 0x1F");
}

/* ========================================================================= */
/* Test 2: GAP 31-Byte Split Advertisement & Dynamic Device Name             */
/* ========================================================================= */

static void test_gap_split_advertising_payloads(void)
{
    printf("Testing GAP 31-Byte Split Advertisement & Scan Response Payloads...\n");

    reset_full_ble_test_env();

    const uint8_t mac[6] = {0x30, 0xAE, 0xA4, 0x12, 0xB8, 0x4F};
    ble_transport_mock_set_bt_mac(mac);
    TEST_ASSERT(strcmp(ble_transport_get_device_name(), "Fabrica-B84F") == 0,
                "Dynamic BLE device name formatted as 'Fabrica-B84F' from BT MAC");

    uint8_t adv[BLE_ADV_MAX_LEN];
    uint8_t rsp[BLE_ADV_MAX_LEN];
    size_t adv_len = 0;
    size_t rsp_len = 0;

    esp_err_t err = ble_transport_build_adv_packets(ble_transport_get_device_name(),
                                                    3, adv, &adv_len, rsp, &rsp_len);
    TEST_ASSERT(err == ESP_OK, "ble_transport_build_adv_packets() returns ESP_OK");
    TEST_ASSERT(adv_len == 21 && adv_len <= BLE_ADV_MAX_LEN,
                "Primary Advertisement is 21 bytes exact (<= 31B iOS/Android limit)");
    TEST_ASSERT(rsp_len == 17 && rsp_len <= BLE_ADV_MAX_LEN,
                "Scan Response is 17 bytes exact (<= 31B iOS/Android limit)");

    /* Primary Adv: Flags (02 01 06) + 128-bit UUID 0000FAB0-0000-1000-8000-00805F9B34FB (Little-Endian) */
    const uint8_t expected_adv[21] = {
        0x02, 0x01, 0x06,
        0x11, 0x07,
        0xFB, 0x34, 0x9B, 0x5F, 0x80, 0x00, 0x00, 0x80,
        0x00, 0x10, 0x00, 0x00, 0xB0, 0xFA, 0x00, 0x00
    };
    TEST_ASSERT(memcmp(adv, expected_adv, 21) == 0,
                "Primary Advertisement matches Flags(0x06) + Little-Endian 0000FAB0-... UUID");

    /* Scan Response: Complete Local Name (0D 09 "Fabrica-B84F") + Tx Power (02 0A 03) */
    TEST_ASSERT(rsp[0] == 0x0D && rsp[1] == 0x09 && memcmp(&rsp[2], "Fabrica-B84F", 12) == 0,
                "Scan Response contains Complete Local Name 'Fabrica-B84F'");
    TEST_ASSERT(rsp[14] == 0x02 && rsp[15] == 0x0A && rsp[16] == 0x03,
                "Scan Response contains Tx Power Level (+3 dBm)");
}

/* ========================================================================= */
/* Test 3: GATT DIS (0x180A), 0x2901 User Descriptions & 0x2902 CCCDs        */
/* ========================================================================= */

static void test_gatt_descriptors_and_dis(void)
{
    printf("Testing DIS (0x180A), 0x2901 User Descriptions & 0x2902 CCCDs...\n");

    reset_full_ble_test_env();

    char buf[64];
    TEST_ASSERT(ble_transport_mock_read_dis_char(0x2A24, buf, sizeof(buf)) == ESP_OK &&
                strcmp(buf, "Fabrica-DevKit-v1") == 0,
                "DIS Model Number (0x2A24) == 'Fabrica-DevKit-v1'");
    TEST_ASSERT(ble_transport_mock_read_dis_char(0x2A26, buf, sizeof(buf)) == ESP_OK &&
                strcmp(buf, "v1.13.0") == 0,
                "DIS Firmware Revision (0x2A26) == 'v1.13.0'");
    TEST_ASSERT(ble_transport_mock_read_dis_char(0x2A29, buf, sizeof(buf)) == ESP_OK &&
                strcmp(buf, BLE_DIS_MANUFACTURER_NAME) == 0,
                "DIS Manufacturer Name (0x2A29) matches BLE_DIS_MANUFACTURER_NAME");

    TEST_ASSERT(ble_transport_mock_read_user_desc(0xFAB1, buf, sizeof(buf)) == ESP_OK &&
                strcmp(buf, "Fabrica Control Point (FAB1)") == 0,
                "FAB1 0x2901 User Description == 'Fabrica Control Point (FAB1)'");
    TEST_ASSERT(ble_transport_mock_read_user_desc(0xFAB2, buf, sizeof(buf)) == ESP_OK &&
                strcmp(buf, "Fabrica Status & Telemetry (FAB2)") == 0,
                "FAB2 0x2901 User Description == 'Fabrica Status & Telemetry (FAB2)'");
    TEST_ASSERT(ble_transport_mock_read_user_desc(0xFAB3, buf, sizeof(buf)) == ESP_OK &&
                strcmp(buf, "Fabrica Button Sequences 1-4 (FAB3)") == 0,
                "FAB3 0x2901 User Description == 'Fabrica Button Sequences 1-4 (FAB3)'");

    TEST_ASSERT(ble_transport_mock_set_cccd(0xFAB2, 0x0001) == ESP_OK &&
                ble_transport_mock_get_cccd(0xFAB2) == 0x0001,
                "FAB2 0x2902 CCCD notification subscription enabled");
    TEST_ASSERT(ble_transport_mock_set_cccd(0xFAB3, 0x0001) == ESP_OK &&
                ble_transport_mock_get_cccd(0xFAB3) == 0x0001,
                "FAB3 0x2902 CCCD notification subscription enabled");
}

/* ========================================================================= */
/* Test 4: Strict Hold-to-Pair, SMP IRK Bonding, RPA Rotation & Params/MTU   */
/* ========================================================================= */

static void test_hold_to_pair_smp_rpa_and_conn_params(void)
{
    printf("Testing Hold-to-Pair Window, SMP IRK Bonding, RPA Auto-Reconnect & MTU/Conn Params...\n");

    reset_full_ble_test_env();

    const uint8_t phone_id[6]  = {0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33};
    const uint8_t phone_rpa1[6]= {0x5A, 0x10, 0x20, 0x30, 0x40, 0x50};
    const uint8_t phone_rpa2[6]= {0x6B, 0x99, 0x88, 0x77, 0x66, 0x55};
    const uint8_t phone_irk[16]= {
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10
    };

    /* 1. Unbonded central attempting connection outside 120s Hold-to-Pair window -> REJECTED */
    TEST_ASSERT(state_machine_is_ble_pairing() == false, "Pairing window closed on initial boot");
    esp_err_t err = ble_transport_mock_connect(phone_rpa1, true, phone_id, phone_irk);
    TEST_ASSERT(err == ESP_ERR_INVALID_STATE, "Unbonded central rejected outside 120s pairing window");
    TEST_ASSERT(ble_transport_is_connected() == false, "Peripheral remains disconnected after rejection");
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "Status LED did NOT pulse connected on rejected central");

    /* 2. Simulate 3-second hold on physical Button B1 -> opens 120s pairing window */
    button_gesture_t g = GESTURE_NONE;
    for (int t = 0; t < 310; t++) {
        button_gesture_t step_g = buttons_update_channel(BTN_ID_1, 0, 10);
        if (step_g != GESTURE_NONE) {
            g = step_g;
        }
    }
    buttons_update_channel(BTN_ID_1, 1, 60); /* Release B1 */
    TEST_ASSERT(g == GESTURE_LONG_PRESS, "3-second hold on B1 triggers GESTURE_LONG_PRESS");

    command_t pair_cmd = buttons_translate_gesture(BTN_ID_1, g, state_machine_get_state());
    TEST_ASSERT(pair_cmd.type == CMD_ENTER_BLE_PAIRING, "Long press translates to CMD_ENTER_BLE_PAIRING");
    TEST_ASSERT(state_machine_process_command(&pair_cmd) == ESP_OK, "State machine enters BLE pairing mode");
    TEST_ASSERT(state_machine_is_ble_pairing() == true, "120-second pairing window is now OPEN");
    TEST_ASSERT(led_get_state() == LED_STATE_BLE_PAIRING, "Status LED flashes LED_STATE_BLE_PAIRING");

    /* 3. Connect unbonded central during pairing window -> SMP initiated, IRK saved, window closed */
    err = ble_transport_mock_connect(phone_rpa1, true, phone_id, phone_irk);
    TEST_ASSERT(err == ESP_OK, "Unbonded central accepted while 120s pairing window is open");
    TEST_ASSERT(ble_transport_is_connected() == true, "Central is now connected");
    TEST_ASSERT(ble_transport_get_bond_count() == 1, "1 bond stored in NVS");
    TEST_ASSERT(ble_transport_mock_is_peer_bonded(phone_id) == true, "Peer identity address recorded in bond store");
    TEST_ASSERT(state_machine_is_ble_pairing() == false, "120s pairing window automatically closed upon bonding");
    TEST_ASSERT(led_get_state() == LED_STATE_BLE_CONNECTED, "Status LED pulses LED_STATE_BLE_CONNECTED (1.0s solid)");

    /* Verify 1.0s solid ON pulse returns cleanly to LED_STATE_IDLE */
    TEST_ASSERT(led_get_current_level() == 1, "LED_STATE_BLE_CONNECTED drives GPIO HIGH");
    led_step_ms(1000);
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED_STATE_BLE_CONNECTED returns to LED_STATE_IDLE after 1000ms");

    /* 4. Verify peripheral-initiated MTU, SMP, and Apple/Android connection parameters */
    ble_mock_conn_info_t conn_info;
    ble_transport_mock_get_conn_info(&conn_info);
    TEST_ASSERT(conn_info.advertising_active == false, "Advertising stopped while 1 central is connected");
    TEST_ASSERT(conn_info.peripheral_mtu_initiated == true, "Peripheral proactively initiated MTU exchange for Android");
    TEST_ASSERT(conn_info.smp_security_initiated == true, "Peripheral proactively initiated SMP security");
    TEST_ASSERT(conn_info.param_update_requested == true, "Peripheral requested connection parameter update");
    TEST_ASSERT(conn_info.itvl_min_units == 12 && conn_info.itvl_max_units == 24 &&
                conn_info.latency == 0 && conn_info.supervision_timeout_10ms == 400,
                "Requested params: 15.0ms-30.0ms interval (12..24), 0 latency, 4000ms timeout (400)");

    TEST_ASSERT(ble_transport_mock_exchange_mtu(185) == 185, "iOS central MTU 185 negotiated cleanly");
    TEST_ASSERT(ble_transport_mock_exchange_mtu(517) == 512, "Android central MTU 517 clamped to preferred 512B");

    /* 5. Disconnect and reconnect with a ROTATED 15-minute RPA outside pairing window */
    ble_transport_mock_disconnect();
    ble_transport_mock_get_conn_info(&conn_info);
    TEST_ASSERT(conn_info.advertising_active == true, "Advertising automatically restarted on disconnect");
    TEST_ASSERT(state_machine_is_ble_pairing() == false, "Pairing window remains CLOSED");

    err = ble_transport_mock_connect(phone_rpa2, true, phone_id, phone_irk);
    TEST_ASSERT(err == ESP_OK, "Bonded peer reconnected seamlessly via IRK despite rotated RPA");
    TEST_ASSERT(led_get_state() == LED_STATE_BLE_CONNECTED, "LED pulses LED_STATE_BLE_CONNECTED on bonded reconnect");

    ble_transport_mock_disconnect();

    /* Verify an unknown central with a different IRK is still rejected! */
    const uint8_t stranger_id[6]  = {0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x01};
    const uint8_t stranger_rpa[6] = {0x44, 0x11, 0x22, 0x33, 0x44, 0x55};
    const uint8_t stranger_irk[16]= {0xFF, 0xEE, 0xDD, 0xCC, 0xBB, 0xAA, 0x99, 0x88,
                                     0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00};
    TEST_ASSERT(ble_transport_mock_connect(stranger_rpa, true, stranger_id, stranger_irk) == ESP_ERR_INVALID_STATE,
                "Stranger RPA with unknown IRK is rejected outside pairing window");

    /* 6. Verify 3s button hold (CMD_ENTER_BLE_PAIRING) takes priority over an active bonded connection */
    TEST_ASSERT(ble_transport_mock_connect(phone_rpa2, true, phone_id, phone_irk) == ESP_OK &&
                ble_transport_is_connected() == true,
                "Bonded Phone 1 connected (advertising paused)");
    TEST_ASSERT(state_machine_process_command(&pair_cmd) == ESP_OK,
                "3s button hold dispatches CMD_ENTER_BLE_PAIRING while Phone 1 is connected");
    ble_transport_mock_get_conn_info(&conn_info);
    TEST_ASSERT(ble_transport_is_connected() == false &&
                conn_info.advertising_active == true &&
                state_machine_is_ble_pairing() == true &&
                led_get_state() == LED_STATE_BLE_PAIRING,
                "3s hold priority immediately disconnects Phone 1 and restarts GAP advertising for pairing");
    TEST_ASSERT(ble_transport_mock_connect(stranger_rpa, true, stranger_id, stranger_irk) == ESP_OK &&
                ble_transport_get_bond_count() == 2,
                "Phone 2 immediately discovers and pairs after 3s hold preempted Phone 1");
}

/* ========================================================================= */
/* Test 5: 4-Bond NVS Capacity, FIFO Eviction & B1+B4 5s Hardware Bond Reset */
/* ========================================================================= */

static void test_bond_fifo_eviction_and_b1_b4_hardware_reset(void)
{
    printf("Testing 4-Bond Capacity, FIFO Eviction & B1+B4 5s Hardware Bond Reset...\n");

    reset_full_ble_test_env();

    uint8_t ids[5][6];
    uint8_t irks[5][16];
    for (uint8_t d = 0; d < 5; d++) {
        memset(ids[d], (uint8_t)(0x10 + d), 6);
        memset(irks[d], (uint8_t)(0xA0 + d), 16);

        command_t open_pair = {.type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON};
        TEST_ASSERT(state_machine_process_command(&open_pair) == ESP_OK, "Open pairing window");
        TEST_ASSERT(ble_transport_mock_connect(ids[d], false, ids[d], irks[d]) == ESP_OK,
                    "Paired central device in window");
        ble_transport_mock_disconnect();
    }

    TEST_ASSERT(ble_transport_get_bond_count() == BLE_MAX_BONDS,
                "Bond count capped at BLE_MAX_BONDS (4) after pairing 5 devices");
    TEST_ASSERT(ble_transport_mock_is_peer_bonded(ids[0]) == false,
                "Device 1 (oldest bond) evicted via FIFO when 5th device paired");
    TEST_ASSERT(ble_transport_mock_is_peer_bonded(ids[1]) == true &&
                ble_transport_mock_is_peer_bonded(ids[2]) == true &&
                ble_transport_mock_is_peer_bonded(ids[3]) == true &&
                ble_transport_mock_is_peer_bonded(ids[4]) == true,
                "Devices 2, 3, 4, and 5 remain bonded in NVS");

    /* Reconnect Device 5 before triggering hardware bond reset */
    TEST_ASSERT(ble_transport_mock_connect(ids[4], false, ids[4], irks[4]) == ESP_OK,
                "Bonded Device 5 connected prior to B1+B4 chord reset");

    /* Hold B1 (idx 0) and B4 (idx 3) simultaneously for 5000ms (plus 50ms debounce = 5100ms total) */
    buttons_reset_all();
    bool saw_false_pairing_at_3s = false;
    bool saw_bond_reset_at_5s = false;
    uint8_t reset_btn_idx = 0;

    for (int tick = 0; tick < 515; tick++) {
        button_gesture_t g1 = buttons_update_channel(BTN_ID_1, 0, 10);
        button_gesture_t g4 = buttons_update_channel(BTN_ID_4, 0, 10);

        if (g1 == GESTURE_LONG_PRESS || g4 == GESTURE_LONG_PRESS) {
            saw_false_pairing_at_3s = true;
        }
        if (g1 == GESTURE_BOND_RESET) {
            saw_bond_reset_at_5s = true;
            reset_btn_idx = BTN_ID_1;
        }
        if (g4 == GESTURE_BOND_RESET) {
            saw_bond_reset_at_5s = true;
            reset_btn_idx = BTN_ID_4;
        }
    }

    /* Release both buttons and ensure no spurious short tap fires */
    button_gesture_t rel1 = buttons_update_channel(BTN_ID_1, 1, 60);
    button_gesture_t rel4 = buttons_update_channel(BTN_ID_4, 1, 60);

    TEST_ASSERT(saw_false_pairing_at_3s == false,
                "Simultaneous B1+B4 hold suppressed 3-second single-button CMD_ENTER_BLE_PAIRING");
    TEST_ASSERT(saw_bond_reset_at_5s == true,
                "Simultaneous B1+B4 5-second hold triggered GESTURE_BOND_RESET");
    TEST_ASSERT(rel1 == GESTURE_NONE && rel4 == GESTURE_NONE,
                "Releasing B1+B4 after bond reset emits no trailing short tap");

    command_t reset_cmd = buttons_translate_gesture(reset_btn_idx, GESTURE_BOND_RESET, STATE_IDLE_RUN);
    TEST_ASSERT(reset_cmd.type == CMD_CLEAR_BLE_BONDS,
                "GESTURE_BOND_RESET translates to CMD_CLEAR_BLE_BONDS");
    TEST_ASSERT(state_machine_process_command(&reset_cmd) == ESP_OK,
                "state_machine_process_command(CMD_CLEAR_BLE_BONDS) returns ESP_OK");

    TEST_ASSERT(ble_transport_get_bond_count() == 0, "All NVS bonds erased by B1+B4 hardware reset");
    TEST_ASSERT(ble_transport_is_connected() == false, "Active BLE central disconnected on bond reset");
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR,
                "Status LED flashes LED_STATE_INPUT_ERROR (3 fast flashes) confirmation");
}

/* ========================================================================= */
/* Test 6: FAB3 Notifications, Compact/Full Writes & Motion Write Lock       */
/* ========================================================================= */

static void test_fab3_read_long_read_write_and_motion_lock(void)
{
    printf("Testing FAB3 Table Sync, Compact/Full Writes, Auto-CRC & Motion Write Lock...\n");

    reset_full_ble_test_env();

    /* Connect & subscribe to FAB3 notifications */
    const uint8_t peer_id[6]  = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC};
    const uint8_t peer_irk[16]= {0x22};
    command_t open_pair = {.type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON};
    state_machine_process_command(&open_pair);
    TEST_ASSERT(ble_transport_mock_connect(peer_id, false, peer_id, peer_irk) == ESP_OK, "Connected central");
    ble_transport_mock_set_cccd(0xFAB3, 0x0001);

    /* 1. Verify initial 212-byte FAB3 table snapshot via notification sync */
    TEST_ASSERT(ble_transport_notify_button_config() == ESP_OK &&
                ble_transport_mock_get_fab3_notify_count() == 1,
                "Initial FAB3 212-byte table snapshot emitted to subscribed central");
    uint8_t initial_table[BLE_FAB3_TABLE_SIZE];
    memcpy(initial_table, ble_transport_mock_get_last_fab3_notify(), BLE_FAB3_TABLE_SIZE);

    /* 2. Compact variable-length single-button write (01 02 01 00 00 01 01 00) */
    const uint8_t compact_b1[] = {
        0x01,             /* Preset 1 (B1) */
        0x02,             /* 2 steps */
        0x01, 0x00, 0x00, /* Step 1: 1 motor -> Ch 0 */
        0x01, 0x01, 0x00  /* Step 2: 1 motor -> Ch 1 */
    };
    uint32_t prev_notif = ble_transport_mock_get_fab3_notify_count();
    cmd_status_t st = ble_transport_write_fab3(compact_b1, sizeof(compact_b1));
    TEST_ASSERT(st == CMD_STATUS_OK, "Compact 8-byte FAB3 single-button write accepted (CMD_STATUS_OK)");
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS,
                "Status LED set to LED_STATE_SAVE_SUCCESS (2.0s solid ON)");
    TEST_ASSERT(ble_transport_mock_get_fab3_notify_count() == prev_notif + 1,
                "Subscribed FAB3 central received updated 212-byte notification");

    fold_routine_t saved_b1;
    TEST_ASSERT(storage_load_routine(1, &saved_b1) == ESP_OK, "Loaded updated Preset 1 from NVS with valid CRC32");
    TEST_ASSERT(saved_b1.step_count == 2 &&
                saved_b1.steps[0].motor_count == 1 && saved_b1.steps[0].motor_ids[0] == 0 &&
                saved_b1.steps[1].motor_count == 1 && saved_b1.steps[1].motor_ids[0] == 1 &&
                saved_b1.steps[2].motor_count == 0,
                "Compact write zero-padded unused steps 2..15 and persisted valid CRC32");

    /* 4. Full 54-byte single-button write with checksum == 0 (auto-CRC) vs corrupted non-zero CRC */
    button_sync_param_t sync_b2;
    memset(&sync_b2, 0, sizeof(sync_b2));
    sync_b2.preset_id = 2;
    sync_b2.routine.step_count = 1;
    sync_b2.routine.steps[0].motor_count = 2;
    sync_b2.routine.steps[0].motor_ids[0] = 2;
    sync_b2.routine.steps[0].motor_ids[1] = 3;
    sync_b2.routine.checksum = 0; /* Request firmware auto-CRC32 */

    TEST_ASSERT(ble_transport_write_fab3((const uint8_t *)&sync_b2, sizeof(sync_b2)) == CMD_STATUS_OK,
                "54-byte single-button write with checksum == 0 auto-computed CRC32 and saved");

    /* Corrupt non-zero checksum -> must reject with CMD_STATUS_ERR_CRC_MISMATCH */
    sync_b2.routine.steps[0].motor_ids[0] = 9;
    sync_b2.routine.checksum = 0xDEADBEEFU;
    TEST_ASSERT(ble_transport_write_fab3((const uint8_t *)&sync_b2, sizeof(sync_b2)) == CMD_STATUS_ERR_CRC_MISMATCH,
                "54-byte write with corrupted non-zero CRC32 rejected (CMD_STATUS_ERR_CRC_MISMATCH)");

    fold_routine_t check_b2;
    storage_load_routine(2, &check_b2);
    TEST_ASSERT(check_b2.steps[0].motor_ids[0] == 2,
                "Corrupted write did not overwrite previously saved Preset 2 in NVS");

    /* 5. Full 212-byte 4-button table write */
    uint8_t full_table[BLE_FAB3_TABLE_SIZE];
    memcpy(full_table, ble_transport_mock_get_last_fab3_notify(), BLE_FAB3_TABLE_SIZE);
    fold_routine_t *r4 = (fold_routine_t *)&full_table[3 * sizeof(fold_routine_t)];
    memset(r4, 0, sizeof(*r4));
    r4->step_count = 1;
    r4->steps[0].motor_count = 1;
    r4->steps[0].motor_ids[0] = 5;
    r4->checksum = 0; /* Auto-CRC */
    TEST_ASSERT(ble_transport_write_fab3(full_table, sizeof(full_table)) == CMD_STATUS_OK,
                "212-byte full 4-button table write accepted and persisted");

    /* 6. Active Motion Write Lock (CMD_STATUS_ERR_BUSY) */
    motion_mock_set_status(MOTION_STATUS_RUNNING);
    TEST_ASSERT(ble_transport_write_fab3(compact_b1, sizeof(compact_b1)) == CMD_STATUS_ERR_BUSY,
                "FAB3 write rejected with CMD_STATUS_ERR_BUSY while motion_is_busy() is active");
    motion_reset_state();
}

/* ========================================================================= */
/* Test 7: FAB1 Control Point Ingress, FAB2 Telemetry & Robot Identify       */
/* ========================================================================= */

static void test_fab1_command_ingress_fab2_telemetry_and_identify(void)
{
    printf("Testing FAB1 Control Point Opcodes, FAB2 Telemetry & Robot Identify...\n");

    reset_full_ble_test_env();

    const uint8_t peer_id[6]  = {0x99, 0x88, 0x77, 0x66, 0x55, 0x44};
    const uint8_t peer_irk[16]= {0x33};
    command_t open_pair = {.type = CMD_ENTER_BLE_PAIRING, .source = SOURCE_PHYSICAL_BUTTON};
    state_machine_process_command(&open_pair);
    ble_transport_mock_connect(peer_id, false, peer_id, peer_irk);
    ble_transport_mock_set_cccd(0xFAB2, 0x0001);
    ble_transport_mock_set_cccd(0xFAB3, 0x0001);
    led_step_ms(1000); /* Return from LED_STATE_BLE_CONNECTED to LED_STATE_IDLE */

    command_t popped;

    /* 1. 0x0E: CMD_IDENTIFY_ROBOT (3 fast double-blinks restoring prior base) */
    const uint8_t op_identify[] = {BLE_OP_IDENTIFY_ROBOT};
    TEST_ASSERT(ble_transport_write_fab1(op_identify, sizeof(op_identify)) == CMD_STATUS_OK,
                "FAB1 opcode 0x0E (Identify) accepted");
    TEST_ASSERT(ble_transport_mock_pop_command(&popped) &&
                popped.source == SOURCE_BLE && popped.type == CMD_IDENTIFY_ROBOT,
                "Opcode 0x0E enqueued CMD_IDENTIFY_ROBOT with SOURCE_BLE");
    TEST_ASSERT(state_machine_process_command(&popped) == ESP_OK &&
                led_get_state() == LED_STATE_IDENTIFY,
                "CMD_IDENTIFY_ROBOT activates LED_STATE_IDENTIFY");
    led_step_ms(3000);
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE,
                "LED_STATE_IDENTIFY completes 3000ms locator sequence and restores LED_STATE_IDLE");

    /* 2. Unknown opcode (e.g., 0x0F) is cleanly rejected with CMD_STATUS_ERR_INVALID_ARG */
    const uint8_t op_unknown[] = {0x0F};
    TEST_ASSERT(ble_transport_write_fab1(op_unknown, sizeof(op_unknown)) == CMD_STATUS_ERR_INVALID_ARG,
                "Unknown FAB1 opcode 0x0F rejected with CMD_STATUS_ERR_INVALID_ARG");

    /* 3. 0x0D: CMD_JOG_MOTOR_ANGLE (Ch 3 -> 135 deg) + FAB2 Telemetry live angle readback */
    const uint8_t op_jog[] = {BLE_OP_JOG_MOTOR_ANGLE, 3, 135};
    TEST_ASSERT(ble_transport_write_fab1(op_jog, sizeof(op_jog)) == CMD_STATUS_OK,
                "FAB1 opcode 0x0D (Jog Ch 3 -> 135 deg) accepted");
    TEST_ASSERT(ble_transport_mock_pop_command(&popped) &&
                popped.type == CMD_JOG_MOTOR_ANGLE &&
                popped.payload.jog_param.channel == 3 &&
                popped.payload.jog_param.angle_deg == 135.0f,
                "Opcode 0x0D enqueued CMD_JOG_MOTOR_ANGLE");
    TEST_ASSERT(state_machine_process_command(&popped) == ESP_OK, "Servo Ch 3 jogged to 135 deg");

    telemetry_packet_t tpkt;
    ble_transport_build_telemetry(&tpkt);
    TEST_ASSERT(sizeof(tpkt) == 31, "FAB2 telemetry_packet_t is exact 31 bytes");
    TEST_ASSERT(tpkt.channel_angles[3] == 135,
                "FAB2 telemetry reports live Channel 3 angle == 135 deg");

    /* 4. 0x00 (Run Preset), 0x0A (Set Button Seq compact), 0x0C (Restore Factory), 0x10 (Get Telemetry) */
    const uint8_t op_run_p1[] = {BLE_OP_RUN_PRESET, 1};
    TEST_ASSERT(ble_transport_write_fab1(op_run_p1, sizeof(op_run_p1)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&popped) &&
                popped.type == CMD_RUN_PRESET && popped.payload.preset_id == 1,
                "FAB1 opcode 0x00 01 enqueues CMD_RUN_PRESET(1) with SOURCE_BLE");

    const uint8_t op_set_btn_compact[] = {BLE_OP_SET_BUTTON_SEQUENCE, 4, 1, 1, 2, 0};
    TEST_ASSERT(ble_transport_write_fab1(op_set_btn_compact, sizeof(op_set_btn_compact)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&popped) &&
                popped.type == CMD_SET_BUTTON_SEQUENCE &&
                popped.payload.button_sync.preset_id == 4 &&
                popped.payload.button_sync.routine.step_count == 1,
                "FAB1 opcode 0x0A compact enqueues CMD_SET_BUTTON_SEQUENCE(4)");
    TEST_ASSERT(state_machine_process_command(&popped) == ESP_OK, "Saved Preset 4 via FAB1");

    const uint8_t op_factory[] = {BLE_OP_RESTORE_FACTORY_PRESETS};
    TEST_ASSERT(ble_transport_write_fab1(op_factory, sizeof(op_factory)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&popped) &&
                popped.type == CMD_RESTORE_FACTORY_PRESETS,
                "FAB1 opcode 0x0C enqueues CMD_RESTORE_FACTORY_PRESETS");
    TEST_ASSERT(state_machine_process_command(&popped) == ESP_OK, "Factory presets restored via FAB1");

    const uint8_t op_get_telem[] = {BLE_OP_GET_TELEMETRY};
    uint32_t prev_f2 = ble_transport_mock_get_fab2_notify_count();
    TEST_ASSERT(ble_transport_write_fab1(op_get_telem, sizeof(op_get_telem)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&popped) &&
                state_machine_process_command(&popped) == ESP_OK &&
                ble_transport_mock_get_fab2_notify_count() == prev_f2 + 1,
                "FAB1 opcode 0x10 triggers immediate 31-byte FAB2 notification");

    /* 5. Busy guard on 0x00 vs Core 1 fast-path E-Stop preemption on 0x02 / 0x03 */
    motion_mock_set_status(MOTION_STATUS_RUNNING);
    TEST_ASSERT(ble_transport_write_fab1(op_run_p1, sizeof(op_run_p1)) == CMD_STATUS_ERR_BUSY,
                "FAB1 0x00 rejected with CMD_STATUS_ERR_BUSY while motion is active");

    const uint8_t op_estop[] = {BLE_OP_EMERGENCY_STOP};
    TEST_ASSERT(ble_transport_write_fab1(op_estop, sizeof(op_estop)) == CMD_STATUS_OK,
                "FAB1 0x03 (E-Stop) accepted immediately during active motion");
    TEST_ASSERT(motion_get_status() == MOTION_STATUS_ABORTED,
                "Core 1 fast-path immediately aborted motion before queue consumer ran");
    TEST_ASSERT(ble_transport_mock_pop_command(&popped) && popped.type == CMD_EMERGENCY_STOP,
                "CMD_EMERGENCY_STOP also enqueued for State Machine cleanup");
    TEST_ASSERT(state_machine_process_command(&popped) == ESP_OK, "State Machine completed E-Stop cleanup");

    const uint8_t op_stop[] = {BLE_OP_STOP_SEQUENCE};
    TEST_ASSERT(ble_transport_write_fab1(op_stop, sizeof(op_stop)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&popped) &&
                popped.type == CMD_STOP_SEQUENCE &&
                state_machine_process_command(&popped) == ESP_OK,
                "FAB1 0x02 (Stop Sequence) cleanly resets robot to STATE_IDLE_RUN");

    /* Verify CMD_STOP_SEQUENCE preserves an open BLE pairing window & LED_STATE_BLE_PAIRING */
    state_machine_process_command(&open_pair);
    TEST_ASSERT(ble_transport_write_fab1(op_stop, sizeof(op_stop)) == CMD_STATUS_OK &&
                ble_transport_mock_pop_command(&popped) &&
                state_machine_process_command(&popped) == ESP_OK &&
                state_machine_is_ble_pairing() == true &&
                led_get_state() == LED_STATE_BLE_PAIRING,
                "CMD_STOP_SEQUENCE preserves open BLE pairing window and LED_STATE_BLE_PAIRING");
}

/* ========================================================================= */
/* Test Main Runner                                                          */
/* ========================================================================= */

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 8 Unit Test: NimBLE GATT Transport\n");
    printf("============================================================\n");

    test_packed_wire_struct_sizes();
    test_gap_split_advertising_payloads();
    test_gatt_descriptors_and_dis();
    test_hold_to_pair_smp_rpa_and_conn_params();
    test_bond_fifo_eviction_and_b1_b4_hardware_reset();
    test_fab3_read_long_read_write_and_motion_lock();
    test_fab1_command_ingress_fab2_telemetry_and_identify();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
