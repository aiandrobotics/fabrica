#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "buttons.h"
#include "motion.h"
#include "state_machine.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_BUTTONS";
static QueueHandle_t s_cmd_queue = NULL;
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
static bool s_bond_reset_chord_active = false;
static bool s_bond_reset_triggered = false;
static bool s_factory_reset_chord_active = false;
static bool s_factory_reset_triggered = false;

/**
 * @brief Reset internal debounce filter timers and gesture state for all buttons.
 */
void buttons_reset_all(void)
{
    s_bond_reset_chord_active = false;
    s_bond_reset_triggered = false;
    s_factory_reset_chord_active = false;
    s_factory_reset_triggered = false;
    for (int i = 0; i < BTN_ID_COUNT; i++) {
        s_buttons[i].gpio_num = s_btn_gpios[i];
        s_buttons[i].current_stable_state = 1; /* Default released (Active Low) */
        s_buttons[i].last_raw_level = 1;
        s_buttons[i].debounce_timer_ms = 0;
        s_buttons[i].press_duration_ms = 0;
        s_buttons[i].long_press_triggered = false;
    }
}

/**
 * @brief Get the debounced stable logic level for a button channel.
 *
 * @param btn_idx Button channel index (0 to 3 for B1..B4).
 * @return 0 if pressed (active-low), 1 if released, 1 if invalid index.
 */
int buttons_get_stable_state(uint8_t btn_idx)
{
    if (btn_idx >= BTN_ID_COUNT) {
        return 1;
    }
    return s_buttons[btn_idx].current_stable_state;
}

/**
 * @brief Feed a raw GPIO reading into the debounce filter and gesture detector.
 *
 * Applies a low-pass filter window (50ms debounce). Once stable:
 *   - Short tap is triggered on release if pressed for < 500ms.
 *   - Long press is triggered immediately once held for >= 3000ms.
 *
 * @param btn_idx Button index (0 to 3).
 * @param raw_level Current instantaneous GPIO logic level (0 = pressed, 1 = released).
 * @param elapsed_ms Milliseconds elapsed since last sample.
 * @return Detected button_gesture_t (GESTURE_NONE, GESTURE_SHORT_TAP, or GESTURE_LONG_PRESS).
 */
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

    /* 2. Continuous hold duration tracking & B1+B4 5s bond-reset / B1+B3+B4 10s factory-reset chord detection */
    if (btn->current_stable_state == 0) {
        btn->press_duration_ms += elapsed_ms;

        bool b1_b3_b4_held = (s_buttons[BTN_ID_1].current_stable_state == 0) &&
                             (s_buttons[BTN_ID_3].current_stable_state == 0) &&
                             (s_buttons[BTN_ID_4].current_stable_state == 0);

        bool b1_b4_held = (s_buttons[BTN_ID_1].current_stable_state == 0) &&
                          (s_buttons[BTN_ID_4].current_stable_state == 0);

        if (b1_b3_b4_held && (btn_idx == BTN_ID_1 || btn_idx == BTN_ID_3 || btn_idx == BTN_ID_4)) {
            /* 3-button Factory Reset chord (B1+B3+B4 10s): suppress 3s pairing gesture and 5s bond reset */
            s_factory_reset_chord_active = true;
            s_buttons[BTN_ID_1].long_press_triggered = true;
            s_buttons[BTN_ID_3].long_press_triggered = true;
            s_buttons[BTN_ID_4].long_press_triggered = true;

            if (!s_factory_reset_triggered &&
                s_buttons[BTN_ID_1].press_duration_ms >= BUTTON_FACTORY_RESET_MS &&
                s_buttons[BTN_ID_3].press_duration_ms >= BUTTON_FACTORY_RESET_MS &&
                s_buttons[BTN_ID_4].press_duration_ms >= BUTTON_FACTORY_RESET_MS) {
                s_factory_reset_triggered = true;
                detected_gesture = GESTURE_FACTORY_RESET;
            }
        } else if (b1_b4_held && !s_factory_reset_chord_active && (s_buttons[BTN_ID_3].current_stable_state == 1) && (btn_idx == BTN_ID_1 || btn_idx == BTN_ID_4)) {
            /* 2-button Bond Reset chord (B1+B4 5s): suppress single-button 3s pairing gesture */
            s_bond_reset_chord_active = true;
            s_buttons[BTN_ID_1].long_press_triggered = true;
            s_buttons[BTN_ID_4].long_press_triggered = true;

            if (!s_bond_reset_triggered &&
                s_buttons[BTN_ID_1].press_duration_ms >= BUTTON_BOND_RESET_MS &&
                s_buttons[BTN_ID_4].press_duration_ms >= BUTTON_BOND_RESET_MS) {
                s_bond_reset_triggered = true;
                detected_gesture = GESTURE_BOND_RESET;
            }
        } else if (!btn->long_press_triggered && (btn->press_duration_ms >= BUTTON_LONG_PRESS_MS)) {
            /* Single-button Long press trigger condition: >= 3000ms */
            btn->long_press_triggered = true;
            detected_gesture = GESTURE_LONG_PRESS;
        }
    }

    if (s_factory_reset_chord_active &&
        s_buttons[BTN_ID_1].current_stable_state == 1 &&
        s_buttons[BTN_ID_3].current_stable_state == 1 &&
        s_buttons[BTN_ID_4].current_stable_state == 1) {
        s_factory_reset_chord_active = false;
        s_factory_reset_triggered = false;
    }

    if (s_bond_reset_chord_active &&
        s_buttons[BTN_ID_1].current_stable_state == 1 &&
        s_buttons[BTN_ID_4].current_stable_state == 1) {
        s_bond_reset_chord_active = false;
        s_bond_reset_triggered = false;
    }

    return detected_gesture;
}

/**
 * @brief Map a button gesture and active system state to a concrete system command.
 *
 * Routing Rules:
 *   - Any short tap during STATE_RUNNING_MOTION -> CMD_EMERGENCY_STOP.
 *   - Short tap in STATE_IDLE_RUN -> CMD_RUN_PRESET (Preset 1..4).
 *   - Long press (>=3s) in STATE_IDLE_RUN -> CMD_ENTER_BLE_PAIRING (120s BLE discovery window).
 *   - B1+B4 chord hold (>=5s) in STATE_IDLE_RUN -> CMD_CLEAR_BLE_BONDS.
 *   - B1+B3+B4 chord hold (>=10s) in STATE_IDLE_RUN -> CMD_FACTORY_RESET_ALL.
 *
 * @param btn_idx Button index (0 to 3).
 * @param gesture Detected gesture (GESTURE_SHORT_TAP, GESTURE_LONG_PRESS, GESTURE_BOND_RESET, GESTURE_FACTORY_RESET).
 * @param current_state Current system_state_t.
 * @return Constructed command_t structure ready for queue dispatch.
 */
command_t buttons_translate_gesture(uint8_t btn_idx, button_gesture_t gesture, system_state_t current_state)
{
    command_t cmd;
    memset(&cmd, 0, sizeof(cmd));
    cmd.source = SOURCE_PHYSICAL_BUTTON;

    if (btn_idx >= BTN_ID_COUNT) {
        return cmd;
    }

    if (gesture == GESTURE_SHORT_TAP) {
        if (current_state == STATE_RUNNING_MOTION || motion_is_busy()) {
            cmd.type = CMD_EMERGENCY_STOP;
        } else if (current_state == STATE_ESTOP || current_state == STATE_CALIBRATING) {
            cmd.type = CMD_STOP_SEQUENCE;
        } else if (current_state == STATE_IDLE_RUN) {
            cmd.type = CMD_RUN_PRESET;
            cmd.payload.preset_id = btn_idx + 1; /* Preset 1..4 */
        }
    } else if (gesture == GESTURE_LONG_PRESS) {
        if (current_state == STATE_IDLE_RUN ||
            current_state == STATE_ESTOP ||
            current_state == STATE_CALIBRATING) {
            cmd.type = CMD_ENTER_BLE_PAIRING;
        }
    } else if (gesture == GESTURE_BOND_RESET) {
        if (current_state == STATE_IDLE_RUN ||
            current_state == STATE_ESTOP ||
            current_state == STATE_CALIBRATING) {
            cmd.type = CMD_CLEAR_BLE_BONDS;
        }
    } else if (gesture == GESTURE_FACTORY_RESET) {
        if (current_state == STATE_IDLE_RUN ||
            current_state == STATE_ESTOP ||
            current_state == STATE_CALIBRATING) {
            cmd.type = CMD_FACTORY_RESET_ALL;
        }
    }

    return cmd;
}

#ifdef ESP_PLATFORM
/**
 * @brief Bind the FreeRTOS command queue handle for event dispatching.
 *
 * @param queue Handle to the system command queue.
 */
void buttons_set_command_queue(QueueHandle_t queue)
{
    s_cmd_queue = queue;
}

/**
 * @brief Translate gesture into a command and push to FreeRTOS command queue.
 *
 * If motion is currently active, immediately triggers motion_emergency_stop()
 * without waiting for queue processing to ensure sub-millisecond safety latency.
 *
 * @param btn_idx Button index (0 to 3).
 * @param gesture Detected gesture.
 */
static void dispatch_button_command(uint8_t btn_idx, button_gesture_t gesture)
{
    if (s_cmd_queue == NULL) {
        ESP_LOGW(TAG, "Command queue not initialized, discarding button event.");
        return;
    }

    system_state_t cur_state = state_machine_get_state();
    command_t cmd = buttons_translate_gesture(btn_idx, gesture, cur_state);

    if (gesture == GESTURE_SHORT_TAP) {
        if (cur_state == STATE_RUNNING_MOTION || motion_is_busy()) {
            ESP_LOGW(TAG, "[BUTTON B%d] Pressed while motion is active -> Triggered EMERGENCY STOP!", btn_idx + 1);
            motion_emergency_stop();
        } else if (cur_state == STATE_ESTOP || cur_state == STATE_CALIBRATING) {
            ESP_LOGI(TAG, "[BUTTON B%d] Short Tap in state %d -> Dispatched CMD_STOP_SEQUENCE (Clear/Home)",
                     btn_idx + 1, cur_state);
        } else if (cur_state == STATE_IDLE_RUN) {
            ESP_LOGI(TAG, "[BUTTON B%d] Short Tap detected -> Dispatched CMD_RUN_PRESET (Preset %d)",
                     btn_idx + 1, cmd.payload.preset_id);
        } else {
            return;
        }
    } else if (gesture == GESTURE_LONG_PRESS) {
        if (cur_state == STATE_IDLE_RUN || cur_state == STATE_ESTOP || cur_state == STATE_CALIBRATING) {
            ESP_LOGI(TAG, "[BUTTON B%d] Long Press (>=3s) detected -> Dispatched CMD_ENTER_BLE_PAIRING (120s window)",
                     btn_idx + 1);
        } else {
            return;
        }
    } else if (gesture == GESTURE_BOND_RESET) {
        if (cur_state == STATE_IDLE_RUN || cur_state == STATE_ESTOP || cur_state == STATE_CALIBRATING) {
            ESP_LOGW(TAG, "[BUTTON B1+B4] Simultaneous 5s Hold detected -> Dispatched CMD_CLEAR_BLE_BONDS");
        } else {
            return;
        }
    } else {
        return;
    }

    if (xQueueSend(s_cmd_queue, &cmd, 0) != pdTRUE) {
        ESP_LOGE(TAG, "Command queue full! Dropped command type %d from Button B%d", cmd.type, btn_idx + 1);
    }
}

/**
 * @brief Sample all 4 button GPIOs, step debounce filters, and dispatch gestures.
 *
 * @param elapsed_ms Milliseconds elapsed since previous tick (typically 10ms).
 */
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
 * @brief Dedicated FreeRTOS task running on Core 1 for button scanning and state timer.
 *
 * Executes periodically on a 10ms tick, sampling GPIOs with 50ms low-pass debounce,
 * and stepping the BLE pairing window timeout.
 *
 * @param pvParameters Unused task parameters pointer.
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
        state_machine_tick(10);
    }
}

/**
 * @brief Initialize the 4-button hardware subsystem and spawn Core 1 UI task.
 *
 * Configures GPIO 4, 16, 17, 5 with internal pull-up resistors and creates app_ui_task.
 *
 * @return ESP_OK on success, or an ESP-IDF error code on failure.
 */
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
/**
 * @brief Process button ticks (stub for host testing).
 *
 * @param elapsed_ms Milliseconds elapsed.
 */
void buttons_process_tick(uint32_t elapsed_ms)
{
    (void)elapsed_ms;
}

/**
 * @brief Initialize button subsystem for off-target simulation/unit testing.
 *
 * @return ESP_OK on success.
 */
esp_err_t buttons_init(void)
{
    buttons_reset_all();
    return ESP_OK;
}
#endif
