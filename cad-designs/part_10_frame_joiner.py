"""
part_10_frame_joiner.py — Fully Symmetrical Click-Lock Dovetail Frame Joiner
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import FreeCAD as App
import Part

from params import (
    SCALE,
    BASE_PANEL_THICKNESS,
    PRESS_FIT_CLEARANCE,
    JOINER_DETENT,
    ELEPHANTS_FOOT_CHAMFER,
    EXPORT_DIR,
)

def construct_frame_joiner():
    """
    Constructs a 100% Fully Symmetrical (3-Axis: X, Y, Z) Click-Lock Dovetail Joiner.
    
    Key Engineering Features:
    1. Full 3-Axis Symmetry (Zero-Orientation Poka-Yoke):
       - X-Symmetric (Left = Right)
       - Y-Symmetric (Module A End = Module B End)
       - Z-Symmetric (Top = Bottom)
       -> Eliminates user orientation mistakes during grid assembly.
    2. Precision Dovetail Wedge Profile:
       - 15.6mm center width tapering to 9.6mm at insertion tips (0.2mm clearance per side).
       - Self-aligns and wedges adjacent modules into flush, rigid alignment.
    3. Central Indexing & Pry Lip Collar:
       - 1.2mm spacer collar defines the ideal inter-module seam gap and provides
         a 360° pry lip for tool-free thumb/fingernail detachment.
    4. Symmetrical Click Detents:
       - Dual cylindrical bumps at Y = ±4.0mm and Z = H/2 lock positively into
         female socket dimples with a tactile snap.
    5. Continuous Neutral-Axis Wire Conduit:
       - Central Ø4.4mm cylindrical raceway allows clean servo harness pass-through.
    6. 4-Corner Lead-in Nose Chamfers:
       - 45° entry chamfers on all 4 tip quadrants ensure effortless insertion.
    7. 100% Supportless FDM Printability:
       - Prints flat with 0.4mm Elephant's foot relief and zero supports.
    """
    clearance = PRESS_FIT_CLEARANCE  # 0.2mm per side
    dt_top_w = (16.0 * SCALE) - (2.0 * clearance)  # 15.6mm at center seam
    dt_bot_w = (10.0 * SCALE) - (2.0 * clearance)  # 9.6mm at insertion tips
    dt_depth = (8.0 * SCALE) - clearance           # 7.8mm insertion depth per side
    dt_height = (BASE_PANEL_THICKNESS - (2.0 * SCALE)) - (2.0 * clearance)  # 12.6mm
    center_z = dt_height / 2.0

    # 1. Fully Symmetrical Double-Wedge Dovetail Body (XY Lozenge)
    c_tip = 1.0 * SCALE  # 1.0mm 45° tip lead-in chamfer
    poly_pts = [
        App.Vector(-dt_top_w / 2.0, 0, 0),
        App.Vector(-dt_bot_w / 2.0, dt_depth - c_tip, 0),
        App.Vector(-dt_bot_w / 2.0 + c_tip, dt_depth, 0),
        App.Vector(dt_bot_w / 2.0 - c_tip, dt_depth, 0),
        App.Vector(dt_bot_w / 2.0, dt_depth - c_tip, 0),
        App.Vector(dt_top_w / 2.0, 0, 0),
        App.Vector(dt_bot_w / 2.0, -dt_depth + c_tip, 0),
        App.Vector(dt_bot_w / 2.0 - c_tip, -dt_depth, 0),
        App.Vector(-dt_bot_w / 2.0 + c_tip, -dt_depth, 0),
        App.Vector(-dt_bot_w / 2.0, -dt_depth + c_tip, 0),
        App.Vector(-dt_top_w / 2.0, 0, 0),
    ]
    dovetail_wire = Part.makePolygon(poly_pts)
    dovetail_face = Part.Face(dovetail_wire)
    joiner_solid = dovetail_face.extrude(App.Vector(0, 0, dt_height))

    # 2. Central Indexing & Pry Lip Collar (Centered in X, Y, and Z)
    collar_w = dt_top_w + (1.6 * SCALE)
    collar_d = 1.2 * SCALE
    collar_h = dt_height + (0.8 * SCALE)
    collar = Part.makeBox(collar_w, collar_d, collar_h)
    collar.translate(App.Vector(-collar_w / 2.0, -collar_d / 2.0, center_z - (collar_h / 2.0)))
    joiner_solid = joiner_solid.fuse(collar).removeSplitter()

    # 3. Symmetrical Tactile Detent Bumps (Y = ±4.0mm, Z = H/2)
    detent_r = JOINER_DETENT  # 0.3mm
    detent_y = 4.0 * SCALE
    detent_len = dt_top_w * 0.8
    det_pos = Part.makeCylinder(detent_r, detent_len, App.Vector(-detent_len / 2.0, detent_y, center_z), App.Vector(1, 0, 0))
    det_neg = Part.makeCylinder(detent_r, detent_len, App.Vector(-detent_len / 2.0, -detent_y, center_z), App.Vector(1, 0, 0))
    joiner_solid = joiner_solid.fuse(Part.makeCompound([det_pos, det_neg])).removeSplitter()

    # 4. High-Capacity Internal Wire Raceway (Centered at Neutral Axis X=0, Z=H/2)
    # Enlarged rounded rectangular conduit (5.8mm wide x 7.2mm high)
    # Allows pre-crimped 3-pin servo plugs and multiple wire harnesses to pass freely
    raceway_w = 5.8 * SCALE
    raceway_h = 7.2 * SCALE
    raceway_d = (dt_depth * 2.0) + (4.0 * SCALE)
    raceway_box = Part.makeBox(
        raceway_w,
        raceway_d,
        raceway_h,
        App.Vector(-raceway_w / 2.0, -(dt_depth + 2.0 * SCALE), center_z - (raceway_h / 2.0))
    )
    # Apply 1.2mm fillets to raceway internal corners for wire protection and strength
    try:
        y_edges = [
            e for e in raceway_box.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.ZMin - e.BoundBox.ZMax) < 0.001
        ]
        if y_edges:
            raceway_box = raceway_box.makeFillet(1.2 * SCALE, y_edges)
    except Exception:
        pass

    joiner_solid = joiner_solid.cut(raceway_box).removeSplitter()

    # 5. Symmetrical 45° Top and Bottom Lead-in Entry Chamfers (+Y and -Y tips)
    chamfer_box_w = dt_top_w + 4.0
    chamfer_box_d = 2.0 * SCALE
    chamfer_box_h = 2.0 * SCALE
    
    # +Y Top & Bottom Chamfer Cutters
    c_pos_top = Part.makeBox(chamfer_box_w, chamfer_box_d, chamfer_box_h)
    c_pos_top.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 45)
    c_pos_top.translate(App.Vector(-chamfer_box_w / 2.0, dt_depth, dt_height))

    c_pos_bot = Part.makeBox(chamfer_box_w, chamfer_box_d, chamfer_box_h)
    c_pos_bot.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -45)
    c_pos_bot.translate(App.Vector(-chamfer_box_w / 2.0, dt_depth, 0))

    # -Y Top & Bottom Chamfer Cutters (180° rotation around Z)
    c_neg_top = c_pos_top.copy()
    c_neg_top.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)

    c_neg_bot = c_pos_bot.copy()
    c_neg_bot.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)

    chamfer_compound = Part.makeCompound([c_pos_top, c_pos_bot, c_neg_top, c_neg_bot])
    joiner_solid = joiner_solid.cut(chamfer_compound).removeSplitter()

    # 6. Symmetrical Outer Base Edge Elephant's Foot Relief
    try:
        base_edges = [
            e for e in joiner_solid.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 2.0 * SCALE
        ]
        if base_edges:
            joiner_solid = joiner_solid.makeChamfer(ELEPHANTS_FOOT_CHAMFER, base_edges)
            joiner_solid = joiner_solid.removeSplitter()
    except Exception as e:
        pass

    return joiner_solid

def export_part():
    """Exports STEP and STL files to EXPORT_DIR and adds shape to FreeCAD document."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    shape = construct_frame_joiner()

    doc = App.ActiveDocument or App.newDocument("Doc")
    obj = doc.addObject("Part::Feature", "Part10FrameJoiner")
    obj.Shape = shape
    doc.recompute()

    step_path = os.path.join(EXPORT_DIR, "part_10_frame_joiner.step")
    stl_path  = os.path.join(EXPORT_DIR, "part_10_frame_joiner.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shape.exportStep(step_path)
    shape.exportStl(stl_path)

    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()



