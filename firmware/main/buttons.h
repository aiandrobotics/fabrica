#pragma once
#ifndef FABRICA_BUTTONS_H
#define FABRICA_BUTTONS_H

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
#include "config.h"
#include "command.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Zero-indexed button identifiers.
 */
typedef enum {
    BTN_ID_1 = 0, /* Button 1: Preset 1 / Cycle & Nudge */
    BTN_ID_2 = 1, /* Button 2: Preset 2 / Stage & Toggle */
    BTN_ID_3 = 2, /* Button 3: Preset 3 / Lock Step */
    BTN_ID_4 = 3, /* Button 4: Preset 4 / Save & Exit */
    BTN_ID_COUNT = 4
} button_id_t;

/**
 * @brief Detected physical button gesture types.
 */
typedef enum {
    GESTURE_NONE = 0,
    GESTURE_SHORT_TAP = 1,   /**< Pressed and released in < 500ms */
    GESTURE_LONG_PRESS = 2   /**< Held continuously for >= 3000ms */
} button_gesture_t;

/**
 * @brief Per-button debouncing and gesture tracking state.
 */
typedef struct {
    uint8_t gpio_num;
    int current_stable_state;    /**< Stable logical state: 0 = Pressed, 1 = Released */
    int last_raw_level;          /**< Most recent raw GPIO reading */
    uint32_t debounce_timer_ms;  /**< Time raw level has differed from stable state */
    uint32_t press_duration_ms;  /**< Accumulated continuous press duration */
    bool long_press_triggered;   /**< Flag to ensure single long press event dispatch */
} button_state_t;

/**
 * @brief Initialize 4-button GPIOs with pull-ups and spawn app_ui_task on Core 1.
 * @return ESP_OK on success, or ESP error code.
 */
esp_err_t buttons_init(void);

/**
 * @brief Process one sampling tick across all 4 buttons.
 * @param elapsed_ms Elapsed milliseconds since previous tick (typically 10ms).
 */
void buttons_process_tick(uint32_t elapsed_ms);

/**
 * @brief Process single button step with simulated raw level (for unit tests).
 * @param btn_idx Button index (0 to 3).
 * @param raw_level Raw GPIO level (0 = Pressed, 1 = Released).
 * @param elapsed_ms Elapsed time in ms.
 * @return Detected gesture, if any on this tick.
 */
button_gesture_t buttons_update_channel(uint8_t btn_idx, int raw_level, uint32_t elapsed_ms);

/**
 * @brief Reset internal debouncing and gesture tracking state across all channels.
 */
void buttons_reset_all(void);

/**
 * @brief Query current stable state of a button.
 * @param btn_idx Button index (0 to 3).
 * @return 0 for Pressed, 1 for Released.
 */
int buttons_get_stable_state(uint8_t btn_idx);

#ifdef ESP_PLATFORM
/**
 * @brief Set the command queue destination for button event dispatch.
 * @param queue FreeRTOS command queue handle.
 */
void buttons_set_command_queue(QueueHandle_t queue);
#endif

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_BUTTONS_H */
