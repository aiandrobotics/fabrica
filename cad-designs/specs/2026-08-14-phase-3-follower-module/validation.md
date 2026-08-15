# Validation — Phase 3: Passive Follower Module

Validation specification and acceptance criteria for the Passive Follower Module.

---

## Required Checks

### 1. Headless Build Verification (`export_all.py` / `run.sh`)
- Execute `./run.sh follower_frame.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh follower_flap.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh frame_joiner.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh hex_drive_coupler.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh assembly.py` -> exit code `0`, valid `assembly.step` and `.stl` generated in `exports/`.
- Run `./run.sh export_all` -> all 6 scripts build without warnings or boolean topology errors.

### 2. Kinematic & Interference Check (`check_interference`)
- Verify axle and bearing knuckle engagement:
  - $\varnothing 13.0\text{ mm}$ continuous solid drive axle inside $\varnothing 13.5\text{ mm}$ closed bore: $0.25\text{ mm}$ radial clearance.
- Continuous rotational clearance:
  - Flap perimeter maintains full clearance from frame cavity walls throughout $0^\circ \to 90^\circ \to 180^\circ$ sweep.
  - 4th wall tie-bar stays flush at $Z = 3.0\text{ mm}$, providing $100\%$ collision-free clearance for $180^\circ$ flap rotation.
  - Boolean overlap volume check (`check_interference`): `overlap_volume_mm3 == 0.00000 mm³` across all 5 assembly pairs.

### 3. Visual Validation (`freecad-visual-validation`)
- Execute multi-view burst (`render_freecad_script`) on `follower_frame.py`, `follower_flap.py`, and `assembly.py`:
  - `Isometric`, `Front`, `Top`, `Right`, `Back`, `Bottom` views.
- Confirm checks:
  - [x] No floating geometry.
  - [x] No knife-edge walls.
  - [x] No unintended support-requiring overhangs.
  - [x] Axle seats cleanly inside bearing knuckles.
  - [x] Micro-grip texture, shadow bevel, and mass cutouts match design specs.
  - [x] True sliding dovetail joiners insert vertically from top and seat with 0.000 mm³ interference.
  - [x] 4th wall through-dovetail joint is clean and solid with continuous outer walls and flush top surface.

---

## Kinematic Interference Matrix (Zero Overlap Verified)

| Assembly Pair | Overlap Volume | Kinematic Status |
|---|---|---|
| `FollowerFrame` ↔ `FollowerFlap` | `0.00000 mm³` | ✅ PASS |
| `FollowerFrame` ↔ `FrameJoiner_Front` | `0.00000 mm³` | ✅ PASS |
| `FollowerFrame` ↔ `FrameJoiner_Right` | `0.00000 mm³` | ✅ PASS |
| `FollowerFlap` ↔ `HexDriveCoupler` | `0.00000 mm³` | ✅ PASS |
| `FollowerFrame` ↔ `HexDriveCoupler` | `0.00000 mm³` | ✅ PASS |

**Result**: PASS — Zero Interference (`0.00000 mm³`).

---

## Sign-off Summary
- `follower_frame.py` is fully verified with 360° closed bearing knuckles, concave blend ramps, open-bottom weight reduction, 4th wall through-dovetail joint ($3.0\text{ mm}$ solid walls), rubber foot sockets, TPU bumper slots, and push-out dovetail access holes.
- `follower_flap.py` is fully verified with continuous solid $\varnothing 13.0\text{ mm}$ axle, dual female hex sockets, ~45% gradient mass cutouts, $1.2\text{ mm}$ shadow bevel, $0.8\text{ mm}$ hole chamfers, and $0.6\text{ mm}$ diamond knurling.
- `hex_drive_coupler.py` is fully verified with dual $8.0\text{ mm}$ hex pegs, locating stop collar, self-aligning chamfers, and sliding-fit clearances.
- `assembly.py` demonstrates zero interference across all component pairs (`0.00000 mm³`).
- Phase 3 is **100% COMPLETE & PASS**. Ready to proceed to **Phase 4: Active Motorized Module**. All spec files (`plan.md`, `requirements.md`, `validation.md`, `roadmap.md`, `tech-stack.md`) fully synchronized and committed.
