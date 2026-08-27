#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

#include "config.h"
#include "command.h"
#include "led.h"
#include "buttons.h"

static int test_count = 0;
static int pass_count = 0;

#define TEST_ASSERT(cond, msg) do { \
    test_count++; \
    if (cond) { \
        pass_count++; \
        printf("  [PASS] %s\n", msg); \
    } else { \
        printf("  [FAIL] %s (Line %d)\n", msg, __LINE__); \
        assert(cond); \
    } \
} while(0)

/* ========================================================================= */
/* LED Engine Unit Tests                                                     */
/* ========================================================================= */

void test_led_patterns(void)
{
    printf("Testing Status LED pattern engine...\n");

    /* 1. Test LED_STATE_IDLE (Heartbeat: 100ms ON / 1900ms OFF) */
    led_set_state(LED_STATE_IDLE);
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "LED starts in LED_STATE_IDLE");
    TEST_ASSERT(led_get_current_level() == 1, "IDLE segment 0 starts HIGH (ON)");

    /* Step 50ms -> still HIGH */
    led_step_ms(50);
    TEST_ASSERT(led_get_current_level() == 1, "IDLE at 50ms is HIGH");

    /* Step 60ms (total 110ms) -> transitions to LOW */
    led_step_ms(60);
    TEST_ASSERT(led_get_current_level() == 0, "IDLE at 110ms transitions to LOW");

    /* Step 1800ms (total 1910ms) -> still LOW */
    led_step_ms(1800);
    TEST_ASSERT(led_get_current_level() == 0, "IDLE at 1910ms is LOW");

    /* Step 100ms (total 2010ms) -> wraps to HIGH */
    led_step_ms(100);
    TEST_ASSERT(led_get_current_level() == 1, "IDLE at 2010ms wraps to HIGH");

    /* 2. Test LED_STATE_RUNNING (Solid ON continuous) */
    led_set_state(LED_STATE_RUNNING);
    TEST_ASSERT(led_get_state() == LED_STATE_RUNNING, "LED state is LED_STATE_RUNNING");
    TEST_ASSERT(led_get_current_level() == 1, "RUNNING is HIGH");
    led_step_ms(5000);
    TEST_ASSERT(led_get_current_level() == 1, "RUNNING remains HIGH after 5 seconds");

    /* 3. Test LED_STATE_PROGRAMMING (Slow blink: 1000ms ON / 1000ms OFF) */
    led_set_state(LED_STATE_PROGRAMMING);
    TEST_ASSERT(led_get_state() == LED_STATE_PROGRAMMING, "LED state is LED_STATE_PROGRAMMING");
    TEST_ASSERT(led_get_current_level() == 1, "PROGRAMMING starts HIGH");
    led_step_ms(1000);
    TEST_ASSERT(led_get_current_level() == 0, "PROGRAMMING at 1000ms transitions to LOW");
    led_step_ms(1000);
    TEST_ASSERT(led_get_current_level() == 1, "PROGRAMMING at 2000ms wraps to HIGH");

    /* 4. Test LED_STATE_STEP_LOCKED (2 fast flashes 80ms ON/OFF -> returns to base PROGRAMMING) */
    led_set_state(LED_STATE_STEP_LOCKED);
    TEST_ASSERT(led_get_state() == LED_STATE_STEP_LOCKED, "LED state set to transient STEP_LOCKED");
    TEST_ASSERT(led_get_current_level() == 1, "Flash 1 ON");
    led_step_ms(80);
    TEST_ASSERT(led_get_current_level() == 0, "Flash 1 OFF");
    led_step_ms(80);
    TEST_ASSERT(led_get_current_level() == 1, "Flash 2 ON");
    led_step_ms(80);
    TEST_ASSERT(led_get_current_level() == 0, "Flash 2 OFF");
    led_step_ms(80);
    TEST_ASSERT(led_get_state() == LED_STATE_PROGRAMMING, "STEP_LOCKED reverted to base PROGRAMMING state");

    /* 5. Test LED_STATE_INPUT_ERROR (3 fast flashes 60ms ON/OFF -> returns to base PROGRAMMING) */
    led_set_state(LED_STATE_INPUT_ERROR);
    TEST_ASSERT(led_get_state() == LED_STATE_INPUT_ERROR, "LED state set to transient INPUT_ERROR");
    for (int i = 0; i < 3; i++) {
        TEST_ASSERT(led_get_current_level() == 1, "Error pulse ON");
        led_step_ms(60);
        TEST_ASSERT(led_get_current_level() == 0, "Error pulse OFF");
        led_step_ms(60);
    }
    TEST_ASSERT(led_get_state() == LED_STATE_PROGRAMMING, "INPUT_ERROR reverted to base PROGRAMMING state");

    /* 6. Test LED_STATE_SAVE_SUCCESS (Solid ON for 2000ms -> returns to IDLE) */
    led_set_state(LED_STATE_SAVE_SUCCESS);
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS, "LED state is SAVE_SUCCESS");
    TEST_ASSERT(led_get_current_level() == 1, "SAVE_SUCCESS is HIGH");
    led_step_ms(1990);
    TEST_ASSERT(led_get_state() == LED_STATE_SAVE_SUCCESS, "SAVE_SUCCESS still active at 1990ms");
    led_step_ms(20);
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "SAVE_SUCCESS completed and reverted to IDLE");

    /* 7. Test LED_STATE_ESTOP (5 rapid flashes 50ms ON/OFF -> returns to IDLE) */
    led_set_state(LED_STATE_RUNNING); /* Base = RUNNING */
    led_set_state(LED_STATE_ESTOP);
    TEST_ASSERT(led_get_state() == LED_STATE_ESTOP, "LED state is ESTOP");
    for (int i = 0; i < 5; i++) {
        TEST_ASSERT(led_get_current_level() == 1, "ESTOP pulse ON");
        led_step_ms(50);
        TEST_ASSERT(led_get_current_level() == 0, "ESTOP pulse OFF");
        led_step_ms(50);
    }
    TEST_ASSERT(led_get_state() == LED_STATE_IDLE, "ESTOP completed and safely reverted to IDLE");
}

/* ========================================================================= */
/* Button Debouncer & Gesture Unit Tests                                     */
/* ========================================================================= */

void test_button_debouncer(void)
{
    printf("Testing Button Debouncer and Filter logic...\n");

    buttons_reset_all();

    /* Initial state: all released (1) */
    for (int i = 0; i < BTN_ID_COUNT; i++) {
        TEST_ASSERT(buttons_get_stable_state(i) == 1, "Initial button state is RELEASED (1)");
    }

    /* Test 1: Noise glitch rejection (<50ms) */
    button_gesture_t g;
    /* Glitch goes LOW for 30ms then returns HIGH */
    g = buttons_update_channel(BTN_ID_1, 0, 10);
    TEST_ASSERT(g == GESTURE_NONE && buttons_get_stable_state(BTN_ID_1) == 1, "10ms glitch rejected");
    g = buttons_update_channel(BTN_ID_1, 0, 20);
    TEST_ASSERT(g == GESTURE_NONE && buttons_get_stable_state(BTN_ID_1) == 1, "30ms glitch rejected");
    g = buttons_update_channel(BTN_ID_1, 1, 10);
    TEST_ASSERT(g == GESTURE_NONE && buttons_get_stable_state(BTN_ID_1) == 1, "Glitch returned to 1, no state change");

    /* Test 2: Valid press transition (stable LOW for >= 50ms) */
    buttons_update_channel(BTN_ID_1, 0, 20);
    buttons_update_channel(BTN_ID_1, 0, 20);
    buttons_update_channel(BTN_ID_1, 0, 10); /* Total 50ms */
    TEST_ASSERT(buttons_get_stable_state(BTN_ID_1) == 0, "Stable 50ms LOW transitions button to PRESSED (0)");
}

void test_button_gestures(void)
{
    printf("Testing Button Gestures (Short Tap vs Long Press)...\n");

    buttons_reset_all();

    /* Test 1: Short Tap on B1 (<500ms press) */
    button_gesture_t g = GESTURE_NONE;
    /* Press button B1 (150ms hold) */
    buttons_update_channel(BTN_ID_1, 0, 50); /* Stable pressed at 50ms */
    buttons_update_channel(BTN_ID_1, 0, 100); /* +100ms (total press = 150ms) */
    /* Release button (needs 50ms debounce to register release) */
    buttons_update_channel(BTN_ID_1, 1, 20);
    buttons_update_channel(BTN_ID_1, 1, 20);
    g = buttons_update_channel(BTN_ID_1, 1, 10); /* +50ms release confirmed */
    TEST_ASSERT(g == GESTURE_SHORT_TAP, "B1 short press registered GESTURE_SHORT_TAP");

    /* Test 2: Short Tap on B2, B3, B4 */
    for (uint8_t btn = BTN_ID_2; btn <= BTN_ID_4; btn++) {
        buttons_update_channel(btn, 0, 50);
        buttons_update_channel(btn, 0, 150);
        g = buttons_update_channel(btn, 1, 50);
        TEST_ASSERT(g == GESTURE_SHORT_TAP, "Button short press registered GESTURE_SHORT_TAP");
    }

    /* Test 3: Long Press on B1 (>=3000ms hold) */
    buttons_reset_all();
    /* Press B1 */
    buttons_update_channel(BTN_ID_1, 0, 50); /* Stable pressed at 50ms */
    /* Hold for 2900ms more (total = 2950ms) -> should NOT trigger yet */
    g = buttons_update_channel(BTN_ID_1, 0, 2900);
    TEST_ASSERT(g == GESTURE_NONE, "B1 at 2950ms hold has not triggered long press yet");

    /* Hold for another 50ms (total = 3000ms) -> triggers immediately! */
    g = buttons_update_channel(BTN_ID_1, 0, 50);
    TEST_ASSERT(g == GESTURE_LONG_PRESS, "B1 at 3000ms hold triggered GESTURE_LONG_PRESS immediately");

    /* Continue holding for another 1000ms -> should not re-trigger */
    g = buttons_update_channel(BTN_ID_1, 0, 1000);
    TEST_ASSERT(g == GESTURE_NONE, "B1 continuing hold does not re-trigger long press");

    /* Release B1 -> should NOT trigger a Short Tap */
    buttons_update_channel(BTN_ID_1, 1, 50);
    g = buttons_update_channel(BTN_ID_1, 1, 10);
    TEST_ASSERT(g == GESTURE_NONE, "B1 release after long press produces zero trailing tap gesture");

    /* Test 4: Long Press on B4 */
    buttons_reset_all();
    buttons_update_channel(BTN_ID_4, 0, 50); /* Stable pressed */
    buttons_update_channel(BTN_ID_4, 0, 2900); /* Total 2900ms */
    g = buttons_update_channel(BTN_ID_4, 0, 100); /* Reaches 3000ms */
    TEST_ASSERT(g == GESTURE_LONG_PRESS, "B4 hold >=3000ms triggers GESTURE_LONG_PRESS");
    buttons_update_channel(BTN_ID_4, 1, 50);
    g = buttons_update_channel(BTN_ID_4, 1, 0);
    TEST_ASSERT(g == GESTURE_NONE, "B4 release produces no tap");
}

int main(void)
{
    printf("============================================================\n");
    printf(" Fabrica Firmware Phase 2 Unit Test: UI Subsystem\n");
    printf("============================================================\n");

    test_led_patterns();
    test_button_debouncer();
    test_button_gestures();

    printf("------------------------------------------------------------\n");
    printf(" Test Results: %d / %d checks passed (100%% Success)\n", pass_count, test_count);
    printf("============================================================\n");

    return 0;
}
