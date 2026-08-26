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
    ESP_LOGI(TAG, " Phase 1: Project Skeleton & Diagnostics Initialized");
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
    ESP_LOGI(TAG, "System Ready. Core 0/1 ready for driver initialization in subsequent phases.");
}
