idf_component_register(
    SRCS "main.c" "led.c" "buttons.c" "pca9685.c" "storage.c" "motion.c"
    INCLUDE_DIRS "."
    REQUIRES driver esp_driver_gpio esp_driver_i2c esp_system esp_timer esp_common freertos nvs_flash esp_hw_support spi_flash log
)


