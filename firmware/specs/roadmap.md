# Roadmap — ESP32 Firmware

Each phase is a small, independently buildable and testable unit of work.
Build, validate, and verify each milestone before moving to the next phase.

---

## Phase 0 — Project Constitution & Firmware Specs ✅
- Create `firmware/specs/mission.md`, `firmware/specs/tech-stack.md`, and `firmware/specs/roadmap.md`.
- Establish target hardware architecture: **ESP32 Dev Board v1**, **PCA9685 16-Channel 12-Bit PWM Driver**, **4 Push Buttons (B1–B4)**, **1 Status LED**, and **up to 16 MG996R Servos**.
- Define dual-core FreeRTOS task partition: Core 0 for real-time motion and I2C actuation; Core 1 for UI event loop, button debouncing, LED patterns, and NVS storage.
- Align code patterns and project structure with the reference implementation in `poc/esp_hello_world`.

---

## Phase 1 — Project Skeleton, Hardware Configuration & Diagnostics (`main.c`, `config.h`, `command.h`) ✅
- Create root `CMakeLists.txt`, `main/CMakeLists.txt`, `Makefile`, and `sdkconfig.defaults`.
- Create `main/config.h` as the single source of truth for GPIO pin assignments (`LED_GPIO 2`, `BTN1_GPIO 0`, `BTN2_GPIO 4`, `BTN3_GPIO 16`, `BTN4_GPIO 17`, `I2C_SDA_GPIO 21`, `I2C_SCL_GPIO 22`), PWM limits, timing constants, and system constraints.
- Create `main/command.h` defining the source-agnostic `command_t` schema (`SOURCE_PHYSICAL_BUTTON`, `SOURCE_BLE`, `SOURCE_WIFI`) and unified command queue to guarantee forward compatibility with the mobile app.
- Implement `main/main.c` system startup and diagnostics (adapted from `poc/esp_hello_world/main/hello_world_main.c`):
  - Print ESP32 chip details (model, silicon revision, CPU cores, WiFi/BT features).
  - Print SPI flash size and monitor heap memory via `esp_get_minimum_free_heap_size()`.
  - Initialize FreeRTOS inter-task communication primitives (queues and event groups).
- **Validation**: Verified with host unit tests (`make test`, 50/50 pass), ESP-IDF build compilation, and live hardware flash/monitor on ESP32 (`/dev/cu.usbserial-0001`).

---

## Phase 2 — UI Subsystem: 4-Button Debouncer & Non-Blocking LED Pattern Engine (`buttons.c`, `led.c`)
- **Status LED Pattern Engine** (`main/led.h`, `main/led.c`):
  - Implement non-blocking FreeRTOS software timer / task driving 7 visual state feedback patterns:
    1. `LED_STATE_IDLE`: Soft heartbeat (10% duty cycle / 0.5 Hz) or OFF awaiting input.
    2. `LED_STATE_RUNNING`: Solid ON continuous throughout routine execution.
    3. `LED_STATE_PROGRAMMING`: Slow blink (1.0s ON / 1.0s OFF / 0.5 Hz).
    4. `LED_STATE_STEP_LOCKED`: 2 fast flashes (80ms ON / 80ms OFF).
    5. `LED_STATE_SAVE_SUCCESS`: Solid ON for 2.0 seconds then OFF.
    6. `LED_STATE_INPUT_ERROR`: 3 fast flashes (60ms ON / 60ms OFF).
    7. `LED_STATE_ESTOP`: 5 rapid flashes (50ms ON / 50ms OFF).
- **4-Button Debouncing & Gesture Recognition** (`main/buttons.h`, `main/buttons.c`):
  - Configure `GPIO 0`, `GPIO 4`, `GPIO 16`, and `GPIO 17` as inputs with internal pull-ups (`GPIO_PULLUP_ONLY`).
  - Implement 50ms low-pass debounce sampling.
  - Distinguish between **Short Tap** (<500ms) and **Long Press** (≥3000ms continuous hold).
  - Translate physical button gestures into standardized `command_t` structs and dispatch to the unified command queue.
- **Validation**: Verify button tap vs 3-second hold detection and non-blocking visual LED output patterns on bench test.

---

## Phase 3 — I2C PCA9685 16-Channel PWM Servo Driver (`pca9685.c`)
- **I2C Master Initialization & Configuration** (`main/pca9685.h`, `main/pca9685.c`):
  - Initialize ESP32 I2C Master peripheral on `GPIO 21 (SDA)` and `GPIO 22 (SCL)` at 100 kHz.
  - Configure PCA9685 controller (`0x40` address): wake from sleep, set prescale register for 50 Hz PWM ($20\text{ms}$ period), enable auto-increment mode.
- **Angle to 12-Bit PWM Conversion**:
  - Implement conversion from degrees ($0^\circ \text{ to } 180^\circ$) to 12-bit PWM register counts ($500\,\mu\text{s} \to 2500\,\mu\text{s}$, $102 \to 512$ counts).
  - Implement single channel angle command: `pca9685_set_servo_angle(channel, angle_deg)`.
  - Implement synchronized multi-channel angle command: `pca9685_set_multi_servo_angles(mask, angle_deg)`.
  - Implement mechanical identification nudge ($15^\circ$) and visual staging hold ($30^\circ$).
  - Implement all-channel home reset ($0^\circ$ for all channels 0–15).
- **Validation**: Verify I2C transactions and 50Hz PWM pulse output across all 16 channels via oscilloscope / servo movement.

---

## Phase 4 — Non-Volatile Storage (NVS) Sequence Manager (`storage.c`)
- **NVS Partition Initialization & Management** (`main/storage.h`, `main/storage.c`):
  - Initialize ESP-IDF NVS flash subsystem (`nvs_flash_init()`) with auto-erase on partition corruption.
  - Define binary serialization schema for `fold_routine_t` (Presets 1–4, up to 16 steps, max 2 motors per step, CRC32 checksum).
- **CRUD Operations**:
  - `storage_save_routine(preset_id, &routine)`: Write sequence blob and update CRC checksum.
  - `storage_load_routine(preset_id, &routine)`: Read and validate blob with CRC verification; fallback to empty/default on failure.
  - `storage_init_factory_defaults()`: Seed default factory folding sequences (T-shirt, Pants, Towel) on initial first boot.
- **Validation**: Verify sequence persistence, power-cut tolerance, and CRC validation across reboot cycles.

---

## Phase 5 — Motion Engine & Daily Run Mode Execution (`motion.c`)
- **Core 0 Real-Time Motion Task** (`main/motion.h`, `main/motion.c`):
  - High-priority FreeRTOS task pinned to Core 0 executing sequence steps sequentially (Step 1 to $N$).
  - **Single Motor Sweep**: Target servo sweeps $0^\circ \rightarrow 180^\circ$, dwells for 300ms, then returns $180^\circ \rightarrow 0^\circ$.
  - **Parallel Motor Sweep**: Both assigned servos sweep synchronously $0^\circ \rightarrow 180^\circ$, dwell for 300ms, and return synchronously $180^\circ \rightarrow 0^\circ$.
  - **Inter-Step Settling Delay**: 200ms pause between consecutive steps.
  - Turn LED Solid ON during execution; turn OFF when returning to Idle.
- **Daily Run Mode Trigger & Safeguards**:
  - Single short tap on B1–B4 triggers execution of Preset 1–4.
  - **Emergency Stop (E-Stop)**: Tapping **any button** while motion is active immediately halts PWM pulses, commands all 16 channels to $0^\circ$, delivers 5 rapid LED flashes, and aborts the routine in $<50\text{ms}$.
  - **Empty Preset Protection**: Tapping a button with 0 recorded steps produces 3 fast LED flashes without activating motors.
- **Validation**: Verify smooth single/parallel flap articulation, dwell/settling timing, and instantaneous E-Stop abort handling.

---

## Phase 6 — Visual Staging Programming Mode & State Machine Integration (`state_machine.c`)
- **Mode Transition & Staging Coordinator** (`main/state_machine.h`, `main/state_machine.c`):
  - Hold B1–B4 for 3 seconds $\rightarrow$ Enter Programming Mode for that preset; set LED to Slow Blink (0.5 Hz).
- **Physical Staging Workflow**:
  - **B1 (CYCLE / NUDGE)**: Increment target servo index (1–16) and trigger $15^\circ$ physical nudge for quick identification.
  - **B2 (STAGE / TOGGLE)**: Lift identified flap to $30^\circ$ and hold in position. Tapping B2 on an already-staged flap drops it to $0^\circ$. Support up to 2 simultaneously staged flaps.
  - **B3 (NEXT STEP)**: Lock staged flap(s) into step buffer, flash LED 2 times rapidly, drop flaps flat to $0^\circ$, increment step buffer index.
  - **B4 (SAVE & EXIT)**: Commit sequence buffer to NVS flash, turn LED Solid ON for 2.0 seconds, and return to Daily Run Mode.
- **Programming Safeguards & Failsafes**:
  - **2-Motor Limit**: Staging a 3rd motor in 1 step is rejected with 3 fast flashes.
  - **Empty Step Skip**: Pressing B3 with no staged flaps is ignored.
  - **Inactivity Timeout**: 20 seconds with no button presses drops all flaps to $0^\circ$, discards buffer, and safely exits to Run Mode.
  - **16-Step Cap**: Reaching 16 steps automatically saves sequence to NVS and exits.
- **Validation**: End-to-end testing of visual programming workflow without screen/computer, verifying correct NVS save and subsequent Run Mode playback.

---

## Phase 7 — End-to-End System Validation, Stress Testing & Preset Library
- **Factory Preset Library**:
  - Preset 1: Standard Adult T-Shirt (Left fold $\to$ Right fold $\to$ Bottom fold).
  - Preset 2: Long-Sleeve Shirt (Parallel sleeve fold $\to$ Body folds).
  - Preset 3: Trousers / Jeans (Half fold $\to$ Full fold).
  - Preset 4: Towel / Linen (Quarter square fold).
- **Stress & Endurance Testing**:
  - 100-cycle continuous run test verifying zero heap memory leaks (`esp_get_minimum_free_heap_size()`).
  - Stress testing E-Stop triggers under active mid-sweep conditions.
  - Verification of power loss resilience during NVS write operations.
- **Final Documentation**: Update `firmware/README.md` with wiring diagrams, flashing guides, and user operation instructions.

---

## Phase 8 — Future Expansion: Mobile App Wireless Integration (BLE / Wi-Fi) [Post-MVP]
- **Transport Abstraction Implementation**:
  - Activate `transport_interface_t` for wireless ingress/egress.
- **Bluetooth Low Energy (BLE) GATT Driver**:
  - Implement NimBLE GATT service (`0000FAB0-0000-1000-8000-00805F9B34FB`) on Core 1.
  - Add Control Point Characteristic for wireless routine triggers, manual motor jogging, and wireless E-Stop.
  - Add Telemetry Characteristic streaming live status (10 Hz).
  - Add Profile Transfer Characteristic for bidirectional NVS sequence synchronization with the mobile app.
- **Wi-Fi & Local WebSockets Interface**:
  - Implement lightweight WebSocket / REST RPC interface for local network discovery and remote control.
- **Validation**: Bi-directional communication test with cross-platform mobile app simulator, verifying routine streaming, real-time motor jog, and wireless emergency stop without touching Core 0 motion engine code.

