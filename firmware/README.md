# MicroPython Firmware

This folder contains the MicroPython firmware running on the **ESP32** for the Fabrica Cloth Folding Robot.

create specs for firmware.. create mission, roadmap, tech-stack
Will use esp32 dev board v1
Example code for project setup is in /Users/intelligentmachine/Documents/workspace/poc/esp_hello_world
Look at code for tech stack
my requirements are 
- should be able to interface max 16 servo motors.. user can interface 1-16 any number
- use esp32 devboard v1
- PCA9685 16-channel PWM driver control over I2C to control servo
- use dualcode from esp32
- 4 buttons use for programming and operation
- each button can be programmed for sequence.
- max 2 motors can run parallel (per fold) and sequence can have max 10 folds. come up with right terms -fold, sequence 
- To operate user press button once and sequence gets executed (each flap 0-180 and back to 0)
- 
- 



## Architecture

- `main.py` - Main entry point and event loop (runs automatically on boot)
- `button.py` - Polling-based 4-button handler with short/long press detection and LED feedback
- `servo_controller.py` - PCA9685 16-channel PWM driver control over I2C
- `motion_plan_executor.py` - Parallel motor trajectory executor
- `motion_plan_storage.py` - Persistent Flash storage with atomic write protection (`motion_plans.json`)
- `config_mode.py` - Interactive button-counting sequence recorder
- `config.py` - Pin mappings and hardware parameters
