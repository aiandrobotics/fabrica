# Requirements — Phase 3: I2C PCA9685 16-Channel PWM Servo Driver

## Scope

Phase 3 delivers the hardware actuation driver subsystem for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. It encompasses:
1. **Low-Level I2C Master Driver & PCA9685 Communication (`main/pca9685.h`, `main/pca9685.c`)**: Native I2C Master controller initialization on `GPIO 21` (SDA) and `GPIO 22` (SCL) operating at 100 kHz, interfacing with the PCA9685 16-channel 12-bit PWM generator at address `0x40`.
2. **Frequency Configuration & Prescaler**: Proper prescaler configuration ($50\text{ Hz}$ refresh rate / $20\text{ms}$ frame period) using PCA9685 internal $25\text{ MHz}$ oscillator.
3. **Angle-to-PWM Conversion Engine**: High-precision conversion mapping angular inputs ($0.0^\circ \text{ to } 180.0^\circ$) to 12-bit PWM counts ($102 \text{ to } 512$ counts corresponding to $500\,\mu\text{s} \text{ to } 2500\,\mu\text{s}$ pulses for MG996R servos).
4. **Single and Multi-Channel Command APIs**: Support for single-servo angle commands, bitmask-driven multi-servo synchronized updates, all-channel homing, identification nudging ($15^\circ$), and visual staging ($30^\circ$).
5. **Thread-Safe Bus Arbitration**: FreeRTOS mutex protection for all I2C read/write transactions.
6. **Host-Based Unit Test Suite (`test/test_pca9685.c`)**: Mocked register verification and mathematical validation under GCC/Clang host builds.

---

## Decisions & Technical Specifications

### 1. I2C Bus Configuration (`config.h`, `pca9685.c`)

| Parameter | Value / Pin | Description |
|---|---|---|
| **I2C Port** | `I2C_NUM_0` | ESP32 hardware I2C controller 0 |
| **SDA Pin** | `GPIO_NUM_21` | I2C Serial Data line connected to PCA9685 SDA |
| **SCL Pin** | `GPIO_NUM_22` | I2C Serial Clock line connected to PCA9685 SCL |
| **Clock Speed** | `100000` Hz (100 kHz) | Standard mode I2C clock |
| **Pull-Up Mode** | Internal pull-up enabled | `GPIO_PULLUP_ENABLE` on both SDA and SCL |
| **I2C Address** | `0x40` | Default hardware address with address lines A0–A5 grounded |
| **Bus Timeout** | `100` ms (`pdMS_TO_TICKS(100)`) | Max wait duration for I2C transaction completion |

### 2. PCA9685 Register Map & Initialization Sequence

| Register Name | Address | Configured Value | Description |
|---|---|---|---|
| `PCA9685_REG_MODE1` | `0x00` | `0x21` (`MODE1_AI \| MODE1_ALLCALL`) | Auto-increment enabled, all-call enabled, sleep disabled |
| `PCA9685_REG_MODE2` | `0x01` | `0x04` (`MODE2_OUTDRV`) | Totem-pole output structure (drives external servo signal lines high and low) |
| `PCA9685_REG_PRESCALE` | `0xFE` | `121` (`0x79`) | Prescaler for 50 Hz PWM frequency ($\text{round}(25\text{MHz} / (4096 \times 50)) - 1 = 121$) |
| `PCA9685_REG_ALL_LED_ON_L` | `0xFA` | `0x00` | Broadcast channel ON count low byte |
| `PCA9685_REG_ALL_LED_ON_H` | `0xFB` | `0x00` | Broadcast channel ON count high byte |
| `PCA9685_REG_ALL_LED_OFF_L` | `0xFC` | `0x66` (102 low byte) | Broadcast channel OFF count low byte ($0^\circ$ home) |
| `PCA9685_REG_ALL_LED_OFF_H` | `0xFD` | `0x00` (102 high byte) | Broadcast channel OFF count high byte ($0^\circ$ home) |

#### Initialization Step-by-Step Sequence:
1. Initialize ESP-IDF I2C driver on `I2C_NUM_0` in master mode.
2. Initialize FreeRTOS mutex `s_pca9685_mutex`.
3. Probe device at `0x40`; return `ESP_ERR_NOT_FOUND` if unacknowledged.
4. Put oscillator to sleep by writing `MODE1_SLEEP` (`0x10`) to `MODE1` (`0x00`).
5. Write prescaler value `121` (`0x79`) to `PRESCALE` (`0xFE`).
6. Wake oscillator by clearing sleep bit (write `MODE1_AI` `0x20` to `MODE1`).
7. Wait 500 $\mu\text{s}$ (`esp_rom_delay_us(500)` or `ets_delay_us(500)`) for oscillator stabilization.
8. Set restart bit (write `MODE1_RESTART | MODE1_AI` to `MODE1`).
9. Configure output drive by writing `MODE2_OUTDRV` (`0x04`) to `MODE2` (`0x01`).
10. Reset all 16 channels to $0^\circ$ home position ($102$ counts).

### 3. Angle-to-PWM Conversion Math & Limits

- **Pulse Width Range**: $500\,\mu\text{s}$ (at $0.0^\circ$) to $2500\,\mu\text{s}$ (at $180.0^\circ$).
- **PWM Frame Period**: $20\,000\,\mu\text{s}$ ($50\text{ Hz}$).
- **Resolution**: 12-bit ($4096\text{ counts}$).
- **Formula**:
  $$\text{Pulse}(\mu\text{s}) = 500.0 + \left(\frac{\text{angle}}{180.0}\right) \times 2000.0$$
  $$\text{Count} = \text{round}\left(\frac{\text{Pulse}(\mu\text{s}) \times 4096.0}{20000.0}\right)$$

| Angle ($\theta$) | Pulse Width ($\mu\text{s}$) | 12-Bit Off Count | Hex Value | Operational Meaning |
|---|---|---|---|---|
| $0.0^\circ$ | $500.0\,\mu\text{s}$ | **102** | `0x0066` | Flat home rest position (`HOME_ANGLE_DEG`) |
| $15.0^\circ$ | $666.7\,\mu\text{s}$ | **137** | `0x0089` | Motor identification nudge (`NUDGE_ANGLE_DEG`) |
| $30.0^\circ$ | $833.3\,\mu\text{s}$ | **171** | `0x00AB` | Visual staging hold angle (`STAGE_ANGLE_DEG`) |
| $45.0^\circ$ | $1000.0\,\mu\text{s}$ | **205** | `0x00CD` | Intermediate angle |
| $90.0^\circ$ | $1500.0\,\mu\text{s}$ | **307** | `0x0133` | Vertical fold angle |
| $135.0^\circ$ | $2000.0\,\mu\text{s}$ | **410** | `0x019A` | Intermediate angle |
| $180.0^\circ$ | $2500.0\,\mu\text{s}$ | **512** | `0x0200` | Full fold articulation (`FOLD_ANGLE_DEG`) |

### 4. API Function Signatures (`main/pca9685.h`)

```c
esp_err_t pca9685_init(void);
esp_err_t pca9685_probe(void);
esp_err_t pca9685_write_reg(uint8_t reg, uint8_t val);
esp_err_t pca9685_read_reg(uint8_t reg, uint8_t *val);
esp_err_t pca9685_set_pwm(uint8_t channel, uint16_t on_count, uint16_t off_count);
esp_err_t pca9685_set_all_pwm(uint16_t on_count, uint16_t off_count);
esp_err_t pca9685_set_servo_angle(uint8_t channel, float angle_deg);
esp_err_t pca9685_set_multi_servo_angles(uint16_t channel_mask, float angle_deg);
esp_err_t pca9685_home_all(void);
esp_err_t pca9685_nudge_channel(uint8_t channel);
esp_err_t pca9685_stage_channel(uint8_t channel);
esp_err_t pca9685_sleep(bool enable);
uint16_t pca9685_angle_to_counts(float angle_deg);
```

---

## Constraints

- **ESP-IDF v5.x Compatibility**: Implemented using standard `driver/i2c.h` with thread-safe FreeRTOS mutex synchronization to maintain cross-version compatibility and thread safety.
- **Strict Parameter Validation**:
  - Out-of-bounds angles must be clamped to $[0.0^\circ, 180.0^\circ]$.
  - Channel numbers must be validated against `TOTAL_SERVO_CHANNELS` ($16$); channel $\ge 16$ must return `ESP_ERR_INVALID_ARG`.
- **Non-Blocking / Bounded I2C Latency**: All I2C operations must use bounded timeouts ($\le 100\text{ms}$) to guarantee that temporary hardware disconnects do not deadlock Core 0 or Core 1.
- **Host Testability**: Conversion math and register encoding logic must be decoupled from hardware registers to enable 100% test coverage under host GCC/Clang test runners without ESP-IDF toolchain dependencies.

---

## Non-Goals

- Trajectory pacing, intermediate stepping, or dwell delays (Phase 5 Motion Engine).
- Storing or retrieving sequence presets from NVS flash (Phase 4).
- User input handling or physical button state reading (Phase 2 UI Subsystem).
- Wireless BLE/Wi-Fi PCA9685 control (Phase 8).

---

## Context

Phase 3 builds upon the system configuration and pin assignments established in Phase 1 (`config.h`), providing the foundational physical actuator driver required by the Phase 5 Motion Engine and Phase 6 Visual Staging State Machine.
