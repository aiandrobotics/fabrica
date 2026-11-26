"""
base_module.py — Monolithic Stationary Base Chassis Module (4-Wall Frame Architecture)
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import sys
import os

# Ensure cad-designs root is in Python path for importing params.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import FreeCAD as App
import Part

from params import (
    ELEPHANTS_FOOT_CHAMFER,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    DOVETAIL_NECK_WIDTH,
    DOVETAIL_FLARE_WIDTH,
    DOVETAIL_DEPTH,
    EXPORT_DIR,
)

TOP_PLATE_THICKNESS = 2.4
BOTTOM_FLOOR_THICKNESS = 3.0

def construct_base_module():
    """
    Constructs the 4-Wall Monolithic Base Chassis Module with open-bottom interior,
    garment alignment reticles, silent-flip TPU bumper slots, sliding dovetails, and anti-slip feet.
    """
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    t = params.BASE_PANEL_THICKNESS
    rail_w = 15.0                         # 15.0mm reinforced dovetail boss depth
    thin_rail = 8.0                       # 8.0mm slimmed perimeter rail elsewhere (~30% lighter)
    boss_half_w = 22.0                    # 44.0mm wide dovetail boss centered on each wall
    top_t = TOP_PLATE_THICKNESS           # 2.4mm top deck plate
    bottom_floor = BOTTOM_FLOOR_THICKNESS # 3.0mm

    # 1. Main outer solid box (w x h x 15mm)
    base_box = Part.makeBox(w, h, t, App.Vector(0, 0, 0))

    # 2. Open-Bottom Slim-Rail Cavity (8.0mm perimeter walls, 15.0mm reinforced bosses at the 4 dovetail midpoints)
    cavity_z = t - top_t  # 12.6mm (Z = 0 to 12.6mm)
    cx_mid = w / 2.0
    cy_mid = h / 2.0
    cav_pts = [
        App.Vector(thin_rail, thin_rail, 0),
        App.Vector(cx_mid - boss_half_w, thin_rail, 0),
        App.Vector(cx_mid - boss_half_w, rail_w, 0),
        App.Vector(cx_mid + boss_half_w, rail_w, 0),
        App.Vector(cx_mid + boss_half_w, thin_rail, 0),
        App.Vector(w - thin_rail, thin_rail, 0),
        App.Vector(w - thin_rail, cy_mid - boss_half_w, 0),
        App.Vector(w - rail_w, cy_mid - boss_half_w, 0),
        App.Vector(w - rail_w, cy_mid + boss_half_w, 0),
        App.Vector(w - thin_rail, cy_mid + boss_half_w, 0),
        App.Vector(w - thin_rail, h - thin_rail, 0),
        App.Vector(cx_mid + boss_half_w, h - thin_rail, 0),
        App.Vector(cx_mid + boss_half_w, h - rail_w, 0),
        App.Vector(cx_mid - boss_half_w, h - rail_w, 0),
        App.Vector(cx_mid - boss_half_w, h - thin_rail, 0),
        App.Vector(thin_rail, h - thin_rail, 0),
        App.Vector(thin_rail, cy_mid + boss_half_w, 0),
        App.Vector(rail_w, cy_mid + boss_half_w, 0),
        App.Vector(rail_w, cy_mid - boss_half_w, 0),
        App.Vector(thin_rail, cy_mid - boss_half_w, 0),
        App.Vector(thin_rail, thin_rail, 0),
    ]
    cavity = Part.Face(Part.makePolygon(cav_pts)).extrude(App.Vector(0, 0, cavity_z + 0.1))
    cavity.translate(App.Vector(0, 0, -0.1))
    try:
        c_edges = [
            e for e in cavity.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.YMin - e.BoundBox.YMax) < 0.001
        ]
        if c_edges:
            cavity = cavity.makeFillet(2.5, c_edges)
    except Exception:
        pass
    main_shell = base_box.cut(cavity).removeSplitter()

    # 3. 4x Solid Corner Mounting Pads + Countersunk Nail / M3 Screw Holes (Ø3.5mm through, Ø6.5mm flush countersink)
    corner_inset = 10.0
    pad_r = 6.0
    nail_r = 1.75        # Ø3.5mm through-hole for nails or M3 screws
    csink_r = 3.25       # Ø6.5mm 45° countersink (1.5mm deep) so heads sit 100% flush below cloth
    csink_d = csink_r - nail_r  # 1.5mm
    top_z = t
    panel_z_min = t - top_t

    corner_coords = [
        (corner_inset, corner_inset),
        (w - corner_inset, corner_inset),
        (w - corner_inset, h - corner_inset),
        (corner_inset, h - corner_inset),
    ]
    corner_pads = [
        Part.makeCylinder(pad_r, t, App.Vector(cx, cy, 0.0))
        for cx, cy in corner_coords
    ]
    main_shell = main_shell.fuse(corner_pads).removeSplitter()

    # 3b. Multi-Tiered Organic Circular Weight-Reduction Cutouts through top plate (~35% mass saving)
    scale_geo = min(w, h) / 220.0
    hole_specs = [
        (w * 0.30, h * 0.32, 16.0 * scale_geo),
        (w * 0.70, h * 0.32, 16.0 * scale_geo),
        (w * 0.30, h * 0.68, 16.0 * scale_geo),
        (w * 0.70, h * 0.68, 16.0 * scale_geo),
        (w * 0.50, h * 0.50, 18.0 * scale_geo),
        (w * 0.50, h * 0.26, 11.0 * scale_geo),
        (w * 0.50, h * 0.74, 11.0 * scale_geo),
        (w * 0.24, h * 0.50, 12.0 * scale_geo),
        (w * 0.76, h * 0.50, 12.0 * scale_geo),
        (w * 0.18, h * 0.18, 8.5 * scale_geo),
        (w * 0.82, h * 0.18, 8.5 * scale_geo),
        (w * 0.18, h * 0.82, 8.5 * scale_geo),
        (w * 0.82, h * 0.82, 8.5 * scale_geo),
    ]
    cutters = []
    for cx, cy, hr in hole_specs:
        cyl = Part.makeCylinder(hr, top_t + 1.0, App.Vector(cx, cy, panel_z_min - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, top_z - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, panel_z_min - 0.1))
        cutters.extend([cyl, c_top, c_bot])
    main_shell = main_shell.cut(Part.makeCompound(cutters)).removeSplitter()

    # 4. 0.6mm Diagonal Micro-Grip Surface Texture (uniform +45° stripes matching flaps)
    tex_cutters = []
    tex_spacing = 14.0
    tex_w = 0.8
    tex_d = TEXTURE_HEIGHT

    for i in range(-int(h), int(w + h), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, (w + h) * 1.2, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, top_z - tex_d))
        tex_cutters.append(g1)

    tex_bound = Part.makeBox(w - 2 * 3.0, h - 2 * 3.0, top_t + 2.0)
    tex_bound.translate(App.Vector(3.0, 3.0, panel_z_min - 1.0))
    main_shell = main_shell.cut(Part.makeCompound(tex_cutters).common(tex_bound)).removeSplitter()

    # Cut the 4x countersunk corner nail/screw holes cleanly after texture
    nail_cutters = []
    for cx, cy in corner_coords:
        nail_cutters.append(Part.makeCylinder(nail_r, t + 1.0, App.Vector(cx, cy, -0.5)))
        nail_cutters.append(Part.makeCone(nail_r, csink_r, csink_d + 0.1, App.Vector(cx, cy, top_z - csink_d)))
    main_shell = main_shell.cut(Part.makeCompound(nail_cutters)).removeSplitter()

    # 5. Female Open-Top True Sliding Dovetail Joiner Sockets (All 4 outer side walls)
    dt_neck_w = DOVETAIL_NECK_WIDTH
    dt_flare_w = DOVETAIL_FLARE_WIDTH
    dt_depth = DOVETAIL_DEPTH
    dt_cut_h = t - bottom_floor + 0.5

    poly_pts = [
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
    ]
    dt_wire = Part.makePolygon(poly_pts)
    dt_face = Part.Face(dt_wire)
    dt_cutter = dt_face.extrude(App.Vector(0, 0, dt_cut_h))
    dt_cutter.translate(App.Vector(0, 0, bottom_floor))

    # Wire pass-through conduit (through back wall of dovetail boss directly into interior cavity)
    wire_hole_w = 8.0
    wire_hole_h = 8.6
    wire_conduit = Part.makeBox(wire_hole_w, rail_w + 2.0, wire_hole_h)
    wire_conduit.translate(App.Vector(-wire_hole_w / 2.0, 0.0, 9.0 - (wire_hole_h / 2.0)))
    try:
        w_edges = [
            e for e in wire_conduit.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.ZMin - e.BoundBox.ZMax) < 0.001
        ]
        if w_edges:
            wire_conduit = wire_conduit.makeFillet(1.0, w_edges)
    except Exception:
        pass

    dt_cutter_complete = dt_cutter.fuse(wire_conduit).removeSplitter()

    dovetail_cuts = []
    # Front wall (Y=0) -> cuts in +Y direction
    c_front = dt_cutter_complete.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))
    dovetail_cuts.append(c_front)

    # Back wall (Y=h) -> cuts in -Y direction
    c_back = dt_cutter_complete.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h, 0))
    dovetail_cuts.append(c_back)

    # Left wall (X=0) -> cuts in +X direction
    c_left = dt_cutter_complete.copy()
    c_left.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -90)
    c_left.translate(App.Vector(0, h / 2.0, 0))
    dovetail_cuts.append(c_left)

    # Right wall (X=w) -> cuts in -X direction
    c_right = dt_cutter_complete.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))
    dovetail_cuts.append(c_right)

    main_shell = main_shell.cut(Part.makeCompound(dovetail_cuts)).removeSplitter()

    # 8. Smooth rounded outer vertical corner fillets (R=3.0mm on all 4 outer corners)
    corner_trims = []
    for cx, cy in [(0, 0), (w, 0), (w, h), (0, h)]:
        bx = -3.0 if cx == 0 else cx - 3.0
        by = -3.0 if cy == 0 else cy - 3.0
        ax = 3.0 if cx == 0 else cx - 3.0
        ay = 3.0 if cy == 0 else cy - 3.0
        c_box = Part.makeBox(6.0, 6.0, t + 2.0)
        c_box.translate(App.Vector(bx, by, -1.0))
        c_cyl = Part.makeCylinder(3.0, t + 2.0, App.Vector(ax, ay, -1.0))
        corner_trims.append(c_box.cut(c_cyl))

    main_shell = main_shell.cut(Part.makeCompound(corner_trims)).removeSplitter()

    # 10. Elephant's Foot Relief Chamfer along bottom outer edges (0.4mm)
    try:
        base_edges = [
            e for e in main_shell.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 10.0
        ]
        if base_edges:
            main_shell = main_shell.makeChamfer(ELEPHANTS_FOOT_CHAMFER, base_edges)
            main_shell = main_shell.removeSplitter()
    except Exception as e:
        print(f"Warning: Elephant foot chamfer skipped on base module: {e}")

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "base_module.step")
    stl_path  = os.path.join(EXPORT_DIR, "base_module.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    main_shell.exportStep(step_path)
    main_shell.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return main_shell

def main():
    doc = App.newDocument("BaseModule")
    shape = construct_base_module()
    feature = doc.addObject("Part::Feature", "BaseModule")
    feature.Shape = shape

main()
