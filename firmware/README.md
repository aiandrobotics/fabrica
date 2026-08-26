# Embedded Firmware — Fabrica Cloth Folding Robot

This directory contains the production-grade embedded C / FreeRTOS firmware running natively on the **ESP32 Dev Board v1** for the **Fabrica Cloth Folding Robot**.

---

## System Overview

The Fabrica firmware coordinates the physical user interface, non-volatile storage, state machine workflows, and the **PCA9685 16-channel 12-bit PWM driver** over I2C to actuate up to 16 MG996R servo motors in modular cloth-folding grids.

* **Target Hardware**: ESP32 Dev Board v1 (Xtensa dual-core @ 240 MHz, 4MB Flash)
* **Actuation**: PCA9685 16-Channel 12-Bit PWM Driver over I2C (`GPIO 21 SDA`, `GPIO 22 SCL`)
* **User Interface**: 4 Push Buttons (`B1–B4`) + 1 Multi-Pattern Status LED (`GPIO 2`)
* **Architecture**: Dual-Core FreeRTOS (Core 0: Motion & I2C Bus / Core 1: UI, Buttons & NVS Storage)
* **Operating Modes**:
  1. **Daily Run Mode**: Single-tap execution of Presets 1–4, parallel servo motion, 300ms fold dwell, 200ms inter-step delay, instant E-Stop abort protection.
  2. **Visual Staging Programming Mode**: Computer-free teaching mode (3s hold entry, B1 cycle/nudge $15^\circ$, B2 stage/toggle $30^\circ$, B3 lock step, B4 save to NVS flash, 20s inactivity timeout).

---

## Specifications & Documentation

* **[Mission Specification](file:///Users/intelligentmachine/Documents/workspace/fabrica/firmware/specs/mission.md)**: High-level firmware mission, operating modes, subsystem architecture, and success criteria.
* **[Tech Stack Specification](file:///Users/intelligentmachine/Documents/workspace/fabrica/firmware/specs/tech-stack.md)**: Embedded toolchain, ESP-IDF drivers, dual-core task distribution, pinouts, timing constants, PCA9685 configuration, and unified command protocol.
* **[Roadmap Specification](file:///Users/intelligentmachine/Documents/workspace/fabrica/firmware/specs/roadmap.md)**: Phased implementation roadmap and testable milestones from Phase 0 to Phase 8.

---

## Build & Test Instructions

### 1. Host-Based Unit Testing
Run the host C test harness to validate hardware pin definitions, system constants, and command structure memory alignments:
```bash
make test
# Or manually:
gcc -Wall -Wextra -Werror -I./main -o /tmp/test_headers test/test_headers.c && /tmp/test_headers
```

### 2. ESP-IDF Target Build
Build the firmware binary targeting the ESP32:
```bash
idf.py build
```

### 3. Flashing & Serial Monitor
Flash the firmware to an attached ESP32 Dev Board and monitor diagnostic output:
```bash
idf.py -p /dev/tty.usbserial-* flash monitor
```