#pragma once
#ifndef FABRICA_BLE_TRANSPORT_H
#define FABRICA_BLE_TRANSPORT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "command.h"
#include "config.h"

#ifdef ESP_PLATFORM
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#else
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK 0
#endif
#ifndef ESP_FAIL
#define ESP_FAIL -1
#endif
#ifndef ESP_ERR_NO_MEM
#define ESP_ERR_NO_MEM 0x101
#endif
#ifndef ESP_ERR_INVALID_ARG
#define ESP_ERR_INVALID_ARG 0x102
#endif
#ifndef ESP_ERR_INVALID_STATE
#define ESP_ERR_INVALID_STATE 0x103
#endif
#ifndef ESP_ERR_INVALID_SIZE
#define ESP_ERR_INVALID_SIZE 0x104
#endif
#ifndef ESP_ERR_NOT_FOUND
#define ESP_ERR_NOT_FOUND 0x105
#endif
#ifndef ESP_ERR_INVALID_CRC
#define ESP_ERR_INVALID_CRC 0x109
#endif
typedef void *QueueHandle_t;
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================= */
/* BLE GATT Constants, Strings & Wire Opcodes                                */
/* ========================================================================= */

/** Total byte length of the 4-button sequence table on FAB3 (4 x 53 = 212
 * bytes) */
#define BLE_FAB3_TABLE_SIZE (TOTAL_PRESET_COUNT * sizeof(fold_routine_t))

/** Maximum legacy BLE 4.x advertising / scan response packet size */
#define BLE_ADV_MAX_LEN 31

/** Standard Device Information Service (0x180A) static metadata strings */
#define BLE_DIS_MODEL_NUMBER "Fabrica-DevKit-v1"
#define BLE_DIS_FIRMWARE_REVISION "v1.13.0"
#define BLE_DIS_MANUFACTURER_NAME "AIR Robotics"

/** Characteristic User Description (0x2901) human-readable strings */
#define BLE_DSC_FAB1_USER_DESC "Fabrica Control Point (FAB1)"
#define BLE_DSC_FAB2_USER_DESC "Fabrica Status & Telemetry (FAB2)"
#define BLE_DSC_FAB3_USER_DESC "Fabrica Button Sequences 1-4 (FAB3)"

/** FAB1 Control Point Wire Opcodes */
typedef enum {
  BLE_OP_RUN_PRESET = 0x00,       /**< [0x00][preset_id 1..4] */
  BLE_OP_RUN_RAW_SEQUENCE = 0x01, /**< [0x01][53B routine | compact steps] */
  BLE_OP_STOP_SEQUENCE = 0x02,    /**< [0x02] */
  BLE_OP_EMERGENCY_STOP = 0x03,   /**< [0x03] */
  BLE_OP_SET_BUTTON_SEQUENCE =
      0x0A, /**< [0x0A][preset_id][53B routine | compact steps] */
  BLE_OP_GET_BUTTON_CONFIG = 0x0B,       /**< [0x0B] */
  BLE_OP_RESTORE_FACTORY_PRESETS = 0x0C, /**< [0x0C] */
  BLE_OP_JOG_MOTOR_ANGLE = 0x0D,     /**< [0x0D][channel 0..15][angle 0..180] */
  BLE_OP_IDENTIFY_ROBOT = 0x0E,      /**< [0x0E] */
  BLE_OP_GET_TELEMETRY = 0x10,       /**< [0x10] */
  BLE_OP_SET_TELEMETRY_STREAM = 0x11 /**< [0x11][enable 0|1] */
} ble_opcode_t;

/* ========================================================================= */
/* BLE Transport Public API                                                  */
/* ========================================================================= */

/**
 * @brief Initialize and start the Apache NimBLE stack, SMP security store, and
 * GATT server on Core 1.
 *
 * Note: Named ble_transport_start() to avoid colliding with Apache NimBLE's
 * internal HCI transport symbol `void ble_transport_init(void)` in
 * `nimble/transport.h`.
 *
 * @param cmd_queue FreeRTOS command queue handle for dispatching SOURCE_BLE
 * commands.
 * @return ESP_OK on success, or ESP-IDF error code.
 */
esp_err_t ble_transport_start(QueueHandle_t cmd_queue);

/**
 * @brief Format dynamic BLE device name ("Fabrica-XXXX") from a 6-byte
 * Bluetooth MAC address.
 *
 * @param bt_mac 6-byte Bluetooth MAC address.
 * @param out_name Output buffer (at least 16 bytes).
 */
void ble_transport_format_device_name(const uint8_t bt_mac[6],
                                      char out_name[16]);

/**
 * @brief Get the active BLE local device name ("Fabrica-XXXX").
 *
 * @return Null-terminated device name string.
 */
const char *ble_transport_get_device_name(void);

/**
 * @brief Construct the 31-byte-compliant Primary Advertisement and Scan
 * Response payloads.
 *
 * Primary Adv (21 bytes): Flags (0x06, 3B) + Complete 128-bit UUID 0000FAB0-...
 * (18B). Scan Response (17 bytes): Complete Local Name ("Fabrica-XXXX", 14B) +
 * Tx Power (3B).
 *
 * @param device_name Null-terminated device name (typically "Fabrica-XXXX", <=
 * 26 chars).
 * @param tx_pwr_dbm Signed TX power level in dBm.
 * @param adv_out 31-byte buffer for Primary Advertisement payload.
 * @param adv_len Output byte count written to adv_out.
 * @param rsp_out 31-byte buffer for Scan Response payload.
 * @param rsp_len Output byte count written to rsp_out.
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if parameters are invalid or
 * exceed 31 bytes.
 */
esp_err_t ble_transport_build_adv_packets(const char *device_name,
                                          int8_t tx_pwr_dbm,
                                          uint8_t adv_out[BLE_ADV_MAX_LEN],
                                          size_t *adv_len,
                                          uint8_t rsp_out[BLE_ADV_MAX_LEN],
                                          size_t *rsp_len);

/**
 * @brief Query whether a BLE central is currently connected.
 *
 * @return true if connected, false otherwise.
 */
bool ble_transport_is_connected(void);

/**
 * @brief Query the currently negotiated ATT MTU on the active connection.
 *
 * @return Negotiated MTU in bytes (default 23 when disconnected or prior to
 * exchange).
 */
uint16_t ble_transport_get_mtu(void);

/**
 * @brief Query the status of the most recently processed BLE command or GATT
 * write.
 *
 * @return Latest cmd_status_t value.
 */
cmd_status_t ble_transport_get_last_cmd_status(void);

/**
 * @brief Enter BLE pairing mode with priority: disconnect any active central so
 *        GAP advertising restarts immediately for a new mobile device to pair.
 *
 * @return ESP_OK on success.
 */
esp_err_t ble_transport_enter_pairing_mode(void);

/**
 * @brief Erase all stored BLE bonds in NVS, clear RPA resolving entries, and
 * disconnect active central.
 *
 * @return ESP_OK on success.
 */
esp_err_t ble_transport_clear_bonds(void);

/**
 * @brief Query the number of bonded central devices currently persisted in NVS.
 *
 * @return Count of bonded peers (0 to BLE_MAX_BONDS).
 */
int ble_transport_get_bond_count(void);

/**
 * @brief Enable or disable periodic BLE telemetry streaming state flag.
 *
 * @param enable true to enable telemetry notifications, false to disable.
 */
void ble_transport_set_telemetry_stream(bool enable);

/**
 * @brief Query whether periodic BLE telemetry streaming is enabled.
 *
 * @return true if enabled, false otherwise.
 */
bool ble_transport_is_telemetry_stream_enabled(void);

/**
 * @brief Query whether a connected central has subscribed to FAB2 telemetry CCCD.
 *
 * @return true if CCCD notifications are enabled, false otherwise.
 */
bool ble_transport_is_telemetry_subscribed(void);

/**
 * @brief Build a 31-byte packed telemetry_packet_t snapshot of current robot
 * state.
 *
 * @param out_pkt Output pointer to 31-byte telemetry_packet_t.
 */
void ble_transport_build_telemetry(telemetry_packet_t *out_pkt);

/**
 * @brief Push a 31-byte FAB2 telemetry GATT notification if a central is
 * connected and subscribed.
 *
 * @return ESP_OK on success or if no subscriber is active.
 */
esp_err_t ble_transport_notify_telemetry(void);

/**
 * @brief Process a GATT Write to FAB3 (212B full table, 54B single-button,
 * or 5..50B compact).
 *
 * Enforces active-motion write lock (CMD_STATUS_ERR_BUSY), zero-pads unused
 * steps, auto-computes IEEE 802.3 CRC32 when checksum == 0 (or compact format),
 * commits to NVS, triggers LED_STATE_SAVE_SUCCESS, and emits a FAB3
 * notification.
 *
 * @param data Raw GATT write payload bytes.
 * @param len Payload length in bytes.
 * @return CMD_STATUS_OK on success, or specific cmd_status_t error reason.
 */
cmd_status_t ble_transport_write_fab3(const uint8_t *data, size_t len);

/**
 * @brief Push a 212-byte FAB3 button sequence table GATT notification to
 * subscribed central.
 *
 * @return ESP_OK on success or if no subscriber is active.
 */
esp_err_t ble_transport_notify_button_config(void);

/**
 * @brief Process a GATT Write / Write-Without-Response to FAB1 Control Point.
 *
 * Delegates to remote_cmd_handle_fab1_write() to validate wire opcodes (0x00-0x03,
 * 0x0A-0x11), invoke Core 1 fast-path E-Stop for 0x02/0x03, enforce busy and E-Stop
 * guards, and enqueue command_t (SOURCE_BLE) to xCommandQueue.
 *
 * @param data Raw GATT write payload bytes.
 * @param len Payload length in bytes.
 * @return CMD_STATUS_OK on acceptance, or specific cmd_status_t error reason.
 */
cmd_status_t ble_transport_write_fab1(const uint8_t *data, size_t len);

/**
 * @brief Enqueue a validated SOURCE_BLE command into xCommandQueue (or host test FIFO).
 *
 * @param cmd Pointer to populated command_t structure.
 * @return ESP_OK on success, or ESP_ERR_NO_MEM / ESP_ERR_INVALID_STATE.
 */
esp_err_t ble_transport_enqueue_command(const command_t *cmd);

/* ========================================================================= */
/* Host Simulation & Unit Test Inspection Hooks (Non-ESP_PLATFORM Only)      */
/* ========================================================================= */
#ifndef ESP_PLATFORM

typedef struct {
  uint16_t itvl_min_units; /**< Requested min interval in 1.25ms units (12
                              = 15.0ms) */
  uint16_t itvl_max_units; /**< Requested max interval in 1.25ms units (24
                              = 30.0ms) */
  uint16_t latency;        /**< Requested slave latency (0) */
  uint16_t supervision_timeout_10ms; /**< Requested supervision timeout in 10ms
                                        units (400 = 4000ms) */
  bool param_update_requested;       /**< True if peripheral requested
                                        ble_gap_update_params */
  bool peripheral_mtu_initiated;     /**< True if peripheral initiated
                                        ble_gattc_exchange_mtu */
  bool smp_security_initiated;       /**< True if peripheral called
                                        ble_gap_security_initiate */
  bool advertising_active; /**< True if peripheral is currently advertising */
} ble_mock_conn_info_t;

void ble_transport_mock_reset(void);
void ble_transport_mock_set_bt_mac(const uint8_t bt_mac[6]);

/**
 * @brief Simulate a BLE central connection attempt (with optional RPA + IRK).
 *
 * @param ota_addr 6-byte over-the-air address (public, static random, or
 * rotating RPA).
 * @param is_rpa true if ota_addr is a Resolvable Private Address derived from
 * peer_irk.
 * @param peer_id_addr 6-byte static identity address of the central.
 * @param peer_irk 16-byte Identity Resolving Key of the central.
 * @return ESP_OK if connection accepted (and bonded/encrypted),
 * ESP_ERR_INVALID_STATE if terminated.
 */
esp_err_t ble_transport_mock_connect(const uint8_t ota_addr[6], bool is_rpa,
                                     const uint8_t peer_id_addr[6],
                                     const uint8_t peer_irk[16]);

void ble_transport_mock_disconnect(void);
uint16_t ble_transport_mock_exchange_mtu(uint16_t central_mtu);
void ble_transport_mock_get_conn_info(ble_mock_conn_info_t *out_info);
bool ble_transport_mock_is_peer_bonded(const uint8_t peer_id_addr[6]);

esp_err_t ble_transport_mock_read_dis_char(uint16_t char_uuid16, char *out_buf,
                                           size_t max_len);
esp_err_t ble_transport_mock_read_user_desc(uint16_t fab_char_short_id,
                                            char *out_buf, size_t max_len);
esp_err_t ble_transport_mock_set_cccd(uint16_t fab_char_short_id,
                                      uint16_t cccd_val);
uint16_t ble_transport_mock_get_cccd(uint16_t fab_char_short_id);

uint32_t ble_transport_mock_get_fab2_notify_count(void);
const telemetry_packet_t *ble_transport_mock_get_last_fab2_notify(void);
uint32_t ble_transport_mock_get_fab3_notify_count(void);
const uint8_t *ble_transport_mock_get_last_fab3_notify(void);

bool ble_transport_mock_pop_command(command_t *out_cmd);
size_t ble_transport_mock_get_queued_command_count(void);

#endif /* !ESP_PLATFORM */

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_BLE_TRANSPORT_H */
