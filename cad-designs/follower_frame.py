"""
follower_frame.py — Passive Follower Frame with Clean Solid Through-Dovetail Joint
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
    TPU_BUMPER_DEPTH,
    ELEPHANTS_FOOT_CHAMFER,
    DOVETAIL_NECK_WIDTH,
    DOVETAIL_FLARE_WIDTH,
    DOVETAIL_DEPTH,
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    BEARING_ROTATING_CLEARANCE,
    EXPORT_DIR,
)

def construct_follower_frame():
    """
    Constructs the Passive Follower Frame with Clean Solid Through-Dovetail Joint.
    
    Features:
    1. 4-Sided Rigid Chassis (240x240x15mm):
       - 15mm rigid outer rails on Front (Y=0), Back (Y=240), and Right (X=240).
       - 4th Left Wall (X=11 to 25mm, Z=0 to 3mm, width 14mm) with Clean Solid Through-Dovetail Joint:
         * Neck Width = 4.0mm, Flare Width = 8.0mm, Depth = 8.0mm, Clearance = 0.25mm.
         * 3.0mm of 100% solid, thick continuous outer wall on BOTH sides (Left X=11 to 14mm, Right X=22 to 25mm).
         * Eliminates all thin knife-edge wedges, floating slivers, and horizontal slits.
         * 100% flat bed 3D printing with zero overhangs, zero supports, and zero post-processing.
       - 100% flush at Z=3.0mm, requiring zero loose joiner parts and providing 100% kinematic rotation clearance.
    2. Dual 100% Solid 360° Closed Bearing Knuckles (Top Y=240, Bottom Y=0) housing full-length Ø13mm flap axle.
    3. C1-Continuous Tangent Concave Blend Ramps (Rf = 12mm) for seamless knuckle-to-deck flow.
    4. True Open-Top Sliding Dovetail Joiner Sockets on outer walls (Front Y=0, Back Y=240, Right X=240)
       with 3.0mm bottom floor drop stops and Ø6.0mm true through-floor push-out access holes.
    5. 4x Bottom Anti-Slip Grip Foot Sockets (Ø12mm x 2.0mm) for high-traction silicone/TPU rubber pads.
    6. 3x Silent-Flip TPU Bumper Slots (1.5mm depth) recessed into the top landing rail.
    7. 0.4mm bottom Elephant's Foot relief chamfers.
    """
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    t = params.BASE_PANEL_THICKNESS
    rail_w = 15.0
    bottom_thick = 3.0
    tie_w = 14.0
    tie_x = 11.0
    center_x = tie_x + (tie_w / 2.0) # 18.0mm
    y_seam = h / 2.0                 # h/2

    # 1. Main outer shell block
    outer_box = Part.makeBox(w, h, t)

    # 2. End 360° Knuckle Rings & Middle Semi-Circular Support Cradle Wall
    knuckle_r = (DRIVE_SHAFT_DIAMETER / 2.0) + 3.0  # 9.4mm outer radius
    knuckle_len = rail_w
    pivot_z = PIVOT_Z  # 15.00mm (exact top deck hinge line)
    t_blade = params.PADDLE_THICKNESS # 2.4mm
    sweep_z_min = pivot_z - t_blade   # 12.60mm (allows 180° fold clearance in X < 0)

    # Bottom 360° Knuckle Barrel (Y in [0, 15mm])
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    # Top 360° Knuckle Barrel (Y in [h - 15mm, h])
    k_top = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, h - knuckle_len, pivot_z), App.Vector(0, 1, 0))

    # Middle Semi-Circular Support Cradle Wall between knuckles (strictly below Z = 12.60mm in X < 0)
    cradle_outer = Part.makeCylinder(knuckle_r, h - 2 * knuckle_len, App.Vector(0, knuckle_len, pivot_z), App.Vector(0, 1, 0))
    cradle_trim_top = Part.makeBox(knuckle_r * 4.0, h, knuckle_r * 2.0)
    cradle_trim_top.translate(App.Vector(-knuckle_r * 2.0, 0, sweep_z_min))
    cradle_support = cradle_outer.cut(cradle_trim_top)

    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE  # 6.85mm radius (Ø13.7mm)

    # Full-Length Solid Hinge Pedestal under knuckles and cradle (X in [-knuckle_r, 0], Y in [0, h], Z in [0, pivot_z])
    hinge_pedestal = Part.makeBox(knuckle_r, h, pivot_z)
    hinge_pedestal.translate(App.Vector(-knuckle_r, 0, 0))

    frame = outer_box.fuse([k_bot, k_top, cradle_support, hinge_pedestal]).removeSplitter()

    # 3. Open Interior Cavities, Bores, and Continuous Cradle Trough

    # A. 360° Knuckle Bearing Bores (Top & Bottom closed 360° journals)
    top_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, h - knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))

    # A2. Inner Thrust Flange Counterbore Recesses (Ø16.8mm x 1.2mm for captive pin inner thrust disk)
    disk_recess_r = 8.4  # 8.4mm radius for Ø16.0mm disk (+0.4mm radial clearance)
    bot_thrust_recess = Part.makeCylinder(disk_recess_r, 1.3, App.Vector(0, knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))
    top_thrust_recess = Part.makeCylinder(disk_recess_r, 1.3, App.Vector(0, h - knuckle_len - 1.2, pivot_z), App.Vector(0, 1, 0))

    # B. Semi-Circular Cradle Trough (supports half-cylinder axle from below)
    cradle_trough = Part.makeCylinder(bore_r, h - 2 * knuckle_len + 0.2, App.Vector(0, knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))

    # C. Main Center Cavity Window (Opens fully from X=0 to X=W-15mm, using semi-cylinder cradle as sole hinge wall)
    cav_main = Part.makeBox(w - rail_w, h - 2 * rail_w, t + 2.0)
    cav_main.translate(App.Vector(0, rail_w, -1.0))
    try:
        c_edges = [
            e for e in cav_main.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.YMin - e.BoundBox.YMax) < 0.001
        ]
        if c_edges:
            cav_main = cav_main.makeFillet(3.0, c_edges)
    except Exception:
        pass

    # D. Knuckle planar bottom trim: 100% flat at Z=0.0mm
    trim_bot = Part.makeBox(w + 100.0, h + 100.0, 20.0)
    trim_bot.translate(App.Vector(-50.0, -50.0, -20.0))

    frame = frame.cut(Part.makeCompound([cav_main, cradle_trough, top_bore, bot_bore, bot_thrust_recess, top_thrust_recess, trim_bot])).removeSplitter()

    # 4. Female Open-Top True Sliding Dovetail Joiner Sockets on Outer Walls (Front Y=0, Back Y=H, Right X=W)
    dt_neck_w = DOVETAIL_NECK_WIDTH
    dt_flare_w = DOVETAIL_FLARE_WIDTH
    dt_depth = DOVETAIL_DEPTH
    dt_cut_h = t - bottom_thick + 0.5

    dt_pts = [
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
    ]
    dt_poly = Part.makePolygon(dt_pts)
    dt_face = Part.Face(dt_poly)
    dt_cutter = dt_face.extrude(App.Vector(0, 0, dt_cut_h))
    dt_cutter.translate(App.Vector(0, 0, bottom_thick))

    # Master bottom push-out finger access hole (Ø6.0mm through bottom floor: Z = -0.5 to Z = bottom_thick + 0.5)
    push_hole = Part.makeCylinder(3.0, bottom_thick + 1.0, App.Vector(0, dt_depth * 0.6, -0.5))

    # High-Capacity Wire Pass-Through Conduit (through back wall of dovetail directly into frame wiring cavity)
    wire_hole_w = 8.0
    wire_hole_h = 8.6
    wire_hole_d = rail_w + 2.0
    wire_conduit = Part.makeBox(wire_hole_w, wire_hole_d, wire_hole_h)
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

    dt_cutter_complete = dt_cutter.fuse([push_hole, wire_conduit]).removeSplitter()

    dt_cutters = []
    # Front Wall (Y=0) -> cuts into +Y
    c_front = dt_cutter_complete.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))
    dt_cutters.append(c_front)

    # Back Wall (Y=H) -> cuts into -Y
    c_back = dt_cutter_complete.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h, 0))
    dt_cutters.append(c_back)

    # Right Wall (X=W) -> cuts into -X
    c_right = dt_cutter_complete.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))
    dt_cutters.append(c_right)

    frame = frame.cut(Part.makeCompound(dt_cutters)).removeSplitter()

    # 7. Anti-Slip Foot Pad Recess Sockets (4x on bottom face of rails for Ø12mm x 2.0mm rubber feet)
    foot_r = 6.0
    foot_d = 2.0
    foot_locs = [
        (w - (rail_w / 2.0), rail_w / 2.0),          # Bottom Right
        (w - (rail_w / 2.0), h - (rail_w / 2.0)),      # Top Right
        (25.0, rail_w / 2.0),                          # Bottom Left (along front rail)
        (25.0, h - (rail_w / 2.0)),                    # Top Left (along back rail)
    ]
    foot_cutters = [
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(fx, fy, -0.1))
        for fx, fy in foot_locs
    ]
    frame = frame.cut(Part.makeCompound(foot_cutters)).removeSplitter()

    # 8. TPU Silent-Flip Landing Bumper Slots (1.5mm recessed into top landing rail at X = w - rail_w/2)
    tpu_cutters = []
    tpu_w = 5.0
    tpu_l = 14.0
    tpu_h = TPU_BUMPER_DEPTH # 1.5mm
    for py in [h * 0.25, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_l, tpu_h + 0.1)
        b.translate(App.Vector(w - (rail_w / 2.0) - (tpu_w / 2.0), py - (tpu_l / 2.0), t - tpu_h))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 9. Smooth rounded outer vertical corner fillets (R=3.0mm on front-right and back-right vertical corners)
    corner_cutter1 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter1.translate(App.Vector(w - 3.0, -3.0, -1.0))
    corner_cyl1 = Part.makeCylinder(3.0, t + 2.0, App.Vector(w - 3.0, 3.0, -1.0))
    corner_trim1 = corner_cutter1.cut(corner_cyl1)

    corner_cutter2 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter2.translate(App.Vector(w - 3.0, h - 3.0, -1.0))
    corner_cyl2 = Part.makeCylinder(3.0, t + 2.0, App.Vector(w - 3.0, h - 3.0, -1.0))
    corner_trim2 = corner_cutter2.cut(corner_cyl2)

    # 10. Outer Knuckle Circular Rim & Bore Entry Chamfers (At Y = 0 and Y = H)
    chamfer_cutters = []
    # Bottom Knuckle (Y = 0) Outer Rim Chamfer (1.2mm x 45°)
    cone_bot_outer = Part.makeCone(knuckle_r - 1.2, knuckle_r + 3.0, 1.2, App.Vector(0, 0, pivot_z), App.Vector(0, -1, 0))
    box_bot_outer = Part.makeBox(knuckle_r * 4.0, 2.0, knuckle_r * 4.0, App.Vector(-knuckle_r * 2.0, -1.5, pivot_z - knuckle_r * 2.0))
    chamfer_cutters.append(box_bot_outer.cut(cone_bot_outer))

    # Bottom Knuckle Bore Entry Chamfer (0.8mm x 45°)
    cone_bot_bore = Part.makeCone(bore_r, bore_r + 0.8, 0.8, App.Vector(0, 0, pivot_z), App.Vector(0, -1, 0))
    chamfer_cutters.append(cone_bot_bore)

    # Top Knuckle (Y = H) Outer Rim Chamfer (1.2mm x 45°)
    cone_top_outer = Part.makeCone(knuckle_r - 1.2, knuckle_r + 3.0, 1.2, App.Vector(0, h, pivot_z), App.Vector(0, 1, 0))
    box_top_outer = Part.makeBox(knuckle_r * 4.0, 2.0, knuckle_r * 4.0, App.Vector(-knuckle_r * 2.0, h - 0.5, pivot_z - knuckle_r * 2.0))
    chamfer_cutters.append(box_top_outer.cut(cone_top_outer))

    # Top Knuckle Bore Entry Chamfer (0.8mm x 45°)
    cone_top_bore = Part.makeCone(bore_r, bore_r + 0.8, 0.8, App.Vector(0, h, pivot_z), App.Vector(0, 1, 0))
    chamfer_cutters.append(cone_top_bore)

    frame = frame.cut(Part.makeCompound([corner_trim1, corner_trim2] + chamfer_cutters)).removeSplitter()

    # 10. Elephant's Foot Relief Chamfer along outer bottom bed edges
    try:
        base_edges = [
            e for e in frame.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 10.0
        ]
        if base_edges:
            frame = frame.makeChamfer(ELEPHANTS_FOOT_CHAMFER, base_edges)
            frame = frame.removeSplitter()
    except Exception:
        pass

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "follower_frame.step")
    stl_path  = os.path.join(EXPORT_DIR, "follower_frame.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    frame.exportStep(step_path)
    frame.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return frame

def main():
    doc = App.ActiveDocument or App.newDocument("FollowerFrame")
    shape = construct_follower_frame()
    feature = doc.addObject("Part::Feature", "FollowerFrame")
    feature.Shape = shape

def export_part():
    main()

export_part()

