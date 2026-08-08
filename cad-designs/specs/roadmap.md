# Roadmap

Each phase is a small, independently buildable unit of work.
Build, validate, and commit before moving to the next phase.

---

## Phase 0 — Project Constitution ✅
- Create `specs/mission.md`, `specs/tech-stack.md`, `specs/roadmap.md`
- Review all reference images
- Lock dimensions and part list

---

## Phase 1 — Project Skeleton ✅
- Create `params.py` with all dimensions (inches → mm), `SCALE`, build-plate constants, tolerances, `PROJECT_DIR`, `EXPORT_DIR`
- Create `exports/`, `3d-print/`, `media/` directories
- Create `run.sh` (executable)
- Create `.gitignore`
- Smoke-test: `python params.py` prints all key values without error

---

## Phase 2 — Leg Segment (`part_01_leg_segment.py`) ✅
- Rectangular hollow segment max length 220 mm (calculated as diagonal of 175x175mm bed minus length of pegs)
- Integrated solid cylindrical threaded male peg at one end
- Integrated cylindrical threaded hole at the opposite end (acting as the female receiver socket)
- Threading geometry is timed so that when segments are fully tightened, their outer rectangular profiles perfectly align to form a continuous visual rod. 
- Print orientation: segment lying flat at 45° diagonal
- Export STEP + STL; visual validation pass

---

## Phase 3 — X-Frame Center Hinge ✅
- Replaced monolithic print-in-place block with a robust 3-part threaded mechanism:
  - `part_02_xframe_hinge_bottom.py`: Bottom hinge bracket featuring a female M16 equivalent thread.
  - `part_03_xframe_hinge_top.py`: Top hinge bracket featuring a clearance bore.
  - `part_04_xframe_hinge_pin.py`: Male threaded locking pivot pin printed flat to ensure strong horizontal layer orientation.
- Integrates seamlessly with X-frame rectangular leg segments (using the threaded cylinder joinery timed for profile alignment)
- Export STEP + STL; visual validation pass

---

## Phase 4 — Universal Modular T-Bracket ✅
- Implemented `part_05_top_l_bracket.py` (updated to Universal T-Bracket): a single-piece rigid L-shaped bracket connecting X-frame legs to horizontal drying rods.
- **Body geometry**: 2D L-shaped profile (vertical arm 60 mm, horizontal arm 45 mm, matching `LEG_WIDTH = 25 mm` square cross-section × `LEG_DEPTH = 25 mm` extrusion depth) extruded with 2 mm fillets on all edges; inner corners chamfered (4 mm) to avoid stress risers at the junctions.
- **Print orientation**: Part lies flat in the XY plane; Z-thickness equals `LEG_DEPTH` (25 mm). All three threaded features print horizontally, consistent with leg segment convention.
- **Universal Sockets**: All three sockets (Top, Bottom, Side) feature identical standard timed female threaded blind sockets (radius = `PEG_THREAD_RADIUS`). This modular design allows the L-bracket to function as a T-junction, fitting anywhere: inline between two leg segments, or capping the top of the rack.
- **Assembly placement** (`assembly.py`): Bracket positioned at leg joints using a mathematical rotation matrix derived from the 65° X-frame deployed angle. The bottom socket receives the leg peg from below, the side socket receives the horizontal rod, and the top socket can receive an adapter pin to continue the leg vertically.
- Export `part_05_top_l_bracket.step` + `.stl`; integrated into `assembly.step`; visual validation pass.

---

## Phase 5 — Universal Drying Rod, Adapter Pin, & Middle Stability Bar (`part_06_drying_rod.py`, `part_07_threaded_adapter_pin.py`) ✅
- **Universal Drying Rod** (`part_06_drying_rod.py`): Stadium profile (pill shape) hollow segment ≤ 220 mm, transitioning to square ends. Uses male threaded peg / female threaded socket joinery. This exact part will be reused for the main top rod, secondary mid-height rod, side arm rod, and the middle stability bars.
- **Threaded Adapter Pin** (`part_07_threaded_adapter_pin.py`): A short male-to-male threaded adapter pin used to connect two female sockets (e.g., joining the right end of a rod assembly to a T-bracket, or connecting a T-bracket's top socket to the next Leg segment).
- **Middle Stability Bar**: Reuses `part_06_drying_rod.py` to span between the two X-frame assemblies at mid-height, and reuses `part_05_top_l_bracket.py` placed inline on the X-frame legs to connect the bar. Completed directly by updating `assembly.py`.
- Export STEP + STL each; visual validation pass

---

## Phase 6 — Anti-Slip Foot Cap (`part_08_foot_cap.py`) ✅
- Cap that slides over the rectangular segment body end
- Textured or recessed base for grip
- Export STEP + STL; visual validation pass

---

## Phase 7 — Rod End Cap (`part_09_rod_end_cap.py`) ✅
- Cylindrical profile matching the main drying rods with a slightly domed outer face for a polished look.
- Uses a standard timed male threaded peg to securely lock into the female sockets on the T-Brackets.
- Export STEP + STL; visual validation pass

---

## Phase 8 — Final Review & Full Assembly ✅
- Visual inspection of each individual part to identify and fix any small lingering issues.
- Update `assembly.py` to position all instances correctly (2 X-frames, 3 rods, 1 stability bar, optionally 6 hinges, 4 foot caps).
- Run final export script to clear `exports/` and regenerate all parts cleanly.
- Export `assembly.step` and `assembly.stl`.
- Final visual validation of the full assembly and tag release commit.

---

## Out of Scope (v1)
- Animated/articulated folding simulation
- Physical load/stress simulation
- Colour/texture rendering
