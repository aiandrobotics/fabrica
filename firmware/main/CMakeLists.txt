idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    REQUIRES driver esp_system esp_timer esp_common freertos nvs_flash esp_hw_support spi_flash log
)
