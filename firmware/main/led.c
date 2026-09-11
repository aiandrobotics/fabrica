#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "config.h"
#include "led.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
static const char *TAG = "FABRICA_LED";
static TaskHandle_t s_led_task_handle = NULL;
#endif

/* Maximum number of steps in a pattern sequence */
#define MAX_PATTERN_SEGMENTS 12

typedef struct {
    uint8_t level;       /* 1 = ON, 0 = OFF */
    uint16_t duration_ms; /* Duration in milliseconds */
} led_segment_t;

typedef struct {
    uint8_t segment_count;
    bool is_transient;     /* True if pattern completes and returns to base */
    led_state_t return_state; /* Target return state if transient */
    bool return_to_prior_base; /* If true, return to s_base_state */
    led_segment_t segments[MAX_PATTERN_SEGMENTS];
} led_pattern_def_t;

/* Internal State Management */
static led_state_t s_current_state = LED_STATE_IDLE;
static led_state_t s_base_state = LED_STATE_IDLE;
static uint8_t s_current_segment_idx = 0;
static uint32_t s_segment_time_elapsed_ms = 0;

/* Define pattern sequences */
static const led_pattern_def_t s_patterns[] = {
    [LED_STATE_IDLE] = {
        .segment_count = 2,
        .is_transient = false,
        .segments = { {1, 100}, {0, 1900} } /* Soft heartbeat: 10% duty cycle @ 0.5Hz */
    },
    [LED_STATE_RUNNING] = {
        .segment_count = 1,
        .is_transient = false,
        .segments = { {1, 1000} } /* Solid ON continuous */
    },
    [LED_STATE_PROGRAMMING] = {
        .segment_count = 2,
        .is_transient = false,
        .segments = { {1, 1000}, {0, 1000} } /* Slow blink: 1.0s ON / 1.0s OFF */
    },
    [LED_STATE_STEP_LOCKED] = {
        .segment_count = 4,
        .is_transient = true,
        .return_to_prior_base = true,
        .segments = { {1, 80}, {0, 80}, {1, 80}, {0, 80} } /* 2 fast flashes */
    },
    [LED_STATE_SAVE_SUCCESS] = {
        .segment_count = 1,
        .is_transient = true,
        .return_to_prior_base = false,
        .return_state = LED_STATE_IDLE,
        .segments = { {1, 2000} } /* Solid ON for 2.0 seconds */
    },
    [LED_STATE_INPUT_ERROR] = {
        .segment_count = 6,
        .is_transient = true,
        .return_to_prior_base = true,
        .segments = { {1, 60}, {0, 60}, {1, 60}, {0, 60}, {1, 60}, {0, 60} } /* 3 fast flashes */
    },
    [LED_STATE_ESTOP] = {
        .segment_count = 10,
        .is_transient = true,
        .return_to_prior_base = false,
        .return_state = LED_STATE_IDLE,
        .segments = {
            {1, 50}, {0, 50},
            {1, 50}, {0, 50},
            {1, 50}, {0, 50},
            {1, 50}, {0, 50},
            {1, 50}, {0, 50}
        } /* 5 rapid flashes */
    }
};

/**
 * @brief Get the currently active LED visual pattern.
 *
 * If a temporary animation is playing (such as error flashes or step lock confirmation),
 * this returns that transient state.
 *
 * @return Current active led_state_t pattern.
 */
led_state_t led_get_state(void)
{
    return s_current_state;
}

/**
 * @brief Get the underlying persistent/background LED state.
 *
 * When a transient pattern (e.g. 3 error flashes) finishes, the LED automatically
 * reverts back to this base state (e.g. IDLE or PROGRAMMING).
 *
 * @return Base led_state_t operating mode.
 */
led_state_t led_get_base_state(void)
{
    return s_base_state;
}

/**
 * @brief Set the LED pattern state and reset pattern sequencer timers.
 *
 * If the requested state is persistent (e.g. IDLE, RUNNING, PROGRAMMING),
 * it also updates the base state. If running on ESP-IDF hardware, this sends a direct
 * FreeRTOS task notification to wake up app_led_task immediately with zero latency.
 *
 * @param state Target led_state_t pattern.
 */
void led_set_state(led_state_t state)
{
    if (state > LED_STATE_ESTOP) {
        state = LED_STATE_IDLE;
    }

    const led_pattern_def_t *pdef = &s_patterns[state];
    if (!pdef->is_transient) {
        s_base_state = state;
    }

    s_current_state = state;
    s_current_segment_idx = 0;
    s_segment_time_elapsed_ms = 0;

#ifdef ESP_PLATFORM
    if (s_led_task_handle != NULL) {
        /* Wake up LED task immediately to apply new state */
        xTaskNotifyGive(s_led_task_handle);
    }
#endif
}

/**
 * @brief Query the physical logic level of the LED for the active pattern segment.
 *
 * Reads the current segment within the active pattern without advancing time.
 *
 * @return 1 for GPIO HIGH (LED ON), 0 for GPIO LOW (LED OFF).
 */
int led_get_current_level(void)
{
    const led_pattern_def_t *pdef = &s_patterns[s_current_state];
    if (s_current_segment_idx >= pdef->segment_count) {
        return 0;
    }
    return pdef->segments[s_current_segment_idx].level;
}

/**
 * @brief Calculate the remaining time in milliseconds for the current pattern segment.
 *
 * Used by app_led_task to determine the exact duration to sleep before advancing
 * to the next segment, avoiding busy-polling and conserving CPU cycles.
 *
 * @return Remaining duration in milliseconds (0 if segment duration has expired).
 */
uint32_t led_get_segment_delay_ms(void)
{
    const led_pattern_def_t *pdef = &s_patterns[s_current_state];
    if (s_current_segment_idx >= pdef->segment_count) {
        return 100;
    }
    uint32_t total = pdef->segments[s_current_segment_idx].duration_ms;
    if (total > s_segment_time_elapsed_ms) {
        return total - s_segment_time_elapsed_ms;
    }
    return 0;
}

/**
 * @brief Advance the LED pattern sequencer by a given elapsed time.
 *
 * Progresses the animation state machine by elapsed_ms. When a segment's duration
 * completes, it transitions to the next segment. When the entire pattern completes:
 *   - Looping patterns (e.g. IDLE) wrap back to the first segment.
 *   - Transient patterns revert to the base state (or return state).
 *
 * @param elapsed_ms Milliseconds elapsed since the previous step.
 * @return Physical logic level (1 = ON, 0 = OFF) after stepping time.
 */
int led_step_ms(uint32_t elapsed_ms)
{
    const led_pattern_def_t *pdef = &s_patterns[s_current_state];
    s_segment_time_elapsed_ms += elapsed_ms;

    while (s_segment_time_elapsed_ms >= pdef->segments[s_current_segment_idx].duration_ms) {
        s_segment_time_elapsed_ms -= pdef->segments[s_current_segment_idx].duration_ms;
        s_current_segment_idx++;

        if (s_current_segment_idx >= pdef->segment_count) {
            /* Pattern cycle completed */
            if (pdef->is_transient) {
                if (pdef->return_to_prior_base) {
                    s_current_state = s_base_state;
                } else {
                    s_current_state = pdef->return_state;
                    s_base_state = pdef->return_state;
                }
                s_current_segment_idx = 0;
                s_segment_time_elapsed_ms = 0;
                pdef = &s_patterns[s_current_state];
            } else {
                /* Loop continuous base pattern */
                s_current_segment_idx = 0;
            }
        }
    }

    return led_get_current_level();
}

#ifdef ESP_PLATFORM
/**
 * @brief Background FreeRTOS task running on Core 1 to drive physical LED output.
 *
 * Runs an event loop that sets the GPIO pin level, calculates the segment delay,
 * and sleeps until the segment duration expires or an instant wake-up notification
 * is received from led_set_state().
 *
 * @param pvParameters Unused task parameters pointer.
 */
static void app_led_task(void *pvParameters)
{
    (void)pvParameters;
    ESP_LOGI(TAG, "Status LED task started on Core %d", xPortGetCoreID());

    while (1) {
        int level = led_get_current_level();
        gpio_set_level(STATUS_LED_GPIO, level);

        uint32_t delay_ms = led_get_segment_delay_ms();
        if (delay_ms == 0) {
            delay_ms = 10;
        }

        /* Wait for segment duration OR instant wake-up notification from led_set_state() */
        uint32_t notified = ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(delay_ms));
        if (notified > 0) {
            /* State was changed externally; immediately update output */
            continue;
        }

        /* Timeout expired; advance to next segment */
        led_step_ms(delay_ms);
    }
}

/**
 * @brief Initialize the Status LED subsystem and start the background sequencer.
 *
 * Configures the GPIO pin as an output, sets the initial state to LED_STATE_IDLE,
 * and spawns app_led_task pinned to Core 1.
 *
 * @return ESP_OK on success, or an ESP-IDF error code on failure.
 */
esp_err_t led_init(void)
{
    ESP_LOGI(TAG, "Initializing Status LED on GPIO %d...", STATUS_LED_GPIO);

    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << STATUS_LED_GPIO),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };

    esp_err_t err = gpio_config(&io_conf);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure GPIO %d: %s", STATUS_LED_GPIO, esp_err_to_name(err));
        return err;
    }

    gpio_set_level(STATUS_LED_GPIO, 0);
    led_set_state(LED_STATE_IDLE);

    /* Create LED task pinned to Core 1 */
    BaseType_t ret = xTaskCreatePinnedToCore(
        app_led_task,
        "app_led_task",
        2048,
        NULL,
        3,                     /* Priority 3 */
        &s_led_task_handle,
        1                      /* Pinned to Core 1 */
    );

    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create app_led_task on Core 1!");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "Status LED initialized successfully (Initial State: LED_STATE_IDLE)");
    return ESP_OK;
}
#else
/**
 * @brief Initialize Status LED state for off-target simulation/unit testing.
 *
 * @return ESP_OK on success.
 */
esp_err_t led_init(void)
{
    led_set_state(LED_STATE_IDLE);
    return ESP_OK;
}
#endif
