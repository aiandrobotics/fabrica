#pragma once
#ifndef FABRICA_TELEMETRY_H
#define FABRICA_TELEMETRY_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "config.h"
#include "command.h"
#include "state_machine.h"
#include "ble_transport.h"

#ifdef ESP_PLATFORM
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#else
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK 0
#endif
#ifndef ESP_FAIL
#define ESP_FAIL -1
#endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the Adaptive Telemetry Subsystem and launch app_telem_task on Core 1.
 *
 * @return ESP_OK on success, or ESP error code.
 */
esp_err_t telemetry_init(void);

/**
 * @brief Start/enable periodic telemetry streaming.
 */
void telemetry_start(void);

/**
 * @brief Stop/disable periodic telemetry streaming.
 */
void telemetry_stop(void);

/**
 * @brief Enable or disable periodic BLE telemetry streaming.
 *
 * @param enabled true to enable periodic streaming, false to pause.
 */
void telemetry_set_stream_enabled(bool enabled);

/**
 * @brief Check if periodic telemetry streaming is enabled.
 *
 * @return true if streaming is enabled, false if paused.
 */
bool telemetry_is_stream_enabled(void);

/**
 * @brief Calculate the adaptive periodic interval for a given system state.
 *
 * @param state Active system_state_t.
 * @return TELEMETRY_INTERVAL_ACTIVE_MS (100ms) for motion/calibrating,
 *         or TELEMETRY_INTERVAL_IDLE_MS (1000ms) for idle/estop/error.
 */
uint32_t telemetry_get_interval_ms(system_state_t state);

/**
 * @brief Get the current adaptive streaming interval based on active state.
 *
 * @return Active interval in milliseconds.
 */
uint32_t telemetry_get_current_interval_ms(void);

/**
 * @brief Execute a single telemetry tick.
 *        Pushes a FAB2 notification if central is connected, CCCD is subscribed,
 *        and periodic streaming is enabled.
 */
void telemetry_tick(void);

/**
 * @brief Notify the telemetry background task of an external state transition
 *        to immediately adapt interval and wake early from low-rate sleep.
 */
void telemetry_notify_state_change(void);

/**
 * @brief Reset telemetry internal state (useful for host testing).
 */
void telemetry_reset_state(void);

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_TELEMETRY_H */
