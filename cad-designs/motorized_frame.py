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
    Open-bottom 4-wall frame architecture matching follower_frame.
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

    # 1. Base 4-Wall Perimeter Frame
    outer_box = Part.makeBox(w, h, t)

    # Knuckles: Bottom (Y=0..15mm) and Top (Y=170..185mm)
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    k_top = Part.makeCylinder(knuckle_r, k_top_len, App.Vector(0, k_top_start_y, pivot_z), App.Vector(0, 1, 0))

    # C1 Fillet Blend Ramps (Rf = 12.0mm)
    rf = 12.0 * SCALE
    xc = math.sqrt((knuckle_r + rf)**2 - (t - pivot_z + rf)**2)
    zc = t + rf
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
    ramp_top = ramp_face.extrude(App.Vector(0, k_top_len, 0))
    ramp_top.translate(App.Vector(0, k_top_start_y, 0))

    # Servo housing corner block at Y=185..240mm, X = -18.0 to 44.0mm
    servo_box = Part.makeBox(62.0 * SCALE, h - 185.0 * SCALE, t)
    servo_box.translate(App.Vector(-18.0 * SCALE, 185.0 * SCALE, 0))

    # Knuckle-to-Housing Gusset Bridge (X = -18.0 to 11.0mm, Y = 170.0 to 185.0mm, Z = 0 to 15.0mm)
    knuckle_bridge = Part.makeBox(29.0 * SCALE, 15.0 * SCALE, t)
    knuckle_bridge.translate(App.Vector(-18.0 * SCALE, k_top_start_y, 0))

    frame = outer_box.fuse([k_bot, k_top, ramp_bot, ramp_top, servo_box, knuckle_bridge]).removeSplitter()

    # 2. Cut open interior cavity (leaving 15mm perimeter rails and 4th tie-bar floor Z=0..3mm)
    # Main open interior cavity (Z = -1 to t+1, completely open top and bottom)
    cav_main = Part.makeBox(w - rail_w - tie_x - tie_w, h - 2 * rail_w, t + 2.0)
    cav_main.translate(App.Vector(tie_x + tie_w, rail_w, -1.0))

    # Left rail interior gap (between bottom knuckle Y=15mm and top knuckle Y=170mm)
    cav_left = Part.makeBox(tie_x + 0.5, k_top_start_y - knuckle_len, t + 2.0)
    cav_left.translate(App.Vector(-0.5, knuckle_len, -1.0))

    # Tie-bar top cutout (leaving Z=0..3mm floor for tie-bar at X in [11, 25mm], Y in [15, 170mm])
    cav_tie = Part.makeBox(tie_w + 2.0 * SCALE, k_top_start_y - knuckle_len, t - tie_h + 2.0)
    cav_tie.translate(App.Vector(tie_x - 1.0 * SCALE, knuckle_len, tie_h))

    for cav in [cav_main, cav_left, cav_tie]:
        frame = frame.cut(cav).removeSplitter()

    # 3. Hinge Bearing Bores
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    top_bore = Part.makeCylinder(bore_r, k_top_len + 0.2, App.Vector(0, k_top_start_y - 0.1, pivot_z), App.Vector(0, 1, 0))
    trim_bot = Part.makeBox(knuckle_r * 4.0, h + 2.0, knuckle_r + 2.0)
    trim_bot.translate(App.Vector(-knuckle_r * 2.0, -1.0, -knuckle_r - 2.0))

    for b in [bot_bore, top_bore, trim_bot]:
        frame = frame.cut(b).removeSplitter()

    # 4. Servo Bay Cavity specifically tailored for Real MG996R STEP Solid:
    # Main motor body pocket (X in [-11.0, 31.0mm], Y in [185.0, 230.5mm])
    pocket_body = Part.makeBox(42.0 * SCALE, 45.5 * SCALE, t + 6.0)
    pocket_body.translate(App.Vector(-11.0 * SCALE, 185.0 * SCALE, -3.0 * SCALE))

    # Outer ear lower casing pocket (X in [-17.5, -10.5mm], Y in [196.0, 225.0mm], Z in [-3.0, 6.0mm])
    pocket_outer_ear_low = Part.makeBox(7.0 * SCALE, 29.0 * SCALE, 9.0 * SCALE)
    pocket_outer_ear_low.translate(App.Vector(-17.5 * SCALE, 196.0 * SCALE, -3.0 * SCALE))

    # Mounting Ear Shelf Recesses (covers ears and top housing flange from Y=194 to 226mm)
    pocket_ears = Part.makeBox(56.0 * SCALE, 32.0 * SCALE, t - 5.5 * SCALE + 2.0)
    pocket_ears.translate(App.Vector(-17.5 * SCALE, 194.0 * SCALE, 5.5 * SCALE))

    # Wire exit tunnel at rear right into central cavity
    pocket_wire = Part.makeBox(14.0 * SCALE, 12.0 * SCALE, 12.0 * SCALE)
    pocket_wire.translate(App.Vector(28.0 * SCALE, 219.0 * SCALE, -1.0 * SCALE))

    # M3 Screw Holes through mounting shelf
    screw_r = 1.4 * SCALE # 2.8mm tap hole for M3 thread
    screws = [
        Part.makeCylinder(screw_r, 12.0 * SCALE, App.Vector(34.95 * SCALE, 196.8 * SCALE, 0.0), App.Vector(0, 0, 1)),
        Part.makeCylinder(screw_r, 12.0 * SCALE, App.Vector(-14.45 * SCALE, 196.8 * SCALE, 0.0), App.Vector(0, 0, 1)),
    ]

    # Slide-in lid retention grooves (widened to 45.5mm on right and -19.0mm on left to cleanly fit tongues)
    groove_l = Part.makeBox(3.0 * SCALE, 52.0 * SCALE, 2.0 * SCALE)
    groove_l.translate(App.Vector(-19.0 * SCALE, 186.0 * SCALE, 13.4 * SCALE))
    groove_r = Part.makeBox(3.5 * SCALE, 52.0 * SCALE, 2.0 * SCALE)
    groove_r.translate(App.Vector(42.0 * SCALE, 186.0 * SCALE, 13.4 * SCALE))

    for p in [pocket_body, pocket_outer_ear_low, pocket_ears, pocket_wire, groove_l, groove_r] + screws:
        frame = frame.cut(p).removeSplitter()

    # 5. Dovetails on Outer Rails
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

    push_hole = Part.makeCylinder(3.0 * SCALE, bottom_thick + 1.0, App.Vector(0, dt_depth * 0.6, -0.5))
    dt_cutter_with_hole = dt_cutter.fuse(push_hole)

    # Front Wall (Y=0)
    c_front = dt_cutter_with_hole.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))

    # Back Wall (Y=H)
    c_back = dt_cutter_with_hole.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h, 0))

    # Right Wall (X=W)
    c_right = dt_cutter_with_hole.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))

    # 4th Wall Joint on Tie-Bar
    dt_lk_neck = 4.0 * SCALE
    dt_lk_flare = 8.0 * SCALE
    dt_lk_depth = 8.0 * SCALE
    gap = 0.25 * SCALE
    x_left = tie_x - (1.0 * SCALE)
    x_right = tie_x + tie_w + (1.0 * SCALE)
    center_x = tie_x + (tie_w / 2.0)
    y_seam = (k_top_start_y + knuckle_len) / 2.0  # 92.5mm

    dt4_poly_pts = [
        App.Vector(x_right, y_seam + gap, 0),
        App.Vector(center_x + dt_lk_neck / 2.0 + gap, y_seam + gap, 0),
        App.Vector(center_x + dt_lk_flare / 2.0 + gap, y_seam + dt_lk_depth + gap, 0),
        App.Vector(center_x - dt_lk_flare / 2.0 - gap, y_seam + dt_lk_depth + gap, 0),
        App.Vector(center_x - dt_lk_neck / 2.0 - gap, y_seam + gap, 0),
        App.Vector(x_left, y_seam + gap, 0),
        App.Vector(x_left, y_seam, 0),
        App.Vector(center_x - dt_lk_neck / 2.0, y_seam, 0),
        App.Vector(center_x - dt_lk_flare / 2.0, y_seam + dt_lk_depth, 0),
        App.Vector(center_x + dt_lk_flare / 2.0, y_seam + dt_lk_depth, 0),
        App.Vector(center_x + dt_lk_neck / 2.0, y_seam, 0),
        App.Vector(x_right, y_seam, 0),
        App.Vector(x_right, y_seam + gap, 0),
    ]
    dt4_cutter = Part.Face(Part.makePolygon(dt4_poly_pts)).extrude(App.Vector(0, 0, tie_h + 2.0))
    dt4_cutter.translate(App.Vector(0, 0, -1.0))

    for dt in [c_front, c_back, c_right, dt4_cutter]:
        frame = frame.cut(dt).removeSplitter()

    # 6. Anti-Slip Rubber Foot Sockets
    foot_r = 6.0 * SCALE
    foot_d = 2.0 * SCALE
    foot_locs = [
        (w - (rail_w / 2.0), rail_w / 2.0),
        (w - (rail_w / 2.0), h - (rail_w / 2.0)),
        (25.0 * SCALE, rail_w / 2.0),
        (25.0 * SCALE, h - (rail_w / 2.0)),
    ]
    for fx, fy in foot_locs:
        fc = Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(fx, fy, -0.1))
        frame = frame.cut(fc).removeSplitter()

    # 7. Silent-Flip TPU Bumper Slots
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
    for bmp in bumpers:
        frame = frame.cut(bmp).removeSplitter()

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
