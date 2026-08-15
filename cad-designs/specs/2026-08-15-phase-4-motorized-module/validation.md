# Validation — Phase 4: Active Motorized Module (Horizontal Drive & Modular Horn Adapter Architecture)

Validation specification and acceptance criteria for the Active Motorized Module.

---

## Required Checks

### 1. Headless Build Verification (`export_all.py` / `run.sh`)
- Execute `./run.sh motorized_frame.py` -> exit code `0`, valid `motorized_frame.step` and `motorized_frame.stl` generated in `exports/`.
- Execute `./run.sh motorized_flap.py` -> exit code `0`, valid `motorized_flap.step` and `motorized_flap.stl` generated in `exports/`.
- Execute `./run.sh motorized_servo_adapter.py` -> exit code `0`, valid `motorized_servo_adapter.step` and `motorized_servo_adapter.stl` generated in `exports/`.
- Execute `./run.sh motorized_servo_cover.py` -> exit code `0`, valid `motorized_servo_cover.step` and `motorized_servo_cover.stl` generated in `exports/`.
- Execute `./run.sh motorized_assembly.py` -> exit code `0`, valid `motorized_assembly.step` and `motorized_assembly.stl` generated in `exports/`.
- Run `python3 export_all.py` -> all CAD scripts build cleanly without warnings or OpenCASCADE boolean topology errors.

### 2. Kinematic & Interference Check (`check_interference`)
- **Flat Base Verification**: All frame undersides coplanar at $Z = 0.0\text{ mm}$ with zero downward bumps or steps.
- **Pivot Centerline Alignment**: All axles, knuckles, and coupler ports centered at $Z_{pivot} = 10.0\text{ mm}$.
- **Servo Drive Adapter Interface**:
  - 4x M2/M2.5 screw holes aligned with round horn disk bolt pattern.
  - Male 8.0mm hex peg engages into flap top female hex socket with $0.00000\text{ mm}^3$ interference.
- **Boolean Overlap Volume Check**: `0.00000 mm³` overlap across all mating assembly pairs.

---

## Kinematic Interference Matrix (Zero Overlap Acceptance)

| Assembly Pair | Target Overlap Volume | Kinematic Acceptance Status |
|---|---|---|
| `MotorizedFrame` ↔ `MotorizedFlap` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `MotorizedServoCover` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `ServoMotor` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFlap` ↔ `ServoMotor` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFlap` ↔ `MotorizedServoCover` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedServoCover` ↔ `ServoMotor` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `FrameJoiner_Front` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `FrameJoiner_Right` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFlap` ↔ `HexDriveCoupler` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFlap` ↔ `ServoDriveAdapter` | `0.00000 mm³` | REQUIRED PASS |
| `ServoDriveAdapter` ↔ `ServoMotor` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `ServoDriveAdapter` | `0.00000 mm³` | REQUIRED PASS |

**Threshold**: Total boolean intersection volume $\le 0.00000\text{ mm³}$.
