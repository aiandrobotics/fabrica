#pragma once
#ifndef FABRICA_CONFIG_H
#define FABRICA_CONFIG_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================= */
/* GPIO Pin Allocations                                                      */
/* ========================================================================= */

#define STATUS_LED_GPIO              2   /* Built-in Status LED (Active High) */

#define BTN1_GPIO                    4   /* Button 1: Preset 1 (Adult T-Shirt) */
#define BTN2_GPIO                    16  /* Button 2: Preset 2 (Long-Sleeve Shirt) */
#define BTN3_GPIO                    17  /* Button 3: Preset 3 (Trousers / Jeans) */
#define BTN4_GPIO                    5   /* Button 4: Preset 4 (Towel / Linen) */

#define I2C_SDA_GPIO                 21  /* PCA9685 I2C Data line (SDA) */
#define I2C_SCL_GPIO                 22  /* PCA9685 I2C Clock line (SCL) */

/* ========================================================================= */
/* System Operational Limits                                                 */
/* ========================================================================= */

#define MAX_STEPS_PER_ROUTINE        16  /* Max steps per folding preset */
#define MAX_MOTORS_PER_STEP          2   /* Max motors active simultaneously */
#define TOTAL_SERVO_CHANNELS         16  /* PCA9685 servo channels (0 to 15) */
#define TOTAL_PRESET_COUNT           4   /* Hardware preset buttons (1 to 4) */
#define COMMAND_QUEUE_LENGTH         16  /* Unified command queue capacity */

/* ========================================================================= */
/* Physical Servo Flap Channel Assignments (Standard Folding Grid)          */
/* ========================================================================= */

#define SERVO_FLAP_LEFT              0   /* Left side folding flap */
#define SERVO_FLAP_RIGHT             1   /* Right side folding flap */
#define SERVO_FLAP_BOTTOM            2   /* Bottom / waist folding flap */
#define SERVO_FLAP_TOP               3   /* Top / collar folding flap */

/* ========================================================================= */
/* System Timing Parameters (Milliseconds)                                   */
/* ========================================================================= */

#define BUTTON_DEBOUNCE_MS           50     /* Low-pass debounce filter */
#define BUTTON_SHORT_PRESS_MAX_MS    500    /* Maximum tap gesture duration */
#define BUTTON_LONG_PRESS_MS         3000   /* Hold time (3s) to enter BLE pairing mode */
#define BUTTON_BOND_RESET_MS         5000   /* Simultaneous B1+B4 hold time (5s) to clear BLE bonds */
#define BLE_PAIRING_TIMEOUT_MS       120000 /* 120-second (2-minute) BLE discovery/pairing window */
#define FOLD_DWELL_TIME_MS           300    /* Flap hold time at fold angle */
#define INTER_STEP_DELAY_MS          200    /* Delay between routine steps */
#define CALIBRATION_THERMAL_TIMEOUT_MS    10000 /* Stationary servo PCA9685 sleep cutoff (10s) */
#define CALIBRATION_INACTIVITY_TIMEOUT_MS 15000 /* Calibration auto-home & exit timeout (15s) */

/* ========================================================================= */
/* Bluetooth Low Energy (NimBLE) Transport Parameters                        */
/* ========================================================================= */

#define BLE_DEVICE_NAME_PREFIX           "Fabrica" /* Prefix for "Fabrica-XXXX" local name */
#define BLE_ADV_INTERVAL_MS              100    /* Fast advertising interval (100ms) */
#define BLE_ADV_INTERVAL_UNITS           160    /* 160 * 0.625ms = 100ms (0x00A0) */
#define BLE_CONN_INTERVAL_MIN_MS         15.0f  /* Apple Accessory compliant min interval (12 units) */
#define BLE_CONN_INTERVAL_MAX_MS         30.0f  /* Apple Accessory compliant max interval (24 units) */
#define BLE_CONN_INTERVAL_MIN_UNITS      12     /* 12 * 1.25ms = 15.0ms */
#define BLE_CONN_INTERVAL_MAX_UNITS      24     /* 24 * 1.25ms = 30.0ms */
#define BLE_CONN_SLAVE_LATENCY           0      /* Zero skipped connection events */
#define BLE_SUPERVISION_TIMEOUT_MS       4000   /* Supervision timeout (4000ms <= 6000ms Apple max) */
#define BLE_SUPERVISION_TIMEOUT_UNITS    400    /* 400 * 10ms = 4000ms */
#define BLE_CONN_PARAM_UPDATE_DELAY_MS   1500   /* Delay before peripheral requests conn param update */
#define BLE_PREFERRED_MTU                512    /* Target ATT MTU (>= 247B for 212B table transfer) */
#define BLE_MAX_BONDS                    4      /* Max trusted peer identities persisted in NVS */

/* ========================================================================= */
/* Servo Articulation Angles (Degrees)                                       */
/* ========================================================================= */

#define HOME_ANGLE_DEG               0.0f   /* Flat resting angle */
#define NUDGE_ANGLE_DEG              15.0f  /* Identification nudge angle */
#define STAGE_ANGLE_DEG              30.0f  /* Visual staging hold angle */
#define FOLD_ANGLE_DEG               180.0f /* Full folding sweep angle */

/* ========================================================================= */
/* PCA9685 I2C & PWM Configuration                                           */
/* ========================================================================= */

#define PCA9685_I2C_ADDR             0x40      /* Default I2C address */
#define PCA9685_I2C_FREQ_HZ          100000    /* 100 kHz Standard mode */
#define PCA9685_PWM_FREQ_HZ          50        /* 50 Hz PWM servo refresh rate */
#define PCA9685_PWM_RES_BITS         12        /* 12-bit resolution (4096 steps) */
#define PCA9685_PRESCALE_VAL         121       /* Prescale for 50Hz with 25MHz osc */

#define SERVO_MIN_PULSE_US           500       /* 0 deg pulse width (us) */
#define SERVO_MAX_PULSE_US           2500      /* 180 deg pulse width (us) */

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_CONFIG_H */
