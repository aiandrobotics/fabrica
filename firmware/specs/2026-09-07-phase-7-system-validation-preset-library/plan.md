# Plan — Phase 7: End-to-End System Validation, Stress Testing & Preset Library

## Overview

Phase 7 executes the final validation, stress testing, and factory preset standardization for the **Fabrica Cloth Folding Robot** on the **ESP32 Dev Board v1**. This milestone integrates all previously implemented firmware subsystems—**UI & Button Debouncer** (`buttons.c`), **LED Pattern Engine** (`led.c`), **PCA9685 16-Channel PWM Driver** (`pca9685.c`), **NVS Sequence Manager** (`storage.c`), **Core 0 Real-Time Motion Engine** (`motion.c`), and **Visual Staging State Machine** (`state_machine.c`). 

Key goals include:
1. Standardizing the 4 factory preset routines in `storage.c` to map to physical garment folding kinematics (T-Shirt, Long-Sleeve Shirt, Trousers/Jeans, and Towel/Linen).
2. Implementing a dedicated end-to-end stress and endurance test harness (`test/test_e2e_stress.c`) validating 100 continuous run cycles with zero heap leaks, mid-sweep Emergency Stop preemption in $<50\text{ms}$, and power-loss resilience during NVS operations.
3. Updating system documentation in `firmware/README.md` with complete hardware wiring diagrams, ESP-IDF build/flash procedures, and an operator manual.

---

## Task Group 1: Standardize Factory Preset Library & Servo Mapping (`main/storage.c`, `main/config.h`)
1. Review and formalize physical servo flap channel assignments:
   - Define named channel aliases in `main/config.h` or `main/storage.c`:
     - Channel 0: Left Side Flap (`SERVO_FLAP_LEFT`)
     - Channel 1: Right Side Flap (`SERVO_FLAP_RIGHT`)
     - Channel 2: Bottom Flap (`SERVO_FLAP_BOTTOM`)
     - Channel 3: Top / Collar Flap (`SERVO_FLAP_TOP`)
2. Audit and update `storage_get_default_routine()` in `firmware/main/storage.c`:
   - **Preset 1 (Adult T-Shirt, 3 Steps)**:
     - Step 1: Left fold (Channel 0)
     - Step 2: Right fold (Channel 1)
     - Step 3: Bottom fold (Channel 2)
   - **Preset 2 (Long-Sleeve Shirt, 4 Steps)**:
     - Step 1: Parallel sleeve folds (Channel 0 & Channel 1 synchronously)
     - Step 2: Left body fold (Channel 0)
     - Step 3: Right body fold (Channel 1)
     - Step 4: Bottom fold (Channel 2)
   - **Preset 3 (Trousers / Jeans, 2 Steps)**:
     - Step 1: Vertical half fold (Channel 0)
     - Step 2: Bottom fold (Channel 2)
   - **Preset 4 (Towel / Linen, 3 Steps)**:
     - Step 1: Left half fold (Channel 0)
     - Step 2: Right quarter fold (Channel 1)
     - Step 3: Bottom final fold (Channel 2)
3. Ensure CRC32 checksum generation and validation deterministically matches factory data across all 4 presets.
4. Verify first-boot factory seeding (`"preset_init"` key) correctly seeds the updated sequences into NVS flash.

---

## Task Group 2: End-to-End Stress & Endurance Test Suite (`test/test_e2e_stress.c`, `firmware/Makefile`)
1. Create `firmware/test/test_e2e_stress.c` linking all subsystems (`buttons.c`, `led.c`, `pca9685.c`, `storage.c`, `motion.c`, `state_machine.c`):
   - **100-Cycle Continuous Execution Test**:
     - Execute 100 consecutive fold sequences sequentially cycling through Presets 1 to 4 in Daily Run Mode.
     - Verify zero dropped FreeRTOS commands, zero memory leaks, and steady-state heap stability across all 100 iterations.
   - **Mid-Sweep Emergency Stop Preemption Test**:
     - Trigger active motion for multi-step routines.
     - Inject Emergency Stop (`CMD_EMERGENCY_STOP` via button press or simulated interrupt) at variable timing offsets:
       - During outward sweep ($0^\circ \to 180^\circ$)
       - During fold dwell (300ms hold)
       - During return sweep ($180^\circ \to 0^\circ$)
       - During inter-step settling delay (200ms pause)
     - Verify all 16 PCA9685 channels drop flat to $0^\circ$ within $<50\text{ms}$ of abort injection.
     - Verify state machine returns immediately to `STATE_IDLE_RUN` with `LED_STATE_ESTOP` (5 rapid flashes).
   - **NVS Power-Loss & Flash Corruption Resilience**:
     - Simulate partial/interrupted NVS blob writes.
     - Inject single-bit and multi-bit mutations into stored routine blobs.
     - Verify `storage_load_routine()` detects CRC32 mismatch (`ESP_ERR_INVALID_CRC`), prevents mechanical corruption, and automatically reloads clean factory defaults.
   - **Rapid Mode Transition & Inactivity Stress**:
     - Rapidly transition between Daily Run Mode, Programming Mode, and Emergency Stop.
     - Verify watchdog timer resets properly and 20-second timeout consistently homes all servos to $0^\circ$ and discards incomplete buffers.
2. Update `firmware/Makefile`:
   - Add `test_e2e_stress` compilation target with `-Wall -Wextra -Werror`.
   - Integrate `test_e2e_stress` into `make test` pipeline.
   - Ensure all 7 test suites pass with 100% success.

---

## Task Group 3: System Documentation & Hardware Wiring Guide (`firmware/README.md`)
1. Expand `firmware/README.md` into a comprehensive system guide:
   - **Hardware Wiring & Schematic Reference**:
     - Detailed pinout table (ESP32 Dev Board v1 $\leftrightarrow$ PCA9685 $\leftrightarrow$ 4 Push Buttons $\leftrightarrow$ Status LED $\leftrightarrow$ External 5V/6V Power).
     - Power isolation and common ground recommendations for high-current servo loads.
   - **Dual-Core Architecture Overview**:
     - Clear diagram and description of Core 0 (real-time motion, I2C bus, E-Stop) vs Core 1 (UI, buttons, LED, NVS storage).
   - **Operator Manual**:
     - Daily Run Mode (1-touch preset recall on B1–B4).
     - Visual Staging Programming Mode (long-press entry, B1 cycle/nudge $15^\circ$, B2 stage/toggle $30^\circ$, B3 lock step, B4 save to NVS).
     - Emergency Stop operation and visual LED feedback guide.
   - **Build, Test & Flashing Instructions**:
     - Host unit testing (`make test`).
     - ESP-IDF build (`idf.py build`), flashing (`idf.py flash`), and serial monitor (`idf.py monitor`).
2. Verify overall clean build:
   - Run full test suite (`make test`) and verify zero regression.
   - Verify ESP-IDF build prerequisites and configuration integrity.
