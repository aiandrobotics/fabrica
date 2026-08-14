# Validation — Phase 3: Passive Follower Module

Validation specification and acceptance criteria for the Passive Follower Module.

---

## Required Checks

### 1. Headless Build Verification (`export_all.py` / `run.sh`)
- Execute `./run.sh part_02_follower_frame.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh part_03_follower_flap.py` -> exit code `0`, valid `.step` and `.stl` generated in `exports/`.
- Execute `./run.sh assembly` -> exit code `0`, valid `assembly_follower_module.step` and `.stl` generated in `exports/`.
- Run `./run.sh export_all` -> all scripts build without warnings or boolean topology errors.

### 2. Kinematic & Interference Check (`check_interference`)
- Verify pivot pin engagement:
  - Top Male Pin inside $360^\circ$ closed bore: $\ge 0.3\text{ mm}$ radial clearance.
  - Bottom Male Pin inside C-snap socket: $\ge 0.3\text{ mm}$ rotating clearance when seated.
- Continuous rotational clearance:
  - Flap perimeter maintains $\ge 1.0\text{ mm}$ gap from frame cavity walls throughout $0^\circ \to 90^\circ \to 180^\circ$ sweep.
  - Boolean overlap volume check (`check_interference`): `overlap_volume_mm3 <= 0.001 mm³`.

### 3. Visual Validation (`freecad-visual-validation`)
- Execute multi-view burst (`render_freecad_script`) on `part_02_follower_frame.py`, `part_03_follower_flap.py`, and `assembly_follower_module.py`:
  - `Isometric`, `Front`, `Top`, `Right`, `Back` views.
- Confirm checks:
  - [x] No floating geometry.
  - [x] No unexpected intersections or coincident boolean non-manifold edges.
  - [x] Correct proportions and wall thicknesses ($\ge 3.0\text{ mm}$ structural, $\ge 2.0\text{ mm}$ cosmetic).
  - [x] Gradient weight-reduction cutouts clean and filleted ($0.8\text{ mm}$ chamfers).
  - [x] Diamond knurling micro-grip texture debossed $0.6\text{ mm}$ on garment face.
  - [x] Distinct part color coding (Frame: Green, Flap: Orange, Joiners: Blue).
  - [x] Return structured `PASS` report.

---

## Manual Review Steps
1. **Toolless Assembly Check**: Confirm top pin slides smoothly into 360° bore and bottom pin clicks into C-snap socket under gentle finger pressure.
2. **Weight Measurement**: Confirm sliced flap STL mass is $\le 80\text{g}$ with standard 15% gyroid infill.
3. **Flap Free-Swing**: Flap rotates freely under gravity without stick-slip friction.

---

## Merge Criteria
- All 3 headless part and assembly scripts pass with zero errors.
- `assembly_follower_module.py` demonstrates zero interference across $0^\circ \to 180^\circ$.
- Visual validation report returns `PASS`.
- All spec files (`plan.md`, `requirements.md`, `validation.md`) committed to `feat/phase-3-follower-module`.
