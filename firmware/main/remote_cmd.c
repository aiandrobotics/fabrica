#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "storage.h"
#include "motion.h"
#include "state_machine.h"
#include "ble_transport.h"
#include "remote_cmd.h"

/* ========================================================================= */
/* Internal Remote Command Dispatch State                                    */
/* ========================================================================= */

static volatile cmd_status_t s_last_cmd_status = CMD_STATUS_OK;
static volatile bool s_completion_snapshot_active = false;
static volatile uint8_t s_completion_step_idx = 0;
static volatile uint8_t s_completion_total_steps = 0;
static volatile uint8_t s_completion_progress_pct = 0;

/* ========================================================================= */
/* Status & Telemetry Snapshot Helpers                                       */
/* ========================================================================= */

void remote_cmd_reset(void)
{
    s_last_cmd_status = CMD_STATUS_OK;
    s_completion_snapshot_active = false;
    s_completion_step_idx = 0;
    s_completion_total_steps = 0;
    s_completion_progress_pct = 0;
}

cmd_status_t remote_cmd_get_last_status(void)
{
    return s_last_cmd_status;
}

void remote_cmd_set_last_status(cmd_status_t status, bool notify_fab2)
{
    s_last_cmd_status = status;
    if (notify_fab2) {
        (void)ble_transport_notify_telemetry();
    }
}

void remote_cmd_notify_completion(uint8_t total_steps)
{
    s_last_cmd_status = CMD_STATUS_OK;
    s_completion_snapshot_active = true;
    s_completion_total_steps = total_steps;
    s_completion_step_idx = (total_steps > 0) ? (uint8_t)(total_steps - 1U) : 0;
    s_completion_progress_pct = 100U;

    (void)ble_transport_notify_telemetry();

    s_completion_snapshot_active = false;
    s_completion_step_idx = 0;
    s_completion_total_steps = 0;
    s_completion_progress_pct = 0;
}

void remote_cmd_get_progress_snapshot(uint8_t *out_step_idx,
                                      uint8_t *out_total_steps,
                                      uint8_t *out_progress_pct,
                                      uint16_t *out_elapsed_ms)
{
    if (s_completion_snapshot_active) {
        if (out_step_idx != NULL) {
            *out_step_idx = s_completion_step_idx;
        }
        if (out_total_steps != NULL) {
            *out_total_steps = s_completion_total_steps;
        }
        if (out_progress_pct != NULL) {
            *out_progress_pct = s_completion_progress_pct;
        }
        if (out_elapsed_ms != NULL) {
            *out_elapsed_ms = 0;
        }
        return;
    }

    motion_get_progress(out_step_idx, out_total_steps, out_progress_pct, out_elapsed_ms);
}

/* ========================================================================= */
/* Sequence Unpacking, Bounds Validation & CRC32 Normalization               */
/* ========================================================================= */

cmd_status_t remote_cmd_validate_routine(const uint8_t *buf,
                                         size_t buf_len,
                                         bool is_compact,
                                         fold_routine_t *out_routine)
{
    if (buf == NULL || out_routine == NULL || buf_len < 1U) {
        return CMD_STATUS_ERR_INVALID_ARG;
    }

    uint8_t step_count = buf[0];
    if (step_count == 0) {
        return CMD_STATUS_ERR_INVALID_STEP;
    }
    if (step_count > MAX_STEPS_PER_ROUTINE) {
        return CMD_STATUS_ERR_ROUTINE_FULL;
    }

    fold_routine_t candidate;
    memset(&candidate, 0, sizeof(candidate));

    if (is_compact) {
        size_t expected_len = 1U + ((size_t)step_count * sizeof(fold_step_t));
        if (buf_len != expected_len) {
            return CMD_STATUS_ERR_INVALID_ARG;
        }
        candidate.step_count = step_count;
        memcpy(candidate.steps, &buf[1], (size_t)step_count * sizeof(fold_step_t));
        candidate.checksum = 0;
    } else {
        if (buf_len != sizeof(fold_routine_t)) {
            return CMD_STATUS_ERR_INVALID_ARG;
        }
        memcpy(&candidate, buf, sizeof(fold_routine_t));

        /* Verify caller-supplied non-zero IEEE 802.3 CRC32 before normalizing */
        if (candidate.checksum != 0) {
            uint32_t expected_crc = storage_compute_crc32(&candidate);
            if (expected_crc != candidate.checksum) {
                return CMD_STATUS_ERR_CRC_MISMATCH;
            }
        }
    }

    /* Validate motor counts (1..2) and servo channel indices (0..15) across active steps */
    for (uint8_t s = 0; s < step_count; s++) {
        uint8_t m_cnt = candidate.steps[s].motor_count;
        if (m_cnt == 0 || m_cnt > MAX_MOTORS_PER_STEP) {
            return CMD_STATUS_ERR_MOTOR_BOUNDS;
        }
        for (uint8_t m = 0; m < m_cnt; m++) {
            if (candidate.steps[s].motor_ids[m] >= TOTAL_SERVO_CHANNELS) {
                return CMD_STATUS_ERR_MOTOR_BOUNDS;
            }
        }
        if (is_compact || candidate.checksum == 0) {
            for (uint8_t m = m_cnt; m < MAX_MOTORS_PER_STEP; m++) {
                candidate.steps[s].motor_ids[m] = 0;
            }
        }
    }

    /* Zero-pad unused trailing steps and auto-compute CRC32 when checksum == 0 or compact */
    if (is_compact || candidate.checksum == 0) {
        if (step_count < MAX_STEPS_PER_ROUTINE) {
            memset(&candidate.steps[step_count], 0,
                   (size_t)(MAX_STEPS_PER_ROUTINE - step_count) * sizeof(fold_step_t));
        }
        candidate.checksum = storage_compute_crc32(&candidate);
    }

    *out_routine = candidate;
    return CMD_STATUS_OK;
}

/* ========================================================================= */
/* FAB3 GATT Write Handler (212B Table / 54B Slot / 5..50B Compact)          */
/* ========================================================================= */

cmd_status_t remote_cmd_handle_fab3_write(const uint8_t *data, size_t len)
{
    if (data == NULL || len == 0) {
        led_set_state(LED_STATE_INPUT_ERROR);
        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
        return CMD_STATUS_ERR_INVALID_ARG;
    }

    system_state_t sys_state = state_machine_get_state();
    if (motion_is_busy() || sys_state == STATE_RUNNING_MOTION || sys_state == STATE_ESTOP) {
        remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
        return CMD_STATUS_ERR_BUSY;
    }

    if (len == BLE_FAB3_TABLE_SIZE) {
        /* Full 212-byte 4-button table write: validate all 4 slots atomically before saving */
        fold_routine_t validated[TOTAL_PRESET_COUNT];
        for (uint8_t i = 0; i < TOTAL_PRESET_COUNT; i++) {
            cmd_status_t st = remote_cmd_validate_routine(
                &data[(size_t)i * sizeof(fold_routine_t)],
                sizeof(fold_routine_t),
                false,
                &validated[i]);
            if (st != CMD_STATUS_OK) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(st, true);
                return st;
            }
        }
        for (uint8_t i = 0; i < TOTAL_PRESET_COUNT; i++) {
            if (storage_save_routine(i + 1U, &validated[i]) != ESP_OK) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
        }
    } else if (len == sizeof(button_sync_param_t)) {
        /* Single-button 54-byte write: [1B preset_id][53B fold_routine_t] */
        uint8_t preset_id = data[0];
        if (preset_id < 1U || preset_id > TOTAL_PRESET_COUNT) {
            led_set_state(LED_STATE_INPUT_ERROR);
            remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
            return CMD_STATUS_ERR_INVALID_ARG;
        }
        fold_routine_t validated;
        cmd_status_t st = remote_cmd_validate_routine(&data[1], sizeof(fold_routine_t), false, &validated);
        if (st != CMD_STATUS_OK) {
            led_set_state(LED_STATE_INPUT_ERROR);
            remote_cmd_set_last_status(st, true);
            return st;
        }
        if (storage_save_routine(preset_id, &validated) != ESP_OK) {
            led_set_state(LED_STATE_INPUT_ERROR);
            remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
            return CMD_STATUS_ERR_INVALID_ARG;
        }
    } else if (len >= 2U) {
        /* Compact variable-length single-button write: [1B preset_id][1B step_count][3B * step_count] */
        uint8_t preset_id = data[0];
        if (preset_id < 1U || preset_id > TOTAL_PRESET_COUNT) {
            led_set_state(LED_STATE_INPUT_ERROR);
            remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
            return CMD_STATUS_ERR_INVALID_ARG;
        }
        fold_routine_t validated;
        cmd_status_t st = remote_cmd_validate_routine(&data[1], len - 1U, true, &validated);
        if (st != CMD_STATUS_OK) {
            led_set_state(LED_STATE_INPUT_ERROR);
            remote_cmd_set_last_status(st, true);
            return st;
        }
        if (storage_save_routine(preset_id, &validated) != ESP_OK) {
            led_set_state(LED_STATE_INPUT_ERROR);
            remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
            return CMD_STATUS_ERR_INVALID_ARG;
        }
    } else {
        led_set_state(LED_STATE_INPUT_ERROR);
        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
        return CMD_STATUS_ERR_INVALID_ARG;
    }

    led_set_state(LED_STATE_SAVE_SUCCESS);
    (void)ble_transport_notify_button_config();
    remote_cmd_set_last_status(CMD_STATUS_OK, true);
    return CMD_STATUS_OK;
}

/* ========================================================================= */
/* FAB1 Control Point Wire Command Parser & Fast-Path Ingress Guard          */
/* ========================================================================= */

cmd_status_t remote_cmd_handle_fab1_write(const uint8_t *data, size_t len)
{
    if (data == NULL || len == 0) {
        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
        return CMD_STATUS_ERR_INVALID_ARG;
    }

    uint8_t opcode = data[0];
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.source = SOURCE_BLE;

    system_state_t sys_state = state_machine_get_state();
    bool motion_active = motion_is_busy() || (sys_state == STATE_RUNNING_MOTION);
    bool busy_or_estop = motion_active || (sys_state == STATE_ESTOP);

    switch (opcode) {
        case BLE_OP_RUN_PRESET: {
            if (len != 2U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            uint8_t preset_id = data[1];
            if (preset_id < 1U || preset_id > TOTAL_PRESET_COUNT) {
                if (!busy_or_estop) {
                    led_set_state(LED_STATE_INPUT_ERROR);
                }
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            if (busy_or_estop) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
                return CMD_STATUS_ERR_BUSY;
            }
            /* Pre-check stored preset for empty 0-step configuration */
            fold_routine_t stored;
            memset(&stored, 0, sizeof(stored));
            esp_err_t load_err = storage_load_routine(preset_id, &stored);
            if (load_err != ESP_OK && load_err != ESP_ERR_INVALID_CRC) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                return CMD_STATUS_ERR_INVALID_STEP;
            }
            if (stored.step_count == 0) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                return CMD_STATUS_ERR_INVALID_STEP;
            }
            cmd.type = CMD_RUN_PRESET;
            cmd.payload.preset_id = preset_id;
            break;
        }

        case BLE_OP_RUN_RAW_SEQUENCE: {
            if (len < 2U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            if (busy_or_estop) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
                return CMD_STATUS_ERR_BUSY;
            }
            bool is_compact = (len != (1U + sizeof(fold_routine_t)));
            cmd_status_t st = remote_cmd_validate_routine(&data[1], len - 1U, is_compact,
                                                          &cmd.payload.raw_routine);
            if (st != CMD_STATUS_OK) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(st, true);
                return st;
            }
            cmd.type = CMD_RUN_RAW_SEQUENCE;
            break;
        }

        case BLE_OP_STOP_SEQUENCE: {
            if (len != 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            /* Core 1 fast-path stop preemption (<50ms latency) when motion is active */
            if (motion_is_busy()) {
                motion_emergency_stop();
            }
            cmd.type = CMD_STOP_SEQUENCE;
            break;
        }

        case BLE_OP_EMERGENCY_STOP: {
            if (len != 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            /* Core 1 fast-path E-Stop preemption (<50ms latency) */
            motion_emergency_stop();
            cmd.type = CMD_EMERGENCY_STOP;
            break;
        }

        case BLE_OP_SET_BUTTON_SEQUENCE: {
            if (len < 3U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            if (busy_or_estop) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
                return CMD_STATUS_ERR_BUSY;
            }
            uint8_t preset_id = data[1];
            if (preset_id < 1U || preset_id > TOTAL_PRESET_COUNT) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            bool is_compact = (len != (1U + sizeof(button_sync_param_t)));
            cmd_status_t st = remote_cmd_validate_routine(&data[2], len - 2U, is_compact,
                                                          &cmd.payload.button_sync.routine);
            if (st != CMD_STATUS_OK) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(st, true);
                return st;
            }
            cmd.type = CMD_SET_BUTTON_SEQUENCE;
            cmd.payload.button_sync.preset_id = preset_id;
            break;
        }

        case BLE_OP_GET_BUTTON_CONFIG: {
            if (len != 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            cmd.type = CMD_SYNC_PRESETS;
            break;
        }

        case BLE_OP_RESTORE_FACTORY_PRESETS: {
            if (len != 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            if (busy_or_estop) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
                return CMD_STATUS_ERR_BUSY;
            }
            cmd.type = CMD_RESTORE_FACTORY_PRESETS;
            break;
        }

        case BLE_OP_JOG_MOTOR_ANGLE: {
            if (len != 3U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            if (busy_or_estop) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
                return CMD_STATUS_ERR_BUSY;
            }
            uint8_t channel = data[1];
            uint8_t angle_deg = data[2];
            if (channel >= TOTAL_SERVO_CHANNELS || (float)angle_deg > FOLD_ANGLE_DEG) {
                led_set_state(LED_STATE_INPUT_ERROR);
                remote_cmd_set_last_status(CMD_STATUS_ERR_MOTOR_BOUNDS, true);
                return CMD_STATUS_ERR_MOTOR_BOUNDS;
            }
            cmd.type = CMD_JOG_MOTOR_ANGLE;
            cmd.payload.jog_param.channel = channel;
            cmd.payload.jog_param.angle_deg = (float)angle_deg;
            break;
        }

        case BLE_OP_IDENTIFY_ROBOT: {
            if (len != 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            cmd.type = CMD_IDENTIFY_ROBOT;
            break;
        }

        case BLE_OP_GET_TELEMETRY: {
            if (len != 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            cmd.type = CMD_GET_TELEMETRY;
            break;
        }

        case BLE_OP_SET_TELEMETRY_STREAM: {
            if (len != 2U || data[1] > 1U) {
                remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                return CMD_STATUS_ERR_INVALID_ARG;
            }
            cmd.type = CMD_SET_TELEMETRY_STREAM;
            cmd.payload.stream_enable = (data[1] != 0);
            break;
        }

        default:
            remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
            return CMD_STATUS_ERR_INVALID_ARG;
    }

    if (ble_transport_enqueue_command(&cmd) != ESP_OK) {
        remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
        return CMD_STATUS_ERR_BUSY;
    }

    remote_cmd_set_last_status(CMD_STATUS_OK, false);
    return CMD_STATUS_OK;
}
