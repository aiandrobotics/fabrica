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

#define BTN1_GPIO                    0   /* Button 1: Preset 1 / Cycle Flap */
#define BTN2_GPIO                    4   /* Button 2: Preset 2 / Stage Flap */
#define BTN3_GPIO                    16  /* Button 3: Preset 3 / Lock Step */
#define BTN4_GPIO                    17  /* Button 4: Preset 4 / Save & Exit */

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
/* System Timing Parameters (Milliseconds)                                   */
/* ========================================================================= */

#define BUTTON_DEBOUNCE_MS           50    /* Low-pass debounce filter */
#define BUTTON_SHORT_PRESS_MAX_MS    500   /* Maximum tap gesture duration */
#define BUTTON_LONG_PRESS_MS         3000  /* Hold time to enter program mode */
#define PROGRAMMING_TIMEOUT_MS       20000 /* Inactivity timeout in program mode */
#define FOLD_DWELL_TIME_MS           300   /* Flap hold time at fold angle */
#define INTER_STEP_DELAY_MS          200   /* Delay between routine steps */

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
