# Plan — Phase 1: Project Skeleton, Hardware Configuration & Diagnostics

## Overview

Phase 1 establishes the foundational embedded C / ESP-IDF build architecture, hardware pinout mapping, system timing constants, scalable command schemas, and system startup diagnostics for the **Fabrica Cloth Folding Robot** firmware. This phase lays the foundation for all subsequent hardware drivers (buttons, LED, PCA9685 I2C, motion engine, and NVS storage).

---

## Task Group 1: ESP-IDF Build Infrastructure & SDK Configuration
1. Create root project build configuration files:
   - `firmware/CMakeLists.txt`: ESP-IDF project definition registering project name `fabrica_firmware` and standard component path discovery.
   - `firmware/Makefile`: Helper entrypoint for standard build commands (`build`, `flash`, `monitor`, `clean`).
   - `firmware/sdkconfig.defaults`: Baseline ESP32 configuration specifying:
     - Xtensa Dual-Core CPU frequency @ 240 MHz (`CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240=y`).
     - FreeRTOS tick rate @ 1000 Hz / 1 ms tick (`CONFIG_FREERTOS_HZ=1000`).
     - 4 MB SPI Flash support with standard DIO mode (`CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y`).
     - Compiler optimization levels and console UART baud rate (115200 bps).
2. Create `firmware/main/CMakeLists.txt`:
   - Register component sources (`main.c`) and header include directories.
   - Declare requirements on core ESP-IDF drivers (`driver`, `esp_system`, `esp_timer`, `esp_common`, `freertos`, `nvs_flash`, `esp_hw_support`, `spi_flash`).

---

## Task Group 2: Hardware Configuration & Unified Command Protocol Headers
1. Create `firmware/main/config.h`:
   - Define single source of truth for GPIO pin allocations:
     - `STATUS_LED_GPIO = GPIO_NUM_2` (Built-in DevKit status indicator)
     - `BTN1_GPIO = GPIO_NUM_0` (B1: Preset 1 / Cycle & Nudge)
     - `BTN2_GPIO = GPIO_NUM_4` (B2: Preset 2 / Stage & Toggle)
     - `BTN3_GPIO = GPIO_NUM_16` (B3: Preset 3 / Lock Step)
     - `BTN4_GPIO = GPIO_NUM_17` (B4: Preset 4 / Save & Exit)
     - `I2C_SDA_GPIO = GPIO_NUM_21` (PCA9685 I2C Data line)
     - `I2C_SCL_GPIO = GPIO_NUM_22` (PCA9685 I2C Clock line)
   - Define system operational limits and timing constants:
     - `MAX_STEPS_PER_ROUTINE = 16`
     - `MAX_MOTORS_PER_STEP = 2`
     - `TOTAL_SERVO_CHANNELS = 16`
     - `BUTTON_DEBOUNCE_MS = 50`
     - `BUTTON_LONG_PRESS_MS = 3000`
     - `BUTTON_SHORT_PRESS_MAX_MS = 500`
     - `PROGRAMMING_TIMEOUT_MS = 20000`
     - `FOLD_DWELL_TIME_MS = 300`
     - `INTER_STEP_DELAY_MS = 200`
     - `NUDGE_ANGLE_DEG = 15.0f`
     - `STAGE_ANGLE_DEG = 30.0f`
     - `HOME_ANGLE_DEG = 0.0f`
     - `FOLD_ANGLE_DEG = 180.0f`
   - Define PCA9685 constants (I2C address `0x40`, 50 Hz PWM frequency, 12-bit resolution ticks).
2. Create `firmware/main/command.h`:
   - Define transport sources enum `cmd_source_t` (`SOURCE_PHYSICAL_BUTTON`, `SOURCE_BLE`, `SOURCE_WIFI`, `SOURCE_INTERNAL_TIMER`).
   - Define command types enum `cmd_type_t` (`CMD_RUN_PRESET`, `CMD_RUN_RAW_SEQUENCE`, `CMD_EMERGENCY_STOP`, `CMD_ENTER_PROGRAM_MODE`, `CMD_CYCLE_NUDGE_MOTOR`, `CMD_STAGE_TOGGLE_MOTOR`, `CMD_LOCK_STEP`, `CMD_SAVE_EXIT_PROGRAM`, `CMD_JOG_MOTOR_ANGLE`, `CMD_GET_TELEMETRY`, `CMD_SYNC_PRESETS`).
   - Define sequence structures `fold_step_t` and `fold_routine_t` with CRC32 checksum field.
   - Define command payload union `cmd_payload_t` and unified `command_t` message container.
   - Define queue depth constant `COMMAND_QUEUE_LENGTH = 16`.

---

## Task Group 3: Startup Diagnostics, FreeRTOS IPC Primitives & App Bootstrap (`main.c`)
1. Implement `firmware/main/main.c`:
   - `app_main()` entrypoint function.
   - System Diagnostic Banner:
     - Query and log chip information via `esp_chip_info()` (chip model, silicon revision, number of CPU cores, WiFi/BT capabilities).
     - Query and log SPI flash size via `esp_flash_get_size()`.
     - Monitor heap memory metrics (current free heap and minimum free heap ever available via `esp_get_minimum_free_heap_size()`).
   - FreeRTOS Inter-Task Communication Initialization:
     - Create the unified command queue (`xQueueCreate(COMMAND_QUEUE_LENGTH, sizeof(command_t))`).
     - Create the system state / abort event group (`xEventGroupCreate()`).
     - Verify valid allocation of all IPC handles before task spawning.
   - Structured startup logging using `esp_log.h` with tag `TAG = "FABRICA_MAIN"`.

---

## Task Group 4: Host Verification Harness & ESP-IDF Build Validation
1. Create `firmware/test/test_headers.c`:
   - Host-compilable validation harness to verify syntax, enum values, struct byte packing, and size alignments of `config.h` and `command.h`.
2. Execute automated build and static syntax validation:
   - Compile host verification test using GCC / Clang with `-Wall -Wextra -Werror`.
   - Validate clean compilation of full firmware tree with ESP-IDF CMake build system.
