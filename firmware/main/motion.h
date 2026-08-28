#pragma once
#ifndef FABRICA_MOTION_H
#define FABRICA_MOTION_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "pca9685.h"
#include "storage.h"

#ifdef ESP_PLATFORM
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#else
/* Standard types for host test harness */
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
/* Motion Engine Constants & Event Bits                                      */
/* ========================================================================= */

#define MOTION_TASK_STACK_SIZE          4096
#define MOTION_TASK_PRIORITY            10
#define MOTION_ABORT_CHECK_MS           10

#define MOTION_EVENT_START_BIT          (1U << 0)
#define MOTION_EVENT_ESTOP_BIT          (1U << 1)
#define MOTION_EVENT_COMPLETE_BIT       (1U << 2)

/* ========================================================================= */
/* Motion Engine Status States                                               */
/* ========================================================================= */

typedef enum {
    MOTION_STATUS_IDLE = 0,     /**< Motion engine is idle awaiting trigger */
    MOTION_STATUS_RUNNING = 1,  /**< Routine / step motion is actively executing */
    MOTION_STATUS_STOPPING = 2, /**< Motion engine is terminating active motion */
    MOTION_STATUS_ABORTED = 3   /**< Routine was preempted by E-Stop */
} motion_status_t;

/* ========================================================================= */
/* Motion Engine Public API                                                  */
/* ========================================================================= */

/**
 * @brief Initialize Motion Engine, bind IPC primitives, and spawn app_motion_task on Core 0.
 * @param cmd_queue FreeRTOS command queue handle.
 * @param evt_group FreeRTOS system event group handle.
 * @return ESP_OK on success, or ESP error code.
 */
esp_err_t motion_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group);

/**
 * @brief Query current motion engine status.
 * @return Current motion_status_t.
 */
motion_status_t motion_get_status(void);

/**
 * @brief Check if motion is actively running or executing steps.
 * @return true if status is MOTION_STATUS_RUNNING or MOTION_STATUS_STOPPING, false otherwise.
 */
bool motion_is_busy(void);

/**
 * @brief Execute a single folding step (single or parallel dual-motor sweep).
 *        Sweeps target motor(s) 0° -> 180°, dwells for FOLD_DWELL_TIME_MS (300ms),
 *        and returns to 0°. Checks for E-Stop abort every 10ms.
 * @param step Pointer to fold_step_t structure.
 * @return ESP_OK on clean completion, ESP_ERR_TIMEOUT if aborted by E-Stop, or ESP_ERR_INVALID_ARG.
 */
esp_err_t motion_execute_step(const fold_step_t *step);

/**
 * @brief Execute a complete multi-step folding routine sequentially (Step 1 to N).
 *        Sets LED_STATE_RUNNING during motion, pauses for INTER_STEP_DELAY_MS (200ms)
 *        between steps, and restores LED_STATE_IDLE and homes all channels on completion.
 * @param routine Pointer to fold_routine_t structure.
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if empty, ESP_ERR_TIMEOUT if aborted, or ESP error code.
 */
esp_err_t motion_execute_routine(const fold_routine_t *routine);

/**
 * @brief Load preset routine from NVS and trigger execution in Daily Run Mode.
 *        Guards against empty presets (0 steps) by flashing LED_STATE_INPUT_ERROR without moving servos.
 * @param preset_id Preset index (1 to 4).
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if preset empty, or ESP error code.
 */
esp_err_t motion_trigger_preset(uint8_t preset_id);

/**
 * @brief Trigger an immediate Emergency Stop (E-Stop).
 *        Signals abort flag, halts active PWM commands, commands all 16 channels to 0° (flat),
 *        sets LED_STATE_ESTOP (5 rapid flashes), and transitions motion status to MOTION_STATUS_ABORTED.
 * @return ESP_OK on success.
 */
esp_err_t motion_emergency_stop(void);

/**
 * @brief Reset internal motion engine state (useful for host testing and reset sequences).
 */
void motion_reset_state(void);

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_MOTION_H */
