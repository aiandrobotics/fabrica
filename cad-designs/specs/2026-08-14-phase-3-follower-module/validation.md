# Validation — Phase 3: Passive Follower Module

Validation specification and acceptance criteria for the Passive Follower Module.

---

## Required Checks

### 1. Headless Build Verification (`export_all.py` / `run.sh`)
- Execute `./run.sh part_02_follower_frame.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh part_03_follower_flap.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh part_10_frame_joiner.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh part_11_hex_drive_coupler.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh assembly_follower_module.py` -> exit code `0`, valid `assembly_follower_module.step` and `.stl` generated in `exports/`.
- Run `./run.sh export_all` -> all 6 scripts build without warnings or boolean topology errors.

### 2. Kinematic & Interference Check (`check_interference`)
- Verify axle and bearing knuckle engagement:
  - $\varnothing 13.0\text{ mm}$ continuous solid drive axle inside $\varnothing 13.5\text{ mm}$ closed bore: $0.25\text{ mm}$ radial clearance.
- Continuous rotational clearance:
  - Flap perimeter maintains full clearance from frame cavity walls throughout $0^\circ \to 90^\circ \to 180^\circ$ sweep.
  - 4th wall tie-bar stays flush at $Z = 3.0\text{ mm}$, providing $100\%$ collision-free clearance for $180^\circ$ flap rotation.
  - Boolean overlap volume check (`check_interference`): `overlap_volume_mm3 == 0.00000 mm³` across all 5 assembly pairs.

### 3. Visual Validation (`freecad-visual-validation`)
- Execute multi-view burst (`render_freecad_script`) on `part_02_follower_frame.py`, `part_03_follower_flap.py`, and `assembly_follower_module.py`:
  - `Isometric`, `Front`, `Top`, `Right`, `Back`, `Bottom` views.
- Confirm checks:
  - [x] No floating geometry.
  - [x] No unexpected intersections or coincident boolean non-manifold edges.
  - [x] Correct proportions and wall thicknesses ($3.0\text{ mm}$ solid continuous outer walls on dovetail joint, $\ge 3.0\text{ mm}$ structural, $\ge 2.4\text{ mm}$ flap blade).
  - [x] Gradient weight-reduction cutouts clean and filleted ($0.8\text{ mm}$ chamfers).
  - [x] Diamond knurling micro-grip texture debossed $0.6\text{ mm}$ on garment face.
  - [x] Distinct part color coding (Frame: Green, Flap: Orange, Joiners: Blue, Coupler: Purple).
  - [x] Return structured `PASS` report.

---

## Manual Review Steps
- **Toolless Assembly Check**: Confirm drive axle rotates smoothly in 360° closed bores and Part 11 Hex Coupler mates into hex drive sockets with zero angular slop.
- **Weight Measurement**: Confirm sliced flap STL mass is $\le 80\text{g}$ with standard 15% gyroid infill.
- **Flap Free-Swing**: Flap rotates freely under gravity without stick-slip friction.

---

## Merge Criteria
- All 6 headless part and assembly scripts pass with zero errors.
- `assembly_follower_module.py` demonstrates zero interference across all component pairs (`0.00000 mm³`).
- Visual validation report returns `PASS`.
- All spec files (`plan.md`, `requirements.md`, `validation.md`, `roadmap.md`, `tech-stack.md`) fully synchronized and committed.
