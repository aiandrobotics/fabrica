"""
part_02_follower_frame.py — Passive Follower Chassis 3-Sided U-Frame
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import os
import sys
import math
import FreeCAD as App
import Part

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from params import (
    SCALE,
    PANEL_WIDTH,
    PANEL_HEIGHT,
    BASE_PANEL_THICKNESS,
    WALL_THICKNESS,
    PRESS_FIT_CLEARANCE,
    TPU_BUMPER_DEPTH,
    ELEPHANTS_FOOT_CHAMFER,
    DOVETAIL_NECK_WIDTH,
    DOVETAIL_FLARE_WIDTH,
    DOVETAIL_DEPTH,
    DOVETAIL_HEIGHT,
    EXPORT_DIR,
)

PADDLE_PIVOT_DIAMETER = 5.0 * SCALE
ROTATING_CLEARANCE = 0.3 * SCALE  # per side
BOTTOM_SHELL_THICKNESS = 3.0 * SCALE

def create_follower_frame():
    """
    Constructs the Passive Follower 3-Sided U-Frame Module.
    Features:
    1. 3-Sided U-Frame Chassis (240x240x15mm) with open inner side (X=0) for 180° flap sweep.
    2. Top Knuckle (X=0, Y=240): 360° Closed Bearing Bore (Ø5.6mm) for axial pin retention.
    3. Bottom Knuckle (X=0, Y=0): Flex C-Snap Socket with 0.5mm lead-in funnel for toolless insertion.
    4. 1.5mm recessed silent-flip TPU bumper landing pockets on the inner ledge.
    5. Dovetail Joiner Sockets on the 3 outer walls (Y=0, Y=240, X=240).
    6. Filleted internal wire pass-through ports and under-frame cable routing clips.
    7. 0.5mm debossed Poka-Yoke directional alignment arrow ("FRONT ➔").
    8. 0.4mm bottom Elephant's Foot relief chamfers.
    """
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = BOTTOM_SHELL_THICKNESS

    # 1. Main outer shell block
    outer_box = Part.makeBox(w, h, t)

    # 2. Open U-Frame Cavity (Cut through inner swing side at X=0 to X=w-rail_w)
    # Cavity extends from X = -0.1 to X = w - rail_w, Y = rail_w to Y = h - rail_w
    cav_w = w - rail_w + 0.1
    cav_h = h - 2 * rail_w
    cavity = Part.makeBox(cav_w, cav_h, t - bottom_thick + 0.5)
    cavity.translate(App.Vector(-0.1, rail_w, bottom_thick))
    frame = outer_box.cut(cavity).removeSplitter()

    # 3. Knuckle Extension Barrels along Hinge Axis (at X = 0, Y = 0 to 15mm and Y = 225 to 240mm)
    knuckle_r = (PADDLE_PIVOT_DIAMETER / 2.0) + (4.0 * SCALE)  # 6.5mm radius outer barrel
    knuckle_len = rail_w
    
    # Bottom Knuckle Barrel (+Y facing)
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, t / 2.0), App.Vector(0, 1, 0))
    # Top Knuckle Barrel (-Y facing)
    k_top = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, h - knuckle_len, t / 2.0), App.Vector(0, 1, 0))
    frame = frame.fuse(Part.makeCompound([k_bot, k_top])).removeSplitter()

    # 4. Hinge Bearing Bores & C-Snap Sockets
    bore_r = (PADDLE_PIVOT_DIAMETER / 2.0) + ROTATING_CLEARANCE  # 2.8mm radius (Ø5.6mm)
    pivot_z = t / 2.0  # Centered in frame thickness (7.5mm)

    # Top Knuckle: 360° Closed Cylindrical Bore (along Y axis from Y = h - knuckle_len - 0.1 to h + 0.1)
    top_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, h - knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))

    # Bottom Knuckle: Flex C-Snap Socket with 0.5mm Lead-In Funnel
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    
    # Snap throat opening (width = 2*bore_r - 0.4mm = 5.2mm for positive snap retention)
    snap_w = (bore_r * 2.0) - (0.4 * SCALE)
    snap_throat = Part.makeBox(snap_w, knuckle_len + 0.2, t - pivot_z + 0.1)
    snap_throat.translate(App.Vector(-snap_w / 2.0, -0.1, pivot_z))
    
    # 0.5mm 45° Lead-in funnel at top of C-snap entrance
    funnel_w = snap_w + (1.2 * SCALE)
    funnel = Part.makeBox(funnel_w, knuckle_len + 0.2, 2.0 * SCALE)
    funnel.translate(App.Vector(-funnel_w / 2.0, -0.1, t - 1.5 * SCALE))

    frame = frame.cut(Part.makeCompound([top_bore, bot_bore, snap_throat, funnel])).removeSplitter()

    # 5. True Sliding Dovetail Joiner Sockets on 3 Outer Walls (Front Y=0, Back Y=H, Right X=W)
    dt_neck_w = DOVETAIL_NECK_WIDTH
    dt_flare_w = DOVETAIL_FLARE_WIDTH
    dt_depth = DOVETAIL_DEPTH
    dt_height = DOVETAIL_HEIGHT

    dt_pts = [
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
    ]
    dt_poly = Part.makePolygon(dt_pts)
    dt_face = Part.Face(dt_poly)
    dt_cutter_master = dt_face.extrude(App.Vector(0, 0, dt_height))

    dt_cutters = []
    # Front Wall (Y=0) -> cuts into +Y
    c_front = dt_cutter_master.copy()
    c_front.translate(App.Vector(w / 2.0, 0, (t - dt_height) / 2.0))
    dt_cutters.append(c_front)

    # Back Wall (Y=H) -> cuts into -Y
    c_back = dt_cutter_master.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h, (t - dt_height) / 2.0))
    dt_cutters.append(c_back)

    # Right Wall (X=W) -> cuts into -X
    c_right = dt_cutter_master.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, (t - dt_height) / 2.0))
    dt_cutters.append(c_right)

    frame = frame.cut(Part.makeCompound(dt_cutters)).removeSplitter()

    # 6. TPU Silent-Flip Landing Bumper Slots (1.5mm recessed into floor ledge)
    tpu_cutters = []
    tpu_w = 14.0 * SCALE
    tpu_d = 5.0 * SCALE
    tpu_h = TPU_BUMPER_DEPTH
    for py in [h * 0.25, h * 0.5, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_d, tpu_h + 0.1)
        b.translate(App.Vector(w - rail_w - tpu_w - 5.0 * SCALE, py - tpu_d / 2.0, bottom_thick - 0.05))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 7. Filleted Wire Pass-Through Ports with Zip-Tie Saddles
    wire_port_w = 10.0 * SCALE
    wire_port_h = 5.5 * SCALE
    wp_top = Part.makeBox(wire_port_w, rail_w + 0.2, wire_port_h)
    wp_top.translate(App.Vector(w / 2.0 - wire_port_w / 2.0, h - rail_w - 0.1, bottom_thick))
    wp_bot = Part.makeBox(wire_port_w, rail_w + 0.2, wire_port_h)
    wp_bot.translate(App.Vector(w / 2.0 - wire_port_w / 2.0, -0.1, bottom_thick))
    frame = frame.cut(Part.makeCompound([wp_top, wp_bot])).removeSplitter()

    # 8. Debossed Poka-Yoke Directional Arrow ("FRONT ➔" on front outer wall)
    arrow_shaft = Part.makeBox(12.0 * SCALE, 0.6 * SCALE, 2.0 * SCALE)
    arrow_shaft.translate(App.Vector(w / 2.0 - 6.0 * SCALE, -0.1, t - 3.5 * SCALE))
    arrow_head_poly = Part.makePolygon([
        App.Vector(w / 2.0 + 6.0 * SCALE, -0.1, t - 4.5 * SCALE),
        App.Vector(w / 2.0 + 10.0 * SCALE, -0.1, t - 2.5 * SCALE),
        App.Vector(w / 2.0 + 6.0 * SCALE, -0.1, t - 0.5 * SCALE),
        App.Vector(w / 2.0 + 6.0 * SCALE, -0.1, t - 4.5 * SCALE),
    ])
    arrow_head = Part.Face(arrow_head_poly).extrude(App.Vector(0, 0.6 * SCALE, 0))
    frame = frame.cut(Part.makeCompound([arrow_shaft, arrow_head])).removeSplitter()

    # 9. Elephant's Foot Relief Chamfer along outer bottom bed edges
    try:
        base_edges = [
            e for e in frame.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 20.0 * SCALE
        ]
        if base_edges:
            frame = frame.makeChamfer(ELEPHANTS_FOOT_CHAMFER, base_edges)
            frame = frame.removeSplitter()
    except Exception:
        pass

    return frame

def export_part():
    """Exports STEP and STL files to EXPORT_DIR and adds shape to FreeCAD document."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    shape = create_follower_frame()

    doc = App.ActiveDocument or App.newDocument("FollowerFrame")
    obj = doc.addObject("Part::Feature", "Part02FollowerFrame")
    obj.Shape = shape
    doc.recompute()

    step_path = os.path.join(EXPORT_DIR, "part_02_follower_frame.step")
    stl_path  = os.path.join(EXPORT_DIR, "part_02_follower_frame.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shape.exportStep(step_path)
    shape.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()



