#include <stdio.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_log.h"

#include "config.h"
#include "command.h"
#include "led.h"
#include "buttons.h"
#include "pca9685.h"

static const char *TAG = "FABRICA_MAIN";

/* Global Inter-Task Communication Handles */
QueueHandle_t xCommandQueue = NULL;
EventGroupHandle_t xSystemEventGroup = NULL;

/**
 * @brief Print comprehensive chip diagnostics and system telemetry.
 */
static void print_system_diagnostics(void)
{
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);

    uint32_t flash_size_bytes = 0;
    esp_flash_get_size(NULL, &flash_size_bytes);
    uint32_t flash_size_mb = flash_size_bytes / (1024 * 1024);

    size_t free_heap = esp_get_free_heap_size();
    size_t min_free_heap = esp_get_minimum_free_heap_size();

    ESP_LOGI(TAG, "============================================================");
    ESP_LOGI(TAG, " Fabrica Cloth Folding Robot - ESP32 Firmware");
    ESP_LOGI(TAG, " Phase 3: I2C PCA9685 16-Channel PWM Servo Driver Ready");
    ESP_LOGI(TAG, "============================================================");

    ESP_LOGI(TAG, "Chip Model       : %s", (chip_info.model == CHIP_ESP32) ? "ESP32" : "Unknown");
    ESP_LOGI(TAG, "Silicon Revision : %d", chip_info.revision);
    ESP_LOGI(TAG, "CPU Cores        : %d @ 240 MHz", chip_info.cores);
    ESP_LOGI(TAG, "Features         : %s%s%s",
             (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? "802.11b/g/n " : "",
             (chip_info.features & CHIP_FEATURE_BT) ? "BT " : "",
             (chip_info.features & CHIP_FEATURE_BLE) ? "BLE" : "");
    ESP_LOGI(TAG, "SPI Flash Size   : %" PRIu32 " MB (%s)", flash_size_mb,
             (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "Embedded" : "External");
    ESP_LOGI(TAG, "Current Free Heap: %u bytes (%u KB)", (unsigned int)free_heap, (unsigned int)(free_heap / 1024));
    ESP_LOGI(TAG, "Minimum Free Heap: %u bytes (%u KB)", (unsigned int)min_free_heap, (unsigned int)(min_free_heap / 1024));
    ESP_LOGI(TAG, "Tick Rate        : %d Hz (1 ms tick)", CONFIG_FREERTOS_HZ);
    ESP_LOGI(TAG, "------------------------------------------------------------");
}

/**
 * @brief Initialize FreeRTOS inter-task communication queues and event groups.
 */
static esp_err_t init_ipc_primitives(void)
{
    ESP_LOGI(TAG, "Initializing FreeRTOS IPC primitives...");

    /* Allocate unified command queue */
    xCommandQueue = xQueueCreate(COMMAND_QUEUE_LENGTH, sizeof(command_t));
    if (xCommandQueue == NULL) {
        ESP_LOGE(TAG, "Failed to create xCommandQueue! Insufficient heap memory.");
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG, "Command Queue created (Depth: %d, Item Size: %zu bytes)",
             COMMAND_QUEUE_LENGTH, sizeof(command_t));

    /* Allocate system event group for state synchronization and E-Stop */
    xSystemEventGroup = xEventGroupCreate();
    if (xSystemEventGroup == NULL) {
        ESP_LOGE(TAG, "Failed to create xSystemEventGroup! Insufficient heap memory.");
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG, "System Event Group created successfully.");

    return ESP_OK;
}

/**
 * @brief Application entrypoint executing on Core 0.
 */
void app_main(void)
{
    /* 1. Print Startup Banner & Telemetry */
    print_system_diagnostics();

    /* 2. Initialize FreeRTOS Queues & Events */
    esp_err_t err = init_ipc_primitives();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "System bootstrap failed with error: %s (0x%x)", esp_err_to_name(err), err);
        return;
    }

    ESP_LOGI(TAG, "GPIO Configuration: LED=%d, B1=%d, B2=%d, B3=%d, B4=%d, SDA=%d, SCL=%d",
             STATUS_LED_GPIO, BTN1_GPIO, BTN2_GPIO, BTN3_GPIO, BTN4_GPIO, I2C_SDA_GPIO, I2C_SCL_GPIO);
    ESP_LOGI(TAG, "PCA9685 Driver: Addr=0x%02X, PWM Freq=%d Hz, Channels=%d",
             PCA9685_I2C_ADDR, PCA9685_PWM_FREQ_HZ, TOTAL_SERVO_CHANNELS);

    /* 3. Initialize Status LED Engine (Core 1) */
    err = led_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize Status LED engine: %s", esp_err_to_name(err));
        return;
    }

    /* 4. Initialize 4-Button Subsystem (Core 1) */
    buttons_set_command_queue(xCommandQueue);
    err = buttons_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize 4-Button subsystem: %s", esp_err_to_name(err));
        return;
    }

    /* 5. Initialize PCA9685 16-Channel PWM Servo Driver (I2C Master on Core 0) */
    err = pca9685_init();
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "PCA9685 initialization returned: %s (Check I2C bus wiring/pullups)", esp_err_to_name(err));
    } else {
        ESP_LOGI(TAG, "PCA9685 driver ready. All 16 channels initialized to home position (0 deg).");
    }

    ESP_LOGI(TAG, "System initialization complete. Awaiting button & motion commands...");

    /* 6. Command Queue Consumer Loop */
    command_t cmd;
    while (1) {
        if (xQueueReceive(xCommandQueue, &cmd, portMAX_DELAY) == pdTRUE) {
            ESP_LOGI(TAG, "[CMD RECEIVED] Type: %d, Source: %d, Preset: %d",
                     cmd.type, cmd.source, cmd.payload.preset_id);

            switch (cmd.type) {
                case CMD_RUN_PRESET:
                    ESP_LOGI(TAG, "-> Daily Run Mode: Triggered Preset %d", cmd.payload.preset_id);
                    /* Provide locked feedback pulse and demonstrate channel articulation */
                    led_set_state(LED_STATE_STEP_LOCKED);
                    /* Test pulse: nudge corresponding servo channel (0 to 3) */
                    if (cmd.payload.preset_id >= 1 && cmd.payload.preset_id <= 4) {
                        uint8_t target_ch = (uint8_t)(cmd.payload.preset_id - 1);
                        pca9685_nudge_channel(target_ch);
                        vTaskDelay(pdMS_TO_TICKS(200));
                        pca9685_home_all();
                    }
                    break;
                case CMD_ENTER_PROGRAM_MODE:
                    ESP_LOGI(TAG, "-> Visual Staging Mode: Entered programming for Preset %d", cmd.payload.preset_id);
                    led_set_state(LED_STATE_PROGRAMMING);
                    break;
                case CMD_CYCLE_NUDGE_MOTOR:
                    ESP_LOGI(TAG, "-> Cycle Nudge Motor: Channel %d", cmd.payload.jog_param.channel);
                    pca9685_nudge_channel(cmd.payload.jog_param.channel);
                    break;
                case CMD_STAGE_TOGGLE_MOTOR:
                    ESP_LOGI(TAG, "-> Stage Motor: Channel %d", cmd.payload.jog_param.channel);
                    pca9685_stage_channel(cmd.payload.jog_param.channel);
                    break;
                case CMD_EMERGENCY_STOP:
                    ESP_LOGW(TAG, "-> EMERGENCY STOP Triggered! Homing all servos...");
                    pca9685_home_all();
                    led_set_state(LED_STATE_ESTOP);
                    break;
                default:
                    ESP_LOGI(TAG, "-> Unhandled command type: %d", cmd.type);
                    break;
            }
        }
    }
}
