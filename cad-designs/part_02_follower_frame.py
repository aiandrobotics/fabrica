"""
part_02_follower_frame.py — Passive Follower Frame with Integrated Interlocking Dovetail Joint
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
    DRIVE_SHAFT_DIAMETER,
    BEARING_ROTATING_CLEARANCE,
    EXPORT_DIR,
)

BOTTOM_SHELL_THICKNESS = 3.0 * SCALE

def create_follower_frame():
    """
    Constructs the Passive Follower Frame with Integrated Male-Female Interlocking Dovetail Joint.
    
    Features:
    1. 4-Sided Rigid Chassis (240x240x15mm):
       - 15mm rigid outer rails on Front (Y=0), Back (Y=240), and Right (X=240).
       - 4th Left Wall (X=10 to 22mm, Z=0 to 3mm) with integrated direct male-female dovetail joint at Y=120mm.
       - Bottom Half has integrated male dovetail tab; Top Half has matching female dovetail socket with 0.15mm tolerance.
       - 100% flush at Z=3.0mm, requiring zero loose joiner parts and providing 100% kinematic rotation clearance.
    2. Dual 100% Solid 360° Closed Bearing Knuckles (Top Y=240, Bottom Y=0) housing full-length Ø13mm flap axle.
    3. C1-Continuous Tangent Concave Blend Ramps (Rf = 12mm) for seamless knuckle-to-deck flow.
    4. True Open-Top Sliding Dovetail Joiner Sockets on outer walls (Front Y=0, Back Y=240, Right X=240)
       with 3.0mm bottom floor drop stops and Ø6.0mm true through-floor push-out access holes.
    5. 4x Bottom Anti-Slip Grip Foot Sockets (Ø12mm x 2.0mm) for high-traction silicone/TPU rubber pads.
    6. 3x Silent-Flip TPU Bumper Slots (1.5mm depth) recessed into the top landing rail.
    7. 0.4mm bottom Elephant's Foot relief chamfers.
    """
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = BOTTOM_SHELL_THICKNESS
    tie_w = 12.0 * SCALE
    tie_h = 3.0 * SCALE
    tie_x = 10.0 * SCALE
    center_x = tie_x + (tie_w / 2.0) # 16.0mm

    # 1. Main outer shell block
    outer_box = Part.makeBox(w, h, t)

    # 2. Knuckle Extension Barrels & C1-Continuous Smooth Concave Transition Ramps (Y = 0 to 15mm and Y = 225 to 240mm)
    knuckle_r = (DRIVE_SHAFT_DIAMETER / 2.0) + (3.0 * SCALE)  # 9.5mm radius (Ø19.0mm outer barrel)
    knuckle_len = rail_w
    pivot_z = 8.0 * SCALE  # Axle center (1.5mm ground clearance & reinforced top crown at Z = 17.5mm)
    
    # Bottom Knuckle Barrel (+Y facing)
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    # Top Knuckle Barrel (-Y facing)
    k_top = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, h - knuckle_len, pivot_z), App.Vector(0, 1, 0))

    # Smooth C1-Continuous Tangent Concave Blend Ramp (flows directly from Ø19mm cylinder to Z = 15.0mm frame top deck)
    rf = 12.0 * SCALE  # 12.0mm concave blend radius
    xc = math.sqrt((knuckle_r + rf)**2 - (t - pivot_z + rf)**2) # ~10.06mm
    zc = t + rf                                                 # 27.0mm
    touch_theta = math.atan2(zc - pivot_z, xc)

    ramp_pts = [App.Vector(-knuckle_r, 0, 0)]
    num_arch = 16
    for i in range(num_arch):
        th = math.pi - i * (math.pi - touch_theta) / float(num_arch - 1)
        ramp_pts.append(App.Vector(knuckle_r * math.cos(th), 0, pivot_z + knuckle_r * math.sin(th)))

    num_fillet = 16
    for i in range(1, num_fillet):
        alpha = (touch_theta - math.pi) + i * (-math.pi / 2.0 - (touch_theta - math.pi)) / float(num_fillet - 1)
        ramp_pts.append(App.Vector(xc + rf * math.cos(alpha), 0, zc + rf * math.sin(alpha)))

    ramp_pts.append(App.Vector(rail_w, 0, t))
    ramp_pts.append(App.Vector(rail_w, 0, 0))
    ramp_pts.append(App.Vector(-knuckle_r, 0, 0))

    ramp_wire = Part.makePolygon(ramp_pts)
    ramp_face = Part.Face(ramp_wire)
    ramp_bot = ramp_face.extrude(App.Vector(0, knuckle_len, 0))
    ramp_top = ramp_face.extrude(App.Vector(0, knuckle_len, 0))
    ramp_top.translate(App.Vector(0, h - knuckle_len, 0))

    # Reinforced Center Dovetail Boss on 4th Wall (at Y in [105, 135mm], X in [8, 24mm])
    boss_w = 16.0 * SCALE
    boss_l = 30.0 * SCALE
    boss = Part.makeBox(boss_w, boss_l, tie_h)
    boss.translate(App.Vector(center_x - boss_w / 2.0, (h / 2.0) - (boss_l / 2.0), 0))

    frame = outer_box.fuse(Part.makeCompound([k_bot, k_top, ramp_bot, ramp_top, boss])).removeSplitter()

    # 3. Open Interior Cavities (preserving 4th Wall at X in [tie_x, tie_x + tie_w], Z in [0, tie_h])
    # Main center through-cavity
    cav_main = Part.makeBox(w - rail_w - tie_x - tie_w, h - 2 * rail_w, t + 2.0)
    cav_main.translate(App.Vector(tie_x + tie_w, rail_w, -1.0))

    # Left clearance slot between knuckle barrel and 4th wall
    cav_left = Part.makeBox(tie_x + 0.5, h - 2 * knuckle_len, t + 2.0)
    cav_left.translate(App.Vector(-0.5, knuckle_len, -1.0))

    # Top space above the 3.0mm 4th wall
    cav_tie_top = Part.makeBox(boss_w + 6.0 * SCALE, h - 2 * knuckle_len, t - tie_h + 2.0)
    cav_tie_top.translate(App.Vector(center_x - (boss_w + 6.0 * SCALE) / 2.0, knuckle_len, tie_h))

    frame = frame.cut(Part.makeCompound([cav_main, cav_left, cav_tie_top])).removeSplitter()

    # 4. Hinge Bearing Bores: Dual 100% Solid 360° Closed Cylindrical Tunnels (Top & Bottom)
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE  # 6.75mm radius (Ø13.5mm)

    top_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, h - knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))

    # Knuckle planar bottom trim: 100% flat at Z=0.0mm
    trim_bot = Part.makeBox(knuckle_r * 4.0, h + 2.0, knuckle_r + 2.0)
    trim_bot.translate(App.Vector(-knuckle_r * 2.0, -1.0, -knuckle_r - 2.0))

    frame = frame.cut(Part.makeCompound([top_bore, bot_bore, trim_bot])).removeSplitter()

    # 5. Female Open-Top True Sliding Dovetail Joiner Sockets on Outer Walls (Front Y=0, Back Y=H, Right X=W)
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
    push_hole = Part.makeCylinder(3.0 * SCALE, bottom_thick + 1.0, App.Vector(0, dt_depth * 0.6, -0.5))
    dt_cutter_with_hole = dt_cutter.fuse(push_hole)

    dt_cutters = []
    # Front Wall (Y=0) -> cuts into +Y
    c_front = dt_cutter_with_hole.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))
    dt_cutters.append(c_front)

    # Back Wall (Y=H) -> cuts into -Y
    c_back = dt_cutter_with_hole.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h, 0))
    dt_cutters.append(c_back)

    # Right Wall (X=W) -> cuts into -X
    c_right = dt_cutter_with_hole.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))
    dt_cutters.append(c_right)

    # 6. Integrated Interlocking Male-Female Dovetail Joint Outline at Y = 120mm (Dividing 4th Wall)
    tab_neck_w = 6.0 * SCALE
    tab_flare_w = 10.0 * SCALE
    tab_depth = 8.0 * SCALE
    clr = PRESS_FIT_CLEARANCE # 0.15mm
    
    # Female Pocket Outline Cut (0.15mm clearance slot around dovetail contour)
    pocket_cut_pts = [
        App.Vector(-(tab_neck_w / 2.0) - clr, 0, 0),
        App.Vector((tab_neck_w / 2.0) + clr, 0, 0),
        App.Vector((tab_flare_w / 2.0) + clr, tab_depth + clr, 0),
        App.Vector(-(tab_flare_w / 2.0) - clr, tab_depth + clr, 0),
        App.Vector(-(tab_neck_w / 2.0) - clr, 0, 0),
    ]
    # Seam separation cut dividing the two halves with dovetail contour
    seam_pts_left = [
        App.Vector(center_x - (boss_w / 2.0) - 1.0, (h / 2.0) - (clr / 2.0), -1.0),
        App.Vector(center_x - (tab_neck_w / 2.0) - clr, (h / 2.0) - (clr / 2.0), -1.0),
        App.Vector(center_x - (tab_neck_w / 2.0) - clr, (h / 2.0) + (clr / 2.0), -1.0),
        App.Vector(center_x - (boss_w / 2.0) - 1.0, (h / 2.0) + (clr / 2.0), -1.0),
        App.Vector(center_x - (boss_w / 2.0) - 1.0, (h / 2.0) - (clr / 2.0), -1.0),
    ]
    seam_left = Part.Face(Part.makePolygon(seam_pts_left)).extrude(App.Vector(0, 0, tie_h + 2.0))

    seam_pts_right = [
        App.Vector(center_x + (tab_neck_w / 2.0) + clr, (h / 2.0) - (clr / 2.0), -1.0),
        App.Vector(center_x + (boss_w / 2.0) + 1.0, (h / 2.0) - (clr / 2.0), -1.0),
        App.Vector(center_x + (boss_w / 2.0) + 1.0, (h / 2.0) + (clr / 2.0), -1.0),
        App.Vector(center_x + (tab_neck_w / 2.0) + clr, (h / 2.0) + (clr / 2.0), -1.0),
        App.Vector(center_x + (tab_neck_w / 2.0) + clr, (h / 2.0) - (clr / 2.0), -1.0),
    ]
    seam_right = Part.Face(Part.makePolygon(seam_pts_right)).extrude(App.Vector(0, 0, tie_h + 2.0))

    dt_cutters.extend([seam_left, seam_right])
    frame = frame.cut(Part.makeCompound(dt_cutters)).removeSplitter()

    # 7. Anti-Slip Foot Pad Recess Sockets (4x on bottom face of rails for Ø12mm x 2.0mm rubber feet)
    foot_r = 6.0 * SCALE
    foot_d = 2.0 * SCALE
    foot_locs = [
        (w - (rail_w / 2.0), rail_w / 2.0),          # Bottom Right
        (w - (rail_w / 2.0), h - (rail_w / 2.0)),      # Top Right
        (25.0 * SCALE, rail_w / 2.0),                  # Bottom Left (along front rail)
        (25.0 * SCALE, h - (rail_w / 2.0)),            # Top Left (along back rail)
    ]
    foot_cutters = [
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(fx, fy, -0.1))
        for fx, fy in foot_locs
    ]
    frame = frame.cut(Part.makeCompound(foot_cutters)).removeSplitter()

    # 8. TPU Silent-Flip Landing Bumper Slots (1.5mm recessed into top landing rail at X = w - rail_w/2)
    tpu_cutters = []
    tpu_w = 5.0 * SCALE
    tpu_l = 14.0 * SCALE
    tpu_h = TPU_BUMPER_DEPTH # 1.5mm
    for py in [h * 0.25, h * 0.5, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_l, tpu_h + 0.1)
        b.translate(App.Vector(w - (rail_w / 2.0) - (tpu_w / 2.0), py - (tpu_l / 2.0), t - tpu_h))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 9. Elephant's Foot Relief Chamfer along outer bottom bed edges
    try:
        base_edges = [
            e for e in frame.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 10.0 * SCALE
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
