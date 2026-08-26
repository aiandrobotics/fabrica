#pragma once
#ifndef FABRICA_COMMAND_H
#define FABRICA_COMMAND_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "config.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================= */
/* Command Transport Sources                                                 */
/* ========================================================================= */

typedef enum {
    SOURCE_PHYSICAL_BUTTON = 0, /* On-board physical 4-button pad */
    SOURCE_BLE             = 1, /* Bluetooth LE GATT connection (Mobile App) */
    SOURCE_WIFI            = 2, /* Wi-Fi / Local WebSocket JSON RPC */
    SOURCE_INTERNAL_TIMER  = 3  /* Internal RTOS timer / safety watchdog */
} cmd_source_t;

/* ========================================================================= */
/* Unified Command Types                                                     */
/* ========================================================================= */

typedef enum {
    CMD_RUN_PRESET = 0,         /* Execute saved preset routine (1 to 4) */
    CMD_RUN_RAW_SEQUENCE,       /* Execute unsaved sequence payload directly */
    CMD_EMERGENCY_STOP,         /* Immediate E-Stop halt & home all servos */
    CMD_ENTER_PROGRAM_MODE,     /* Enter visual staging mode for target preset */
    CMD_CYCLE_NUDGE_MOTOR,      /* Cycle motor index and pulse 15° nudge */
    CMD_STAGE_TOGGLE_MOTOR,     /* Toggle target motor staged (30°) / rest (0°) */
    CMD_LOCK_STEP,              /* Commit staged motor(s) to step buffer */
    CMD_SAVE_EXIT_PROGRAM,      /* Commit buffer to NVS flash and exit */
    CMD_JOG_MOTOR_ANGLE,        /* Live position jog (0° to 180°) for calibration */
    CMD_GET_TELEMETRY,          /* Request real-time status telemetry */
    CMD_SYNC_PRESETS            /* Synchronize presets over wireless transport */
} cmd_type_t;

/* ========================================================================= */
/* Folding Routine & Step Data Structures                                    */
/* ========================================================================= */

/**
 * @brief Single folding step containing 1 or 2 simultaneous servo motions.
 */
typedef struct {
    uint8_t motor_count;                     /**< Number of active motors (1 or 2) */
    uint8_t motor_ids[MAX_MOTORS_PER_STEP];  /**< Zero-indexed servo IDs (0 to 15) */
} fold_step_t;

/**
 * @brief Complete folding routine sequence stored in NVS flash blob.
 */
typedef struct {
    uint8_t step_count;                       /**< Number of steps (1 to 16) */
    fold_step_t steps[MAX_STEPS_PER_ROUTINE]; /**< Array of sequence steps */
    uint32_t checksum;                        /**< CRC32 integrity checksum */
} fold_routine_t;

/**
 * @brief Parameter payload for live motor angle jogging.
 */
typedef struct {
    uint8_t channel;    /**< Servo channel (0 to 15) */
    float angle_deg;    /**< Target angle (0.0° to 180.0°) */
} jog_param_t;

/**
 * @brief Polymorphic command payload union.
 */
typedef union {
    uint8_t preset_id;          /**< Preset ID (1 to 4) */
    fold_routine_t raw_routine; /**< Direct routine sequence payload */
    jog_param_t jog_param;      /**< Single motor jog parameter */
} cmd_payload_t;

/**
 * @brief Standardized source-agnostic command structure.
 */
typedef struct {
    cmd_type_t type;       /**< Command operation type */
    cmd_source_t source;   /**< Command origin transport */
    cmd_payload_t payload; /**< Command-specific data payload */
} command_t;

#ifdef __cplusplus
}
#endif

#endif /* FABRICA_COMMAND_H */
