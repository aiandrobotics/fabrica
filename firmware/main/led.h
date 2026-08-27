#pragma once
#ifndef FABRICA_LED_H
#define FABRICA_LED_H

#include <stdint.h>
#include <stdbool.h>
#ifdef ESP_PLATFORM
#include "esp_err.h"
#else
typedef int esp_err_t;
#define ESP_OK          0
#define ESP_FAIL        -1
#define ESP_ERR_NO_MEM  0x101
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Visual status LED pattern states.
 */
typedef enum {
    LED_STATE_IDLE = 0,     /**< Soft heartbeat (100ms ON / 1900ms OFF) */
    LED_STATE_RUNNING,      /**< Solid ON throughout routine motion */
    LED_STATE_PROGRAMMING,  /**< Slow blink (1000ms ON / 1000ms OFF / 0.5 Hz) */
    LED_STATE_STEP_LOCKED,  /**< 2 fast flashes (80ms ON / 80ms OFF) -> return to base */
    LED_STATE_SAVE_SUCCESS, /**< Solid ON for 2000ms -> return to IDLE */
    LED_STATE_INPUT_ERROR,  /**< 3 fast flashes (60ms ON / 60ms OFF) -> return to base */
    LED_STATE_ESTOP         /**< 5 rapid flashes (50ms ON / 50ms OFF) -> return to IDLE */
} led_state_t;

/**
 * @brief Initialize the Status LED GPIO (GPIO 2) and spawn app_led_task on Core 1.
 * @return ESP_OK on success, or ESP error code.
 */
esp_err_t led_init(void);

/**
 * @brief Update the active LED feedback pattern in a thread-safe manner.
 * @param state Desired led_state_t pattern.
 */
void led_set_state(led_state_t state);

/**
 * @brief Query the currently active LED state.
 * @return Active led_state_t.
 */
led_state_t led_get_state(void);

/**
 * @brief Query the underlying base LED state (for transient pattern returns).
 * @return Base led_state_t.
 */
led_state_t led_get_base_state(void);

/**
 * @brief Internal step sequencer to advance pattern by elapsed milliseconds.
 *        Used by app_led_task and host unit test harness.
 * @param elapsed_ms Milliseconds elapsed since previous step.
 * @return Current physical LED GPIO level (1 = HIGH/ON, 0 = LOW/OFF).
 */
int led_step_ms(uint32_t elapsed_ms);

/**
 * @brief Get the duration in milliseconds remaining for the current pattern segment.
 * @return Segment duration in ms.
 */
uint32_t led_get_segment_delay_ms(void);

/**
 * @brief Query current physical level without stepping time.
 * @return 1 for ON, 0 for OFF.
 */
int led_get_current_level(void);

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_LED_H */
