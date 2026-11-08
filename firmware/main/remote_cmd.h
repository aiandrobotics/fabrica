#pragma once
#ifndef FABRICA_REMOTE_CMD_H
#define FABRICA_REMOTE_CMD_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "command.h"
#include "config.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Reset remote command dispatch state and cached command status.
 */
void remote_cmd_reset(void);

/**
 * @brief Query the execution/validation status of the most recent BLE command.
 *
 * @return Latest cmd_status_t code.
 */
cmd_status_t remote_cmd_get_last_status(void);

/**
 * @brief Update the last command status code and optionally emit an immediate FAB2 telemetry push.
 *
 * @param status Result status code (CMD_STATUS_OK or CMD_STATUS_ERR_*).
 * @param notify_fab2 true to immediately push a 31-byte FAB2 notification if subscribed.
 */
void remote_cmd_set_last_status(cmd_status_t status, bool notify_fab2);

/**
 * @brief Emit a dedicated 100% routine completion telemetry frame over FAB2 before
 *        transitioning the state machine back to STATE_IDLE_RUN.
 *
 * @param total_steps Total number of steps in the completed routine (1 to 16).
 */
void remote_cmd_notify_completion(uint8_t total_steps);

/**
 * @brief Populate active progress fields when building a FAB2 telemetry snapshot.
 *
 * @param out_step_idx Output current step index (0 to 15).
 * @param out_total_steps Output total steps (0 to 16).
 * @param out_progress_pct Output step progress percentage (0 to 100).
 */
void remote_cmd_get_progress_snapshot(uint8_t *out_step_idx,
                                      uint8_t *out_total_steps,
                                      uint8_t *out_progress_pct);

/**
 * @brief Validate, zero-pad, and compute/verify IEEE 802.3 CRC32 for a full (53B)
 *        or compact variable-length ([step_count][3B * step_count]) routine payload.
 *
 * @param buf Raw routine bytes starting at step_count.
 * @param buf_len Length of buf in bytes.
 * @param is_compact true for variable-length compact format, false for fixed 53B struct.
 * @param out_routine Output validated and normalized 53-byte fold_routine_t.
 * @return CMD_STATUS_OK on success, or specific cmd_status_t validation error.
 */
cmd_status_t remote_cmd_validate_routine(const uint8_t *buf,
                                         size_t buf_len,
                                         bool is_compact,
                                         fold_routine_t *out_routine);

/**
 * @brief Parse, validate, guard, and dispatch a GATT write to FAB1 Control Point.
 *
 * Executes Core 1 fast-path preemption on 0x02 (Stop) and 0x03 (E-Stop), enforces
 * busy and latched E-Stop interlocks, validates compact/full sequence payloads and
 * servo jog bounds, and enqueues command_t (SOURCE_BLE) to xCommandQueue.
 *
 * @param data Raw GATT write bytes.
 * @param len Length in bytes.
 * @return CMD_STATUS_OK on acceptance, or specific cmd_status_t rejection code.
 */
cmd_status_t remote_cmd_handle_fab1_write(const uint8_t *data, size_t len);

/**
 * @brief Parse, validate, and commit a GATT write to FAB3 Button Sequence Table.
 *
 * Supports 212B full 4-button table writes, 54B single-button writes, and 5..50B
 * compact single-button writes with active-motion / E-Stop write lock.
 *
 * @param data Raw GATT write bytes.
 * @param len Length in bytes.
 * @return CMD_STATUS_OK on success, or specific cmd_status_t rejection code.
 */
cmd_status_t remote_cmd_handle_fab3_write(const uint8_t *data, size_t len);

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_REMOTE_CMD_H */
