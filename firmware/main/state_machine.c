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
#include "ble_transport.h"
#include "remote_cmd.h"
#include "state_machine.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_SM";
static QueueHandle_t s_sm_cmd_queue = NULL;
#endif

/* ========================================================================= */
/* Internal State Machine Data                                               */
/* ========================================================================= */

static volatile system_state_t s_system_state = STATE_IDLE_RUN;
static volatile uint8_t s_active_preset_id = 0;
static bool s_ble_pairing_active = false;
static uint32_t s_ble_pairing_timer_ms = 0;

static uint32_t s_calib_inactivity_ms = 0;
static volatile bool s_calib_thermal_sleep = false;
static bool s_calib_thermal_dispatched = false;
static bool s_calib_autohome_dispatched = false;

/* ========================================================================= */
/* Internal Calibration & Recovery Helpers                                   */
/* ========================================================================= */

static void reset_calibration_tracking(void)
{
    s_calib_inactivity_ms = 0;
    s_calib_thermal_dispatched = false;
    s_calib_autohome_dispatched = false;
}

static void exit_calibration_and_home(void)
{
    if (s_calib_thermal_sleep) {
        (void)pca9685_sleep(false);
        s_calib_thermal_sleep = false;
    }
    reset_calibration_tracking();
    (void)pca9685_home_all();
}

/* ========================================================================= */
/* Public API Implementation                                                 */
/* ========================================================================= */

void state_machine_set_command_queue(QueueHandle_t queue)
{
#ifdef ESP_PLATFORM
    s_sm_cmd_queue = queue;
#else
    (void)queue;
#endif
}

/**
 * @brief Reset the state machine to STATE_IDLE_RUN and clear BLE pairing & calibration timers.
 */
void state_machine_reset(void)
{
    s_system_state = STATE_IDLE_RUN;
    s_active_preset_id = 0;
    s_ble_pairing_active = false;
    s_ble_pairing_timer_ms = 0;
    s_calib_thermal_sleep = false;
    reset_calibration_tracking();
}

/**
 * @brief Get the current system operating state.
 *
 * @return Active system_state_t (0..4).
 */
system_state_t state_machine_get_state(void)
{
    return s_system_state;
}

/**
 * @brief Query the currently executing button preset ID (1 to 4), or 0 when idle / running raw sequence.
 *
 * @return Active preset ID (1..4) or 0.
 */
uint8_t state_machine_get_active_preset(void)
{
    return s_active_preset_id;
}

/**
 * @brief Query whether the 120-second BLE pairing/discovery window is active.
 *
 * @return true if pairing window is open for new mobile devices, false otherwise.
 */
bool state_machine_is_ble_pairing(void)
{
    return s_ble_pairing_active;
}

/**
 * @brief Close the active 120-second BLE pairing window and restore base IDLE LED state.
 */
void state_machine_close_ble_pairing(void)
{
    if (s_ble_pairing_active) {
        s_ble_pairing_active = false;
        s_ble_pairing_timer_ms = 0;
        if (led_get_base_state() == LED_STATE_BLE_PAIRING) {
            led_set_state(LED_STATE_IDLE);
        }
    }
}

/**
 * @brief Query whether stationary servos are currently de-energized by the 10s thermal cutoff.
 */
bool state_machine_is_calibrating_thermal_sleep(void)
{
    return s_calib_thermal_sleep;
}

/**
 * @brief Handle BLE link loss: immediately wake/home servos and exit STATE_CALIBRATING.
 */
void state_machine_on_ble_disconnect(void)
{
    if (s_system_state != STATE_CALIBRATING) {
        return;
    }

#ifdef ESP_PLATFORM
    if (s_sm_cmd_queue != NULL) {
        command_t stop_cmd;
        memset(&stop_cmd, 0, sizeof(stop_cmd));
        stop_cmd.type = CMD_STOP_SEQUENCE;
        stop_cmd.source = SOURCE_INTERNAL_TIMER;
        if (xQueueSend(s_sm_cmd_queue, &stop_cmd, 0) == pdTRUE) {
            return;
        }
    }
#endif

    exit_calibration_and_home();
    s_system_state = STATE_IDLE_RUN;
    led_set_state(s_ble_pairing_active ? LED_STATE_BLE_PAIRING : LED_STATE_IDLE);
    remote_cmd_set_last_status(CMD_STATUS_OK, true);
}

/**
 * @brief Initialize the System State Machine.
 *
 * @return ESP_OK on success.
 */
esp_err_t state_machine_init(void)
{
#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Initializing System State Machine...");
#endif
    state_machine_reset();

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "System State Machine initialized in STATE_IDLE_RUN.");
#endif
    return ESP_OK;
}

/**
 * @brief Periodic timer tick managing the 120s BLE pairing window and 10s/15s calibration watchdogs.
 *
 * @param elapsed_ms Milliseconds elapsed since last tick (typically 10ms).
 */
void state_machine_tick(uint32_t elapsed_ms)
{
    if (s_ble_pairing_active) {
        s_ble_pairing_timer_ms += elapsed_ms;
        if (s_ble_pairing_timer_ms >= BLE_PAIRING_TIMEOUT_MS) {
#ifdef ESP_PLATFORM
            ESP_LOGI(TAG, "BLE pairing window (%d ms) expired. Returning to IDLE.",
                     BLE_PAIRING_TIMEOUT_MS);
#endif
            s_ble_pairing_active = false;
            s_ble_pairing_timer_ms = 0;
            led_set_state(LED_STATE_IDLE);
        }
    }

    if (s_system_state == STATE_CALIBRATING) {
        s_calib_inactivity_ms += elapsed_ms;

        /* 15-second inactivity watchdog: wake PCA9685, home all 16 servos, exit to STATE_IDLE_RUN */
        if (s_calib_inactivity_ms >= CALIBRATION_INACTIVITY_TIMEOUT_MS) {
            if (!s_calib_autohome_dispatched) {
                s_calib_autohome_dispatched = true;
#ifdef ESP_PLATFORM
                ESP_LOGI(TAG, "Calibration inactivity timeout (%d ms) reached. Auto-homing all servos.",
                         CALIBRATION_INACTIVITY_TIMEOUT_MS);
                if (s_sm_cmd_queue != NULL) {
                    command_t stop_cmd;
                    memset(&stop_cmd, 0, sizeof(stop_cmd));
                    stop_cmd.type = CMD_STOP_SEQUENCE;
                    stop_cmd.source = SOURCE_INTERNAL_TIMER;
                    if (xQueueSend(s_sm_cmd_queue, &stop_cmd, 0) == pdTRUE) {
                        return;
                    }
                }
#endif
                exit_calibration_and_home();
                s_system_state = STATE_IDLE_RUN;
                led_set_state(s_ble_pairing_active ? LED_STATE_BLE_PAIRING : LED_STATE_IDLE);
                remote_cmd_set_last_status(CMD_STATUS_OK, true);
            }
            return;
        }

        /* 10-second thermal safety cutoff: put PCA9685 oscillator to sleep to prevent coil heating */
        if (s_calib_inactivity_ms >= CALIBRATION_THERMAL_TIMEOUT_MS && !s_calib_thermal_dispatched) {
            s_calib_thermal_dispatched = true;
#ifdef ESP_PLATFORM
            ESP_LOGI(TAG, "Calibration thermal cutoff (%d ms): putting PCA9685 into low-power sleep.",
                     CALIBRATION_THERMAL_TIMEOUT_MS);
            if (s_sm_cmd_queue != NULL) {
                command_t sleep_cmd;
                memset(&sleep_cmd, 0, sizeof(sleep_cmd));
                sleep_cmd.type = CMD_CALIBRATION_THERMAL_SLEEP;
                sleep_cmd.source = SOURCE_INTERNAL_TIMER;
                if (xQueueSend(s_sm_cmd_queue, &sleep_cmd, 0) == pdTRUE) {
                    return;
                }
            }
#endif
            s_calib_thermal_sleep = true;
            (void)pca9685_sleep(true);
        }
    }
}

/**
 * @brief Process and dispatch an incoming command according to current system state.
 *
 * @param cmd Pointer to incoming command_t.
 * @return ESP_OK on success, or an ESP-IDF error code on rejection.
 */
esp_err_t state_machine_process_command(const command_t *cmd)
{
    if (cmd == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    /* 1. Global Emergency Stop & Clean Stop Sequence overrides */
    if (cmd->type == CMD_EMERGENCY_STOP) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Handling CMD_EMERGENCY_STOP in state %d -> Latching STATE_ESTOP", s_system_state);
#endif
        s_active_preset_id = 0;
        s_ble_pairing_active = false;
        s_ble_pairing_timer_ms = 0;
        if (s_calib_thermal_sleep) {
            (void)pca9685_sleep(false);
            s_calib_thermal_sleep = false;
        }
        reset_calibration_tracking();
        motion_emergency_stop();
        pca9685_home_all();
        s_system_state = STATE_ESTOP;
        remote_cmd_set_last_status(CMD_STATUS_OK, true);
        return ESP_OK;
    }

    if (cmd->type == CMD_STOP_SEQUENCE) {
#ifdef ESP_PLATFORM
        ESP_LOGI(TAG, "Handling CMD_STOP_SEQUENCE in state %d -> Returning to STATE_IDLE_RUN", s_system_state);
#endif
        s_active_preset_id = 0;
        if (s_system_state == STATE_RUNNING_MOTION || motion_is_busy()) {
            motion_emergency_stop();
        }
        motion_reset_state();
        exit_calibration_and_home();
        s_system_state = STATE_IDLE_RUN;
        led_set_state(s_ble_pairing_active ? LED_STATE_BLE_PAIRING : LED_STATE_IDLE);
        remote_cmd_set_last_status(CMD_STATUS_OK, true);
        return ESP_OK;
    }

    if (cmd->type == CMD_CALIBRATION_THERMAL_SLEEP) {
        if (s_system_state == STATE_CALIBRATING &&
            s_calib_inactivity_ms >= CALIBRATION_THERMAL_TIMEOUT_MS &&
            !s_calib_thermal_sleep) {
            s_calib_thermal_sleep = true;
            (void)pca9685_sleep(true);
        }
        return ESP_OK;
    }

    if (cmd->type == CMD_IDENTIFY_ROBOT) {
#ifdef ESP_PLATFORM
        ESP_LOGI(TAG, "Triggering 3.0s robot visual locator pulse (LED_STATE_IDENTIFY)...");
#endif
        led_set_state(LED_STATE_IDENTIFY);
        remote_cmd_set_last_status(CMD_STATUS_OK, true);
        return ESP_OK;
    }

    if (cmd->type == CMD_GET_TELEMETRY) {
        remote_cmd_set_last_status(CMD_STATUS_OK, false);
        return ble_transport_notify_telemetry();
    }

    if (cmd->type == CMD_SET_TELEMETRY_STREAM) {
        ble_transport_set_telemetry_stream(cmd->payload.stream_enable);
        remote_cmd_set_last_status(CMD_STATUS_OK, true);
        return ESP_OK;
    }

    if (cmd->type == CMD_SYNC_PRESETS) {
        esp_err_t sync_err = ble_transport_notify_button_config();
        remote_cmd_set_last_status(CMD_STATUS_OK, true);
        return sync_err;
    }

    /* 2. Priority Physical Button Hold Gestures (3s Pairing & 5s Bond Reset) when not moving */
    if (s_system_state != STATE_RUNNING_MOTION && !motion_is_busy()) {
        if (cmd->type == CMD_ENTER_BLE_PAIRING) {
#ifdef ESP_PLATFORM
            ESP_LOGI(TAG, "Entering 120-second BLE Pairing Mode (preempting active BLE link & advertising)...");
#endif
            if (s_system_state == STATE_CALIBRATING) {
                exit_calibration_and_home();
                s_system_state = STATE_IDLE_RUN;
            } else if (s_system_state == STATE_ESTOP) {
                motion_reset_state();
                pca9685_home_all();
                s_system_state = STATE_IDLE_RUN;
            }
            s_ble_pairing_active = true;
            s_ble_pairing_timer_ms = 0;
            led_set_state(LED_STATE_BLE_PAIRING);
            (void)ble_transport_enter_pairing_mode();
            return ESP_OK;
        }

        if (cmd->type == CMD_CLEAR_BLE_BONDS) {
#ifdef ESP_PLATFORM
            ESP_LOGW(TAG, "Hardware bond reset triggered (B1+B4 5s hold). Clearing all BLE bonds...");
#endif
            if (s_system_state == STATE_CALIBRATING) {
                exit_calibration_and_home();
                s_system_state = STATE_IDLE_RUN;
            }
            state_machine_close_ble_pairing();
            esp_err_t err = ble_transport_clear_bonds();
            led_set_state(LED_STATE_INPUT_ERROR);
            return err;
        }
    }

    /* 3. State-dependent command dispatch */
    switch (s_system_state) {
        case STATE_IDLE_RUN:
        case STATE_CALIBRATING: {
            switch (cmd->type) {
                case CMD_RUN_PRESET: {
                    uint8_t preset_id = cmd->payload.preset_id;
                    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
#ifdef ESP_PLATFORM
                        ESP_LOGE(TAG, "Invalid preset ID: %d", preset_id);
#endif
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                        return ESP_ERR_INVALID_ARG;
                    }

                    fold_routine_t routine;
                    memset(&routine, 0, sizeof(routine));
                    esp_err_t load_err = storage_load_routine(preset_id, &routine);
                    if (load_err != ESP_OK && load_err != ESP_ERR_INVALID_CRC) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                        return load_err;
                    }
                    if (routine.step_count == 0) {
#ifdef ESP_PLATFORM
                        ESP_LOGW(TAG, "Preset %d has 0 steps; rejecting execution.", preset_id);
#endif
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                        return ESP_ERR_INVALID_STATE;
                    }

                    if (s_system_state == STATE_CALIBRATING) {
                        exit_calibration_and_home();
                    }

#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Starting Preset %d execution (%d steps)", preset_id, routine.step_count);
#endif
                    s_ble_pairing_active = false;
                    s_ble_pairing_timer_ms = 0;
                    s_active_preset_id = preset_id;
                    s_system_state = STATE_RUNNING_MOTION;
                    remote_cmd_set_last_status(CMD_STATUS_OK, true);

                    esp_err_t err = motion_trigger_preset(preset_id);
                    if (err == ESP_OK) {
                        remote_cmd_notify_completion(routine.step_count);
                        s_active_preset_id = 0;
                        s_system_state = STATE_IDLE_RUN;
                    } else if (err == ESP_ERR_TIMEOUT || motion_get_status() == MOTION_STATUS_ABORTED) {
                        s_active_preset_id = 0;
                        s_system_state = STATE_ESTOP;
                        remote_cmd_set_last_status(CMD_STATUS_OK, true);
                    } else {
                        s_active_preset_id = 0;
                        s_system_state = STATE_IDLE_RUN;
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                    }
                    return err;
                }

                case CMD_RUN_RAW_SEQUENCE: {
                    uint8_t step_cnt = cmd->payload.raw_routine.step_count;
                    if (step_cnt == 0) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                        return ESP_ERR_INVALID_STATE;
                    }
                    if (step_cnt > MAX_STEPS_PER_ROUTINE) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_ROUTINE_FULL, true);
                        return ESP_ERR_INVALID_ARG;
                    }

                    if (s_system_state == STATE_CALIBRATING) {
                        exit_calibration_and_home();
                    }

#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Executing raw sequence (%d steps)", step_cnt);
#endif
                    s_ble_pairing_active = false;
                    s_ble_pairing_timer_ms = 0;
                    s_active_preset_id = 0;
                    s_system_state = STATE_RUNNING_MOTION;
                    remote_cmd_set_last_status(CMD_STATUS_OK, true);

                    esp_err_t err = motion_execute_routine(&cmd->payload.raw_routine);
                    if (err == ESP_OK) {
                        remote_cmd_notify_completion(step_cnt);
                        s_system_state = STATE_IDLE_RUN;
                    } else if (err == ESP_ERR_TIMEOUT || motion_get_status() == MOTION_STATUS_ABORTED) {
                        s_system_state = STATE_ESTOP;
                        remote_cmd_set_last_status(CMD_STATUS_OK, true);
                    } else {
                        s_system_state = STATE_IDLE_RUN;
                        remote_cmd_set_last_status(CMD_STATUS_ERR_MOTOR_BOUNDS, true);
                    }
                    return err;
                }

                case CMD_SET_BUTTON_SEQUENCE: {
                    uint8_t preset_id = cmd->payload.button_sync.preset_id;
                    const fold_routine_t *routine = &cmd->payload.button_sync.routine;
                    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                        return ESP_ERR_INVALID_ARG;
                    }
                    if (routine->step_count == 0) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_STEP, true);
                        return ESP_ERR_INVALID_ARG;
                    }
                    if (routine->step_count > MAX_STEPS_PER_ROUTINE) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_ROUTINE_FULL, true);
                        return ESP_ERR_INVALID_ARG;
                    }
                    esp_err_t err = storage_save_routine(preset_id, routine);
                    if (err == ESP_OK) {
                        led_set_state(LED_STATE_SAVE_SUCCESS);
                        (void)ble_transport_notify_button_config();
                        remote_cmd_set_last_status(CMD_STATUS_OK, true);
                    } else {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                    }
                    return err;
                }

                case CMD_RESTORE_FACTORY_PRESETS: {
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Restoring all button presets to factory defaults...");
#endif
                    if (s_system_state == STATE_CALIBRATING) {
                        exit_calibration_and_home();
                        s_system_state = STATE_IDLE_RUN;
                    }
                    esp_err_t err = storage_init_factory_defaults();
                    pca9685_home_all();
                    if (err == ESP_OK) {
                        led_set_state(LED_STATE_SAVE_SUCCESS);
                        (void)ble_transport_notify_button_config();
                        remote_cmd_set_last_status(CMD_STATUS_OK, true);
                    } else {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                    }
                    return err;
                }

                case CMD_JOG_MOTOR_ANGLE: {
                    uint8_t channel = cmd->payload.jog_param.channel;
                    float angle_deg = cmd->payload.jog_param.angle_deg;
                    if (channel >= TOTAL_SERVO_CHANNELS ||
                        angle_deg < HOME_ANGLE_DEG ||
                        angle_deg > FOLD_ANGLE_DEG) {
                        led_set_state(LED_STATE_INPUT_ERROR);
                        remote_cmd_set_last_status(CMD_STATUS_ERR_MOTOR_BOUNDS, true);
                        return ESP_ERR_INVALID_ARG;
                    }

                    reset_calibration_tracking();
                    if (s_calib_thermal_sleep) {
#ifdef ESP_PLATFORM
                        ESP_LOGI(TAG, "Waking PCA9685 from thermal sleep for servo jog (ch=%u, angle=%.1f)",
                                 channel, angle_deg);
#endif
                        (void)pca9685_sleep(false);
                        s_calib_thermal_sleep = false;
                    }

                    esp_err_t err = pca9685_set_servo_angle(channel, angle_deg);
                    if (err == ESP_OK) {
                        s_system_state = STATE_CALIBRATING;
                        remote_cmd_set_last_status(CMD_STATUS_OK, true);
                    } else {
                        remote_cmd_set_last_status(CMD_STATUS_ERR_MOTOR_BOUNDS, true);
                    }
                    return err;
                }

                default:
#ifdef ESP_PLATFORM
                    ESP_LOGW(TAG, "Command %d rejected in state %d", cmd->type, s_system_state);
#endif
                    remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
                    return ESP_ERR_INVALID_STATE;
            }
        }

        case STATE_RUNNING_MOTION:
        case STATE_ESTOP: {
#ifdef ESP_PLATFORM
            ESP_LOGW(TAG, "Command %d rejected in state %d (busy or E-Stop latched)",
                     cmd->type, s_system_state);
#endif
            remote_cmd_set_last_status(CMD_STATUS_ERR_BUSY, true);
            return ESP_ERR_INVALID_STATE;
        }

        default:
            s_system_state = STATE_IDLE_RUN;
            remote_cmd_set_last_status(CMD_STATUS_ERR_INVALID_ARG, true);
            return ESP_ERR_INVALID_STATE;
    }
}
