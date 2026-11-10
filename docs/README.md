# Fabrica Project Documentation

Welcome to the comprehensive documentation for the **Fabrica Cloth Folding Robot** — an open-source, automated garment folding system designed to be built for \$80–\$150 using standard 3D-printed parts, off-the-shelf electronics, and embedded software.

---

## Documentation Ecosystem

This documentation portal covers everything required to source components, 3D print the modular panels, wire the electrical subsystems, flash the firmware, and operate the robot both standalone and wirelessly.

| Section | Focus Area | Description |
|---|---|---|
| **[CAD & 3D Printing](../cad-designs/README.md)** | Mechanical Assembly | Parametric FreeCAD designs, 3D print slicer configurations (Bambu Lab 256 / Ender-3), STL/STEP exports, and chassis assembly. |
| **[Embedded Firmware](../firmware/README.md)** | Real-Time Control | ESP32 FreeRTOS C firmware, PCA9685 I2C driver, 4-button debounced UI, status LED engine, NVS storage with CRC32, and NimBLE GATT server. |
| **[Mobile Application](../mobile-app/README.md)** | Wireless BLE Control | Mobile companion app overview, BLE services (`FAB0`–`FAB3`), opcodes, pairing workflows, and link to the **[air-robotics-app repository](https://github.com/aiandrobotics/air-robotics-app)**. |
| **[Hardware Wiring](#hardware-wiring--electrical-schematics)** | Electrical Schematics | Power supply isolation, ESP32 DevKit v1 pinouts, PCA9685 connection diagrams, buttons, and status LED. |
| **[Bill of Materials (BOM)](#bill-of-materials-bom)** | Sourcing & Costing | Sourcing guide and component list for building a complete 4-flap folding robot for $80–$150. |
| **[Operation & Usage](#daily-operation--usage-guide)** | Daily Operation | Standalone button operation, factory presets, E-Stop safety, BLE pairing, and calibration. |

---

## Mobile Application

> **Note**: The source code for the Fabrica companion mobile application is maintained in a dedicated external repository:  
> 🔗 **Repository**: [https://github.com/aiandrobotics/air-robotics-app](https://github.com/aiandrobotics/air-robotics-app)

The mobile application enables:
- Wireless garment routine creation and visual folding sequence simulation
- Assigning custom routines to physical Buttons 1–4 with automatic IEEE 802.3 CRC32 verification
- Real-time 10 Hz motor telemetry and visual flap angle streaming
- Single-tap Emergency Stop (<50ms abort latency)
- Factory default preset restoration

---

## Hardware Wiring & Electrical Schematics

The Fabrica electronics system consists of the **ESP32 DevKit v1**, the **PCA9685 16-channel 12-bit PWM servo driver**, high-torque **MG996R servos**, a dedicated **5V/6V 10A–20A external DC power supply**, four tactile push buttons, and a status LED.

```
                  +--------------------------+
                  |      ESP32 DevKit v1     |
                  |                          |
                  |         3V3 Logic   (1)  |------------> PCA9685 VCC
                  |         GND         (2)  |----+-------> PCA9685 GND
                  |         GPIO 21 SDA (3)  |---|--------> PCA9685 SDA
                  |         GPIO 22 SCL (4)  |---|--------> PCA9685 SCL
                  |                          |   |
                  |         GPIO 2 LED       |   |
                  |         GPIO 4  (Btn 1)  |   |
                  |         GPIO 16 (Btn 2)  |   |
                  |         GPIO 17 (Btn 3)  |   |
                  |         GPIO 5  (Btn 4)  |   |
                  +--------------------------+   |
                                                 |
  +-------------------------------+              |
  | External Power Supply         |              |
  | Regulated 5V - 6V DC (10A-20A)|              |
  |                               |              |
  |                     (+) V+    |--------------|-------> PCA9685 V+ (Servos)
  |                     (-) GND   |--------------+-------> Common Ground Rail
  +-------------------------------+
```

> [!WARNING]
> **Power Isolation**: Never attempt to power the MG996R servo motors from the ESP32 board's 3.3V or 5V (VIN) rails. High-torque servos draw peak stall currents exceeding 2.5A each. Always power the PCA9685 servo power terminal (`V+`) from an external 5V/6V supply with shared common ground (`GND`).

### ESP32 Pin Assignment Table

| Pin | Function | Configuration | Description |
|---|---|---|---|
| `GPIO 2` | Status LED | Output (Push-Pull) | Onboard/External Status LED diffuser indicator |
| `GPIO 4` | Button 1 (`B1`) | Input (`PULLUP_ONLY`) | Preset 1 (Adult T-Shirt) / E-Stop / Hold-to-Pair (3s) |
| `GPIO 16` | Button 2 (`B2`) | Input (`PULLUP_ONLY`) | Preset 2 (Long-Sleeve Shirt) / E-Stop / Hold-to-Pair (3s) |
| `GPIO 17` | Button 3 (`B3`) | Input (`PULLUP_ONLY`) | Preset 3 (Trousers / Jeans) / E-Stop / Hold-to-Pair (3s) |
| `GPIO 5` | Button 4 (`B4`) | Input (`PULLUP_ONLY`) | Preset 4 (Towel / Linen) / E-Stop / Hold-to-Pair (3s) |
| `GPIO 21` | I2C Data (`SDA`) | In/Out (Open-Drain + Pullup) | PCA9685 PWM Controller I2C Data |
| `GPIO 22` | I2C Clock (`SCL`) | Output (Open-Drain + Pullup) | PCA9685 PWM Controller I2C Clock |

---

## Bill of Materials (BOM)

| Component | Quantity | Specification / Details | Approx Cost (USD) |
|---|---|---|---|
| **ESP32 DevKit v1** | 1 | 30-pin dual-core Xtensa LX6 @ 240 MHz, 4MB Flash | \$4.00 – \$6.00 |
| **PCA9685 PWM Driver** | 1 | 16-channel 12-bit PWM I2C breakout module | \$3.00 – \$5.00 |
| **MG996R Servos** | 4 | Metal-gear high-torque 180° servos (10–13 kg·cm) | \$24.00 – \$32.00 |
| **DC Power Supply** | 1 | Regulated 5V or 6V DC @ 10A–20A (50W–100W) | \$15.00 – \$25.00 |
| **DC Barrel Jack** | 1 | 5.5mm × 2.1mm panel-mount female connector | \$1.00 |
| **Tactile Push Buttons** | 4 | 16mm momentary waterproof/metal round buttons | \$6.00 – \$10.00 |
| **Status Diffuser LED** | 1 | 5mm diffused LED + 220Ω resistor (or built-in GPIO 2) | \$0.50 |
| **3D Printing Filament** | 2 kg | PETG or PLA+ filament (Black, Gray, or Orange) | \$30.00 – \$40.00 |
| **Fasteners & Hardware** | 1 pack | M3 button head screws (8mm, 12mm, 16mm) & M3 nuts | \$5.00 – \$8.00 |
| **Total Estimated BOM** | — | — | **\$88.50 – \$127.00** |

---

## Daily Operation & Usage Guide

### Standalone Mode (Physical Control Pad)

1. **Power On**: Turn on the external 5V/6V power supply. The ESP32 boots and automatically initializes the PCA9685 driver, homing all flaps to $0^\circ$ (flat resting position). The status LED pulses briefly and remains steady idle (`LED_STATE_IDLE`).
2. **Execute a Folding Preset**:
   - Tap **Button 1**: Folds an **Adult T-Shirt** (Left flap $\to$ Right flap $\to$ Bottom flap $\to$ Top collar flap).
   - Tap **Button 2**: Folds a **Long-Sleeve Shirt** (Collar staged $\to$ Left/Right sweeps $\to$ Waist fold).
   - Tap **Button 3**: Folds **Trousers / Jeans** (Parallel side tuck $\to$ Full bottom fold).
   - Tap **Button 4**: Folds a **Towel / Linen** (Half-fold parallel sweep $\to$ Quarter-fold finish).
3. **Emergency Stop (E-Stop)**:
   - Tap **any button** while motion is executing to immediately abort movement (<50ms) and return all panels to their flat home position. The LED flashes error red. Tap any button again once clear to reset back to idle.

### Wireless Mobile Mode (AIR Robotics App)

1. **Pairing**: Hold any button (**B1–B4**) for 3 seconds. The status LED begins rapid pairing blinks (`LED_STATE_BLE_PAIRING`).
2. **Connect**: Launch the [AIR Robotics App](https://github.com/aiandrobotics/air-robotics-app) or open **nRF Connect for Mobile**. Select `Fabrica-XXXX` and complete pairing.
3. **Customize Routines**: Design custom multi-flap timing sequences, preview them interactively, and tap "Assign to Button" to burn the sequence into the robot's NVS flash memory.
4. **Hardware Bond Reset**: Hold **Button 1 + Button 4 together for 5 seconds** to clear all stored mobile pairings and reset BLE bonds.
