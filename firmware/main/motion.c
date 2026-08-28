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

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_MOTION";
static TaskHandle_t s_motion_task_handle = NULL;
#endif

/* ========================================================================= */
/* Motion Engine Internal State                                              */
/* ========================================================================= */

static volatile motion_status_t s_motion_status = MOTION_STATUS_IDLE;
static volatile bool s_abort_requested = false;

static QueueHandle_t s_cmd_queue_handle = NULL;
static EventGroupHandle_t s_evt_group_handle = NULL;

/* Host testing simulated time tracking */
#ifndef ESP_PLATFORM
static uint32_t s_simulated_elapsed_ms = 0;
#endif

/* ========================================================================= */
/* Internal Helper Functions                                                 */
/* ========================================================================= */

/**
 * @brief Check if an emergency abort has been signaled.
 */
static inline bool is_abort_signaled(void)
{
    if (s_abort_requested) {
        return true;
    }
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        EventBits_t bits = xEventGroupGetBits(s_evt_group_handle);
        if (bits & MOTION_EVENT_ESTOP_BIT) {
            s_abort_requested = true;
            return true;
        }
    }
#endif
    return false;
}

/**
 * @brief Delay for a given duration with low-latency abort polling (10ms slices).
 * @param duration_ms Delay time in milliseconds.
 * @param poll_abort If true, poll abort flag every 10ms.
 * @return true if aborted during delay, false if completed full duration.
 */
static bool motion_delay_ms(uint32_t duration_ms, bool poll_abort)
{
    uint32_t remaining_ms = duration_ms;

    while (remaining_ms > 0) {
        if (poll_abort && is_abort_signaled()) {
            return true;
        }

        uint32_t slice_ms = (remaining_ms >= MOTION_ABORT_CHECK_MS) ?
                            MOTION_ABORT_CHECK_MS : remaining_ms;

#ifdef ESP_PLATFORM
        vTaskDelay(pdMS_TO_TICKS(slice_ms));
#else
        s_simulated_elapsed_ms += slice_ms;
#endif
        remaining_ms -= slice_ms;
    }

    if (poll_abort && is_abort_signaled()) {
        return true;
    }

    return false;
}

/* ========================================================================= */
/* Public Lifecycle and Status APIs                                          */
/* ========================================================================= */

void motion_reset_state(void)
{
    s_motion_status = MOTION_STATUS_IDLE;
    s_abort_requested = false;
#ifndef ESP_PLATFORM
    s_simulated_elapsed_ms = 0;
#endif
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupClearBits(s_evt_group_handle,
                             MOTION_EVENT_START_BIT | MOTION_EVENT_ESTOP_BIT | MOTION_EVENT_COMPLETE_BIT);
    }
#endif
}

motion_status_t motion_get_status(void)
{
    return s_motion_status;
}

bool motion_is_busy(void)
{
    return (s_motion_status == MOTION_STATUS_RUNNING ||
            s_motion_status == MOTION_STATUS_STOPPING);
}

/* ========================================================================= */
/* Step & Routine Articulation Engines                                       */
/* ========================================================================= */

esp_err_t motion_execute_step(const fold_step_t *step)
{
    if (step == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (step->motor_count < 1 || step->motor_count > MAX_MOTORS_PER_STEP) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Invalid motor count: %d (Max: %d)", step->motor_count, MAX_MOTORS_PER_STEP);
#endif
        return ESP_ERR_INVALID_ARG;
    }

    for (uint8_t i = 0; i < step->motor_count; i++) {
        if (step->motor_ids[i] >= TOTAL_SERVO_CHANNELS) {
#ifdef ESP_PLATFORM
            ESP_LOGE(TAG, "Invalid servo channel ID: %d (Max: %d)", step->motor_ids[i], TOTAL_SERVO_CHANNELS - 1);
#endif
            return ESP_ERR_INVALID_ARG;
        }
    }

    if (is_abort_signaled()) {
        return ESP_ERR_TIMEOUT;
    }

    /* 1. Forward Sweep (0° -> 180°) */
    if (step->motor_count == 1) {
        uint8_t ch = step->motor_ids[0];
#ifdef ESP_PLATFORM
        ESP_LOGI(TAG, "Executing single step on Channel %d (0 -> 180 deg)", ch);
#endif
        pca9685_set_servo_angle(ch, FOLD_ANGLE_DEG);
    } else {
        uint16_t mask = (1U << step->motor_ids[0]) | (1U << step->motor_ids[1]);
#ifdef ESP_PLATFORM
        ESP_LOGI(TAG, "Executing parallel step on Channels %d & %d (Mask: 0x%04X, 0 -> 180 deg)",
                 step->motor_ids[0], step->motor_ids[1], mask);
#endif
        pca9685_set_multi_servo_angles(mask, FOLD_ANGLE_DEG);
    }

    /* 2. Fold Dwell Time (300ms) with low-latency abort polling */
    if (motion_delay_ms(FOLD_DWELL_TIME_MS, true)) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "E-Stop triggered during fold dwell! Aborting step.");
#endif
        pca9685_home_all();
        s_motion_status = MOTION_STATUS_ABORTED;
        return ESP_ERR_TIMEOUT;
    }

    /* 3. Return Sweep (180° -> 0°) */
    if (step->motor_count == 1) {
        pca9685_set_servo_angle(step->motor_ids[0], HOME_ANGLE_DEG);
    } else {
        uint16_t mask = (1U << step->motor_ids[0]) | (1U << step->motor_ids[1]);
        pca9685_set_multi_servo_angles(mask, HOME_ANGLE_DEG);
    }

    return ESP_OK;
}

esp_err_t motion_execute_routine(const fold_routine_t *routine)
{
    if (routine == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (routine->step_count == 0) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Refusing execution: routine contains 0 steps.");
#endif
        led_set_state(LED_STATE_INPUT_ERROR);
        return ESP_ERR_INVALID_STATE;
    }

    if (routine->step_count > MAX_STEPS_PER_ROUTINE) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Routine step count %d exceeds MAX_STEPS_PER_ROUTINE (%d)",
                 routine->step_count, MAX_STEPS_PER_ROUTINE);
#endif
        return ESP_ERR_INVALID_ARG;
    }

    if (motion_is_busy()) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Motion engine is busy, rejecting new routine execution.");
#endif
        return ESP_ERR_INVALID_STATE;
    }

    s_abort_requested = false;
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupClearBits(s_evt_group_handle,
                             MOTION_EVENT_START_BIT | MOTION_EVENT_ESTOP_BIT | MOTION_EVENT_COMPLETE_BIT);
    }
#endif
    s_motion_status = MOTION_STATUS_RUNNING;
    led_set_state(LED_STATE_RUNNING);

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Starting routine execution (%d steps total)...", routine->step_count);
#endif

    for (uint8_t i = 0; i < routine->step_count; i++) {
        if (is_abort_signaled()) {
#ifdef ESP_PLATFORM
            ESP_LOGW(TAG, "E-Stop detected before step %d! Halting routine.", i + 1);
#endif
            pca9685_home_all();
            s_motion_status = MOTION_STATUS_ABORTED;
            led_set_state(LED_STATE_ESTOP);
            return ESP_ERR_TIMEOUT;
        }

#ifdef ESP_PLATFORM
        ESP_LOGI(TAG, "--- Step %d / %d ---", i + 1, routine->step_count);
#endif
        esp_err_t step_err = motion_execute_step(&routine->steps[i]);
        if (step_err != ESP_OK) {
            pca9685_home_all();
            s_motion_status = MOTION_STATUS_ABORTED;
            if (step_err == ESP_ERR_TIMEOUT) {
                led_set_state(LED_STATE_ESTOP);
            } else {
                led_set_state(LED_STATE_INPUT_ERROR);
            }
            return step_err;
        }

        /* Inter-step settling delay (200ms) between consecutive steps */
        if (i < (routine->step_count - 1)) {
            if (motion_delay_ms(INTER_STEP_DELAY_MS, true)) {
#ifdef ESP_PLATFORM
                ESP_LOGW(TAG, "E-Stop triggered during inter-step settling! Aborting routine.");
#endif
                pca9685_home_all();
                s_motion_status = MOTION_STATUS_ABORTED;
                led_set_state(LED_STATE_ESTOP);
                return ESP_ERR_TIMEOUT;
            }
        }
    }

    /* Clean completion */
    pca9685_home_all();
    s_motion_status = MOTION_STATUS_IDLE;
    led_set_state(LED_STATE_IDLE);

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Routine execution completed successfully. All channels homed.");
#endif

    return ESP_OK;
}

esp_err_t motion_trigger_preset(uint8_t preset_id)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Invalid preset ID %d (Valid range: 1 to %d)", preset_id, TOTAL_PRESET_COUNT);
#endif
        return ESP_ERR_INVALID_ARG;
    }

    fold_routine_t routine;
    memset(&routine, 0, sizeof(routine));

    esp_err_t load_err = storage_load_routine(preset_id, &routine);
    if (load_err != ESP_OK) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Failed to load Preset %d from storage: %s", preset_id, esp_err_to_name(load_err));
#endif
        led_set_state(LED_STATE_INPUT_ERROR);
        return load_err;
    }

    if (routine.step_count == 0) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Preset %d is empty (0 steps). Flashing error feedback.", preset_id);
#endif
        led_set_state(LED_STATE_INPUT_ERROR);
        return ESP_ERR_INVALID_STATE;
    }

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Triggered Daily Run Mode for Preset %d (%d steps)", preset_id, routine.step_count);
#endif

    return motion_execute_routine(&routine);
}

esp_err_t motion_emergency_stop(void)
{
    s_abort_requested = true;
    s_motion_status = MOTION_STATUS_ABORTED;

#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupSetBits(s_evt_group_handle, MOTION_EVENT_ESTOP_BIT);
    }
    ESP_LOGW(TAG, "EMERGENCY STOP (E-Stop) triggered! Halting PWM & homing all servos.");
#endif

    /* Cut active motion immediately and home all 16 channels */
    pca9685_home_all();

    /* Trigger 5 rapid flashes */
    led_set_state(LED_STATE_ESTOP);

    return ESP_OK;
}

/* ========================================================================= */
/* Core 0 FreeRTOS Task Bootstrap (ESP32 Platform)                           */
/* ========================================================================= */

#ifdef ESP_PLATFORM
static void app_motion_task(void *pvParameters)
{
    (void)pvParameters;
    ESP_LOGI(TAG, "Motion Engine task started on Core %d (Priority %d)",
             xPortGetCoreID(), uxTaskPriorityGet(NULL));

    while (1) {
        /* Monitor E-Stop or wait for task notifications */
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

esp_err_t motion_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group)
{
    ESP_LOGI(TAG, "Initializing Real-Time Motion Engine on Core 0...");

    s_cmd_queue_handle = cmd_queue;
    s_evt_group_handle = evt_group;
    motion_reset_state();

    BaseType_t ret = xTaskCreatePinnedToCore(
        app_motion_task,
        "app_motion_task",
        MOTION_TASK_STACK_SIZE,
        NULL,
        MOTION_TASK_PRIORITY,
        &s_motion_task_handle,
        0   /* Pinned to Core 0 */
    );

    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create app_motion_task on Core 0!");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "Motion Engine initialized successfully on Core 0.");
    return ESP_OK;
}
#else
esp_err_t motion_init(QueueHandle_t cmd_queue, EventGroupHandle_t evt_group)
{
    s_cmd_queue_handle = cmd_queue;
    s_evt_group_handle = evt_group;
    motion_reset_state();
    return ESP_OK;
}
#endif
