# Fabrica Mobile Application

This folder contains the source code for the mobile application designed to interface with the Fabrica Cloth Folding Robot wirelessly over Bluetooth Low Energy (BLE).

## Core Capabilities & Architecture

- **Hold-to-Pair Security**: Connects during a 120-second pairing window initiated by holding any physical button on the robot for 3 seconds (`LED_STATE_BLE_PAIRING`). Supports up to 4 bonded devices in NVS with Resolvable Private Address (RPA) privacy resolution.
- **Client-Side Garment Profiles**: Manage, build, and share custom garment folding profiles client-side in the app (e.g. T-Shirts, Long Sleeves, Jeans, Towels, Hoodies) with full multi-motor support (up to 16 channels, including Left, Right, Bottom, and Top/Collar flaps).
- **Stateless Routine Preview (`CMD_RUN_RAW_SEQUENCE`)**: Test custom folding sequences directly on the robot from your phone without overwriting physical button slots.
- **Wireless Button Assignment (`CMD_SET_BUTTON_SEQUENCE` / `FAB3`)**: 1-touch persistence of custom profiles to physical Buttons 1–4 with automatic IEEE 802.3 CRC32 checksum generation and flash verification.
- **Real-Time Telemetry & LED Mirroring (`FAB2`)**: Live 10 Hz motor position tracking ($0^\circ \text{ to } 180^\circ$ across all channels) and 1:1 visual LED status mirroring with battery-saving 1 Hz idle throttling.
- **Execution & Safety Control (`FAB1`)**: Wirelessly trigger presets, preview raw sequences, jog motors for calibration, and trigger $<50\text{ms}$ Emergency Stop aborts with automatic panel homing.
- **1-Tap Factory Reset (`CMD_RESTORE_FACTORY_PRESETS`)**: Instantly restore the 4 built-in factory default routines exercising all 4 motors.
