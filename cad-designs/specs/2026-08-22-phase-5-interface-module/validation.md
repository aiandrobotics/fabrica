# Validation — Phase 5: Interface Module & Electronics Enclosure

## Required Checks

### 1. Parametric & Geometric Manifoldness Checks
- [ ] `python3 cad-designs/params.py` executes without error and prints all parameters including `BUTTON_HOLE_DIA = 16.0` and `CONTROL_DECK_ANGLE = 15.0`.
- [ ] All exported STL models pass manifold validity checks (zero non-manifold edges, zero self-intersections, zero unclosed shells).

### 2. Clearance & Fastener Fit Verification
- [ ] PCA9685 mounting hole pattern aligns with M2.5 standoff bosses ($56.5 \times 19.5\text{ mm}$ center-to-center).
- [ ] ESP32 DevKit mounting hole pattern aligns with M3 standoff bosses ($46.0 \times 23.0\text{ mm}$ center-to-center).
- [ ] 4x Ø16.0 mm button hole cutouts have $0.8\text{ mm}$ chamfers and accommodate standard 16mm push button bodies with $>0.2\text{ mm}$ radial clearance.
- [ ] $\varnothing 11.5\text{ mm}$ DC power barrel jack cutout cleanly accommodates standard 5.5×2.1mm threaded panel-mount jack.
- [ ] ESP32 micro-USB / USB-C port cutout provides clean straight-in plug clearance for standard cable overmolds.
- [ ] Dovetail sockets match universal `frame_joiner.py` with $0.20\text{ mm}$ clearance per side.

### 3. Multi-Body Assembly & Interference Checks
- [ ] Multi-body assembly in `assembly_interface_module.py` builds cleanly with:
  - `controller_case`
  - `interface_panel`
  - PCA9685 reference solid
  - ESP32 reference solid
  - 4x 16mm push button reference solids
  - Status LED diffuser solid
- [ ] FreeCAD MCP `check_interference` confirms **$0.0000\,\text{mm}^3$ overlap** across all mated clearance pairs.

### 4. Headless Visual Validation via FreeCAD MCP (v3)
- [ ] Multi-view burst rendering (`render_freecad_script`): Isometric, Front, Top, Right, and Bottom.
- [ ] Exploded view inspection (`inspect_freecad_assembly`): Clear visual confirmation of internal board standoffs, wire channels, and button bezels.
- [ ] Cross-section view (`section_freecad_model`): Verify $3.0\text{ mm}$ structural wall thickness and $0.4\text{ mm}$ Elephant's Foot relief chamfers.

---

## Manual Review Steps
- [ ] Verify tactile button spacing ($28.0\text{ mm}$ pitch) provides comfortable finger reach without accidental adjacent button presses.
- [ ] Confirm status LED diffuser is visible from both direct top and angled 45° tabletop viewing positions.
- [ ] Verify internal wire raceways provide sufficient bend radius for standard 26AWG/28AWG DuPont servo cables.

---

## Merge Criteria
- [ ] `cad-designs/specs/2026-08-22-phase-5-interface-module/` contains approved `plan.md`, `requirements.md`, and `validation.md`.
- [ ] `export_all.py` builds all parts and assemblies with a 100% pass rate.
- [ ] All code and documentation committed to `feature/phase-5-interface-module`.
