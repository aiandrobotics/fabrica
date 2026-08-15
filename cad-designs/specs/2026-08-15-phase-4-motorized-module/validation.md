# Validation — Phase 4: Active Motorized Module

Validation specification and acceptance criteria for the Active Motorized Module.

---

## Required Checks

### 1. Headless Build Verification (`export_all.py` / `run.sh`)
- Execute `./run.sh motorized_frame.py` -> exit code `0`, valid `motorized_frame.step` and `motorized_frame.stl` generated in `exports/`.
- Execute `./run.sh active_flap.py` -> exit code `0`, valid `active_flap.step` and `active_flap.stl` generated in `exports/`.
- Execute `./run.sh servo_cover.py` -> exit code `0`, valid `servo_cover.step` and `servo_cover.stl` generated in `exports/`.
- Execute `./run.sh assembly_motorized_module.py` -> exit code `0`, valid `assembly_motorized_module.step` and `assembly_motorized_module.stl` generated in `exports/`.
- Run `./run.sh export_all` -> all CAD scripts build without warnings or OpenCASCADE boolean topology errors.

### 2. Kinematic & Interference Check (`check_interference`)
- **Axle and Bearing Knuckle Alignment**:
  - $\varnothing 13.0\text{ mm}$ continuous solid drive axle inside $\varnothing 13.5\text{ mm}$ closed bore: $0.25\text{ mm}$ radial clearance.
  - Smooth concentric rotation about hinge axis $(X=0, Z=8.0\text{ mm})$.
- **Servo Horn & Axle Interface**:
  - 25T spline pocket seated tightly on servo horn with $0.2\text{ mm}$ press-fit clearance.
  - Coaxial $\varnothing 3.2\text{ mm}$ M3 screw counterbore accurately aligned with the motor shaft center.
- **Flap Rotational Clearance ($0^\circ \to 90^\circ \to 180^\circ$)**:
  - Flap corner notch ($46.0 \times 26.0\text{ mm}$) maintains full collision-free clearance around the servo body and snap cover throughout the entire sweep.
  - 4th wall tie-bar stays flush at $Z = 3.0\text{ mm}$, providing $100\%$ clearance during $180^\circ$ flip.
  - Boolean overlap volume check (`check_interference`): `overlap_volume_mm3 == 0.00000 mm³` across all mating assembly pairs.

### 3. Visual Validation (`freecad-visual-validation`)
- Execute multi-view burst (`render_freecad_script`) on `motorized_frame.py`, `active_flap.py`, `servo_cover.py`, and `assembly_motorized_module.py`:
  - `Isometric`, `Front`, `Top`, `Right`, `Back`, `Bottom` views.
- Confirm visual criteria:
  - [ ] No floating geometry or disjoint solids.
  - [ ] No knife-edge walls ($< 1.0\text{ mm}$).
  - [ ] Servo mounting bay cleanly houses the MG996R footprint with screw boss alignment.
  - [ ] Wire pass-through channels have smooth $1.5\text{ mm}$ fillets without sharp pinch points.
  - [ ] Snap-latch tabs engage securely into retention slots.
  - [ ] Micro-grip diamond texture, shadow bevel, and gradient mass cutouts match reference visuals.
  - [ ] True sliding dovetail joiners insert vertically from top and seat with 0.000 mm³ interference.
  - [ ] 4th wall through-dovetail joint is clean and solid with continuous outer walls and flush top surface.

---

## Kinematic Interference Matrix (Zero Overlap Acceptance)

| Assembly Pair | Target Overlap Volume | Kinematic Acceptance Status |
|---|---|---|
| `MotorizedFrame` ↔ `ActiveFlap` (Rest $0^\circ$) | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `ActiveFlap` (Vertical $90^\circ$) | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `ActiveFlap` (Flipped $180^\circ$) | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `ServoCover` | `0.00000 mm³` | REQUIRED PASS |
| `ActiveFlap` ↔ `ServoCover` ($0^\circ \to 180^\circ$) | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `FrameJoiner_Front` | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `FrameJoiner_Right` | `0.00000 mm³` | REQUIRED PASS |
| `ActiveFlap` ↔ `HexDriveCoupler` ($Y=0$) | `0.00000 mm³` | REQUIRED PASS |
| `MotorizedFrame` ↔ `HexDriveCoupler` ($Y=0$) | `0.00000 mm³` | REQUIRED PASS |

**Threshold**: Total boolean intersection volume $\le 0.00000\text{ mm³}$.

---

## Merge Criteria
- [ ] All 4 Python scripts (`motorized_frame.py`, `active_flap.py`, `servo_cover.py`, `assembly_motorized_module.py`) implemented in `cad-designs/`.
- [ ] All parts export cleanly to STEP and STL in headless mode via `./run.sh export_all`.
- [ ] Visual validation renders generated and confirmed passing with zero defects.
- [ ] `check_interference` confirms `0.00000 mm³` overlap across all component pairs in the assembly matrix.
- [ ] `cad-designs/README.md` and project changelog updated.
