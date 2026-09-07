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
static staging_context_t s_context;

static QueueHandle_t s_cmd_queue_handle = NULL;
static EventGroupHandle_t s_evt_group_handle = NULL;

/* ========================================================================= */
/* Helper Functions                                                          */
/* ========================================================================= */

static bool is_channel_staged(uint8_t channel)
{
    for (uint8_t i = 0; i < s_context.staged_motor_count; i++) {
        if (s_context.staged_motor_ids[i] == channel) {
            return true;
        }
    }
    return false;
}

/* ========================================================================= */
/* Public API Implementation                                                 */
/* ========================================================================= */

void state_machine_reset(void)
{
    s_system_state = STATE_IDLE_RUN;
    memset(&s_context, 0, sizeof(s_context));
}

system_state_t state_machine_get_state(void)
{
    return s_system_state;
}

const staging_context_t *state_machine_get_context(void)
{
    return &s_context;
}

esp_err_t state_machine_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group)
{
#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Initializing System State Machine...");
#endif
    s_cmd_queue_handle = cmd_queue;
    s_evt_group_handle = evt_group;
    state_machine_reset();

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "System State Machine initialized in STATE_IDLE_RUN.");
#endif
    return ESP_OK;
}

void state_machine_tick(uint32_t elapsed_ms)
{
    if (s_system_state == STATE_PROGRAMMING) {
        s_context.inactivity_timer_ms += elapsed_ms;

        if (s_context.inactivity_timer_ms >= PROGRAMMING_TIMEOUT_MS) {
#ifdef ESP_PLATFORM
            ESP_LOGW(TAG, "Inactivity timeout (%d ms) in Programming Mode! Discarding buffer & returning to Run Mode.",
                     PROGRAMMING_TIMEOUT_MS);
#endif
            pca9685_home_all();
            memset(&s_context, 0, sizeof(s_context));
            led_set_state(LED_STATE_IDLE);
            s_system_state = STATE_IDLE_RUN;
        }
    }
}

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
        motion_emergency_stop();
        if (s_system_state == STATE_PROGRAMMING) {
            pca9685_home_all();
            memset(&s_context, 0, sizeof(s_context));
        }
        s_system_state = STATE_IDLE_RUN;
        return ESP_OK;
    }

    /* Reset inactivity timer on any command received in Programming Mode */
    if (s_system_state == STATE_PROGRAMMING) {
        s_context.inactivity_timer_ms = 0;
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
                    s_system_state = STATE_RUNNING_MOTION;
                    esp_err_t err = motion_trigger_preset(preset_id);
                    s_system_state = STATE_IDLE_RUN;
                    return err;
                }

                case CMD_RUN_RAW_SEQUENCE: {
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Executing raw sequence (%d steps)", cmd->payload.raw_routine.step_count);
#endif
                    s_system_state = STATE_RUNNING_MOTION;
                    esp_err_t err = motion_execute_routine(&cmd->payload.raw_routine);
                    s_system_state = STATE_IDLE_RUN;
                    return err;
                }

                case CMD_ENTER_PROGRAM_MODE: {
                    uint8_t preset_id = cmd->payload.preset_id;
                    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
#ifdef ESP_PLATFORM
                        ESP_LOGE(TAG, "Invalid preset ID for programming: %d", preset_id);
#endif
                        return ESP_ERR_INVALID_ARG;
                    }
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "Entering Visual Staging Programming Mode for Preset %d", preset_id);
#endif
                    memset(&s_context, 0, sizeof(s_context));
                    s_context.target_preset_id = preset_id;
                    s_context.current_channel_idx = 0;
                    s_context.cursor_active = false;
                    s_context.staged_motor_count = 0;
                    s_context.inactivity_timer_ms = 0;

                    s_system_state = STATE_PROGRAMMING;
                    pca9685_home_all();
                    led_set_state(LED_STATE_PROGRAMMING);
                    return ESP_OK;
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

        case STATE_PROGRAMMING: {
            switch (cmd->type) {
                case CMD_CYCLE_NUDGE_MOTOR: {
                    if (!s_context.cursor_active) {
                        /* First B1 press selects Motor 1 (Channel 0) */
                        s_context.current_channel_idx = 0;
                        s_context.cursor_active = true;
                    } else {
                        /* Subsequent B1 presses advance to next channel (wrap 0-15) */
                        s_context.current_channel_idx = (s_context.current_channel_idx + 1) % TOTAL_SERVO_CHANNELS;
                    }
#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "[B1 CYCLE] Target Motor %d (Channel %d)",
                             s_context.current_channel_idx + 1, s_context.current_channel_idx);
#endif
                    if (!is_channel_staged(s_context.current_channel_idx)) {
                        pca9685_nudge_channel(s_context.current_channel_idx);
                    }
                    return ESP_OK;
                }

                case CMD_STAGE_TOGGLE_MOTOR: {
                    s_context.cursor_active = true;
                    uint8_t ch = s_context.current_channel_idx;
                    int staged_idx = -1;

                    for (uint8_t i = 0; i < s_context.staged_motor_count; i++) {
                        if (s_context.staged_motor_ids[i] == ch) {
                            staged_idx = (int)i;
                            break;
                        }
                    }

                    if (staged_idx >= 0) {
                        /* Unstage motor: return to 0 deg */
#ifdef ESP_PLATFORM
                        ESP_LOGI(TAG, "[B2 UNSTAGE] Motor %d (Channel %d) dropped to 0 deg", ch + 1, ch);
#endif
                        pca9685_set_servo_angle(ch, HOME_ANGLE_DEG);
                        for (uint8_t i = (uint8_t)staged_idx; i < s_context.staged_motor_count - 1; i++) {
                            s_context.staged_motor_ids[i] = s_context.staged_motor_ids[i + 1];
                        }
                        s_context.staged_motor_count--;
                        return ESP_OK;
                    } else {
                        /* Stage motor: lift to 30 deg */
                        if (s_context.staged_motor_count < MAX_MOTORS_PER_STEP) {
                            s_context.staged_motor_ids[s_context.staged_motor_count] = ch;
                            s_context.staged_motor_count++;
#ifdef ESP_PLATFORM
                            ESP_LOGI(TAG, "[B2 STAGE] Motor %d (Channel %d) lifted to 30 deg (Staged Count: %d)",
                                     ch + 1, ch, s_context.staged_motor_count);
#endif
                            pca9685_stage_channel(ch);
                            return ESP_OK;
                        } else {
                            /* 3rd motor attempt rejected */
#ifdef ESP_PLATFORM
                            ESP_LOGW(TAG, "[B2 STAGE REJECTED] Exceeded MAX_MOTORS_PER_STEP (%d)",
                                     MAX_MOTORS_PER_STEP);
#endif
                            led_set_state(LED_STATE_INPUT_ERROR);
                            return ESP_ERR_INVALID_STATE;
                        }
                    }
                }

                case CMD_LOCK_STEP: {
                    if (s_context.staged_motor_count == 0) {
#ifdef ESP_PLATFORM
                        ESP_LOGW(TAG, "[B3 LOCK REJECTED] No motors currently staged!");
#endif
                        return ESP_ERR_INVALID_STATE;
                    }

                    uint8_t step_idx = s_context.buffer_routine.step_count;
                    s_context.buffer_routine.steps[step_idx].motor_count = s_context.staged_motor_count;
                    for (uint8_t i = 0; i < s_context.staged_motor_count; i++) {
                        s_context.buffer_routine.steps[step_idx].motor_ids[i] = s_context.staged_motor_ids[i];
                    }
                    s_context.buffer_routine.step_count++;
                    s_context.staged_motor_count = 0;
                    s_context.cursor_active = false;
                    s_context.current_channel_idx = 0;

#ifdef ESP_PLATFORM
                    ESP_LOGI(TAG, "[B3 LOCK STEP] Locked Step %d (%d motors). All flaps dropped flat to 0 deg.",
                             s_context.buffer_routine.step_count,
                             s_context.buffer_routine.steps[step_idx].motor_count);
#endif
                    pca9685_home_all();
                    led_set_state(LED_STATE_STEP_LOCKED);

                    /* 16-Step Maximum Cap: Auto-commit to NVS */
                    if (s_context.buffer_routine.step_count >= MAX_STEPS_PER_ROUTINE) {
#ifdef ESP_PLATFORM
                        ESP_LOGI(TAG, "Reached MAX_STEPS_PER_ROUTINE (%d). Auto-committing to Preset %d NVS...",
                                 MAX_STEPS_PER_ROUTINE, s_context.target_preset_id);
#endif
                        storage_save_routine(s_context.target_preset_id, &s_context.buffer_routine);
                        pca9685_home_all();
                        led_set_state(LED_STATE_SAVE_SUCCESS);
                        s_system_state = STATE_IDLE_RUN;
                    }

                    return ESP_OK;
                }

                case CMD_SAVE_EXIT_PROGRAM: {
                    if (s_context.buffer_routine.step_count > 0) {
#ifdef ESP_PLATFORM
                        ESP_LOGI(TAG, "[B4 SAVE & EXIT] Committing %d steps to Preset %d NVS...",
                                 s_context.buffer_routine.step_count, s_context.target_preset_id);
#endif
                        storage_save_routine(s_context.target_preset_id, &s_context.buffer_routine);
                        pca9685_home_all();
                        led_set_state(LED_STATE_SAVE_SUCCESS);
                    } else {
#ifdef ESP_PLATFORM
                        ESP_LOGI(TAG, "[B4 EXIT] Empty buffer, returning to Run Mode without writing NVS.");
#endif
                        pca9685_home_all();
                        led_set_state(LED_STATE_IDLE);
                    }
                    s_system_state = STATE_IDLE_RUN;
                    return ESP_OK;
                }

                case CMD_ENTER_PROGRAM_MODE: {
                    /* Redundant long press in programming mode; refresh timer */
                    s_context.inactivity_timer_ms = 0;
                    return ESP_OK;
                }

                default:
#ifdef ESP_PLATFORM
                    ESP_LOGW(TAG, "Command %d unhandled in STATE_PROGRAMMING", cmd->type);
#endif
                    return ESP_ERR_INVALID_STATE;
            }
        }

        default:
            s_system_state = STATE_IDLE_RUN;
            return ESP_ERR_INVALID_STATE;
    }
}
