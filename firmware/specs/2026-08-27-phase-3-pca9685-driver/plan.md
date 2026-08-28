# Plan — Phase 3: I2C PCA9685 16-Channel PWM Servo Driver

## Overview

Phase 3 implements the hardware actuation subsystem for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. This subsystem provides the low-level I2C communication and 12-bit PWM servo motor control layer via the **PCA9685 16-Channel PWM Driver** (`main/pca9685.h`, `main/pca9685.c`), enabling precise angular control ($0^\circ \text{ to } 180^\circ$) across up to 16 high-torque MG996R servos driving the modular folding grid panels.

---

## Task Group 1: Low-Level I2C Master & PCA9685 Register Driver (`main/pca9685.h`, `main/pca9685.c`)
1. Create `firmware/main/pca9685.h`:
   - Define PCA9685 register addresses:
     - `PCA9685_REG_MODE1` (`0x00`): Mode register 1 (Restart, Auto-Increment, Sleep, AllCall).
     - `PCA9685_REG_MODE2` (`0x01`): Mode register 2 (Invert, Output change, OutDrv totem-pole).
     - `PCA9685_REG_SUBADR1`–`SUBADR3` (`0x02`–`0x04`): I2C sub-addresses.
     - `PCA9685_REG_ALLCALLADR` (`0x05`): All-call I2C address.
     - `PCA9685_REG_LED0_ON_L` (`0x06`): Channel 0 ON low byte.
     - `PCA9685_REG_LED0_ON_H` (`0x07`): Channel 0 ON high byte.
     - `PCA9685_REG_LED0_OFF_L` (`0x08`): Channel 0 OFF low byte.
     - `PCA9685_REG_LED0_OFF_H` (`0x09`): Channel 0 OFF high byte.
     - `PCA9685_REG_ALL_LED_ON_L` (`0xFA`): All channels ON low byte.
     - `PCA9685_REG_ALL_LED_ON_H` (`0xFB`): All channels ON high byte.
     - `PCA9685_REG_ALL_LED_OFF_L` (`0xFC`): All channels OFF low byte.
     - `PCA9685_REG_ALL_LED_OFF_H` (`0xFD`): All channels OFF high byte.
     - `PCA9685_REG_PRESCALE` (`0xFE`): Prescaler for PWM output frequency.
   - Define control bit masks:
     - `MODE1_RESTART` (`0x80`), `MODE1_EXTCLK` (`0x40`), `MODE1_AI` (`0x20`), `MODE1_SLEEP` (`0x10`), `MODE1_ALLCALL` (`0x01`).
     - `MODE2_INVRT` (`0x10`), `MODE2_OCH` (`0x08`), `MODE2_OUTDRV` (`0x04`), `MODE2_OUTNE_TP` (`0x01`).
   - Declare public API:
     - `esp_err_t pca9685_init(void)`: Configure ESP32 I2C Master peripheral on `GPIO 21 (SDA)` / `GPIO 22 (SCL)` at 100 kHz, wake PCA9685 from sleep, set 50 Hz PWM prescale (`121`), enable Auto-Increment, configure totem-pole output, and initialize FreeRTOS bus mutex.
     - `esp_err_t pca9685_probe(void)`: Check if PCA9685 responds at address `0x40`.
     - `esp_err_t pca9685_write_reg(uint8_t reg, uint8_t val)`: Thread-safe register write.
     - `esp_err_t pca9685_read_reg(uint8_t reg, uint8_t *val)`: Thread-safe register read.
     - `esp_err_t pca9685_sleep(bool enable)`: Put controller into low-power sleep or wake.
2. Implement `firmware/main/pca9685.c`:
   - Initialize ESP-IDF I2C master driver (`i2c_param_config()`, `i2c_driver_install()`) on `I2C_NUM_0`.
   - Implement thread-safe mutex wrapper (`xSemaphoreCreateMutex()`, `xSemaphoreTake()`, `xSemaphoreGive()`) around I2C bus transactions.
   - Implement prescale initialization sequence: put to sleep $\to$ write prescale register $\to$ clear sleep $\to$ delay 500 $\mu\text{s}$ for oscillator stabilization $\to$ set Auto-Increment and restart bit.

---

## Task Group 2: Angle-to-PWM Translation & Multi-Channel Commands (`main/pca9685.h`, `main/pca9685.c`)
1. Extend `firmware/main/pca9685.h`:
   - Declare PWM and angle control API:
     - `esp_err_t pca9685_set_pwm(uint8_t channel, uint16_t on_count, uint16_t off_count)`: Set 12-bit ON/OFF counts for a specific channel (0–15).
     - `esp_err_t pca9685_set_all_pwm(uint16_t on_count, uint16_t off_count)`: Broadcast ON/OFF counts to all 16 channels simultaneously using `ALL_LED` registers.
     - `esp_err_t pca9685_set_servo_angle(uint8_t channel, float angle_deg)`: Convert degrees ($0.0^\circ \text{ to } 180.0^\circ$) to 12-bit pulse count and update single channel.
     - `esp_err_t pca9685_set_multi_servo_angles(uint16_t channel_mask, float angle_deg)`: Update multiple channels synchronously based on a 16-bit bitmask (`bit 0` = channel 0, `bit 15` = channel 15).
     - `uint16_t pca9685_angle_to_counts(float angle_deg)`: Pure conversion helper mapping degrees to 12-bit off-counts.
   - Declare motion and staging helper functions:
     - `esp_err_t pca9685_home_all(void)`: Set all 16 channels to $0.0^\circ$ (flat home position).
     - `esp_err_t pca9685_nudge_channel(uint8_t channel)`: Pulse target channel to $15.0^\circ$ for physical motor identification.
     - `esp_err_t pca9685_stage_channel(uint8_t channel)`: Set target channel to $30.0^\circ$ for visual staging hold.
2. Implement conversion math and command routines in `firmware/main/pca9685.c`:
   - Enforce angle clamping ($0.0^\circ \le \text{angle} \le 180.0^\circ$) and channel range checks ($0 \le \text{channel} < 16$).
   - Implement precise 12-bit count conversion formula:
     $$\text{Pulse}(\mu\text{s}) = \text{SERVO\_MIN\_PULSE\_US} + \frac{\text{angle}}{180.0} \times (\text{SERVO\_MAX\_PULSE\_US} - \text{SERVO\_MIN\_PULSE\_US})$$
     $$\text{Count} = \text{round}\left( \frac{\text{Pulse}(\mu\text{s}) \times 4096}{20000} \right)$$
   - Zero out ON counts (`on_count = 0`) and assign calculated value to `off_count` for standard leading-edge aligned 50 Hz PWM.

---

## Task Group 3: System Startup Integration & Hardware Diagnostics (`main.c`, `CMakeLists.txt`)
1. Update `firmware/main/CMakeLists.txt`:
   - Add `pca9685.c` to the component source registration list (`SRCS`).
2. Update `firmware/main/main.c`:
   - In `app_main()`:
     - Call `pca9685_init()` during hardware initialization.
     - Perform I2C bus probe (`pca9685_probe()`) and log detection status via `ESP_LOGI`.
     - Execute `pca9685_home_all()` to ensure all 16 folding panels reset flat to $0^\circ$ on boot.
     - Add diagnostic servo sweep or channel test in response to command queue events.

---

## Task Group 4: Host Verification Test Harness & Hardware Validation (`test/test_pca9685.c`, `Makefile`)
1. Create `firmware/test/test_pca9685.c`:
   - Implement a host-compilable C test harness with mocked I2C bus registers:
     - Validate `pca9685_init()` register sequence: `MODE1` sleep, `PRESCALE` write (`121`), `MODE1` wake & AI enable, `MODE2` totem-pole configuration.
     - Validate `pca9685_angle_to_counts()` across full range:
       - $0.0^\circ \to 102$ counts ($500\ \mu\text{s}$)
       - $15.0^\circ \to 137$ counts ($667\ \mu\text{s}$)
       - $30.0^\circ \to 171$ counts ($833\ \mu\text{s}$)
       - $90.0^\circ \to 307$ counts ($1500\ \mu\text{s}$)
       - $180.0^\circ \to 512$ counts ($2500\ \mu\text{s}$)
     - Validate input clamping on out-of-range angles (e.g. $-20.0^\circ \to 102$ counts, $250.0^\circ \to 512$ counts).
     - Validate channel validation rejecting channel index $\ge 16$.
     - Validate multi-channel bitmask command updating only the flagged channels.
     - Validate `pca9685_home_all()`, `pca9685_nudge_channel()`, and `pca9685_stage_channel()`.
2. Update `firmware/Makefile`:
   - Add `test_pca9685` executable build and execution to the `make test` recipe.
3. Validate ESP-IDF build:
   - Run `idf.py build` to ensure 0 compiler warnings and 0 errors.
