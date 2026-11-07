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
    SOURCE_INTERNAL_TIMER  = 2  /* Internal RTOS timer / safety watchdog */
} cmd_source_t;

/* ========================================================================= */
/* Unified Command Types                                                     */
/* ========================================================================= */

typedef enum {
    CMD_RUN_PRESET = 0,         /* Execute saved preset routine (1 to 4) */
    CMD_RUN_RAW_SEQUENCE,       /* Execute unsaved sequence payload directly */
    CMD_EMERGENCY_STOP,         /* Immediate E-Stop halt & home all servos */
    CMD_ENTER_BLE_PAIRING,      /* Open 120-second BLE discovery/pairing window (3s hold) */
    CMD_SET_BUTTON_SEQUENCE,    /* Save custom sequence to button slot (1 to 4) over BLE */
    CMD_RESTORE_FACTORY_PRESETS,/* Restore Buttons 1-4 to factory default routines */
    CMD_JOG_MOTOR_ANGLE,        /* Live position jog (0° to 180°) for calibration */
    CMD_GET_TELEMETRY,          /* Request real-time status telemetry */
    CMD_SYNC_PRESETS,           /* Synchronize presets over wireless transport */
    CMD_STOP_SEQUENCE,          /* Cleanly stop active motion / exit calibration / clear E-Stop */
    CMD_IDENTIFY_ROBOT,         /* Trigger 3.0s visual locator LED pulse train */
    CMD_SET_TELEMETRY_STREAM,   /* Enable or disable periodic BLE telemetry streaming */
    CMD_CLEAR_BLE_BONDS         /* Erase all stored BLE bonds in NVS (B1+B4 5s hold) */
} cmd_type_t;

/* ========================================================================= */
/* Command Execution Status Codes                                            */
/* ========================================================================= */

typedef enum {
    CMD_STATUS_OK                = 0, /* Command accepted / completed cleanly */
    CMD_STATUS_ERR_BUSY          = 1, /* Motion active or conflicting state */
    CMD_STATUS_ERR_INVALID_STEP  = 2, /* Step count out of bounds (1-16) or empty preset */
    CMD_STATUS_ERR_MOTOR_BOUNDS  = 3, /* Motor count > 2 or channel ID > 15 */
    CMD_STATUS_ERR_ROUTINE_FULL  = 4, /* Routine exceeded maximum 16 steps */
    CMD_STATUS_ERR_CRC_MISMATCH  = 5, /* IEEE 802.3 CRC32 verification failed */
    CMD_STATUS_ERR_INVALID_ARG   = 6  /* Invalid preset ID (not 1-4) or malformed payload */
} cmd_status_t;

/* ========================================================================= */
/* Folding Routine, Step & Telemetry Packed Data Structures                  */
/* ========================================================================= */

/**
 * @brief Single folding step containing 1 or 2 simultaneous servo motions (3 bytes packed).
 */
typedef struct __attribute__((packed)) {
    uint8_t motor_count;                     /**< Number of active motors (1 or 2) */
    uint8_t motor_ids[MAX_MOTORS_PER_STEP];  /**< Zero-indexed servo IDs (0 to 15) */
} fold_step_t;

/**
 * @brief Complete folding routine sequence stored in NVS flash blob (53 bytes packed).
 */
typedef struct __attribute__((packed)) {
    uint8_t step_count;                       /**< Number of steps (1 to 16) */
    fold_step_t steps[MAX_STEPS_PER_ROUTINE]; /**< Array of sequence steps (48 bytes) */
    uint32_t checksum;                        /**< IEEE 802.3 CRC32 checksum (4 bytes, Little-Endian) */
} fold_routine_t;

/**
 * @brief Packed 31-byte real-time sequence progress & motor telemetry frame (FAB2).
 */
typedef struct __attribute__((packed)) {
    uint8_t system_state;                         /**< Active system_state_t */
    uint8_t led_state;                            /**< Active led_state_t */
    uint8_t active_button_id;                     /**< Active preset (1-4), or 0 if raw preview / idle */
    uint8_t current_step_idx;                     /**< Current step index (0 to 15) */
    uint8_t total_steps;                          /**< Total steps in active routine (0 to 16) */
    uint8_t step_progress_pct;                    /**< Current step completion percentage (0 to 100) */
    uint16_t elapsed_step_time_ms;                /**< Elapsed time in active step (ms, Little-Endian) */
    uint8_t channel_angles[TOTAL_SERVO_CHANNELS]; /**< Live angles for channels 0-15 (0 to 180 deg) */
    uint8_t last_cmd_status;                      /**< Result of last processed command (cmd_status_t) */
    uint16_t free_heap_kb;                        /**< Free internal SRAM in KB (Little-Endian) */
    int8_t ble_rssi_dbm;                          /**< Connected central RSSI in dBm (-128 if disconnected) */
    uint8_t error_code;                           /**< Fault bitmask (BIT0=I2C, BIT1=NVS, BIT2=ESTOP) */
    uint16_t sequence_counter;                    /**< Monotonically increasing frame counter (Little-Endian) */
} telemetry_packet_t;

/**
 * @brief Parameter payload for live motor angle jogging.
 */
typedef struct {
    uint8_t channel;    /**< Servo channel (0 to 15) */
    float angle_deg;    /**< Target angle (0.0° to 180.0°) */
} jog_param_t;

/**
 * @brief Parameter payload for assigning a custom sequence to a physical button slot (54 bytes packed).
 */
typedef struct __attribute__((packed)) {
    uint8_t preset_id;          /**< Target button slot (1 to 4) */
    fold_routine_t routine;     /**< Sequence payload to persist in NVS (53 bytes) */
} button_sync_param_t;

/**
 * @brief Polymorphic command payload union.
 */
typedef union {
    uint8_t preset_id;              /**< Preset ID (1 to 4) */
    fold_routine_t raw_routine;     /**< Direct routine sequence payload */
    button_sync_param_t button_sync;/**< Button preset update payload */
    jog_param_t jog_param;          /**< Single motor jog parameter */
    bool stream_enable;             /**< Telemetry stream enable/disable flag */
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
