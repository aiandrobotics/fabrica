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
    STATE_IDLE_RUN = 0,         /**< Daily Run Mode (Awaiting preset trigger or mobile command) */
    STATE_RUNNING_MOTION = 1    /**< Motion execution active (Core 0 busy) */
} system_state_t;

/* ========================================================================= */
/* State Machine Public API                                                  */
/* ========================================================================= */

/**
 * @brief Initialize State Machine engine.
 * @return ESP_OK on success.
 */
esp_err_t state_machine_init(void);

/**
 * @brief Query current operating state.
 * @return Current system_state_t.
 */
system_state_t state_machine_get_state(void);

/**
 * @brief Query the currently executing button preset ID (1 to 4), or 0 when idle / running raw sequence.
 * @return Active preset ID (1..4) or 0.
 */
uint8_t state_machine_get_active_preset(void);

/**
 * @brief Query whether the 120-second BLE pairing/discovery window is active.
 * @return true if pairing window is open for new mobile devices, false otherwise.
 */
bool state_machine_is_ble_pairing(void);

/**
 * @brief Close the active 120-second BLE pairing window upon successful SMP bonding or bond reset.
 */
void state_machine_close_ble_pairing(void);

/**
 * @brief Process incoming command through the state machine.
 * @param cmd Pointer to command_t structure.
 * @return ESP_OK on success, or error code.
 */
esp_err_t state_machine_process_command(const command_t *cmd);

/**
 * @brief Periodic timer tick hook.
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
