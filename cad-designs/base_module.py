"""
base_module.py — Monolithic Stationary Base Chassis Module (4-Wall Frame Architecture)
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import sys
import os
import math

# Ensure cad-designs root is in Python path for importing params.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import FreeCAD as App
import Part

from params import (
    SCALE,
    PANEL_WIDTH,
    PANEL_HEIGHT,
    BASE_PANEL_THICKNESS,
    WALL_THICKNESS,
    ELEPHANTS_FOOT_CHAMFER,
    FOOT_PAD_DIA,
    FOOT_PAD_DEPTH,
    RETICLE_DEBOSS_DEPTH,
    TPU_BUMPER_DEPTH,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    JOINER_DETENT,
    WIRE_PORT_FILLET,
    DOVETAIL_NECK_WIDTH,
    DOVETAIL_FLARE_WIDTH,
    DOVETAIL_DEPTH,
    DOVETAIL_HEIGHT,
    EXPORT_DIR,
)

TOP_PLATE_THICKNESS = 2.4 * SCALE
BOTTOM_FLOOR_THICKNESS = 3.0 * SCALE

def construct_base_module():
    """
    Constructs the 4-Wall Monolithic Base Chassis Module with open-bottom interior,
    garment alignment reticles, silent-flip TPU bumper slots, sliding dovetails, and anti-slip feet.
    """
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    t = params.BASE_PANEL_THICKNESS
    rail_w = 15.0 * SCALE    # 15.0mm perimeter rails on all 4 sides
    top_t = TOP_PLATE_THICKNESS # 2.4mm top deck plate
    bottom_floor = BOTTOM_FLOOR_THICKNESS # 3.0mm

    # 1. Main outer solid box (240 x 240 x 15mm)
    base_box = Part.makeBox(w, h, t, App.Vector(0, 0, 0))

    # 2. Open-Bottom 4-Wall Cavity (leaves 15mm perimeter rails and 2.4mm top deck plate)
    cavity_w = w - (2.0 * rail_w) # 210mm
    cavity_h = h - (2.0 * rail_w) # 210mm
    cavity_z = t - top_t          # 12.6mm (Z = 0 to 12.6mm)
    cavity = Part.makeBox(cavity_w, cavity_h, cavity_z + 0.1, App.Vector(rail_w, rail_w, -0.1))
    main_shell = base_box.cut(cavity).removeSplitter()

    # 3. Multi-Tiered Organic Circular Weight-Reduction Cutouts through top plate (~35% mass saving)
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
    top_z = t
    panel_z_min = t - top_t
    for cx, cy, hr in hole_specs:
        cyl = Part.makeCylinder(hr, top_t + 1.0, App.Vector(cx, cy, panel_z_min - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, top_z - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, panel_z_min - 0.1))
        cutters.extend([cyl, c_top, c_bot])

    if cutters:
        main_shell = main_shell.cut(Part.makeCompound(cutters)).removeSplitter()

    # 5. 0.6mm Diamond Micro-Grip Surface Texture
    tex_cutters = []
    tex_spacing = 14.0 * SCALE
    tex_w = 0.8 * SCALE
    tex_d = TEXTURE_HEIGHT
    
    for i in range(-int(w), int(w + h), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, h * 1.5, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, top_z - tex_d))
        g2 = Part.makeBox(tex_w, h * 1.5, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, h, top_z - tex_d))
        tex_cutters.extend([g1, g2])

    if tex_cutters:
        tex_bound = Part.makeBox(w - 2 * 3.0 * SCALE, h - 2 * 3.0 * SCALE, top_t + 2.0)
        tex_bound.translate(App.Vector(3.0 * SCALE, 3.0 * SCALE, panel_z_min - 1.0))
        tex_compound = Part.makeCompound(tex_cutters).common(tex_bound)
        main_shell = main_shell.cut(tex_compound).removeSplitter()

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

    # Master bottom push-out finger access hole (Ø6.0mm through bottom floor)
    push_hole = Part.makeCylinder(3.0 * SCALE, bottom_floor + 1.0, App.Vector(0, dt_depth * 0.6, -0.5))
    dt_cutter_with_hole = dt_cutter.fuse(push_hole)

    dovetail_cuts = []
    # Front wall (Y=0) -> cuts in +Y direction
    c_front = dt_cutter_with_hole.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))
    dovetail_cuts.append(c_front)

    # Back wall (Y=h) -> cuts in -Y direction
    c_back = dt_cutter_with_hole.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h, 0))
    dovetail_cuts.append(c_back)

    # Left wall (X=0) -> cuts in +X direction
    c_left = dt_cutter_with_hole.copy()
    c_left.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -90)
    c_left.translate(App.Vector(0, h / 2.0, 0))
    dovetail_cuts.append(c_left)

    # Right wall (X=w) -> cuts in -X direction
    c_right = dt_cutter_with_hole.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))
    dovetail_cuts.append(c_right)

    # Internal Wire Pass-Through Ports (Routing cables from dovetail joiners into central cavity)
    wire_ports = [
        Part.makeBox(12.0 * SCALE, rail_w + 2.0, 7.0 * SCALE), # Front Y=0
        Part.makeBox(12.0 * SCALE, rail_w + 2.0, 7.0 * SCALE), # Back Y=H
        Part.makeBox(rail_w + 2.0, 12.0 * SCALE, 7.0 * SCALE), # Left X=0
        Part.makeBox(rail_w + 2.0, 12.0 * SCALE, 7.0 * SCALE), # Right X=W
    ]
    wire_ports[0].translate(App.Vector(w / 2.0 - 6.0 * SCALE, -1.0, bottom_floor))
    wire_ports[1].translate(App.Vector(w / 2.0 - 6.0 * SCALE, h - rail_w - 1.0, bottom_floor))
    wire_ports[2].translate(App.Vector(-1.0, h / 2.0 - 6.0 * SCALE, bottom_floor))
    wire_ports[3].translate(App.Vector(w - rail_w - 1.0, h / 2.0 - 6.0 * SCALE, bottom_floor))

    main_shell = main_shell.cut(Part.makeCompound(dovetail_cuts + wire_ports)).removeSplitter()

    # 8. Anti-Slip Foot Pad Recess Sockets (4x on bottom face of outer rails for Ø12mm x 2.0mm rubber feet)
    foot_r = 6.0 * SCALE
    foot_d = 2.0 * SCALE
    foot_locs = [
        (rail_w / 2.0, rail_w / 2.0),
        (w - rail_w / 2.0, rail_w / 2.0),
        (w - rail_w / 2.0, h - rail_w / 2.0),
        (rail_w / 2.0, h - rail_w / 2.0),
    ]
    foot_cutters = [
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(fx, fy, -0.1))
        for fx, fy in foot_locs
    ]
    main_shell = main_shell.cut(Part.makeCompound(foot_cutters)).removeSplitter()

    # 9. Elephant's Foot Relief Chamfer along bottom outer edges (0.4mm)
    try:
        base_edges = [
            e for e in main_shell.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 10.0 * SCALE
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
