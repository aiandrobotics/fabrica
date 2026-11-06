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

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_SM";
#endif

/* ========================================================================= */
/* Internal State Machine Data                                               */
/* ========================================================================= */

static volatile system_state_t s_system_state = STATE_IDLE_RUN;
static bool s_ble_pairing_active = false;
static uint32_t s_ble_pairing_timer_ms = 0;

/* ========================================================================= */
/* Public API Implementation                                                 */
/* ========================================================================= */

/**
 * @brief Reset the state machine to STATE_IDLE_RUN and close BLE pairing window.
 */
void state_machine_reset(void)
{
    s_system_state = STATE_IDLE_RUN;
    s_ble_pairing_active = false;
    s_ble_pairing_timer_ms = 0;
}

/**
 * @brief Get the current system operating state.
 *
 * @return Active system_state_t (STATE_IDLE_RUN or STATE_RUNNING_MOTION).
 */
system_state_t state_machine_get_state(void)
{
    return s_system_state;
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
 * @brief Periodic timer tick to manage the 120-second BLE pairing window timeout.
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
}

/**
 * @brief Process and dispatch an incoming command according to current system state.
 *
 * Evaluates state transitions and handles actions:
 *   - CMD_EMERGENCY_STOP: Global preemption, aborts motion, homes servos, reverts to IDLE.
 *   - STATE_IDLE_RUN: Triggers presets, opens 120s BLE pairing window (on 3s button hold),
 *     executes raw sequences, updates button presets from mobile app, restores factory presets,
 *     or jogs servos for calibration.
 *   - STATE_RUNNING_MOTION: Blocks non-emergency commands.
 *
 * @param cmd Pointer to incoming command_t.
 * @return ESP_OK on success, or an ESP-IDF error code on rejection.
 */
esp_err_t state_machine_process_command(const command_t *cmd)
{
    if (cmd == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    /* 1. Global Emergency Stop override */
    if (cmd->type == CMD_EMERGENCY_STOP) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Handling CMD_EMERGENCY_STOP in state %d", s_system_state);
#endif
        s_ble_pairing_active = false;
        s_ble_pairing_timer_ms = 0;
        motion_emergency_stop();
        pca9685_home_all();
        s_system_state = STATE_IDLE_RUN;
        return ESP_OK;
    }

    /* 2. State-dependent command dispatch */
    switch (s_system_state) {
        case STATE_IDLE_RUN: {
            switch (cmd->type) {
                case CMD_RUN_PRESET: {
                    uint8_t preset_id = cmd->payload.preset_id;
                    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
#ifdef ESP_PLATFORM
                        ESP_LOGE(TAG, "Invalid preset ID: %d", preset_id);
#endif
                        return ESP_ERR_INVALID_ARG;
                    }
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Starting Preset %d execution in Daily Run Mode", preset_id);
#endif
                    s_ble_pairing_active = false;
                    s_ble_pairing_timer_ms = 0;
                    s_system_state = STATE_RUNNING_MOTION;
                    esp_err_t err = motion_trigger_preset(preset_id);
                    s_system_state = STATE_IDLE_RUN;
                    return err;
                }

                case CMD_RUN_RAW_SEQUENCE: {
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Executing raw sequence (%d steps)", cmd->payload.raw_routine.step_count);
#endif
                    s_ble_pairing_active = false;
                    s_ble_pairing_timer_ms = 0;
                    s_system_state = STATE_RUNNING_MOTION;
                    esp_err_t err = motion_execute_routine(&cmd->payload.raw_routine);
                    s_system_state = STATE_IDLE_RUN;
                    return err;
                }

                case CMD_ENTER_BLE_PAIRING: {
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Entering 120-second BLE Pairing Mode (LED fast double-blink)...");
#endif
                    s_ble_pairing_active = true;
                    s_ble_pairing_timer_ms = 0;
                    led_set_state(LED_STATE_BLE_PAIRING);
                    return ESP_OK;
                }

                case CMD_SET_BUTTON_SEQUENCE: {
                    uint8_t preset_id = cmd->payload.button_sync.preset_id;
                    const fold_routine_t *routine = &cmd->payload.button_sync.routine;
                    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT ||
                        routine->step_count == 0 || routine->step_count > MAX_STEPS_PER_ROUTINE) {
#ifdef ESP_PLATFORM
                        ESP_LOGE(TAG, "Invalid button sequence parameters (Preset %d, Steps %d)",
                                 preset_id, routine->step_count);
#endif
                        led_set_state(LED_STATE_INPUT_ERROR);
                        return ESP_ERR_INVALID_ARG;
                    }
                    esp_err_t err = storage_save_routine(preset_id, routine);
                    if (err == ESP_OK) {
                        led_set_state(LED_STATE_SAVE_SUCCESS);
                    } else {
                        led_set_state(LED_STATE_INPUT_ERROR);
                    }
                    return err;
                }

                case CMD_RESTORE_FACTORY_PRESETS: {
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Restoring all button presets to factory defaults...");
#endif
                    esp_err_t err = storage_init_factory_defaults();
                    pca9685_home_all();
                    if (err == ESP_OK) {
                        led_set_state(LED_STATE_SAVE_SUCCESS);
                    }
                    return err;
                }

                case CMD_JOG_MOTOR_ANGLE: {
                    return pca9685_set_servo_angle(cmd->payload.jog_param.channel,
                                                   cmd->payload.jog_param.angle_deg);
                }

                default:
#ifdef ESP_PLATFORM
                    ESP_LOGW(TAG, "Command %d rejected in STATE_IDLE_RUN", cmd->type);
#endif
                    return ESP_ERR_INVALID_STATE;
            }
        }

        case STATE_RUNNING_MOTION: {
            /* While motion is running, non-emergency commands are rejected */
#ifdef ESP_PLATFORM
            ESP_LOGW(TAG, "Command %d rejected while motion is running", cmd->type);
#endif
            return ESP_ERR_INVALID_STATE;
        }

        default:
            s_system_state = STATE_IDLE_RUN;
            return ESP_ERR_INVALID_STATE;
    }
}
