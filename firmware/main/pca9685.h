#pragma once
#ifndef FABRICA_PCA9685_H
#define FABRICA_PCA9685_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef ESP_PLATFORM
#include "esp_err.h"
#else
/* Standard error codes for host testing harness */
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK                  0
#endif
#ifndef ESP_FAIL
#define ESP_FAIL                -1
#endif
#ifndef ESP_ERR_NO_MEM
#define ESP_ERR_NO_MEM          0x101
#endif
#ifndef ESP_ERR_INVALID_ARG
#define ESP_ERR_INVALID_ARG     0x102
#endif
#ifndef ESP_ERR_INVALID_STATE
#define ESP_ERR_INVALID_STATE   0x103
#endif
#ifndef ESP_ERR_TIMEOUT
#define ESP_ERR_TIMEOUT         0x107
#endif
#ifndef ESP_ERR_NOT_FOUND
#define ESP_ERR_NOT_FOUND       0x105
#endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================= */
/* PCA9685 Register Map                                                      */
/* ========================================================================= */

#define PCA9685_REG_MODE1           0x00    /* Mode register 1 */
#define PCA9685_REG_MODE2           0x01    /* Mode register 2 */
#define PCA9685_REG_SUBADR1         0x02    /* I2C-bus subaddress 1 */
#define PCA9685_REG_SUBADR2         0x03    /* I2C-bus subaddress 2 */
#define PCA9685_REG_SUBADR3         0x04    /* I2C-bus subaddress 3 */
#define PCA9685_REG_ALLCALLADR      0x05    /* LED All Call I2C-bus address */
#define PCA9685_REG_LED0_ON_L       0x06    /* LED0 output and brightness control byte 0 */
#define PCA9685_REG_LED0_ON_H       0x07    /* LED0 output and brightness control byte 1 */
#define PCA9685_REG_LED0_OFF_L      0x08    /* LED0 output and brightness control byte 2 */
#define PCA9685_REG_LED0_OFF_H      0x09    /* LED0 output and brightness control byte 3 */
#define PCA9685_REG_ALL_LED_ON_L    0xFA    /* All LED output and brightness control byte 0 */
#define PCA9685_REG_ALL_LED_ON_H    0xFB    /* All LED output and brightness control byte 1 */
#define PCA9685_REG_ALL_LED_OFF_L   0xFC    /* All LED output and brightness control byte 2 */
#define PCA9685_REG_ALL_LED_OFF_H   0xFD    /* All LED output and brightness control byte 3 */
#define PCA9685_REG_PRESCALE        0xFE    /* Prescaler for PWM output frequency */
#define PCA9685_REG_TESTMODE        0xFF    /* Defines the test mode to be entered */

/* Register bit masks */
#define PCA9685_MODE1_RESTART       0x80    /* Restart enabled */
#define PCA9685_MODE1_EXTCLK        0x40    /* External clock pin */
#define PCA9685_MODE1_AI            0x20    /* Auto-Increment enabled */
#define PCA9685_MODE1_SLEEP         0x10    /* Low power mode (oscillator off) */
#define PCA9685_MODE1_SUB1          0x08    /* PCA9685 responds to subaddress 1 */
#define PCA9685_MODE1_SUB2          0x04    /* PCA9685 responds to subaddress 2 */
#define PCA9685_MODE1_SUB3          0x02    /* PCA9685 responds to subaddress 3 */
#define PCA9685_MODE1_ALLCALL       0x01    /* PCA9685 responds to all-call */

#define PCA9685_MODE2_INVRT         0x10    /* Output logic state inverted */
#define PCA9685_MODE2_OCH           0x08    /* Output change on STOP or ACK */
#define PCA9685_MODE2_OUTDRV        0x04    /* Totem-pole output (vs open-drain) */
#define PCA9685_MODE2_OUTNE_TP      0x01    /* Active LOW output mode */

/* Helper macros for channel register addresses */
#define PCA9685_CHANNEL_ON_L(ch)    ((uint8_t)(0x06 + ((ch) * 4)))
#define PCA9685_CHANNEL_ON_H(ch)    ((uint8_t)(0x07 + ((ch) * 4)))
#define PCA9685_CHANNEL_OFF_L(ch)   ((uint8_t)(0x08 + ((ch) * 4)))
#define PCA9685_CHANNEL_OFF_H(ch)   ((uint8_t)(0x09 + ((ch) * 4)))

/* ========================================================================= */
/* Public Driver API                                                         */
/* ========================================================================= */

/**
 * @brief Initialize the ESP32 I2C master driver, configure PCA9685 registers for
 *        50Hz PWM operation, and reset all 16 servo channels to flat home (0 deg).
 *
 * @return ESP_OK on success, or ESP-IDF error code.
 */
esp_err_t pca9685_init(void);

/**
 * @brief Probe the I2C bus to check if the PCA9685 device is present at address 0x40.
 *
 * @return ESP_OK if device ACKed, ESP_ERR_NOT_FOUND if no response.
 */
esp_err_t pca9685_probe(void);

/**
 * @brief Write a single byte to a PCA9685 register.
 *
 * @param reg Register address (0x00 to 0xFF).
 * @param val Byte value to write.
 * @return ESP_OK on success.
 */
esp_err_t pca9685_write_reg(uint8_t reg, uint8_t val);

/**
 * @brief Read a single byte from a PCA9685 register.
 *
 * @param reg Register address.
 * @param val Pointer to output byte.
 * @return ESP_OK on success.
 */
esp_err_t pca9685_read_reg(uint8_t reg, uint8_t *val);

/**
 * @brief Set the 12-bit ON and OFF counts for a single PWM channel (0 to 15).
 *
 * @param channel Channel index (0 to 15).
 * @param on_count 12-bit ON tick (typically 0).
 * @param off_count 12-bit OFF tick (0 to 4095).
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if channel >= 16.
 */
esp_err_t pca9685_set_pwm(uint8_t channel, uint16_t on_count, uint16_t off_count);

/**
 * @brief Set 12-bit ON and OFF counts simultaneously across all 16 channels using
 *        the PCA9685 ALL_LED broadcast registers.
 *
 * @param on_count 12-bit ON tick.
 * @param off_count 12-bit OFF tick.
 * @return ESP_OK on success.
 */
esp_err_t pca9685_set_all_pwm(uint16_t on_count, uint16_t off_count);

/**
 * @brief Convert target angle in degrees (0.0 to 180.0) to 12-bit PWM count and
 *        update the specified servo channel.
 *
 * @param channel Channel index (0 to 15).
 * @param angle_deg Target angle in degrees (automatically clamped between 0.0 and 180.0).
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if channel >= 16.
 */
esp_err_t pca9685_set_servo_angle(uint8_t channel, float angle_deg);

/**
 * @brief Set multiple servo channels to the target angle synchronously using a 16-bit mask.
 *
 * @param channel_mask Bitmask where bit N (0 to 15) corresponds to channel N.
 * @param angle_deg Target angle in degrees for all enabled channels.
 * @return ESP_OK on success.
 */
esp_err_t pca9685_set_multi_servo_angles(uint16_t channel_mask, float angle_deg);

/**
 * @brief Set all 16 servo channels to flat resting home position (0.0 deg / 102 counts).
 *
 * @return ESP_OK on success.
 */
esp_err_t pca9685_home_all(void);

/**
 * @brief Pulse the target channel to 15.0 deg (NUDGE_ANGLE_DEG) for physical flap identification.
 *
 * @param channel Channel index (0 to 15).
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if channel >= 16.
 */
esp_err_t pca9685_nudge_channel(uint8_t channel);

/**
 * @brief Set the target channel to 30.0 deg (STAGE_ANGLE_DEG) for visual staging hold.
 *
 * @param channel Channel index (0 to 15).
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if channel >= 16.
 */
esp_err_t pca9685_stage_channel(uint8_t channel);

/**
 * @brief Put PCA9685 internal oscillator to sleep (low power) or wake it.
 *
 * @param enable True to sleep, False to wake.
 * @return ESP_OK on success.
 */
esp_err_t pca9685_sleep(bool enable);

/**
 * @brief Pure conversion function mapping angle in degrees (0.0 to 180.0) to
 *        12-bit PCA9685 PWM OFF counts (102 to 512 counts).
 *
 * @param angle_deg Angle in degrees.
 * @return 12-bit count value (102 to 512).
 */
uint16_t pca9685_angle_to_counts(float angle_deg);

/* ========================================================================= */
/* Test Harness Mock Helper Functions (Host-Only)                            */
/* ========================================================================= */
#ifndef ESP_PLATFORM
void pca9685_mock_reset(void);
uint8_t pca9685_mock_get_reg(uint8_t reg);
void pca9685_mock_set_reg(uint8_t reg, uint8_t val);
void pca9685_mock_set_probe_success(bool success);
uint16_t pca9685_mock_get_channel_off_count(uint8_t channel);
#endif

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_PCA9685_H */
