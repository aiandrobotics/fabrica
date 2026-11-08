#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "state_machine.h"
#include "ble_transport.h"
#include "motion.h"
#include "telemetry.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_TELEM";
static TaskHandle_t s_telem_task_handle = NULL;
#endif

/* Default streaming enabled upon CCCD subscription per user decision A2 */
static bool s_streaming_enabled = true;

uint32_t telemetry_get_interval_ms(system_state_t state)
{
    if (state == STATE_RUNNING_MOTION || state == STATE_CALIBRATING) {
        return TELEMETRY_INTERVAL_ACTIVE_MS; /* 100ms (10 Hz) */
    }
    return TELEMETRY_INTERVAL_IDLE_MS; /* 1000ms (1 Hz) */
}

uint32_t telemetry_get_current_interval_ms(void)
{
    return telemetry_get_interval_ms(state_machine_get_state());
}

void telemetry_set_stream_enabled(bool enabled)
{
    s_streaming_enabled = enabled;
    ble_transport_set_telemetry_stream(enabled);
}

bool telemetry_is_stream_enabled(void)
{
    return s_streaming_enabled;
}

void telemetry_start(void)
{
    telemetry_set_stream_enabled(true);
}

void telemetry_stop(void)
{
    telemetry_set_stream_enabled(false);
}

void telemetry_tick(void)
{
    /* Only stream if connected, FAB2 CCCD subscribed, and streaming enabled */
    if (!ble_transport_is_connected() ||
        !ble_transport_is_telemetry_subscribed() ||
        !s_streaming_enabled) {
        return;
    }

    (void)ble_transport_notify_telemetry();
}

void telemetry_notify_state_change(void)
{
#ifdef ESP_PLATFORM
    if (s_telem_task_handle != NULL) {
        xTaskNotifyGive(s_telem_task_handle);
    }
#endif
}

void telemetry_reset_state(void)
{
    s_streaming_enabled = true;
    ble_transport_set_telemetry_stream(true);
}

#ifdef ESP_PLATFORM
static void app_telem_task(void *pvParameters)
{
    (void)pvParameters;
    ESP_LOGI(TAG, "Adaptive Telemetry Task started on Core %d (Priority %d)",
             xPortGetCoreID(), uxTaskPriorityGet(NULL));

    while (1) {
        uint32_t interval_ms = telemetry_get_current_interval_ms();
        /* Sleep for interval or wake early on state change notification */
        (void)ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(interval_ms));
        telemetry_tick();
    }
}
#endif

esp_err_t telemetry_init(void)
{
    telemetry_reset_state();

#ifdef ESP_PLATFORM
    if (s_telem_task_handle != NULL) {
        return ESP_OK;
    }

    BaseType_t ret = xTaskCreatePinnedToCore(
        app_telem_task,
        "app_telem_task",
        3072,
        NULL,
        3, /* Priority 3: Below BLE task (4) and UI task (5) */
        &s_telem_task_handle,
        1  /* Core 1 */
    );

    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create app_telem_task!");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Adaptive Telemetry subsystem initialized on Core 1 (Stack: 3072B, Priority: 3)");
#endif

    return ESP_OK;
}
