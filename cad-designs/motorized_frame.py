"""
motorized_frame.py — Motorized Outer Frame Chassis with Real MG996R Step Servo Bay
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
    MODULE_GAP,
    DOVETAIL_NECK_WIDTH,
    DOVETAIL_FLARE_WIDTH,
    DOVETAIL_DEPTH,
    DRIVE_SHAFT_DIAMETER,
    BEARING_ROTATING_CLEARANCE,
    EXPORT_DIR,
)

def construct_motorized_frame():
    """
    Constructs the 4-sided outer perimeter chassis for the Active Motorized Module.
    Houses the real MG996R standard servo horizontally along the rear rail with zero top protrusions.
    """
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = 3.0 * SCALE
    pivot_z = 8.0 * SCALE

    knuckle_r = (DRIVE_SHAFT_DIAMETER / 2.0) + 3.0 * SCALE # 9.5mm radius
    knuckle_len = 15.0 * SCALE
    k_top_len = 15.0 * SCALE
    k_top_start_y = 170.0 * SCALE

    tie_x = 11.0 * SCALE
    tie_w = 14.0 * SCALE
    tie_h = 3.0 * SCALE

    # 1. Base Perimeter Solid Block (240 x 240 x 15mm)
    outer_box = Part.makeBox(w, h, t)

    # 2. Closed Cylindrical Bearing Knuckles & C1 Blend Ramps
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    k_top = Part.makeCylinder(knuckle_r, k_top_len, App.Vector(0, k_top_start_y, pivot_z), App.Vector(0, 1, 0))

    # C1 Fillet Blend Ramps (Rf = 12.0mm)
    zc = t + 12.0 * SCALE
    xc = -math.sqrt((12.0 * SCALE + knuckle_r)**2 - (zc - pivot_z)**2)
    rf = 12.0 * SCALE
    touch_theta = math.atan2(pivot_z - zc, -xc)

    ramp_pts = [App.Vector(xc, 0, zc - rf)]
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
    ramp_top = ramp_face.extrude(App.Vector(0, k_top_len, 0))
    ramp_top.translate(App.Vector(0, k_top_start_y, 0))

    # Reinforced Rear Corner Servo Housing Box enclosing real MG996R (X = -18.0 to 44.0mm, Y = 185.0 to 240.0mm)
    servo_box = Part.makeBox(62.0 * SCALE, (h - 185.0 * SCALE), t)
    servo_box.translate(App.Vector(-18.0 * SCALE, 185.0 * SCALE, 0))

    frame = outer_box.fuse(Part.makeCompound([k_bot, k_top, ramp_bot, ramp_top, servo_box])).removeSplitter()

    # 3. Open Interior Cavities (preserving 4th tie-bar at X in [11, 25mm], Z in [0, 3mm])
    cav_main = Part.makeBox(w - rail_w - tie_x - tie_w, h - 2 * rail_w, t + 4.0 * SCALE)
    cav_main.translate(App.Vector(tie_x + tie_w, rail_w, -2.0 * SCALE))

    cav_left = Part.makeBox(tie_x + 0.5, k_top_start_y - knuckle_len, t + 2.0)
    cav_left.translate(App.Vector(-0.5, knuckle_len, -1.0))

    cav_tie_top = Part.makeBox(tie_w + 2.0 * SCALE, k_top_start_y - knuckle_len, t - tie_h + 2.0)
    cav_tie_top.translate(App.Vector(tie_x - 1.0 * SCALE, knuckle_len, tie_h))

    frame = frame.cut(Part.makeCompound([cav_main, cav_left, cav_tie_top])).removeSplitter()

    # 4. Hinge Bearing Bores (Bottom Y=0..15mm, Top Y=170..185.0mm)
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE  # 6.75mm radius (Ø13.5mm)

    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    top_bore = Part.makeCylinder(bore_r, k_top_len + 0.2, App.Vector(0, k_top_start_y - 0.1, pivot_z), App.Vector(0, 1, 0))

    # Knuckle planar bottom trim: 100% flat at Z=0.0mm
    trim_bot = Part.makeBox(knuckle_r * 4.0, h + 2.0, knuckle_r + 2.0)
    trim_bot.translate(App.Vector(-knuckle_r * 2.0, -1.0, -knuckle_r - 2.0))

    frame = frame.cut(Part.makeCompound([bot_bore, top_bore, trim_bot])).removeSplitter()

    # 5. Servo Bay Cavity specifically matched to the real MG996R STEP solid:
    # Main motor body pocket (with 0.5mm clearance around real body):
    pocket_body = Part.makeBox(41.5 * SCALE, 46.0 * SCALE, t + 6.0)
    pocket_body.translate(App.Vector(-10.5 * SCALE, 185.0 * SCALE, -3.0 * SCALE))

    # Mounting ears pocket (X in [-17.5, 38.0mm], Y in [195.5, 200.5mm]):
    pocket_ears = Part.makeBox(56.0 * SCALE, 5.5 * SCALE, t + 6.0)
    pocket_ears.translate(App.Vector(-17.5 * SCALE, 195.5 * SCALE, -3.0 * SCALE))

    # Wire exit channel routing to open interior cavity:
    pocket_wire = Part.makeBox(14.0 * SCALE, 10.0 * SCALE, t + 6.0)
    pocket_wire.translate(App.Vector(28.0 * SCALE, 220.0 * SCALE, -3.0 * SCALE))

    # M3 mounting screw holes:
    screw_r = 1.6 * SCALE
    screws = [
        Part.makeCylinder(screw_r, 20.0 * SCALE, App.Vector(34.95 * SCALE, 196.8 * SCALE, -2.0 * SCALE), App.Vector(0, 0, 1)),
        Part.makeCylinder(screw_r, 20.0 * SCALE, App.Vector(-14.45 * SCALE, 196.8 * SCALE, -2.0 * SCALE), App.Vector(0, 0, 1)),
    ]

    # Slide-in cover retention grooves at Z = 13.4mm:
    groove_l = Part.makeBox(2.0 * SCALE, 52.0 * SCALE, 2.0 * SCALE)
    groove_l.translate(App.Vector(-18.5 * SCALE, 186.0 * SCALE, 13.4 * SCALE))
    groove_r = Part.makeBox(2.0 * SCALE, 52.0 * SCALE, 2.0 * SCALE)
    groove_r.translate(App.Vector(42.5 * SCALE, 186.0 * SCALE, 13.4 * SCALE))

    frame = frame.cut(Part.makeCompound([pocket_body, pocket_ears, pocket_wire, groove_l, groove_r] + screws)).removeSplitter()

    # 6. Female Open-Top True Sliding Dovetail Joiner Sockets on Outer Walls (Front Y=0, Back Y=H, Right X=W)
    dt_neck_w = DOVETAIL_NECK_WIDTH
    dt_flare_w = DOVETAIL_FLARE_WIDTH
    dt_depth = DOVETAIL_DEPTH
    dt_cut_h = t - bottom_thick + 0.5

    # Front Wall Socket (Y = 0, open to top Z=15mm, solid bottom floor Z=0..3mm)
    dt_pts_front = [
        App.Vector(-dt_flare_w / 2.0, -0.1, 0),
        App.Vector(-dt_neck_w / 2.0, dt_depth, 0),
        App.Vector(dt_neck_w / 2.0, dt_depth, 0),
        App.Vector(dt_flare_w / 2.0, -0.1, 0),
    ]
    dt_wire_f = Part.makePolygon(dt_pts_front)
    dt_face_f = Part.Face(dt_wire_f)
    dt_solid_f = dt_face_f.extrude(App.Vector(0, 0, dt_cut_h + 1.0))
    dt_solid_f.translate(App.Vector(w / 2.0, 0, bottom_thick))

    # Push-out access hole (Ø6mm through floor at Z=0..3mm)
    hole_f = Part.makeCylinder(3.0 * SCALE, bottom_thick + 2.0, App.Vector(w / 2.0, dt_depth / 2.0, -1.0), App.Vector(0, 0, 1))

    # Back Wall Socket (Y = H)
    dt_pts_back = [
        App.Vector(-dt_flare_w / 2.0, 0.1, 0),
        App.Vector(-dt_neck_w / 2.0, -dt_depth, 0),
        App.Vector(dt_neck_w / 2.0, -dt_depth, 0),
        App.Vector(dt_flare_w / 2.0, 0.1, 0),
    ]
    dt_wire_b = Part.makePolygon(dt_pts_back)
    dt_face_b = Part.Face(dt_wire_b)
    dt_solid_b = dt_face_b.extrude(App.Vector(0, 0, dt_cut_h + 1.0))
    dt_solid_b.translate(App.Vector(w / 2.0, h, bottom_thick))
    hole_b = Part.makeCylinder(3.0 * SCALE, bottom_thick + 2.0, App.Vector(w / 2.0, h - dt_depth / 2.0, -1.0), App.Vector(0, 0, 1))

    # Right Wall Socket (X = W)
    dt_pts_right = [
        App.Vector(0.1, -dt_flare_w / 2.0, 0),
        App.Vector(-dt_depth, -dt_neck_w / 2.0, 0),
        App.Vector(-dt_depth, dt_neck_w / 2.0, 0),
        App.Vector(0.1, dt_flare_w / 2.0, 0),
    ]
    dt_wire_r = Part.makePolygon(dt_pts_right)
    dt_face_r = Part.Face(dt_wire_r)
    dt_solid_r = dt_face_r.extrude(App.Vector(0, 0, dt_cut_h + 1.0))
    dt_solid_r.translate(App.Vector(w, h / 2.0, bottom_thick))
    hole_r = Part.makeCylinder(3.0 * SCALE, bottom_thick + 2.0, App.Vector(w - dt_depth / 2.0, h / 2.0, -1.0), App.Vector(0, 0, 1))

    # 4th Wall Continuous Through-Dovetail Joint (Y = 120mm on left rail)
    dt_joint = Part.makePolygon([
        App.Vector(0.1, -dt_flare_w / 2.0, 0),
        App.Vector(-dt_depth, -dt_neck_w / 2.0, 0),
        App.Vector(-dt_depth, dt_neck_w / 2.0, 0),
        App.Vector(0.1, dt_flare_w / 2.0, 0),
    ])
    dt_face_j = Part.Face(dt_joint)
    dt_solid_j = dt_face_j.extrude(App.Vector(0, 0, tie_h + 2.0))
    dt_solid_j.translate(App.Vector(tie_x + tie_w, h / 2.0, -1.0))

    frame = frame.cut(Part.makeCompound([dt_solid_f, hole_f, dt_solid_b, hole_b, dt_solid_r, hole_r, dt_solid_j])).removeSplitter()

    # 7. Anti-Slip Rubber Foot Sockets on Bottom Face (4 corners, Ø12 x 2.0mm)
    foot_r = 6.0 * SCALE
    foot_depth = 2.0 * SCALE
    foot_margin = 7.5 * SCALE

    feet = [
        Part.makeCylinder(foot_r, foot_depth + 0.1, App.Vector(foot_margin, foot_margin, -0.05), App.Vector(0, 0, 1)),
        Part.makeCylinder(foot_r, foot_depth + 0.1, App.Vector(w - foot_margin, foot_margin, -0.05), App.Vector(0, 0, 1)),
        Part.makeCylinder(foot_r, foot_depth + 0.1, App.Vector(w - foot_margin, h - foot_margin, -0.05), App.Vector(0, 0, 1)),
        Part.makeCylinder(foot_r, foot_depth + 0.1, App.Vector(foot_margin, h - foot_margin, -0.05), App.Vector(0, 0, 1)),
    ]
    frame = frame.cut(Part.makeCompound(feet)).removeSplitter()

    # 8. Silent-Flip TPU Bumper Recessed Slots on Top Deck (1.5mm deep)
    bumper_w = 4.0 * SCALE
    bumper_l = 25.0 * SCALE
    bumper_d = 1.5 * SCALE

    bumpers = [
        Part.makeBox(bumper_l, bumper_w, bumper_d + 0.2),
        Part.makeBox(bumper_w, bumper_l, bumper_d + 0.2),
        Part.makeBox(bumper_l, bumper_w, bumper_d + 0.2),
    ]
    bumpers[0].translate(App.Vector(w / 2.0 - bumper_l / 2.0, rail_w / 2.0 - bumper_w / 2.0, t - bumper_d))
    bumpers[1].translate(App.Vector(w - rail_w / 2.0 - bumper_w / 2.0, h / 2.0 - bumper_l / 2.0, t - bumper_d))
    bumpers[2].translate(App.Vector(w / 2.0 - bumper_l / 2.0, h - rail_w / 2.0 - bumper_w / 2.0, t - bumper_d))

    frame = frame.cut(Part.makeCompound(bumpers)).removeSplitter()

    # 9. Bottom Elephant's Foot Relief Chamfer (0.4mm x 45°)
    ef_w = w + 40.0
    ef_h = h + 40.0
    ef_box = Part.makeBox(ef_w, ef_h, 0.45 * SCALE)
    ef_box.translate(App.Vector(-20.0, -20.0, -0.45 * SCALE))
    ef_inner = Part.makeBox(w - 0.8 * SCALE, h - 0.8 * SCALE, 1.0 * SCALE)
    ef_inner.translate(App.Vector(0.4 * SCALE, 0.4 * SCALE, -0.5 * SCALE))
    ef_cutter = ef_box.cut(ef_inner)
    frame = frame.cut(ef_cutter).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_frame.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_frame.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    frame.exportStep(step_path)
    frame.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return frame

def main():
    doc = App.newDocument("MotorizedFrame")
    shape = construct_motorized_frame()
    feature = doc.addObject("Part::Feature", "MotorizedFrame")
    feature.Shape = shape

main()
