#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "pca9685.h"
#include "storage.h"
#include "motion.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_log.h"

static const char *TAG = "FABRICA_MOTION";
#endif

/* ========================================================================= */
/* Motion Engine Internal State                                              */
/* ========================================================================= */

static volatile motion_status_t s_motion_status = MOTION_STATUS_IDLE;
static volatile bool s_abort_requested = false;

static volatile uint8_t s_active_step_idx = 0;
static volatile uint8_t s_active_total_steps = 0;
static volatile uint16_t s_active_elapsed_ms = 0;
static volatile uint8_t s_active_progress_pct = 0;
/* Total active step duration for telemetry progress calculation (900 + 600 + 500 = 2000 ms) */
#define LANDING_RAMP_FRAMES          (LANDING_RAMP_MS / LANDING_STEP_MS)
#define STEP_TARGET_DURATION_MS      (FOLD_FORWARD_SWEEP_MS + LANDING_APPROACH_MS + LANDING_RAMP_MS)

static EventGroupHandle_t s_evt_group_handle = NULL;

/* ========================================================================= */
/* Internal Helper Functions                                                 */
/* ========================================================================= */

/**
 * @brief Check if an emergency abort has been signaled.
 */
static inline bool is_abort_signaled(void)
{
    if (s_abort_requested) {
        return true;
    }
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        EventBits_t bits = xEventGroupGetBits(s_evt_group_handle);
        if (bits & MOTION_EVENT_ESTOP_BIT) {
            s_abort_requested = true;
            return true;
        }
    }
#endif
    return false;
}

/**
 * @brief Delay for a given duration with low-latency abort polling (10ms slices).
 * @param duration_ms Delay time in milliseconds.
 * @param poll_abort If true, poll abort flag every 10ms.
 * @return true if aborted during delay, false if completed full duration.
 */
static bool motion_delay_ms(uint32_t duration_ms, bool poll_abort)
{
    uint32_t remaining_ms = duration_ms;

    while (remaining_ms > 0) {
        if (poll_abort && is_abort_signaled()) {
            return true;
        }

        uint32_t slice_ms = (remaining_ms >= MOTION_ABORT_CHECK_MS) ?
                            MOTION_ABORT_CHECK_MS : remaining_ms;

#ifdef ESP_PLATFORM
        vTaskDelay(pdMS_TO_TICKS(slice_ms));
#endif
        remaining_ms -= slice_ms;
        s_active_elapsed_ms += (uint16_t)slice_ms;
        uint32_t pct = ((uint32_t)s_active_elapsed_ms * 100U) / STEP_TARGET_DURATION_MS;
        s_active_progress_pct = (uint8_t)(pct > 100U ? 100U : pct);
    }

    if (poll_abort && is_abort_signaled()) {
        return true;
    }

    return false;
}

/* ========================================================================= */
/* Public Lifecycle and Status APIs                                          */
/* ========================================================================= */

/**
 * @brief Reset motion engine internal state, flags, and event bits to IDLE.
 */
void motion_reset_state(void)
{
    s_motion_status = MOTION_STATUS_IDLE;
    s_abort_requested = false;
    s_active_step_idx = 0;
    s_active_total_steps = 0;
    s_active_elapsed_ms = 0;
    s_active_progress_pct = 0;
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupClearBits(s_evt_group_handle, MOTION_EVENT_ESTOP_BIT);
    }
#endif
}

#ifndef ESP_PLATFORM
void motion_mock_set_status(motion_status_t status)
{
    s_motion_status = status;
}

void motion_mock_set_progress(uint8_t step_idx,
                              uint8_t total_steps,
                              uint8_t progress_pct,
                              uint16_t elapsed_ms)
{
    s_active_step_idx = step_idx;
    s_active_total_steps = total_steps;
    s_active_progress_pct = progress_pct;
    s_active_elapsed_ms = elapsed_ms;
}
#endif

void motion_get_progress(uint8_t *out_step_idx,
                         uint8_t *out_total_steps,
                         uint8_t *out_progress_pct,
                         uint16_t *out_elapsed_ms)
{
    if (out_step_idx != NULL) {
        *out_step_idx = s_active_step_idx;
    }
    if (out_total_steps != NULL) {
        *out_total_steps = s_active_total_steps;
    }
    if (out_progress_pct != NULL) {
        *out_progress_pct = s_active_progress_pct;
    }
    if (out_elapsed_ms != NULL) {
        *out_elapsed_ms = s_active_elapsed_ms;
    }
}

/**
 * @brief Query current motion engine execution status.
 *
 * @return Active motion_status_t enum.
 */
motion_status_t motion_get_status(void)
{
    return s_motion_status;
}

/**
 * @brief Check if motion engine is actively articulating servos.
 *
 * @return true if running or stopping, false if idle or aborted.
 */
bool motion_is_busy(void)
{
    return (s_motion_status == MOTION_STATUS_RUNNING);
}

/* ========================================================================= */
/* Step & Routine Articulation Engines                                       */
/* ========================================================================= */

/**
 * @brief Command all motors in a fold step to a target angle.
 */
static void set_step_servo_angle(const fold_step_t *step, float angle_deg)
{
    if (step->motor_count == 1) {
        pca9685_set_servo_angle(step->motor_ids[0], angle_deg);
    } else {
        uint16_t mask = (1U << step->motor_ids[0]) | (1U << step->motor_ids[1]);
        pca9685_set_multi_servo_angles(mask, angle_deg);
    }
}

/**
 * @brief Validate a fold step's motor count and servo channel bounds.
 */
static bool is_step_valid(const fold_step_t *step)
{
    if (step == NULL || step->motor_count < 1 || step->motor_count > MAX_MOTORS_PER_STEP) {
        return false;
    }
    for (uint8_t i = 0; i < step->motor_count; i++) {
        if (step->motor_ids[i] >= TOTAL_SERVO_CHANNELS) {
            return false;
        }
    }
    return true;
}

/**
 * @brief Execute a single folding step (single servo or parallel dual servos).
 *
 * Articulation Profile (Direct Fold + Mid-Air Brake @ 30° + Linear Landing, 0° -> 165° -> 30° -> 0°, 2000ms):
 *   1. Direct Forward Sweep: 0° -> 165° (900ms)
 *   2. Return & Brake Hold: 165° -> 30° (600ms)
 *   3. Linear Soft-Landing: 30° -> 0° (25 frames x 20ms = 500ms, -1.2°/frame, 60°/s)
 *
 * @param step Pointer to fold_step_t containing motor count and channel IDs.
 * @return ESP_OK on success, ESP_ERR_TIMEOUT if aborted by E-Stop, or ESP_ERR_INVALID_ARG.
 */
esp_err_t motion_execute_step(const fold_step_t *step)
{
    if (!is_step_valid(step)) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Invalid fold step parameters.");
#endif
        return ESP_ERR_INVALID_ARG;
    }

    if (is_abort_signaled()) {
        return ESP_ERR_TIMEOUT;
    }

#ifdef ESP_PLATFORM
    if (step->motor_count == 1) {
        ESP_LOGI(TAG, "Executing single step on Channel %d (0 -> %.0f -> 0 deg)",
                 step->motor_ids[0], FOLD_TARGET_ANGLE_DEG);
    } else {
        ESP_LOGI(TAG, "Executing parallel step on Channels %d & %d (0 -> %.0f -> 0 deg)",
                 step->motor_ids[0], step->motor_ids[1], FOLD_TARGET_ANGLE_DEG);
    }
#endif

    /* 1. Direct Forward Sweep (0° -> 165°, 900ms) */
#ifdef ESP_PLATFORM
    ESP_LOGD(TAG, "[Phase 1] Forward 0 -> %.0f deg (%dms)",
             FOLD_TARGET_ANGLE_DEG, FOLD_FORWARD_SWEEP_MS);
#endif
    set_step_servo_angle(step, FOLD_TARGET_ANGLE_DEG);
    if (motion_delay_ms(FOLD_FORWARD_SWEEP_MS, true)) {
        goto abort_step;
    }

    /* 2. Return & Mid-Air Brake Hold at 30° (165° -> 30°, 600ms to kill momentum) */
#ifdef ESP_PLATFORM
    ESP_LOGD(TAG, "[Phase 2] Return & brake -> %.0f deg (%dms)",
             LANDING_START_ANGLE_DEG, LANDING_APPROACH_MS);
#endif
    set_step_servo_angle(step, LANDING_START_ANGLE_DEG);
    if (motion_delay_ms(LANDING_APPROACH_MS, true)) {
        goto abort_step;
    }

    /* 3. Linear Soft-Landing (30° -> 0°, 25 frames x 20ms = 500ms, 60°/s) */
#ifdef ESP_PLATFORM
    ESP_LOGD(TAG, "[Phase 3] Soft-landing %.0f -> 0 deg (%dms, %lu frames)",
             LANDING_START_ANGLE_DEG, LANDING_RAMP_MS, (unsigned long)LANDING_RAMP_FRAMES);
#endif
    for (uint32_t frame = 1; frame <= LANDING_RAMP_FRAMES; frame++) {
        float angle = LANDING_START_ANGLE_DEG * (1.0f - ((float)frame / (float)LANDING_RAMP_FRAMES));
        set_step_servo_angle(step, angle);
        if (motion_delay_ms(LANDING_STEP_MS, true)) {
            goto abort_step;
        }
    }

    return ESP_OK;

abort_step:
#ifdef ESP_PLATFORM
    ESP_LOGW(TAG, "E-Stop triggered during fold step! Aborting step.");
#endif
    pca9685_home_all();
    s_motion_status = MOTION_STATUS_ABORTED;
    return ESP_ERR_TIMEOUT;
}

/**
 * @brief Execute a complete multi-step folding routine sequentially.
 *
 * Iterates through all steps, applying an inter-step settling delay of 10ms
 * between steps. Checks for E-Stop abort before and during every motion step.
 * On completion, homes all channels and returns LED to IDLE.
 *
 * @param routine Pointer to fold_routine_t structure.
 * @return ESP_OK on success, ESP_ERR_TIMEOUT on E-Stop, or ESP error code.
 */
esp_err_t motion_execute_routine(const fold_routine_t *routine)
{
    if (routine == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (routine->step_count == 0) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Refusing execution: routine contains 0 steps.");
#endif
        led_set_state(LED_STATE_INPUT_ERROR);
        return ESP_ERR_INVALID_STATE;
    }

    if (routine->step_count > MAX_STEPS_PER_ROUTINE) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Routine step count %d exceeds MAX_STEPS_PER_ROUTINE (%d)",
                 routine->step_count, MAX_STEPS_PER_ROUTINE);
#endif
        return ESP_ERR_INVALID_ARG;
    }

    if (motion_is_busy()) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Motion engine is busy, rejecting new routine execution.");
#endif
        return ESP_ERR_INVALID_STATE;
    }

    s_abort_requested = false;
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupClearBits(s_evt_group_handle, MOTION_EVENT_ESTOP_BIT);
    }
#endif
    s_motion_status = MOTION_STATUS_RUNNING;
    led_set_state(LED_STATE_RUNNING);

    s_active_total_steps = routine->step_count;
    s_active_step_idx = 0;
    s_active_elapsed_ms = 0;
    s_active_progress_pct = 0;

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Starting routine execution (%d steps total)...", routine->step_count);
#endif

    for (uint8_t i = 0; i < routine->step_count; i++) {
        s_active_step_idx = i;
        s_active_elapsed_ms = 0;
        s_active_progress_pct = 0;

        if (is_abort_signaled()) {
#ifdef ESP_PLATFORM
            ESP_LOGW(TAG, "E-Stop detected before step %d! Halting routine.", i + 1);
#endif
            pca9685_home_all();
            s_motion_status = MOTION_STATUS_ABORTED;
            s_active_step_idx = 0;
            s_active_total_steps = 0;
            s_active_elapsed_ms = 0;
            s_active_progress_pct = 0;
            led_set_state(LED_STATE_ESTOP);
            return ESP_ERR_TIMEOUT;
        }

#ifdef ESP_PLATFORM
        ESP_LOGI(TAG, "--- Step %d / %d ---", i + 1, routine->step_count);
#endif
        esp_err_t step_err = motion_execute_step(&routine->steps[i]);
        if (step_err != ESP_OK) {
            pca9685_home_all();
            s_motion_status = MOTION_STATUS_ABORTED;
            s_active_step_idx = 0;
            s_active_total_steps = 0;
            s_active_elapsed_ms = 0;
            s_active_progress_pct = 0;
            if (step_err == ESP_ERR_TIMEOUT) {
                led_set_state(LED_STATE_ESTOP);
            } else {
                led_set_state(LED_STATE_INPUT_ERROR);
            }
            return step_err;
        }

        /* Inter-step settling delay (10ms) between consecutive steps */
        if (i < (routine->step_count - 1U)) {
            s_active_progress_pct = 100U;
            if (motion_delay_ms(INTER_STEP_DELAY_MS, true)) {
#ifdef ESP_PLATFORM
                ESP_LOGW(TAG, "E-Stop triggered during inter-step settling! Aborting routine.");
#endif
                pca9685_home_all();
                s_motion_status = MOTION_STATUS_ABORTED;
                s_active_step_idx = 0;
                s_active_total_steps = 0;
                s_active_elapsed_ms = 0;
                s_active_progress_pct = 0;
                led_set_state(LED_STATE_ESTOP);
                return ESP_ERR_TIMEOUT;
            }
        }
    }

    /* Clean completion */
    pca9685_home_all();
    s_motion_status = MOTION_STATUS_IDLE;
    s_active_step_idx = 0;
    s_active_total_steps = 0;
    s_active_elapsed_ms = 0;
    s_active_progress_pct = 0;
    led_set_state(LED_STATE_IDLE);

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Routine execution completed successfully. All channels homed.");
#endif

    return ESP_OK;
}

/**
 * @brief Load a preset routine from NVS storage and trigger Daily Run Mode execution.
 *
 * @param preset_id Target preset ID (1 to 4).
 * @return ESP_OK on success, or an ESP-IDF error code.
 */
esp_err_t motion_trigger_preset(uint8_t preset_id)
{
    if (preset_id < 1 || preset_id > TOTAL_PRESET_COUNT) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Invalid preset ID %d (Valid range: 1 to %d)", preset_id, TOTAL_PRESET_COUNT);
#endif
        return ESP_ERR_INVALID_ARG;
    }

    fold_routine_t routine;
    memset(&routine, 0, sizeof(routine));

    esp_err_t load_err = storage_load_routine(preset_id, &routine);
    if (load_err != ESP_OK) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Failed to load Preset %d from storage: %s", preset_id, esp_err_to_name(load_err));
#endif
        led_set_state(LED_STATE_INPUT_ERROR);
        return load_err;
    }

    if (routine.step_count == 0) {
#ifdef ESP_PLATFORM
        ESP_LOGW(TAG, "Preset %d is empty (0 steps). Flashing error feedback.", preset_id);
#endif
        led_set_state(LED_STATE_INPUT_ERROR);
        return ESP_ERR_INVALID_STATE;
    }

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Triggered Daily Run Mode for Preset %d (%d steps)", preset_id, routine.step_count);
#endif

    return motion_execute_routine(&routine);
}

/**
 * @brief Immediately halt active motion, set abort flags, home servos, and flash LED.
 *
 * @return ESP_OK on success.
 */
esp_err_t motion_emergency_stop(void)
{
    s_abort_requested = true;
    s_motion_status = MOTION_STATUS_ABORTED;

#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupSetBits(s_evt_group_handle, MOTION_EVENT_ESTOP_BIT);
    }
    ESP_LOGW(TAG, "EMERGENCY STOP (E-Stop) triggered! Halting PWM & homing all servos.");
#endif

    /* Cut active motion immediately and home all 16 channels */
    pca9685_home_all();

    /* Trigger 5 rapid flashes */
    led_set_state(LED_STATE_ESTOP);

    return ESP_OK;
}

/* ========================================================================= */
/* Motion Engine Initialization                                              */
/* ========================================================================= */

/**
 * @brief Initialize the Real-Time Motion Engine and bind system event group.
 *
 * @param evt_group Handle to the system event group for E-Stop monitoring.
 * @return ESP_OK on success.
 */
esp_err_t motion_init(EventGroupHandle_t evt_group)
{
#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Initializing Real-Time Motion Engine on Core 0...");
#endif
    s_evt_group_handle = evt_group;
    motion_reset_state();

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Real-Time Motion Engine initialized successfully on Core 0.");
#endif
    return ESP_OK;
}
