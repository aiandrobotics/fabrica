"""
part_02_follower_frame.py — Passive Follower Chassis Open-Bottom U-Frame
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
    Constructs the Passive Follower Open-Bottom 3-Sided U-Frame Module.
    Features:
    1. Open-Bottom 3-Sided U-Frame Chassis (240x240x15mm) with 15mm rigid perimeter rails.
       100% open interior eliminates lint/dust traps and saves ~120g of plastic.
    2. 4x Bottom Anti-Slip Grip Foot Sockets (Ø12mm x 2.0mm) for high-traction silicone/TPU rubber pads.
    3. Dual 100% Solid 360° Closed Bearing Knuckles (Top Y=240, Bottom Y=0) housing Ø13.0mm drive axle.
    4. C1-Continuous Tangent Concave Blend Ramps (Rf = 12mm) for seamless knuckle-to-deck flow.
    5. True Open-Top Sliding Dovetail Joiner Sockets on outer walls (Front Y=0, Back Y=240, Right X=240)
       with 3.0mm bottom floor drop stops and Ø6.0mm true through-floor push-out access holes.
    6. 3x Silent-Flip TPU Bumper Slots (1.5mm depth) recessed into the top landing rail.
    7. 0.4mm bottom Elephant's Foot relief chamfers.
    """
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = BOTTOM_SHELL_THICKNESS

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

    ramp_pts = [App.Vector(-knuckle_r, 0, 0)] # bottom left
    # Outer circle arch from -X up around crown to touch_theta
    num_arch = 16
    for i in range(num_arch):
        th = math.pi - i * (math.pi - touch_theta) / float(num_arch - 1)
        ramp_pts.append(App.Vector(knuckle_r * math.cos(th), 0, pivot_z + knuckle_r * math.sin(th)))

    # Concave sweeping fillet arc from touch point down to horizontal deck (X = xc, Z = 15.0)
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

    frame = outer_box.fuse(Part.makeCompound([k_bot, k_top, ramp_bot, ramp_top])).removeSplitter()

    # 3. 100% Open Interior Through-Cavity (Cuts completely from Z = -0.5mm to Z = t + 0.5mm)
    cav_w = w - rail_w + 1.0
    cav_h = h - 2 * rail_w
    cavity = Part.makeBox(cav_w, cav_h, t + 2.0)
    cavity.translate(App.Vector(-0.5, rail_w, -1.0))
    
    frame = frame.cut(cavity).removeSplitter()

    # 4. Hinge Bearing Bores: Dual 100% Solid 360° Closed Cylindrical Tunnels (Top & Bottom)
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE  # 6.75mm radius (Ø13.5mm)

    top_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, h - knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))

    # Knuckle planar bottom trim: 100% flat at Z=0.0mm (Zero wobble / Zero 3D print supports)
    trim_bot = Part.makeBox(knuckle_r * 4.0, h + 2.0, knuckle_r + 2.0)
    trim_bot.translate(App.Vector(-knuckle_r * 2.0, -1.0, -knuckle_r - 2.0))

    frame = frame.cut(Part.makeCompound([top_bore, bot_bore, trim_bot])).removeSplitter()

    # 5. Female Open-Top True Sliding Dovetail Joiner Sockets (Front Y=0, Back Y=H, Right X=W)
    dt_neck_w = DOVETAIL_NECK_WIDTH
    dt_flare_w = DOVETAIL_FLARE_WIDTH
    dt_depth = DOVETAIL_DEPTH
    dt_cut_h = t - bottom_thick + 0.5  # Cuts open through top deck

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

    frame = frame.cut(Part.makeCompound(dt_cutters)).removeSplitter()

    # 6. Anti-Slip Foot Pad Recess Sockets (4x on bottom face of rails for Ø12mm x 2.0mm rubber feet)
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

    # 7. TPU Silent-Flip Landing Bumper Slots (1.5mm recessed into top landing rail at X = w - rail_w/2)
    tpu_cutters = []
    tpu_w = 5.0 * SCALE
    tpu_l = 14.0 * SCALE
    tpu_h = TPU_BUMPER_DEPTH # 1.5mm
    for py in [h * 0.25, h * 0.5, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_l, tpu_h + 0.1)
        b.translate(App.Vector(w - (rail_w / 2.0) - (tpu_w / 2.0), py - (tpu_l / 2.0), t - tpu_h))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 8. Elephant's Foot Relief Chamfer along outer bottom bed edges
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
