#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>

#include "config.h"
#include "pca9685.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2c_master.h"
#include "esp_log.h"
#include "esp_rom_sys.h"

static const char *TAG = "FABRICA_PCA9685";
static i2c_master_bus_handle_t s_i2c_bus_handle = NULL;
static i2c_master_dev_handle_t s_pca9685_dev_handle = NULL;

#define I2C_TIMEOUT_MS   100
#else
/* Host testing mock storage */
static uint8_t s_mock_regs[256];
static bool s_mock_probe_success = true;
#endif

/* ========================================================================= */
/* Angle to PWM Conversion Math                                              */
/* ========================================================================= */

uint16_t pca9685_angle_to_counts(float angle_deg)
{
    /* Enforce safe mechanical boundaries */
    if (angle_deg < HOME_ANGLE_DEG) {
        angle_deg = HOME_ANGLE_DEG;
    } else if (angle_deg > FOLD_ANGLE_DEG) {
        angle_deg = FOLD_ANGLE_DEG;
    }

    /* Linear interpolation between SERVO_MIN_PULSE_US (500us) and SERVO_MAX_PULSE_US (2500us) */
    float pulse_us = (float)SERVO_MIN_PULSE_US +
        (angle_deg / FOLD_ANGLE_DEG) * (float)(SERVO_MAX_PULSE_US - SERVO_MIN_PULSE_US);

    /* Convert pulse width (us) to 12-bit counts in a 20,000us (50Hz) frame period:
     * counts = round(pulse_us * 4096 / 20000) */
    float counts_f = (pulse_us * (float)(1 << PCA9685_PWM_RES_BITS)) / 20000.0f;
    return (uint16_t)(roundf(counts_f));
}

/* ========================================================================= */
/* Low-Level I2C Register Read / Write Operations                           */
/* ========================================================================= */

esp_err_t pca9685_probe(void)
{
#ifdef ESP_PLATFORM
    if (s_i2c_bus_handle == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    esp_err_t ret = i2c_master_probe(s_i2c_bus_handle, PCA9685_I2C_ADDR, I2C_TIMEOUT_MS);
    if (ret != ESP_OK) {
        return ESP_ERR_NOT_FOUND;
    }
    return ESP_OK;
#else
    if (!s_mock_probe_success) {
        return ESP_ERR_NOT_FOUND;
    }
    return ESP_OK;
#endif
}

esp_err_t pca9685_write_reg(uint8_t reg, uint8_t val)
{
#ifdef ESP_PLATFORM
    if (s_pca9685_dev_handle == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    uint8_t write_buf[2] = {reg, val};
    return i2c_master_transmit(s_pca9685_dev_handle, write_buf, sizeof(write_buf), I2C_TIMEOUT_MS);
#else
    s_mock_regs[reg] = val;
    return ESP_OK;
#endif
}

esp_err_t pca9685_read_reg(uint8_t reg, uint8_t *val)
{
    if (val == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

#ifdef ESP_PLATFORM
    if (s_pca9685_dev_handle == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit_receive(s_pca9685_dev_handle, &reg, 1, val, 1, I2C_TIMEOUT_MS);
#else
    *val = s_mock_regs[reg];
    return ESP_OK;
#endif
}

/* ========================================================================= */
/* Initialization & Configuration                                            */
/* ========================================================================= */

esp_err_t pca9685_init(void)
{
#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Initializing I2C Master Bus on SDA: GPIO %d, SCL: GPIO %d @ %d Hz...",
             I2C_SDA_GPIO, I2C_SCL_GPIO, PCA9685_I2C_FREQ_HZ);

    /* 1. Initialize modern I2C Master Bus Handle */
    if (s_i2c_bus_handle == NULL) {
        i2c_master_bus_config_t bus_config = {
            .i2c_port = I2C_NUM_0,
            .sda_io_num = (gpio_num_t)I2C_SDA_GPIO,
            .scl_io_num = (gpio_num_t)I2C_SCL_GPIO,
            .clk_source = I2C_CLK_SRC_DEFAULT,
            .glitch_ignore_cnt = 7,
            .flags.enable_internal_pullup = true,
        };

        esp_err_t err = i2c_new_master_bus(&bus_config, &s_i2c_bus_handle);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to create I2C master bus: %s", esp_err_to_name(err));
            return err;
        }
    }

    /* 2. Add PCA9685 Device to Bus */
    if (s_pca9685_dev_handle == NULL) {
        i2c_device_config_t dev_config = {
            .dev_addr_length = I2C_ADDR_BIT_LEN_7,
            .device_address = PCA9685_I2C_ADDR,
            .scl_speed_hz = PCA9685_I2C_FREQ_HZ,
        };

        esp_err_t err = i2c_master_bus_add_device(s_i2c_bus_handle, &dev_config, &s_pca9685_dev_handle);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to add PCA9685 device handle: %s", esp_err_to_name(err));
            return err;
        }
    }
#endif

    /* 3. Probe PCA9685 presence */
    esp_err_t err = pca9685_probe();
    if (err != ESP_OK) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "PCA9685 not detected at I2C address 0x%02X! Check wiring.", PCA9685_I2C_ADDR);
#endif
        return err;
    }

    /* 4. Sleep oscillator to configure prescaler */
    err = pca9685_write_reg(PCA9685_REG_MODE1, PCA9685_MODE1_SLEEP);
    if (err != ESP_OK) return err;

    /* 5. Set PWM frequency prescaler (121 for 50Hz) */
    err = pca9685_write_reg(PCA9685_REG_PRESCALE, PCA9685_PRESCALE_VAL);
    if (err != ESP_OK) return err;

    /* 6. Wake oscillator with Auto-Increment (AI) and All-Call enabled */
    err = pca9685_write_reg(PCA9685_REG_MODE1, PCA9685_MODE1_AI | PCA9685_MODE1_ALLCALL);
    if (err != ESP_OK) return err;

#ifdef ESP_PLATFORM
    /* Wait 500us for internal oscillator to stabilize */
    esp_rom_delay_us(500);
#endif

    /* 7. Clear restart bit by rewriting AI + ALLCALL */
    err = pca9685_write_reg(PCA9685_REG_MODE1, PCA9685_MODE1_RESTART | PCA9685_MODE1_AI | PCA9685_MODE1_ALLCALL);
    if (err != ESP_OK) return err;

    /* 8. Configure output driver for Totem-Pole (MODE2_OUTDRV) */
    err = pca9685_write_reg(PCA9685_REG_MODE2, PCA9685_MODE2_OUTDRV);
    if (err != ESP_OK) return err;

    /* 9. Reset all 16 channels to 0.0 deg home position (102 counts) */
    err = pca9685_home_all();
    if (err != ESP_OK) return err;

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "PCA9685 initialized successfully: Addr=0x%02X, Prescale=%d (50Hz), All 16 channels flat @ 0 deg",
             PCA9685_I2C_ADDR, PCA9685_PRESCALE_VAL);
#endif

    return ESP_OK;
}

/* ========================================================================= */
/* PWM Output & Servo Articulation APIs                                      */
/* ========================================================================= */

esp_err_t pca9685_set_pwm(uint8_t channel, uint16_t on_count, uint16_t off_count)
{
    if (channel >= TOTAL_SERVO_CHANNELS) {
        return ESP_ERR_INVALID_ARG;
    }

    uint8_t write_buf[5] = {
        PCA9685_CHANNEL_ON_L(channel),
        (uint8_t)(on_count & 0xFF),
        (uint8_t)((on_count >> 8) & 0x0F),
        (uint8_t)(off_count & 0xFF),
        (uint8_t)((off_count >> 8) & 0x0F)
    };

#ifdef ESP_PLATFORM
    if (s_pca9685_dev_handle == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit(s_pca9685_dev_handle, write_buf, sizeof(write_buf), I2C_TIMEOUT_MS);
#else
    for (int i = 0; i < 4; i++) {
        s_mock_regs[PCA9685_CHANNEL_ON_L(channel) + i] = write_buf[1 + i];
    }
    return ESP_OK;
#endif
}

esp_err_t pca9685_set_all_pwm(uint16_t on_count, uint16_t off_count)
{
    uint8_t write_buf[5] = {
        PCA9685_REG_ALL_LED_ON_L,
        (uint8_t)(on_count & 0xFF),
        (uint8_t)((on_count >> 8) & 0x0F),
        (uint8_t)(off_count & 0xFF),
        (uint8_t)((off_count >> 8) & 0x0F)
    };

#ifdef ESP_PLATFORM
    if (s_pca9685_dev_handle == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit(s_pca9685_dev_handle, write_buf, sizeof(write_buf), I2C_TIMEOUT_MS);
#else
    for (int i = 0; i < 4; i++) {
        s_mock_regs[PCA9685_REG_ALL_LED_ON_L + i] = write_buf[1 + i];
    }
    /* In hardware, ALL_LED applies to all channels 0-15 */
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        s_mock_regs[PCA9685_CHANNEL_ON_L(ch)]     = (uint8_t)(on_count & 0xFF);
        s_mock_regs[PCA9685_CHANNEL_ON_H(ch)]     = (uint8_t)((on_count >> 8) & 0x0F);
        s_mock_regs[PCA9685_CHANNEL_OFF_L(ch)]    = (uint8_t)(off_count & 0xFF);
        s_mock_regs[PCA9685_CHANNEL_OFF_H(ch)]    = (uint8_t)((off_count >> 8) & 0x0F);
    }
    return ESP_OK;
#endif
}

esp_err_t pca9685_set_servo_angle(uint8_t channel, float angle_deg)
{
    if (channel >= TOTAL_SERVO_CHANNELS) {
        return ESP_ERR_INVALID_ARG;
    }

    uint16_t off_count = pca9685_angle_to_counts(angle_deg);
    return pca9685_set_pwm(channel, 0, off_count);
}

esp_err_t pca9685_set_multi_servo_angles(uint16_t channel_mask, float angle_deg)
{
    uint16_t off_count = pca9685_angle_to_counts(angle_deg);

    /* If all 16 channels are targeted, use fast ALL_LED broadcast */
    if (channel_mask == 0xFFFF) {
        return pca9685_set_all_pwm(0, off_count);
    }

    /* Otherwise, update each specified channel in bitmask */
    for (uint8_t ch = 0; ch < TOTAL_SERVO_CHANNELS; ch++) {
        if (channel_mask & (1U << ch)) {
            esp_err_t err = pca9685_set_pwm(ch, 0, off_count);
            if (err != ESP_OK) {
                return err;
            }
        }
    }

    return ESP_OK;
}

esp_err_t pca9685_home_all(void)
{
    uint16_t home_counts = pca9685_angle_to_counts(HOME_ANGLE_DEG);
    return pca9685_set_all_pwm(0, home_counts);
}

esp_err_t pca9685_nudge_channel(uint8_t channel)
{
    return pca9685_set_servo_angle(channel, NUDGE_ANGLE_DEG);
}

esp_err_t pca9685_stage_channel(uint8_t channel)
{
    return pca9685_set_servo_angle(channel, STAGE_ANGLE_DEG);
}

esp_err_t pca9685_sleep(bool enable)
{
    uint8_t mode1 = 0;
    esp_err_t err = pca9685_read_reg(PCA9685_REG_MODE1, &mode1);
    if (err != ESP_OK) return err;

    if (enable) {
        mode1 |= PCA9685_MODE1_SLEEP;
        return pca9685_write_reg(PCA9685_REG_MODE1, mode1);
    } else {
        mode1 &= ~PCA9685_MODE1_SLEEP;
        err = pca9685_write_reg(PCA9685_REG_MODE1, mode1);
        if (err != ESP_OK) return err;

#ifdef ESP_PLATFORM
        esp_rom_delay_us(500);
#endif
        return pca9685_write_reg(PCA9685_REG_MODE1, mode1 | PCA9685_MODE1_RESTART);
    }
}

/* ========================================================================= */
/* Test Harness Mock Helper Functions (Host-Only)                            */
/* ========================================================================= */
#ifndef ESP_PLATFORM
void pca9685_mock_reset(void)
{
    memset(s_mock_regs, 0, sizeof(s_mock_regs));
    s_mock_probe_success = true;
}

uint8_t pca9685_mock_get_reg(uint8_t reg)
{
    return s_mock_regs[reg];
}

void pca9685_mock_set_reg(uint8_t reg, uint8_t val)
{
    s_mock_regs[reg] = val;
}

void pca9685_mock_set_probe_success(bool success)
{
    s_mock_probe_success = success;
}

uint16_t pca9685_mock_get_channel_off_count(uint8_t channel)
{
    if (channel >= TOTAL_SERVO_CHANNELS) {
        return 0;
    }
    uint8_t l = s_mock_regs[PCA9685_CHANNEL_OFF_L(channel)];
    uint8_t h = s_mock_regs[PCA9685_CHANNEL_OFF_H(channel)];
    return (uint16_t)(l | ((h & 0x0F) << 8));
}
#endif
