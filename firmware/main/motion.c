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
/* Total active step duration for telemetry progress calculation (~2800 ms) */
#define STEP_TARGET_DURATION_MS      (FOLD_DWELL_TIME_MS + LANDING_APPROACH_MS)

static volatile uint32_t s_step_target_duration_ms = STEP_TARGET_DURATION_MS;

static EventGroupHandle_t s_evt_group_handle = NULL;

/* Host testing simulated time tracking */
#ifndef ESP_PLATFORM
static uint32_t s_simulated_elapsed_ms = 0;
#endif

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
#else
        s_simulated_elapsed_ms += slice_ms;
#endif
        remaining_ms -= slice_ms;
        s_active_elapsed_ms += (uint16_t)slice_ms;
        if (s_step_target_duration_ms > 0) {
            uint32_t pct = ((uint32_t)s_active_elapsed_ms * 100U) / s_step_target_duration_ms;
            s_active_progress_pct = (uint8_t)(pct > 100U ? 100U : pct);
        }
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
    s_step_target_duration_ms = STEP_TARGET_DURATION_MS;
#ifndef ESP_PLATFORM
    s_simulated_elapsed_ms = 0;
#endif
#ifdef ESP_PLATFORM
    if (s_evt_group_handle != NULL) {
        xEventGroupClearBits(s_evt_group_handle,
                             MOTION_EVENT_START_BIT | MOTION_EVENT_ESTOP_BIT | MOTION_EVENT_COMPLETE_BIT);
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
    return (s_motion_status == MOTION_STATUS_RUNNING ||
            s_motion_status == MOTION_STATUS_STOPPING);
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
 * @brief Step through an array of target angles at fixed frame delay, checking for E-Stop.
 * @return true if aborted by E-Stop, false if completed cleanly.
 */
static bool execute_angle_table(const fold_step_t *step,
                                const uint8_t *angles,
                                size_t count,
                                uint32_t frame_delay_ms)
{
    for (size_t i = 0; i < count; i++) {
        set_step_servo_angle(step, (float)angles[i]);
        if (motion_delay_ms(frame_delay_ms, true)) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Sweep linearly from start_deg to end_deg (inclusive) in step_deg increments.
 * @return true if aborted by E-Stop, false if completed cleanly.
 */
static bool execute_linear_sweep(const fold_step_t *step,
                                 int32_t start_deg,
                                 int32_t end_deg,
                                 int32_t step_deg,
                                 uint32_t frame_delay_ms)
{
    for (int32_t a = start_deg;
         (step_deg > 0) ? (a <= end_deg) : (a >= end_deg);
         a += step_deg) {
        set_step_servo_angle(step, (float)a);
        if (motion_delay_ms(frame_delay_ms, true)) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Execute a single folding step (single servo or parallel dual servos).
 *
 * Articulation Profile (Balance-Point Braked 5-Phase S-Curve, 0° -> 150° -> 0°, ~2800ms):
 *   1. Soft Start Coupler Take-Up: 0° -> 24° (8 frames @ 25ms = 200ms)
 *   2. Controlled Climb to Vertical: 28° -> 84° (+4° steps @ 25ms = 375ms, 160°/s)
 *   3. Early Balance-Point Brake & Hold: 87° -> 150° (+3° steps @ 25ms = 550ms) + 250ms hold
 *   4. Return Coupler Take-Up & Climb: 148° -> 136° (6 frames @ 25ms = 150ms) + 132° -> 80° (-4° @ 25ms = 350ms)
 *   5. Early Gravity-Braked Descent & Landing: 78° -> 20° (-2° @ 25ms = 750ms, 80°/s) + 16° -> 0° (8 frames @ 25ms = 200ms)
 *
 * @param step Pointer to fold_step_t containing motor count and channel IDs.
 * @return ESP_OK on success, ESP_ERR_TIMEOUT if aborted by E-Stop, or ESP_ERR_INVALID_ARG.
 */
esp_err_t motion_execute_step(const fold_step_t *step)
{
    static const uint8_t s_soft_start_angles[] = { 2, 4, 7, 10, 13, 16, 20, 24 };
    static const uint8_t s_return_start_angles[] = { 148, 146, 144, 142, 139, 136 };
    static const uint8_t s_bottom_landing_angles[] = { 16, 13, 10, 7, 5, 3, 1, 0 };

    if (step == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (step->motor_count < 1 || step->motor_count > MAX_MOTORS_PER_STEP) {
#ifdef ESP_PLATFORM
        ESP_LOGE(TAG, "Invalid motor count: %d (Max: %d)", step->motor_count, MAX_MOTORS_PER_STEP);
#endif
        return ESP_ERR_INVALID_ARG;
    }

    for (uint8_t i = 0; i < step->motor_count; i++) {
        if (step->motor_ids[i] >= TOTAL_SERVO_CHANNELS) {
#ifdef ESP_PLATFORM
            ESP_LOGE(TAG, "Invalid servo channel ID: %d (Max: %d)", step->motor_ids[i], TOTAL_SERVO_CHANNELS - 1);
#endif
            return ESP_ERR_INVALID_ARG;
        }
    }

    if (is_abort_signaled()) {
        return ESP_ERR_TIMEOUT;
    }

#ifdef ESP_PLATFORM
    if (step->motor_count == 1) {
        ESP_LOGI(TAG, "Executing single S-curve step on Channel %d (0 -> %.0f -> 0 deg)",
                 step->motor_ids[0], FOLD_TARGET_ANGLE_DEG);
    } else {
        ESP_LOGI(TAG, "Executing parallel S-curve step on Channels %d & %d (0 -> %.0f -> 0 deg)",
                 step->motor_ids[0], step->motor_ids[1], FOLD_TARGET_ANGLE_DEG);
    }
#endif

    /* Phase 1: Soft Start Coupler Slack Take-Up (0° -> 24°, 200ms) */
    if (execute_angle_table(step, s_soft_start_angles, sizeof(s_soft_start_angles), SCURVE_FRAME_MS)) {
        goto abort_step;
    }

    /* Phase 2: Controlled Climb to Vertical (28° -> 84°, +4° @ 25ms = 375ms) */
    if (execute_linear_sweep(step, 28, 84, (int32_t)SCURVE_CRUISE_STEP_DEG, SCURVE_FRAME_MS)) {
        goto abort_step;
    }

    /* Phase 3: Early Balance-Point Flip & Top Gravity Brake (87° -> 150°, +3° @ 25ms) + Top Settle Hold (250ms) */
    if (execute_linear_sweep(step, 87, (int32_t)FOLD_TARGET_ANGLE_DEG, 3, SCURVE_BRAKE_FRAME_MS)) {
        goto abort_step;
    }
    if (motion_delay_ms(FOLD_TOP_HOLD_MS, true)) {
        goto abort_step;
    }

    /* Phase 4: Return Coupler Slack Take-Up (148° -> 136°, 150ms) & Climb to Balance Point (132° -> 80°, 350ms) */
    if (execute_angle_table(step, s_return_start_angles, sizeof(s_return_start_angles), SCURVE_FRAME_MS)) {
        goto abort_step;
    }
    if (execute_linear_sweep(step, 132, 80, -(int32_t)SCURVE_CRUISE_STEP_DEG, SCURVE_FRAME_MS)) {
        goto abort_step;
    }

    /* Phase 5: Early Gravity-Braked Descent (78° -> 20°, -2° @ 25ms = 750ms) & Soft Table Touch-Down (16° -> 0°, 200ms) */
    if (execute_linear_sweep(step, 78, 20, -2, SCURVE_BRAKE_FRAME_MS)) {
        goto abort_step;
    }
    if (execute_angle_table(step, s_bottom_landing_angles, sizeof(s_bottom_landing_angles), SCURVE_BRAKE_FRAME_MS)) {
        goto abort_step;
    }

    set_step_servo_angle(step, HOME_ANGLE_DEG);
    return ESP_OK;

abort_step:
#ifdef ESP_PLATFORM
    ESP_LOGW(TAG, "E-Stop triggered during S-curve step! Aborting step.");
#endif
    pca9685_home_all();
    s_motion_status = MOTION_STATUS_ABORTED;
    return ESP_ERR_TIMEOUT;
}

/**
 * @brief Execute a complete multi-step folding routine sequentially.
 *
 * Iterates through all steps, applying an inter-step settling delay of 200ms
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
        xEventGroupClearBits(s_evt_group_handle,
                             MOTION_EVENT_START_BIT | MOTION_EVENT_ESTOP_BIT | MOTION_EVENT_COMPLETE_BIT);
    }
#endif
    s_motion_status = MOTION_STATUS_RUNNING;
    led_set_state(LED_STATE_RUNNING);

    s_active_total_steps = routine->step_count;
    s_active_step_idx = 0;
    s_active_elapsed_ms = 0;
    s_active_progress_pct = 0;
    s_step_target_duration_ms = STEP_TARGET_DURATION_MS;

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Starting routine execution (%d steps total)...", routine->step_count);
#endif

    for (uint8_t i = 0; i < routine->step_count; i++) {
        s_active_step_idx = i;
        s_active_elapsed_ms = 0;
        s_active_progress_pct = 0;
        s_step_target_duration_ms = STEP_TARGET_DURATION_MS;

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

        /* Inter-step settling delay (200ms) between consecutive steps */
        if (i < (routine->step_count - 1)) {
            s_step_target_duration_ms = 0;
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
    s_step_target_duration_ms = STEP_TARGET_DURATION_MS;
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
