"""
part_10_frame_joiner.py — 20mm Extended Bridge Click-Lock Dovetail Frame Joiner
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
    MODULE_GAP,
    ELEPHANTS_FOOT_CHAMFER,
    EXPORT_DIR,
)

def construct_frame_joiner():
    """
    Constructs a 100% Fully Symmetrical (3-Axis: X, Y, Z) 20mm Bridge Frame Joiner.
    
    Key Engineering Features:
    1. 20mm Inter-Module Fabric Relief Bridge (Y in [-10.0, +10.0] mm):
       - Spaces adjacent module frames exactly 20.0mm apart for heavy garment bend relief
         (hoodies, denim, towels) and flap-to-flap sweep clearance.
       - 100% completely flat and flush top bridge deck across the inter-module gap,
         providing a smooth runway so clothes glide across seamlessly without snagging.
    2. Precision Double Dovetail Smooth Wedge Keys (Y in [+10.0, +17.8] & [-10.0, -17.8] mm):
       - 15.6mm width at frame seam tapering down to 9.6mm at insertion tips (0.2mm clearance).
       - Completely smooth flat side walls slide in silk-smoothly and wedge firmly into sockets.
    3. 3-Servo High-Capacity Wire Raceway (6.8mm x 8.6mm):
       - Generous filleted raceway fits 3 full servo motor harnesses (9 wires + connectors).
    4. 4-Corner Lead-in Nose Chamfers:
       - 45° entry chamfers on all 4 tip quadrants ensure smooth insertion.
    5. 100% Supportless FDM Printability:
       - Prints flat with 0.4mm Elephant's foot relief and zero supports.
    """
    clearance = PRESS_FIT_CLEARANCE  # 0.2mm per side
    gap_half = MODULE_GAP / 2.0      # 10.0mm half-gap bridge length
    dt_top_w = (16.0 * SCALE) - (2.0 * clearance)  # 15.6mm at frame boundary
    dt_bot_w = (10.0 * SCALE) - (2.0 * clearance)  # 9.6mm at insertion tips
    dt_depth = (8.0 * SCALE) - clearance           # 7.8mm insertion depth per side
    dt_height = (BASE_PANEL_THICKNESS - (2.0 * SCALE)) - (2.0 * clearance)  # 12.6mm
    total_tip_y = gap_half + dt_depth              # 17.8mm from center
    center_z = dt_height / 2.0

    # 1. Fully Symmetrical 20mm Bridge + Dovetail Body (XY Lozenge)
    # Forms a 100% flat, flush bridge deck across the 20mm inter-module gap
    c_tip = 1.0 * SCALE  # 1.0mm 45° tip lead-in chamfer
    poly_pts = [
        # Center bridge right edge
        App.Vector(-dt_top_w / 2.0, 0, 0),
        App.Vector(-dt_top_w / 2.0, gap_half, 0),
        # +Y Dovetail wedge & chamfered nose
        App.Vector(-dt_bot_w / 2.0, total_tip_y - c_tip, 0),
        App.Vector(-dt_bot_w / 2.0 + c_tip, total_tip_y, 0),
        App.Vector(dt_bot_w / 2.0 - c_tip, total_tip_y, 0),
        App.Vector(dt_bot_w / 2.0, total_tip_y - c_tip, 0),
        App.Vector(dt_top_w / 2.0, gap_half, 0),
        # Center bridge left edge
        App.Vector(dt_top_w / 2.0, 0, 0),
        App.Vector(dt_top_w / 2.0, -gap_half, 0),
        # -Y Dovetail wedge & chamfered nose
        App.Vector(dt_bot_w / 2.0, -total_tip_y + c_tip, 0),
        App.Vector(dt_bot_w / 2.0 - c_tip, -total_tip_y, 0),
        App.Vector(-dt_bot_w / 2.0 + c_tip, -total_tip_y, 0),
        App.Vector(-dt_bot_w / 2.0, -total_tip_y + c_tip, 0),
        App.Vector(-dt_top_w / 2.0, -gap_half, 0),
        App.Vector(-dt_top_w / 2.0, 0, 0),
    ]
    dovetail_wire = Part.makePolygon(poly_pts)
    dovetail_face = Part.Face(dovetail_wire)
    joiner_solid = dovetail_face.extrude(App.Vector(0, 0, dt_height))

    # 2. High-Capacity Internal Wire Raceway (6.8mm x 8.6mm with 1.0mm Fillets)
    # Designed specifically to fit 3 full servo motor harnesses (9 wires + connectors)
    raceway_w = 6.8 * SCALE
    raceway_h = 8.6 * SCALE
    raceway_d = (total_tip_y * 2.0) + (4.0 * SCALE)
    raceway_box = Part.makeBox(
        raceway_w,
        raceway_d,
        raceway_h,
        App.Vector(-raceway_w / 2.0, -(total_tip_y + 2.0 * SCALE), center_z - (raceway_h / 2.0))
    )
    try:
        y_edges = [
            e for e in raceway_box.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.ZMin - e.BoundBox.ZMax) < 0.001
        ]
        if y_edges:
            raceway_box = raceway_box.makeFillet(1.0 * SCALE, y_edges)
    except Exception:
        pass

    joiner_solid = joiner_solid.cut(raceway_box).removeSplitter()

    # 5. Symmetrical 45° Top and Bottom Lead-in Entry Chamfers (+Y and -Y tips)
    chamfer_box_w = dt_top_w + 4.0
    chamfer_box_d = 2.0 * SCALE
    chamfer_box_h = 2.0 * SCALE
    
    # +Y Top & Bottom Chamfer Cutters at total_tip_y
    c_pos_top = Part.makeBox(chamfer_box_w, chamfer_box_d, chamfer_box_h)
    c_pos_top.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 45)
    c_pos_top.translate(App.Vector(-chamfer_box_w / 2.0, total_tip_y, dt_height))

    c_pos_bot = Part.makeBox(chamfer_box_w, chamfer_box_d, chamfer_box_h)
    c_pos_bot.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -45)
    c_pos_bot.translate(App.Vector(-chamfer_box_w / 2.0, total_tip_y, 0))

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
    except Exception:
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




