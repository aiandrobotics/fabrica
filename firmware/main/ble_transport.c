#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "pca9685.h"
#include "storage.h"
#include "motion.h"
#include "state_machine.h"
#include "ble_transport.h"
#include "remote_cmd.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/timers.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_system.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "host/ble_att.h"
#include "host/ble_gap.h"
#include "host/ble_gatt.h"
#include "host/ble_store.h"
#include "host/ble_uuid.h"
#include "host/util/util.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"

void ble_store_config_init(void);
static int8_t ble_platform_query_rssi(void);

static const char *TAG = "FABRICA_BLE";
#endif

/* ========================================================================= */
/* Compile-Time Wire Structure Packing Assertions                            */
/* ========================================================================= */

_Static_assert(sizeof(fold_step_t) == 3, "fold_step_t must be 3 bytes packed");
_Static_assert(sizeof(fold_routine_t) == 53, "fold_routine_t must be 53 bytes packed");
_Static_assert(sizeof(button_sync_param_t) == 54, "button_sync_param_t must be 54 bytes packed");
_Static_assert(sizeof(telemetry_packet_t) == 31, "telemetry_packet_t must be 31 bytes packed");
_Static_assert(BLE_FAB3_TABLE_SIZE == 212, "BLE_FAB3_TABLE_SIZE must equal 212 bytes");

/* ========================================================================= */
/* Shared BLE Transport State & UUID Bytes                                   */
/* ========================================================================= */

/** Little-Endian 128-bit UUID bytes for 0000FAB0-0000-1000-8000-00805F9B34FB */
static const uint8_t s_fab0_uuid128_le[16] = {
    0xFB, 0x34, 0x9B, 0x5F, 0x80, 0x00, 0x00, 0x80,
    0x00, 0x10, 0x00, 0x00, 0xB0, 0xFA, 0x00, 0x00
};

static char s_device_name[16] = "Fabrica-0000";
static bool s_is_connected = false;
static uint16_t s_negotiated_mtu = 23;
static bool s_telemetry_stream_enabled = false;
static uint16_t s_telemetry_seq_counter = 0;

/* ========================================================================= */
/* Shared Pure-C Protocol, Advertisement & GATT Payload Logic                */
/* ========================================================================= */

void ble_transport_format_device_name(const uint8_t bt_mac[6], char out_name[16])
{
    if (out_name == NULL) {
        return;
    }
    if (bt_mac == NULL) {
        snprintf(out_name, 16, "%s-0000", BLE_DEVICE_NAME_PREFIX);
        return;
    }
    snprintf(out_name, 16, "%s-%02X%02X", BLE_DEVICE_NAME_PREFIX, bt_mac[4], bt_mac[5]);
}

const char *ble_transport_get_device_name(void)
{
    return s_device_name;
}

esp_err_t ble_transport_build_adv_packets(const char *device_name,
                                          int8_t tx_pwr_dbm,
                                          uint8_t adv_out[BLE_ADV_MAX_LEN],
                                          size_t *adv_len,
                                          uint8_t rsp_out[BLE_ADV_MAX_LEN],
                                          size_t *rsp_len)
{
    if (device_name == NULL || adv_out == NULL || adv_len == NULL ||
        rsp_out == NULL || rsp_len == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    size_t name_len = strlen(device_name);
    /* Scan response needs (2 + name_len) + 3 bytes for TX power <= 31 bytes => name_len <= 26 */
    if (name_len == 0 || (name_len + 5) > BLE_ADV_MAX_LEN) {
        return ESP_ERR_INVALID_ARG;
    }

    memset(adv_out, 0, BLE_ADV_MAX_LEN);
    memset(rsp_out, 0, BLE_ADV_MAX_LEN);

    /* Primary Advertisement (21 bytes exact <= 31B):
     *   [0..2]  Flags (0x01): 0x06 (LE General Discoverable | BR/EDR Not Supported)
     *   [3..20] Complete 128-bit Service UUIDs (0x07): 0000FAB0-0000-1000-8000-00805F9B34FB
     */
    size_t a_idx = 0;
    adv_out[a_idx++] = 0x02;
    adv_out[a_idx++] = 0x01;
    adv_out[a_idx++] = 0x06;

    adv_out[a_idx++] = 0x11; /* 1 byte type + 16 bytes UUID */
    adv_out[a_idx++] = 0x07; /* Complete List of 128-bit Service Class UUIDs */
    memcpy(&adv_out[a_idx], s_fab0_uuid128_le, sizeof(s_fab0_uuid128_le));
    a_idx += sizeof(s_fab0_uuid128_le);
    *adv_len = a_idx;

    /* Scan Response (17 bytes for "Fabrica-XXXX" <= 31B):
     *   [0..name_len+1] Complete Local Name (0x09)
     *   [next 3 bytes]  Tx Power Level (0x0A)
     */
    size_t r_idx = 0;
    rsp_out[r_idx++] = (uint8_t)(name_len + 1);
    rsp_out[r_idx++] = 0x09; /* Complete Local Name */
    memcpy(&rsp_out[r_idx], device_name, name_len);
    r_idx += name_len;

    rsp_out[r_idx++] = 0x02;
    rsp_out[r_idx++] = 0x0A; /* Tx Power Level */
    rsp_out[r_idx++] = (uint8_t)tx_pwr_dbm;
    *rsp_len = r_idx;

    return ESP_OK;
}

bool ble_transport_is_connected(void)
{
    return s_is_connected;
}

uint16_t ble_transport_get_mtu(void)
{
    return s_negotiated_mtu;
}

cmd_status_t ble_transport_get_last_cmd_status(void)
{
    return remote_cmd_get_last_status();
}

void ble_transport_set_telemetry_stream(bool enable)
{
    s_telemetry_stream_enabled = enable;
}

bool ble_transport_is_telemetry_stream_enabled(void)
{
    return s_telemetry_stream_enabled;
}

static esp_err_t build_fab3_table_bytes(uint8_t out_table[BLE_FAB3_TABLE_SIZE])
{
    if (out_table == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    for (uint8_t id = 1; id <= TOTAL_PRESET_COUNT; id++) {
        fold_routine_t routine;
        memset(&routine, 0, sizeof(routine));
        esp_err_t err = storage_load_routine(id, &routine);
        if (err != ESP_OK && err != ESP_ERR_INVALID_CRC) {
            storage_get_default_routine(id, &routine);
        }
        memcpy(&out_table[(size_t)(id - 1) * sizeof(fold_routine_t)],
               &routine,
               sizeof(fold_routine_t));
    }

    return ESP_OK;
}

void ble_transport_build_telemetry(telemetry_packet_t *out_pkt)
{
    if (out_pkt == NULL) {
        return;
    }

    memset(out_pkt, 0, sizeof(*out_pkt));
    out_pkt->system_state = (uint8_t)state_machine_get_state();
    out_pkt->led_state = (uint8_t)led_get_state();
    out_pkt->active_button_id = (out_pkt->system_state == STATE_RUNNING_MOTION)
                                ? state_machine_get_active_preset()
                                : 0;

    uint8_t step_idx = 0;
    uint8_t total_steps = 0;
    uint8_t progress_pct = 0;
    uint16_t elapsed_ms = 0;
    remote_cmd_get_progress_snapshot(&step_idx, &total_steps, &progress_pct, &elapsed_ms);
    out_pkt->current_step_idx = step_idx;
    out_pkt->total_steps = total_steps;
    out_pkt->step_progress_pct = progress_pct;
    out_pkt->elapsed_step_time_ms = elapsed_ms;

    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        out_pkt->channel_angles[ch] = pca9685_get_channel_angle(ch);
    }

    out_pkt->last_cmd_status = (uint8_t)remote_cmd_get_last_status();

#ifdef ESP_PLATFORM
    out_pkt->free_heap_kb = (uint16_t)(esp_get_free_heap_size() / 1024U);
#else
    out_pkt->free_heap_kb = 220U;
#endif

    out_pkt->ble_rssi_dbm = -128;
#ifdef ESP_PLATFORM
    if (s_is_connected) {
        out_pkt->ble_rssi_dbm = ble_platform_query_rssi();
    }
#else
    if (s_is_connected) {
        out_pkt->ble_rssi_dbm = -52;
    }
#endif

    uint8_t err_mask = 0;
    if (out_pkt->system_state == STATE_ESTOP || motion_get_status() == MOTION_STATUS_ABORTED) {
        err_mask |= (1U << 2);
    }
    out_pkt->error_code = err_mask;
    out_pkt->sequence_counter = s_telemetry_seq_counter++;
}

cmd_status_t ble_transport_write_fab3(const uint8_t *data, size_t len)
{
    return remote_cmd_handle_fab3_write(data, len);
}

cmd_status_t ble_transport_write_fab1(const uint8_t *data, size_t len)
{
    return remote_cmd_handle_fab1_write(data, len);
}

/* ========================================================================= */
/* Target Implementation: ESP32 Apache NimBLE Stack (Core 1)                 */
/* ========================================================================= */
#ifdef ESP_PLATFORM

static QueueHandle_t s_cmd_queue = NULL;
static TimerHandle_t s_conn_param_timer = NULL;
static uint8_t s_own_addr_type = BLE_OWN_ADDR_PUBLIC;
static uint16_t s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
static uint16_t s_fab1_val_handle = 0;
static uint16_t s_fab2_val_handle = 0;
static uint16_t s_fab3_val_handle = 0;
static bool s_fab2_subscribed = false;
static bool s_fab3_subscribed = false;

/* Standard Device Information Service (0x180A) UUIDs */
static const ble_uuid16_t s_dis_svc_uuid  = BLE_UUID16_INIT(0x180A);
static const ble_uuid16_t s_dis_model_uuid = BLE_UUID16_INIT(0x2A24);
static const ble_uuid16_t s_dis_fwrev_uuid = BLE_UUID16_INIT(0x2A26);
static const ble_uuid16_t s_dis_mfg_uuid   = BLE_UUID16_INIT(0x2A29);

/* Characteristic User Description Descriptor (0x2901) UUID */
static const ble_uuid16_t s_user_desc_uuid = BLE_UUID16_INIT(0x2901);

/* Fabrica Custom Primary Service & Characteristic 128-bit UUIDs (Little-Endian) */
static const ble_uuid128_t s_fab0_svc_uuid =
    BLE_UUID128_INIT(0xFB, 0x34, 0x9B, 0x5F, 0x80, 0x00, 0x00, 0x80,
                     0x00, 0x10, 0x00, 0x00, 0xB0, 0xFA, 0x00, 0x00);

static const ble_uuid128_t s_fab1_chr_uuid =
    BLE_UUID128_INIT(0xFB, 0x34, 0x9B, 0x5F, 0x80, 0x00, 0x00, 0x80,
                     0x00, 0x10, 0x00, 0x00, 0xB1, 0xFA, 0x00, 0x00);

static const ble_uuid128_t s_fab2_chr_uuid =
    BLE_UUID128_INIT(0xFB, 0x34, 0x9B, 0x5F, 0x80, 0x00, 0x00, 0x80,
                     0x00, 0x10, 0x00, 0x00, 0xB2, 0xFA, 0x00, 0x00);

static const ble_uuid128_t s_fab3_chr_uuid =
    BLE_UUID128_INIT(0xFB, 0x34, 0x9B, 0x5F, 0x80, 0x00, 0x00, 0x80,
                     0x00, 0x10, 0x00, 0x00, 0xB3, 0xFA, 0x00, 0x00);

static int ble_gap_event_handler(struct ble_gap_event *event, void *arg);
static void ble_start_advertising(void);

static int8_t ble_platform_query_rssi(void)
{
    int8_t rssi = -128;
    if (s_conn_handle != BLE_HS_CONN_HANDLE_NONE) {
        if (ble_gap_conn_rssi(s_conn_handle, &rssi) != 0) {
            rssi = -128;
        }
    }
    return rssi;
}

esp_err_t ble_transport_enqueue_command(const command_t *cmd)
{
    if (s_cmd_queue == NULL || cmd == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    if (xQueueSend(s_cmd_queue, cmd, 0) != pdTRUE) {
        ESP_LOGE(TAG, "xCommandQueue full! Dropped BLE command %d", cmd->type);
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}

static int dis_gatt_access_cb(uint16_t conn_handle,
                              uint16_t attr_handle,
                              struct ble_gatt_access_ctxt *ctxt,
                              void *arg)
{
    (void)conn_handle;
    (void)attr_handle;
    (void)arg;

    if (ctxt->op != BLE_GATT_ACCESS_OP_READ_CHR) {
        return BLE_ATT_ERR_READ_NOT_PERMITTED;
    }

    uint16_t uuid16 = ble_uuid_u16(ctxt->chr->uuid);
    const char *str = NULL;
    if (uuid16 == 0x2A24) {
        str = BLE_DIS_MODEL_NUMBER;
    } else if (uuid16 == 0x2A26) {
        str = BLE_DIS_FIRMWARE_REVISION;
    } else if (uuid16 == 0x2A29) {
        str = BLE_DIS_MANUFACTURER_NAME;
    } else {
        return BLE_ATT_ERR_UNLIKELY;
    }

    int rc = os_mbuf_append(ctxt->om, str, (uint16_t)strlen(str));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

static int user_desc_access_cb(uint16_t conn_handle,
                               uint16_t attr_handle,
                               struct ble_gatt_access_ctxt *ctxt,
                               void *arg)
{
    (void)conn_handle;
    (void)attr_handle;

    if (ctxt->op != BLE_GATT_ACCESS_OP_READ_DSC) {
        return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
    }

    const char *desc_str = (const char *)arg;
    if (desc_str == NULL) {
        return BLE_ATT_ERR_UNLIKELY;
    }

    int rc = os_mbuf_append(ctxt->om, desc_str, (uint16_t)strlen(desc_str));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

static int fabrica_gatt_access_cb(uint16_t conn_handle,
                                  uint16_t attr_handle,
                                  struct ble_gatt_access_ctxt *ctxt,
                                  void *arg)
{
    (void)conn_handle;
    (void)arg;

    if (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) {
        /* Note: NimBLE slices ctxt->om automatically for ATT_READ_BLOB_REQ offsets */
        if (attr_handle == s_fab2_val_handle) {
            telemetry_packet_t pkt;
            ble_transport_build_telemetry(&pkt);
            int rc = os_mbuf_append(ctxt->om, &pkt, sizeof(pkt));
            return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
        }
        if (attr_handle == s_fab3_val_handle) {
            uint8_t table[BLE_FAB3_TABLE_SIZE];
            build_fab3_table_bytes(table);
            int rc = os_mbuf_append(ctxt->om, table, sizeof(table));
            return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
        }
        return BLE_ATT_ERR_READ_NOT_PERMITTED;
    }

    if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
        uint16_t om_len = OS_MBUF_PKTLEN(ctxt->om);
        if (om_len == 0 || om_len > BLE_PREFERRED_MTU) {
            return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
        }

        uint8_t flat_buf[BLE_PREFERRED_MTU];
        uint16_t copied_len = 0;
        if (ble_hs_mbuf_to_flat(ctxt->om, flat_buf, sizeof(flat_buf), &copied_len) != 0) {
            return BLE_ATT_ERR_UNLIKELY;
        }

        if (attr_handle == s_fab1_val_handle) {
            cmd_status_t st = ble_transport_write_fab1(flat_buf, copied_len);
            return (st == CMD_STATUS_OK) ? 0 : BLE_ATT_ERR_VALUE_NOT_ALLOWED;
        }

        if (attr_handle == s_fab3_val_handle) {
            cmd_status_t st = ble_transport_write_fab3(flat_buf, copied_len);
            return (st == CMD_STATUS_OK) ? 0 : BLE_ATT_ERR_VALUE_NOT_ALLOWED;
        }

        return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
    }

    return BLE_ATT_ERR_UNLIKELY;
}

static const struct ble_gatt_svc_def s_gatt_svcs[] = {
    {
        /* Standard Device Information Service (0x180A) */
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &s_dis_svc_uuid.u,
        .characteristics = (struct ble_gatt_chr_def[]) {
            {
                .uuid = &s_dis_model_uuid.u,
                .access_cb = dis_gatt_access_cb,
                .flags = BLE_GATT_CHR_F_READ,
            },
            {
                .uuid = &s_dis_fwrev_uuid.u,
                .access_cb = dis_gatt_access_cb,
                .flags = BLE_GATT_CHR_F_READ,
            },
            {
                .uuid = &s_dis_mfg_uuid.u,
                .access_cb = dis_gatt_access_cb,
                .flags = BLE_GATT_CHR_F_READ,
            },
            { 0 }
        },
    },
    {
        /* Custom Fabrica Control & Sequence Service (0000FAB0-...) */
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &s_fab0_svc_uuid.u,
        .characteristics = (struct ble_gatt_chr_def[]) {
            {
                /* FAB1: Control Point (Write | Write Without Response) */
                .uuid = &s_fab1_chr_uuid.u,
                .access_cb = fabrica_gatt_access_cb,
                .flags = BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_WRITE_NO_RSP,
                .val_handle = &s_fab1_val_handle,
                .descriptors = (struct ble_gatt_dsc_def[]) {
                    {
                        .uuid = &s_user_desc_uuid.u,
                        .att_flags = BLE_ATT_F_READ,
                        .access_cb = user_desc_access_cb,
                        .arg = (void *)BLE_DSC_FAB1_USER_DESC,
                    },
                    { 0 }
                },
            },
            {
                /* FAB2: Status & Telemetry (Read | Notify + auto 0x2902 CCCD) */
                .uuid = &s_fab2_chr_uuid.u,
                .access_cb = fabrica_gatt_access_cb,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &s_fab2_val_handle,
                .descriptors = (struct ble_gatt_dsc_def[]) {
                    {
                        .uuid = &s_user_desc_uuid.u,
                        .att_flags = BLE_ATT_F_READ,
                        .access_cb = user_desc_access_cb,
                        .arg = (void *)BLE_DSC_FAB2_USER_DESC,
                    },
                    { 0 }
                },
            },
            {
                /* FAB3: Button Sequences 1-4 (Read | Write | Notify + auto 0x2902 CCCD) */
                .uuid = &s_fab3_chr_uuid.u,
                .access_cb = fabrica_gatt_access_cb,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &s_fab3_val_handle,
                .descriptors = (struct ble_gatt_dsc_def[]) {
                    {
                        .uuid = &s_user_desc_uuid.u,
                        .att_flags = BLE_ATT_F_READ,
                        .access_cb = user_desc_access_cb,
                        .arg = (void *)BLE_DSC_FAB3_USER_DESC,
                    },
                    { 0 }
                },
            },
            { 0 }
        },
    },
    { 0 }
};

static bool is_peer_bonded_in_store(const ble_addr_t *peer_id_addr)
{
    if (peer_id_addr == NULL) {
        return false;
    }

    ble_addr_t peers[BLE_MAX_BONDS];
    int num_peers = 0;
    if (ble_store_util_bonded_peers(peers, &num_peers, BLE_MAX_BONDS) != 0) {
        return false;
    }

    uint8_t norm_type = peer_id_addr->type & 0x01U;
    for (int i = 0; i < num_peers; i++) {
        if ((peers[i].type & 0x01U) == norm_type &&
            memcmp(peers[i].val, peer_id_addr->val, 6) == 0) {
            return true;
        }
    }
    return false;
}

static void ble_conn_param_timer_cb(TimerHandle_t xTimer)
{
    (void)xTimer;
    if (s_conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return;
    }

    struct ble_gap_upd_params params = {
        .itvl_min = BLE_CONN_INTERVAL_MIN_UNITS,
        .itvl_max = BLE_CONN_INTERVAL_MAX_UNITS,
        .latency = BLE_CONN_SLAVE_LATENCY,
        .supervision_timeout = BLE_SUPERVISION_TIMEOUT_UNITS,
        .min_ce_len = 0,
        .max_ce_len = 0
    };

    int rc = ble_gap_update_params(s_conn_handle, &params);
    if (rc != 0) {
        ESP_LOGW(TAG, "ble_gap_update_params returned rc=%d", rc);
    } else {
        ESP_LOGI(TAG, "Requested BLE connection params: 15.0ms-30.0ms, latency=0, timeout=4000ms");
    }
}

static void ble_start_advertising(void)
{
    if (ble_gap_adv_active() || s_is_connected) {
        return;
    }

    uint8_t adv_buf[BLE_ADV_MAX_LEN];
    uint8_t rsp_buf[BLE_ADV_MAX_LEN];
    size_t adv_len = 0;
    size_t rsp_len = 0;

    if (ble_transport_build_adv_packets(s_device_name, 3, adv_buf, &adv_len, rsp_buf, &rsp_len) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to construct split advertisement packets");
        return;
    }

    int rc = ble_gap_adv_set_data(adv_buf, (int)adv_len);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_adv_set_data failed: rc=%d", rc);
        return;
    }

    rc = ble_gap_adv_rsp_set_data(rsp_buf, (int)rsp_len);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_adv_rsp_set_data failed: rc=%d", rc);
        return;
    }

    struct ble_gap_adv_params adv_params;
    memset(&adv_params, 0, sizeof(adv_params));
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;
    adv_params.itvl_min = BLE_ADV_INTERVAL_UNITS;
    adv_params.itvl_max = BLE_ADV_INTERVAL_UNITS;

    rc = ble_gap_adv_start(s_own_addr_type, NULL, BLE_HS_FOREVER,
                           &adv_params, ble_gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_adv_start failed: rc=%d", rc);
    } else {
        ESP_LOGI(TAG, "BLE Advertising started as '%s' (Adv=%zuB, ScanRsp=%zuB, 100ms interval)",
                 s_device_name, adv_len, rsp_len);
    }
}

static int ble_gap_event_handler(struct ble_gap_event *event, void *arg)
{
    (void)arg;
    struct ble_gap_conn_desc desc;

    switch (event->type) {
        case BLE_GAP_EVENT_CONNECT: {
            if (event->connect.status != 0) {
                ESP_LOGW(TAG, "BLE connection attempt failed (status=%d). Restarting advertising.",
                         event->connect.status);
                s_is_connected = false;
                s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
                ble_start_advertising();
                return 0;
            }

            uint16_t conn_handle = event->connect.conn_handle;
            if (ble_gap_conn_find(conn_handle, &desc) != 0) {
                ble_gap_terminate(conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                return 0;
            }

            bool is_bonded = desc.sec_state.bonded || is_peer_bonded_in_store(&desc.peer_id_addr);
            bool pairing_open = state_machine_is_ble_pairing();

            if (!is_bonded && !pairing_open) {
                ESP_LOGW(TAG, "Rejecting unbonded central outside 120s Hold-to-Pair window!");
                ble_gap_terminate(conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                return 0;
            }

            s_conn_handle = conn_handle;
            s_is_connected = true;
            s_negotiated_mtu = ble_att_mtu(conn_handle);
            s_fab2_subscribed = false;
            s_fab3_subscribed = false;

            /* Evict oldest bond (FIFO) if pairing a new 5th device */
            if (!is_bonded && pairing_open) {
                if (ble_transport_get_bond_count() >= BLE_MAX_BONDS) {
                    ESP_LOGW(TAG, "Bond store full (%d/%d). Evicting oldest bonded peer.",
                             BLE_MAX_BONDS, BLE_MAX_BONDS);
                    (void)ble_gap_unpair_oldest_peer();
                }
            }

            /* Proactively initiate peripheral ATT MTU exchange (512B) for Android & iOS */
            (void)ble_gattc_exchange_mtu(conn_handle, NULL, NULL);

            /* Proactively initiate SMP Just Works + IRK encryption/bonding */
            int sec_rc = ble_gap_security_initiate(conn_handle);
            if (sec_rc != 0 && sec_rc != BLE_HS_EALREADY) {
                ESP_LOGW(TAG, "ble_gap_security_initiate returned rc=%d", sec_rc);
            }

            if (is_bonded) {
                ESP_LOGI(TAG, "Bonded central reconnected (conn_handle=%u). Pulsing LED.", conn_handle);
                led_set_state(LED_STATE_BLE_CONNECTED);
            } else {
                ESP_LOGI(TAG, "Unbonded central accepted in pairing window (conn_handle=%u). Awaiting SMP.",
                         conn_handle);
            }

            if (s_conn_param_timer != NULL) {
                xTimerReset(s_conn_param_timer, 0);
            }
            return 0;
        }

        case BLE_GAP_EVENT_DISCONNECT: {
            ESP_LOGI(TAG, "BLE central disconnected (reason=%d). Resuming advertising.",
                     event->disconnect.reason);
            if (s_conn_param_timer != NULL) {
                xTimerStop(s_conn_param_timer, 0);
            }
            s_is_connected = false;
            s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
            s_negotiated_mtu = 23;
            s_fab2_subscribed = false;
            s_fab3_subscribed = false;
            state_machine_on_ble_disconnect();
            ble_start_advertising();
            return 0;
        }

        case BLE_GAP_EVENT_ENC_CHANGE: {
            ESP_LOGI(TAG, "BLE encryption change: status=%d", event->enc_change.status);
            if (event->enc_change.status == 0) {
                if (state_machine_is_ble_pairing()) {
                    ESP_LOGI(TAG, "SMP bonding succeeded! Closing 120s pairing window.");
                    state_machine_close_ble_pairing();
                }
                led_set_state(LED_STATE_BLE_CONNECTED);
            } else if (!state_machine_is_ble_pairing()) {
                ESP_LOGW(TAG, "SMP encryption failed outside pairing window; terminating link.");
                ble_gap_terminate(event->enc_change.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
            }
            return 0;
        }

        case BLE_GAP_EVENT_REPEAT_PAIRING: {
            if (ble_gap_conn_find(event->repeat_pairing.conn_handle, &desc) == 0) {
                ble_store_util_delete_peer(&desc.peer_id_addr);
            }
            return BLE_GAP_REPEAT_PAIRING_RETRY;
        }

        case BLE_GAP_EVENT_MTU: {
            s_negotiated_mtu = event->mtu.value;
            ESP_LOGI(TAG, "ATT MTU negotiated: %u bytes (conn_handle=%u)",
                     s_negotiated_mtu, event->mtu.conn_handle);
            return 0;
        }

        case BLE_GAP_EVENT_SUBSCRIBE: {
            if (event->subscribe.attr_handle == s_fab2_val_handle) {
                s_fab2_subscribed = (event->subscribe.cur_notify != 0);
                ESP_LOGI(TAG, "FAB2 telemetry notifications %s",
                         s_fab2_subscribed ? "ENABLED" : "DISABLED");
            } else if (event->subscribe.attr_handle == s_fab3_val_handle) {
                s_fab3_subscribed = (event->subscribe.cur_notify != 0);
                ESP_LOGI(TAG, "FAB3 button sequence notifications %s",
                         s_fab3_subscribed ? "ENABLED" : "DISABLED");
            }
            return 0;
        }

        case BLE_GAP_EVENT_ADV_COMPLETE: {
            ble_start_advertising();
            return 0;
        }

        default:
            return 0;
    }
}

static void ble_on_reset(int reason)
{
    ESP_LOGE(TAG, "NimBLE host reset (reason=%d)", reason);
}

static void ble_on_sync(void)
{
    int rc = ble_hs_util_ensure_addr(0);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_hs_util_ensure_addr failed: rc=%d", rc);
        return;
    }

    rc = ble_hs_id_infer_auto(0, &s_own_addr_type);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_hs_id_infer_auto failed: rc=%d", rc);
        return;
    }

    /*
     * Peer RPA resolution for bonded iOS/Android centrals is active automatically
     * on ESP32 via NimBLE Host-Based Privacy (BLE_HOST_BASED_PRIVACY=1) paired with
     * BLE_SM_PAIR_KEY_DIST_ID + ble_store_config_init().
     */
    ble_start_advertising();
}

static void ble_host_task(void *param)
{
    (void)param;
    ESP_LOGI(TAG, "NimBLE host task running on Core %d", xPortGetCoreID());
    nimble_port_run();
    nimble_port_freertos_deinit();
}

int ble_transport_get_bond_count(void)
{
    ble_addr_t peers[BLE_MAX_BONDS];
    int num_peers = 0;
    if (ble_store_util_bonded_peers(peers, &num_peers, BLE_MAX_BONDS) != 0) {
        return 0;
    }
    return num_peers;
}

esp_err_t ble_transport_enter_pairing_mode(void)
{
    if (s_conn_handle != BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGI(TAG, "3s Hold-to-Pair priority: disconnecting active central (conn_handle=%u) to advertise for pairing.",
                 s_conn_handle);
        if (ble_gap_terminate(s_conn_handle, BLE_ERR_REM_USER_CONN_TERM) != 0) {
            s_is_connected = false;
            s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
            state_machine_on_ble_disconnect();
            ble_start_advertising();
        }
    } else {
        ble_start_advertising();
    }
    return ESP_OK;
}

esp_err_t ble_transport_clear_bonds(void)
{
    ble_addr_t peers[BLE_MAX_BONDS];
    int num_peers = 0;
    if (ble_store_util_bonded_peers(peers, &num_peers, BLE_MAX_BONDS) == 0) {
        for (int i = 0; i < num_peers; i++) {
            (void)ble_gap_unpair(&peers[i]);
        }
    }
    (void)ble_store_clear();

    if (s_conn_handle != BLE_HS_CONN_HANDLE_NONE) {
        (void)ble_gap_terminate(s_conn_handle, BLE_ERR_REM_USER_CONN_TERM);
    }

    ESP_LOGW(TAG, "All stored BLE bonds cleared from NVS.");
    return ESP_OK;
}

bool ble_transport_is_telemetry_subscribed(void)
{
    return s_is_connected && s_fab2_subscribed && (s_conn_handle != BLE_HS_CONN_HANDLE_NONE);
}

esp_err_t ble_transport_notify_telemetry(void)
{
    if (!s_is_connected || !s_fab2_subscribed || s_conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return ESP_OK;
    }

    telemetry_packet_t pkt;
    ble_transport_build_telemetry(&pkt);

    struct os_mbuf *om = ble_hs_mbuf_from_flat(&pkt, sizeof(pkt));
    if (om == NULL) {
        return ESP_ERR_NO_MEM;
    }

    int rc = ble_gatts_notify_custom(s_conn_handle, s_fab2_val_handle, om);
    return (rc == 0) ? ESP_OK : ESP_FAIL;
}

esp_err_t ble_transport_notify_button_config(void)
{
    if (!s_is_connected || !s_fab3_subscribed || s_conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return ESP_OK;
    }

    uint8_t table[BLE_FAB3_TABLE_SIZE];
    build_fab3_table_bytes(table);

    struct os_mbuf *om = ble_hs_mbuf_from_flat(table, sizeof(table));
    if (om == NULL) {
        return ESP_ERR_NO_MEM;
    }

    int rc = ble_gatts_notify_custom(s_conn_handle, s_fab3_val_handle, om);
    return (rc == 0) ? ESP_OK : ESP_FAIL;
}

esp_err_t ble_transport_start(QueueHandle_t cmd_queue)
{
    s_cmd_queue = cmd_queue;
    remote_cmd_reset();

    uint8_t bt_mac[6] = {0};
    if (esp_read_mac(bt_mac, ESP_MAC_BT) == ESP_OK) {
        ble_transport_format_device_name(bt_mac, s_device_name);
    } else {
        ble_transport_format_device_name(NULL, s_device_name);
    }

    if (s_conn_param_timer == NULL) {
        s_conn_param_timer = xTimerCreate("ble_conn_upd",
                                          pdMS_TO_TICKS(BLE_CONN_PARAM_UPDATE_DELAY_MS),
                                          pdFALSE,
                                          NULL,
                                          ble_conn_param_timer_cb);
    }

    esp_err_t ret = nimble_port_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "nimble_port_init failed: %s (0x%x)", esp_err_to_name(ret), ret);
        return ret;
    }

    /* Configure NimBLE Host & SMP Security Manager ("Just Works" LE SC + IRK Bonding) */
    ble_hs_cfg.reset_cb = ble_on_reset;
    ble_hs_cfg.sync_cb = ble_on_sync;
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;
    ble_hs_cfg.sm_io_cap = BLE_HS_IO_NO_INPUT_OUTPUT;
    ble_hs_cfg.sm_bonding = 1;
    ble_hs_cfg.sm_mitm = 0;
    ble_hs_cfg.sm_sc = 1;
    ble_hs_cfg.sm_our_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;
    ble_hs_cfg.sm_their_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;

    (void)ble_att_set_preferred_mtu(BLE_PREFERRED_MTU);

    ble_svc_gap_init();
    ble_svc_gatt_init();
    (void)ble_svc_gap_device_name_set(s_device_name);

    int rc = ble_gatts_count_cfg(s_gatt_svcs);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gatts_count_cfg failed: rc=%d", rc);
        return ESP_FAIL;
    }

    rc = ble_gatts_add_svcs(s_gatt_svcs);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gatts_add_svcs failed: rc=%d", rc);
        return ESP_FAIL;
    }

    ble_store_config_init();
    nimble_port_freertos_init(ble_host_task);

    ESP_LOGI(TAG, "NimBLE GATT Server initialized on Core 1 as '%s' (Free Heap: %u KB)",
             s_device_name, (unsigned int)(esp_get_free_heap_size() / 1024U));
    return ESP_OK;
}

/* ========================================================================= */
/* Host Simulation Mock Implementation (Unit Testing Harness)                */
/* ========================================================================= */
#else /* !ESP_PLATFORM */

typedef struct {
    bool valid;
    uint8_t id_addr[6];
    uint8_t irk[16];
} mock_bond_entry_t;

static mock_bond_entry_t s_mock_bonds[BLE_MAX_BONDS];
static int s_mock_bond_count = 0;

static ble_mock_conn_info_t s_mock_conn_info;
static uint16_t s_mock_fab2_cccd = 0;
static uint16_t s_mock_fab3_cccd = 0;

static uint32_t s_mock_fab2_notify_count = 0;
static telemetry_packet_t s_mock_last_fab2_pkt;

static uint32_t s_mock_fab3_notify_count = 0;
static uint8_t s_mock_last_fab3_table[BLE_FAB3_TABLE_SIZE];

static command_t s_mock_cmd_fifo[COMMAND_QUEUE_LENGTH];
static size_t s_mock_cmd_head = 0;
static size_t s_mock_cmd_count = 0;

esp_err_t ble_transport_enqueue_command(const command_t *cmd)
{
    if (cmd == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (s_mock_cmd_count >= COMMAND_QUEUE_LENGTH) {
        return ESP_ERR_NO_MEM;
    }
    size_t tail = (s_mock_cmd_head + s_mock_cmd_count) % COMMAND_QUEUE_LENGTH;
    s_mock_cmd_fifo[tail] = *cmd;
    s_mock_cmd_count++;
    return ESP_OK;
}

void ble_transport_mock_reset(void)
{
    const uint8_t default_mac[6] = {0x24, 0x6F, 0x28, 0xAA, 0xA4, 0x7B};
    ble_transport_format_device_name(default_mac, s_device_name);

    s_is_connected = false;
    s_negotiated_mtu = 23;
    remote_cmd_reset();
    s_telemetry_stream_enabled = false;
    s_telemetry_seq_counter = 0;

    memset(s_mock_bonds, 0, sizeof(s_mock_bonds));
    s_mock_bond_count = 0;

    memset(&s_mock_conn_info, 0, sizeof(s_mock_conn_info));
    s_mock_conn_info.advertising_active = true;

    s_mock_fab2_cccd = 0;
    s_mock_fab3_cccd = 0;
    s_mock_fab2_notify_count = 0;
    memset(&s_mock_last_fab2_pkt, 0, sizeof(s_mock_last_fab2_pkt));
    s_mock_fab3_notify_count = 0;
    memset(s_mock_last_fab3_table, 0, sizeof(s_mock_last_fab3_table));

    memset(s_mock_cmd_fifo, 0, sizeof(s_mock_cmd_fifo));
    s_mock_cmd_head = 0;
    s_mock_cmd_count = 0;
}

void ble_transport_mock_set_bt_mac(const uint8_t bt_mac[6])
{
    ble_transport_format_device_name(bt_mac, s_device_name);
}

esp_err_t ble_transport_start(QueueHandle_t cmd_queue)
{
    (void)cmd_queue;
    ble_transport_mock_reset();
    return ESP_OK;
}

int ble_transport_get_bond_count(void)
{
    return s_mock_bond_count;
}

bool ble_transport_mock_is_peer_bonded(const uint8_t peer_id_addr[6])
{
    if (peer_id_addr == NULL) {
        return false;
    }
    for (int i = 0; i < s_mock_bond_count; i++) {
        if (s_mock_bonds[i].valid && memcmp(s_mock_bonds[i].id_addr, peer_id_addr, 6) == 0) {
            return true;
        }
    }
    return false;
}

esp_err_t ble_transport_mock_connect(const uint8_t ota_addr[6],
                                     bool is_rpa,
                                     const uint8_t peer_id_addr[6],
                                     const uint8_t peer_irk[16])
{
    if (ota_addr == NULL || peer_id_addr == NULL || peer_irk == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    /* Enforce single central policy */
    if (s_is_connected) {
        return ESP_ERR_INVALID_STATE;
    }

    int matched_idx = -1;
    for (int i = 0; i < s_mock_bond_count; i++) {
        if (!s_mock_bonds[i].valid) {
            continue;
        }
        if (is_rpa) {
            /* Resolve rotating RPA against stored 16-byte peer IRKs */
            if (memcmp(s_mock_bonds[i].irk, peer_irk, 16) == 0) {
                matched_idx = i;
                break;
            }
        } else {
            if (memcmp(s_mock_bonds[i].id_addr, ota_addr, 6) == 0) {
                matched_idx = i;
                break;
            }
        }
    }

    bool is_bonded = (matched_idx >= 0);
    bool pairing_open = state_machine_is_ble_pairing();

    if (!is_bonded && !pairing_open) {
        /* Reject unbonded central outside 120s Hold-to-Pair window */
        s_is_connected = false;
        s_mock_conn_info.advertising_active = true;
        s_mock_conn_info.smp_security_initiated = false;
        return ESP_ERR_INVALID_STATE;
    }

    /* Connection accepted: stop advertising, initiate peripheral MTU + SMP + Apple conn params */
    s_is_connected = true;
    s_negotiated_mtu = BLE_PREFERRED_MTU;
    s_mock_conn_info.advertising_active = false;
    s_mock_conn_info.peripheral_mtu_initiated = true;
    s_mock_conn_info.smp_security_initiated = true;
    s_mock_conn_info.param_update_requested = true;
    s_mock_conn_info.itvl_min_units = BLE_CONN_INTERVAL_MIN_UNITS;
    s_mock_conn_info.itvl_max_units = BLE_CONN_INTERVAL_MAX_UNITS;
    s_mock_conn_info.latency = BLE_CONN_SLAVE_LATENCY;
    s_mock_conn_info.supervision_timeout_10ms = BLE_SUPERVISION_TIMEOUT_UNITS;

    if (!is_bonded && pairing_open) {
        if (s_mock_bond_count >= BLE_MAX_BONDS) {
            /* FIFO eviction of oldest bond at slot 0 */
            memmove(&s_mock_bonds[0], &s_mock_bonds[1],
                    (size_t)(BLE_MAX_BONDS - 1) * sizeof(mock_bond_entry_t));
            s_mock_bond_count = BLE_MAX_BONDS - 1;
        }
        s_mock_bonds[s_mock_bond_count].valid = true;
        memcpy(s_mock_bonds[s_mock_bond_count].id_addr, peer_id_addr, 6);
        memcpy(s_mock_bonds[s_mock_bond_count].irk, peer_irk, 16);
        s_mock_bond_count++;

        state_machine_close_ble_pairing();
    } else if (pairing_open) {
        state_machine_close_ble_pairing();
    }

    led_set_state(LED_STATE_BLE_CONNECTED);
    return ESP_OK;
}

esp_err_t ble_transport_enter_pairing_mode(void)
{
    if (s_is_connected) {
        ble_transport_mock_disconnect();
    } else {
        s_mock_conn_info.advertising_active = true;
    }
    return ESP_OK;
}

void ble_transport_mock_disconnect(void)
{
    bool was_connected = s_is_connected;
    s_is_connected = false;
    s_negotiated_mtu = 23;
    s_mock_fab2_cccd = 0;
    s_mock_fab3_cccd = 0;
    s_mock_conn_info.advertising_active = true;
    if (was_connected) {
        state_machine_on_ble_disconnect();
    }
}

uint16_t ble_transport_mock_exchange_mtu(uint16_t central_mtu)
{
    uint16_t clamped_central = (central_mtu < 23U) ? 23U : central_mtu;
    s_negotiated_mtu = (clamped_central < BLE_PREFERRED_MTU) ? clamped_central : BLE_PREFERRED_MTU;
    return s_negotiated_mtu;
}

void ble_transport_mock_get_conn_info(ble_mock_conn_info_t *out_info)
{
    if (out_info != NULL) {
        *out_info = s_mock_conn_info;
    }
}

esp_err_t ble_transport_clear_bonds(void)
{
    memset(s_mock_bonds, 0, sizeof(s_mock_bonds));
    s_mock_bond_count = 0;
    if (s_is_connected) {
        ble_transport_mock_disconnect();
    }
    return ESP_OK;
}

esp_err_t ble_transport_mock_read_dis_char(uint16_t char_uuid16, char *out_buf, size_t max_len)
{
    if (out_buf == NULL || max_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    const char *src = NULL;
    if (char_uuid16 == 0x2A24) {
        src = BLE_DIS_MODEL_NUMBER;
    } else if (char_uuid16 == 0x2A26) {
        src = BLE_DIS_FIRMWARE_REVISION;
    } else if (char_uuid16 == 0x2A29) {
        src = BLE_DIS_MANUFACTURER_NAME;
    } else {
        return ESP_ERR_NOT_FOUND;
    }
    snprintf(out_buf, max_len, "%s", src);
    return ESP_OK;
}

esp_err_t ble_transport_mock_read_user_desc(uint16_t fab_char_short_id, char *out_buf, size_t max_len)
{
    if (out_buf == NULL || max_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    const char *src = NULL;
    if (fab_char_short_id == 0xFAB1) {
        src = BLE_DSC_FAB1_USER_DESC;
    } else if (fab_char_short_id == 0xFAB2) {
        src = BLE_DSC_FAB2_USER_DESC;
    } else if (fab_char_short_id == 0xFAB3) {
        src = BLE_DSC_FAB3_USER_DESC;
    } else {
        return ESP_ERR_NOT_FOUND;
    }
    snprintf(out_buf, max_len, "%s", src);
    return ESP_OK;
}

esp_err_t ble_transport_mock_set_cccd(uint16_t fab_char_short_id, uint16_t cccd_val)
{
    if (fab_char_short_id == 0xFAB2) {
        s_mock_fab2_cccd = cccd_val;
        return ESP_OK;
    }
    if (fab_char_short_id == 0xFAB3) {
        s_mock_fab3_cccd = cccd_val;
        return ESP_OK;
    }
    return ESP_ERR_NOT_FOUND;
}

uint16_t ble_transport_mock_get_cccd(uint16_t fab_char_short_id)
{
    if (fab_char_short_id == 0xFAB2) {
        return s_mock_fab2_cccd;
    }
    if (fab_char_short_id == 0xFAB3) {
        return s_mock_fab3_cccd;
    }
    return 0;
}

bool ble_transport_is_telemetry_subscribed(void)
{
    return s_is_connected && ((s_mock_fab2_cccd & 0x0001U) != 0);
}

esp_err_t ble_transport_notify_telemetry(void)
{
    if (!s_is_connected || (s_mock_fab2_cccd & 0x0001U) == 0) {
        return ESP_OK;
    }
    ble_transport_build_telemetry(&s_mock_last_fab2_pkt);
    s_mock_fab2_notify_count++;
    return ESP_OK;
}

esp_err_t ble_transport_notify_button_config(void)
{
    if (!s_is_connected || (s_mock_fab3_cccd & 0x0001U) == 0) {
        return ESP_OK;
    }
    build_fab3_table_bytes(s_mock_last_fab3_table);
    s_mock_fab3_notify_count++;
    return ESP_OK;
}

uint32_t ble_transport_mock_get_fab2_notify_count(void)
{
    return s_mock_fab2_notify_count;
}

const telemetry_packet_t *ble_transport_mock_get_last_fab2_notify(void)
{
    return &s_mock_last_fab2_pkt;
}

uint32_t ble_transport_mock_get_fab3_notify_count(void)
{
    return s_mock_fab3_notify_count;
}

const uint8_t *ble_transport_mock_get_last_fab3_notify(void)
{
    return s_mock_last_fab3_table;
}

bool ble_transport_mock_pop_command(command_t *out_cmd)
{
    if (s_mock_cmd_count == 0) {
        return false;
    }
    if (out_cmd != NULL) {
        *out_cmd = s_mock_cmd_fifo[s_mock_cmd_head];
    }
    s_mock_cmd_head = (s_mock_cmd_head + 1U) % COMMAND_QUEUE_LENGTH;
    s_mock_cmd_count--;
    return true;
}

size_t ble_transport_mock_get_queued_command_count(void)
{
    return s_mock_cmd_count;
}

#endif /* ESP_PLATFORM */
