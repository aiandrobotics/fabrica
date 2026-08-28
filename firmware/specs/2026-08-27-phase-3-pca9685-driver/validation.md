# Validation — Phase 3: I2C PCA9685 16-Channel PWM Servo Driver

## Required Checks

### 1. Host-Based Unit Test Suite (`firmware/test/test_pca9685.c`)
- [ ] Compile and execute host test harness using GCC or Clang:
  ```bash
  gcc -Wall -Wextra -Werror -I./firmware/main -o /tmp/test_pca9685 firmware/test/test_pca9685.c && /tmp/test_pca9685
  ```
- [ ] **Angle to 12-Bit PWM Conversion Formula Validation**:
  - Test $0.0^\circ \implies 102$ counts ($500\,\mu\text{s}$).
  - Test $15.0^\circ \implies 137$ counts ($667\,\mu\text{s}$).
  - Test $30.0^\circ \implies 171$ counts ($833\,\mu\text{s}$).
  - Test $45.0^\circ \implies 205$ counts ($1000\,\mu\text{s}$).
  - Test $90.0^\circ \implies 307$ counts ($1500\,\mu\text{s}$).
  - Test $135.0^\circ \implies 410$ counts ($2000\,\mu\text{s}$).
  - Test $180.0^\circ \implies 512$ counts ($2500\,\mu\text{s}$).
- [ ] **Input Bounds Clamping & Validation**:
  - Test negative angles (e.g., $-45.0^\circ$) clamp correctly to $0.0^\circ$ ($102$ counts).
  - Test excessive angles (e.g., $240.0^\circ$) clamp correctly to $180.0^\circ$ ($512$ counts).
  - Test invalid channel numbers (channel $\ge 16$) return `ESP_ERR_INVALID_ARG`.
- [ ] **PCA9685 Register Initialization Sequence**:
  - Verify initialization writes `MODE1_SLEEP` (`0x10`) to register `0x00`.
  - Verify prescale calculation writes `121` (`0x79`) to register `0xFE`.
  - Verify oscillator wake write `0x20` (`MODE1_AI`) to register `0x00`.
  - Verify totem-pole output configuration writes `0x04` (`MODE2_OUTDRV`) to register `0x01`.
- [ ] **Multi-Channel & Batch Command Validation**:
  - Verify `pca9685_set_multi_servo_angles()` updates exactly the channels enabled in bitmask.
  - Verify `pca9685_home_all()` broadcasts $102$ counts to all 16 channels.
  - Verify `pca9685_nudge_channel()` targets the specified channel with $137$ counts.
  - Verify `pca9685_stage_channel()` targets the specified channel with $171$ counts.

### 2. ESP-IDF Build & Compilation Verification
- [ ] Confirm `main/CMakeLists.txt` registers `pca9685.c`.
- [ ] Execute clean ESP-IDF project compilation:
  ```bash
  idf.py build
  ```
- [ ] Verify compilation completes with **0 warnings** and **0 errors** under `-Wall -Wextra`.
- [ ] Confirm DRAM allocation maintains $\ge 120\text{ KB}$ free heap headroom.

### 3. Integrated Makefile Test Suite
- [ ] Run automated host test suite across all modules:
  ```bash
  make test
  ```
- [ ] Confirm `test_headers`, `test_ui_subsystem`, and `test_pca9685` all pass with 100% success rate.

---

## Manual Review & Hardware Bench Verification

### 1. Serial Monitor I2C Probe Diagnostics
- [ ] Flash ESP32 Dev Board and open serial monitor:
  ```bash
  idf.py flash monitor
  ```
- [ ] Verify serial startup logs confirm successful I2C bus initialization and PCA9685 communication:
  ```text
  [I2C] Initialized I2C Master on SDA: GPIO 21, SCL: GPIO 22 @ 100 kHz
  [PCA9685] PCA9685 detected at I2C address 0x40
  [PCA9685] Prescaler set to 121 (50 Hz PWM)
  [PCA9685] All 16 channels initialized to home position (0 deg / 102 counts)
  ```

### 2. Physical Servo Motor & PWM Verification
- [ ] Connect MG996R servo to Channel 0 and external 5V/6V servo power supply.
- [ ] Verify Channel 0 servo rests quietly at flat home position ($0^\circ$).
- [ ] Trigger test nudge / staging commands and observe physical flap displacement ($15^\circ$ nudge, $30^\circ$ staging hold) with zero jitter or stalling.
- [ ] (Optional) Measure Channel 0 PWM signal with logic analyzer or oscilloscope to verify $50\text{ Hz}$ frequency ($20\text{ms}$ period) and pulse widths ($500\,\mu\text{s}$ at $0^\circ$, $2500\,\mu\text{s}$ at $180^\circ$).

---

## Merge Criteria

- [ ] All three spec documents (`plan.md`, `requirements.md`, `validation.md`) are created in `firmware/specs/2026-08-27-phase-3-pca9685-driver/`.
- [ ] Active working branch is `feature/phase-3-pca9685-driver`.
- [ ] Specs align with `specs/mission.md`, `specs/tech-stack.md`, and `specs/roadmap.md`.
- [ ] No implementation code was written during spec creation.
