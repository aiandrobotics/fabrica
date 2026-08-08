# MicroPython Firmware

This folder contains the MicroPython firmware running on the **Raspberry Pi Pico 2W (RP2350)** for the Fabrica Cloth Folding Robot.

## Architecture

- `main.py` - Main entry point and event loop (runs automatically on boot)
- `button.py` - Polling-based 4-button handler with short/long press detection and LED feedback
- `servo_controller.py` - PCA9685 16-channel PWM driver control over I2C
- `motion_plan_executor.py` - Parallel motor trajectory executor
- `motion_plan_storage.py` - Persistent Flash storage with atomic write protection (`motion_plans.json`)
- `config_mode.py` - Interactive button-counting sequence recorder
- `config.py` - Pin mappings and hardware parameters
