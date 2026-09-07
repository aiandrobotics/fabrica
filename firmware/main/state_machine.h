#pragma once
#ifndef FABRICA_STATE_MACHINE_H
#define FABRICA_STATE_MACHINE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "pca9685.h"
#include "storage.h"
#include "motion.h"

#ifdef ESP_PLATFORM
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#else
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK                  0
#endif
#ifndef ESP_FAIL
#define ESP_FAIL                -1
#endif
#ifndef ESP_ERR_NO_MEM
#define ESP_ERR_NO_MEM          0x101
#endif
#ifndef ESP_ERR_INVALID_ARG
#define ESP_ERR_INVALID_ARG     0x102
#endif
#ifndef ESP_ERR_INVALID_STATE
#define ESP_ERR_INVALID_STATE   0x103
#endif
#ifndef ESP_ERR_TIMEOUT
#define ESP_ERR_TIMEOUT         0x107
#endif
#ifndef ESP_ERR_NOT_FOUND
#define ESP_ERR_NOT_FOUND       0x105
#endif
typedef void *QueueHandle_t;
typedef void *EventGroupHandle_t;
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================= */
/* System Operating States                                                   */
/* ========================================================================= */

typedef enum {
    STATE_IDLE_RUN = 0,         /**< Daily Run Mode (Awaiting preset trigger) */
    STATE_RUNNING_MOTION = 1,   /**< Motion execution active (Core 0 busy) */
    STATE_PROGRAMMING = 2       /**< Visual Staging Programming Mode */
} system_state_t;

/* ========================================================================= */
/* Staging Context Structure                                                 */
/* ========================================================================= */

typedef struct {
    uint8_t target_preset_id;                       /**< Preset slot (1 to 4) */
    uint8_t current_channel_idx;                    /**< Current servo cursor (0 to 15) */
    bool cursor_active;                             /**< True if channel cursor is active */
    uint8_t staged_motor_count;                     /**< Number of staged motors (0 to 2) */
    uint8_t staged_motor_ids[MAX_MOTORS_PER_STEP];  /**< Staged servo channels */
    fold_routine_t buffer_routine;                  /**< Temporary sequence buffer */
    uint32_t inactivity_timer_ms;                   /**< Elapsed time without input */
} staging_context_t;

/* ========================================================================= */
/* State Machine Public API                                                  */
/* ========================================================================= */

/**
 * @brief Initialize State Machine engine and bind IPC handles.
 * @param cmd_queue FreeRTOS command queue handle.
 * @param evt_group FreeRTOS system event group handle.
 * @return ESP_OK on success, or ESP error code.
 */
esp_err_t state_machine_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group);

/**
 * @brief Query current operating state.
 * @return Current system_state_t.
 */
system_state_t state_machine_get_state(void);

/**
 * @brief Query current visual staging context.
 * @return Pointer to read-only staging_context_t.
 */
const staging_context_t *state_machine_get_context(void);

/**
 * @brief Process incoming command through the state machine.
 * @param cmd Pointer to command_t structure.
 * @return ESP_OK on success, or error code.
 */
esp_err_t state_machine_process_command(const command_t *cmd);

/**
 * @brief Periodic timer tick to advance timers (e.g. 20s inactivity watchdog).
 * @param elapsed_ms Elapsed milliseconds since previous tick.
 */
void state_machine_tick(uint32_t elapsed_ms);

/**
 * @brief Reset state machine to initial boot state (for host tests and system resets).
 */
void state_machine_reset(void);

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_STATE_MACHINE_H */
