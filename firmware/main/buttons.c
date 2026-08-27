#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "buttons.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_BUTTONS";
static QueueHandle_t s_cmd_queue = NULL;
extern QueueHandle_t xCommandQueue;
#endif

/* GPIO mapping corresponding to Button 1..4 */
static const uint8_t s_btn_gpios[BTN_ID_COUNT] = {
    BTN1_GPIO, /* GPIO 4 */
    BTN2_GPIO, /* GPIO 16 */
    BTN3_GPIO, /* GPIO 17 */
    BTN4_GPIO  /* GPIO 5 */
};

/* Button debouncing and hold state array */
static button_state_t s_buttons[BTN_ID_COUNT];

void buttons_reset_all(void)
{
    for (int i = 0; i < BTN_ID_COUNT; i++) {
        s_buttons[i].gpio_num = s_btn_gpios[i];
        s_buttons[i].current_stable_state = 1; /* Default released (Active Low) */
        s_buttons[i].last_raw_level = 1;
        s_buttons[i].debounce_timer_ms = 0;
        s_buttons[i].press_duration_ms = 0;
        s_buttons[i].long_press_triggered = false;
    }
}

int buttons_get_stable_state(uint8_t btn_idx)
{
    if (btn_idx >= BTN_ID_COUNT) {
        return 1;
    }
    return s_buttons[btn_idx].current_stable_state;
}

button_gesture_t buttons_update_channel(uint8_t btn_idx, int raw_level, uint32_t elapsed_ms)
{
    if (btn_idx >= BTN_ID_COUNT) {
        return GESTURE_NONE;
    }

    button_state_t *btn = &s_buttons[btn_idx];
    button_gesture_t detected_gesture = GESTURE_NONE;

    btn->last_raw_level = raw_level;

    /* 1. Low-pass debounce filtering (50ms window) */
    if (raw_level != btn->current_stable_state) {
        btn->debounce_timer_ms += elapsed_ms;

        if (btn->debounce_timer_ms >= BUTTON_DEBOUNCE_MS) {
            /* State transition confirmed! */
            btn->current_stable_state = raw_level;
            btn->debounce_timer_ms = 0;

            if (btn->current_stable_state == 0) {
                /* Button transitioned from RELEASED -> PRESSED */
                btn->press_duration_ms = 0;
                btn->long_press_triggered = false;
            } else {
                /* Button transitioned from PRESSED -> RELEASED */
                if (!btn->long_press_triggered && (btn->press_duration_ms < BUTTON_SHORT_PRESS_MAX_MS)) {
                    detected_gesture = GESTURE_SHORT_TAP;
                }
                btn->press_duration_ms = 0;
                btn->long_press_triggered = false;
            }
        }
    } else {
        /* Raw reading matches stable state; reset debounce filter timer */
        btn->debounce_timer_ms = 0;
    }

    /* 2. Continuous hold duration tracking */
    if (btn->current_stable_state == 0) {
        btn->press_duration_ms += elapsed_ms;

        /* Long press trigger condition: >= 3000ms */
        if (!btn->long_press_triggered && (btn->press_duration_ms >= BUTTON_LONG_PRESS_MS)) {
            btn->long_press_triggered = true;
            detected_gesture = GESTURE_LONG_PRESS;
        }
    }

    return detected_gesture;
}

#ifdef ESP_PLATFORM
void buttons_set_command_queue(QueueHandle_t queue)
{
    s_cmd_queue = queue;
}

static void dispatch_button_command(uint8_t btn_idx, button_gesture_t gesture)
{
    QueueHandle_t target_q = (s_cmd_queue != NULL) ? s_cmd_queue : xCommandQueue;
    if (target_q == NULL) {
        ESP_LOGW(TAG, "Command queue not initialized, discarding button event.");
        return;
    }

    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.source = SOURCE_PHYSICAL_BUTTON;
    cmd.payload.preset_id = btn_idx + 1; /* Preset 1..4 */

    if (gesture == GESTURE_SHORT_TAP) {
        cmd.type = CMD_RUN_PRESET;
        ESP_LOGI(TAG, "[BUTTON B%d] Short Tap detected -> Dispatched CMD_RUN_PRESET (Preset %d)",
                 btn_idx + 1, cmd.payload.preset_id);
    } else if (gesture == GESTURE_LONG_PRESS) {
        cmd.type = CMD_ENTER_PROGRAM_MODE;
        ESP_LOGI(TAG, "[BUTTON B%d] Long Press (>=3s) detected -> Dispatched CMD_ENTER_PROGRAM_MODE (Preset %d)",
                 btn_idx + 1, cmd.payload.preset_id);
    } else {
        return;
    }

    if (xQueueSend(target_q, &cmd, 0) != pdTRUE) {
        ESP_LOGE(TAG, "Command queue full! Dropped command type %d from Button B%d", cmd.type, btn_idx + 1);
    }
}

void buttons_process_tick(uint32_t elapsed_ms)
{
    for (uint8_t i = 0; i < BTN_ID_COUNT; i++) {
        int raw_level = gpio_get_level(s_btn_gpios[i]);
        button_gesture_t gesture = buttons_update_channel(i, raw_level, elapsed_ms);
        if (gesture != GESTURE_NONE) {
            dispatch_button_command(i, gesture);
        }
    }
}

/**
 * @brief Dedicated FreeRTOS task running on Core 1 for button scanning.
 */
static void app_ui_task(void *pvParameters)
{
    (void)pvParameters;
    const TickType_t xFrequency = pdMS_TO_TICKS(10); /* 10ms sampling tick */
    TickType_t xLastWakeTime = xTaskGetTickCount();

    ESP_LOGI(TAG, "UI Button scanner task started on Core %d (10ms tick, 50ms debounce)",
             xPortGetCoreID());

    while (1) {
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
        buttons_process_tick(10);
    }
}

esp_err_t buttons_init(void)
{
    ESP_LOGI(TAG, "Initializing 4-Button Subsystem: B1=GPIO%d, B2=GPIO%d, B3=GPIO%d, B4=GPIO%d...",
             BTN1_GPIO, BTN2_GPIO, BTN3_GPIO, BTN4_GPIO);

    buttons_reset_all();

    /* Configure GPIO input pins with internal pull-up */
    uint64_t pin_mask = 0;
    for (int i = 0; i < BTN_ID_COUNT; i++) {
        pin_mask |= (1ULL << s_btn_gpios[i]);
    }

    gpio_config_t io_conf = {
        .pin_bit_mask = pin_mask,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    esp_err_t err = gpio_config(&io_conf);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure Button GPIOs: %s", esp_err_to_name(err));
        return err;
    }

    /* Spawn app_ui_task pinned to Core 1 */
    BaseType_t ret = xTaskCreatePinnedToCore(
        app_ui_task,
        "app_ui_task",
        3072,
        NULL,
        5,                     /* Priority 5 */
        NULL,
        1                      /* Pinned to Core 1 */
    );

    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create app_ui_task on Core 1!");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "4-Button scanner initialized successfully on Core 1.");
    return ESP_OK;
}
#else
void buttons_process_tick(uint32_t elapsed_ms)
{
    (void)elapsed_ms;
}

esp_err_t buttons_init(void)
{
    buttons_reset_all();
    return ESP_OK;
}
#endif
