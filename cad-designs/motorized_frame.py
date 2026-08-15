"""
motorized_frame.py — Motorized Outer Frame Chassis with Solid Mounting Towers, Hex Screw Housings, Inner Enclosure Wall, and Rear Slide-in Servo Bay
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
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    BEARING_ROTATING_CLEARANCE,
    EXPORT_DIR,
)

def make_hex_prism(r_af, depth, center, axis):
    """Creates a regular hexagonal prism aligned with given axis for M3 nut/screw housing."""
    r_corner = r_af / math.cos(math.radians(30))
    pts = []
    for i in range(6):
        ang = math.radians(60 * i + 30)
        pts.append(App.Vector(center.x + r_corner * math.cos(ang), center.y, center.z + r_corner * math.sin(ang)))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    solid = face.extrude(axis * depth)
    return solid

def construct_motorized_frame():
    """
    Constructs the 4-sided outer perimeter chassis for the Active Motorized Module.
    Features:
      1. Complete continuous inner enclosure wall (X in [38.0, 48.0mm], Y in [185.0, 240.0mm])
         sealing the motor compartment from the frame's central cavity.
      2. Solid front mounting towers (Y in [185.0, 195.5mm]) with 4x M3 through-holes (2 top, 2 bottom)
         spaced accurately per MG996R motor specs with captive hex nut housings.
      3. Open rear slide-in slot (Y=240mm) allowing the horizontal MG996R servo to slide directly into place.
      4. 100% Flat Base Plane at Z=0.0mm matching the follower frame base.
      5. Hinge pivot axis at PIVOT_Z = 10.0mm identically matching all follower modules.
    """
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = 3.0 * SCALE
    pivot_z = PIVOT_Z        # 10.0mm

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

    # Servo housing corner block at Y=185..240mm, X = -18.0 to 48.0mm
    servo_box = Part.makeBox(66.0 * SCALE, h - 185.0 * SCALE, t)
    servo_box.translate(App.Vector(-18.0 * SCALE, 185.0 * SCALE, 0))

    # Knuckle-to-Housing Support Gusset (X = -18.0 to 25.0mm, Y = 170.0 to 185.0mm, Z = 0 to 15.0mm)
    knuckle_bridge = Part.makeBox(43.0 * SCALE, 15.0 * SCALE, t)
    knuckle_bridge.translate(App.Vector(-18.0 * SCALE, k_top_start_y, 0))

    frame = outer_box.fuse([k_bot, k_top, ramp_bot, ramp_top, servo_box, knuckle_bridge]).removeSplitter()

    # 2. Cut open interior cavities while preserving inner enclosure wall at X in [38.0, 48.0mm], Y in [185.0, 240.0mm]
    # Lower main cavity (Y = 15 to 185mm, X = 25 to 225mm)
    cav_main_lower = Part.makeBox(w - rail_w - tie_x - tie_w, 170.0 * SCALE, t + 2.0)
    cav_main_lower.translate(App.Vector(tie_x + tie_w, rail_w, -1.0))

    # Upper main cavity (Y = 185 to 225mm, X = 48 to 225mm) — preserves solid inner motor enclosure wall
    cav_main_upper = Part.makeBox(w - rail_w - 48.0 * SCALE, 40.0 * SCALE, t + 2.0)
    cav_main_upper.translate(App.Vector(48.0 * SCALE, 185.0 * SCALE, -1.0))

    # Left rail interior cavity
    cav_left = Part.makeBox(tie_x + 0.5, k_top_start_y - knuckle_len, t + 2.0)
    cav_left.translate(App.Vector(-0.5, knuckle_len, -1.0))

    # Tie bar pocket
    cav_tie = Part.makeBox(tie_w + 2.0 * SCALE, k_top_start_y - knuckle_len, t - tie_h + 2.0)
    cav_tie.translate(App.Vector(tie_x - 1.0 * SCALE, knuckle_len, tie_h))

    for cav in [cav_main_lower, cav_main_upper, cav_left, cav_tie]:
        frame = frame.cut(cav).removeSplitter()

    # 3. Hinge Bearing Bores & Adapter Disk Rotating Clearance Pocket
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    top_bore = Part.makeCylinder(bore_r, k_top_len + 0.2, App.Vector(0, k_top_start_y - 0.1, pivot_z), App.Vector(0, 1, 0))
    
    # 7mm Adapter Disk Clearance Counterbore (Ø20.0mm for Ø19.0mm disk spanning Y=177.5 to 185.1mm)
    adapter_bore = Part.makeCylinder(10.0 * SCALE, 7.6 * SCALE, App.Vector(0, 177.5 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # Planar bottom trim at Z=0.0mm (ensuring base of motor frame is 100% flat)
    trim_bot = Part.makeBox(w + 50.0, h + 50.0, 20.0)
    trim_bot.translate(App.Vector(-25.0, -25.0, -20.0))

    for b in [bot_bore, top_bore, adapter_bore, trim_bot]:
        frame = frame.cut(b).removeSplitter()

    # 4. Slide-in Servo Bay Cavity with Solid Front Towers, Inner Enclosure Wall, and Open Rear Slot (Y=240mm):
    # Main motor body pocket opening through rear wall at Y=240mm (X in [-11.0, 31.0mm], Y in [185.0, 242.0mm], Z in [0.0, t+6.0])
    pocket_body = Part.makeBox(42.0 * SCALE, 57.0 * SCALE, t + 6.0)
    pocket_body.translate(App.Vector(-11.0 * SCALE, 185.0 * SCALE, 0.0))

    # Mounting Ear Recess Bay behind the solid towers (X in [-17.5, 38.0mm], Y in [195.5, 242.0mm], Z in [0.0, 18.0mm])
    # Solid towers are preserved in front at Y in [185.0, 195.5mm]
    pocket_ears_slide = Part.makeBox(55.5 * SCALE, 46.5 * SCALE, t + 6.0)
    pocket_ears_slide.translate(App.Vector(-17.5 * SCALE, 195.5 * SCALE, 0.0))

    # 4x Horizontal M3 Screw Clearance Holes (Ø3.4mm) passing through the solid towers along Y-axis:
    # Top and bottom holes on each mounting ear accurately spaced per MG996R dimensions (Z=4.75mm & Z=15.25mm, X=-14.45mm & X=34.95mm):
    screw_r = 1.7 * SCALE
    screw_holes = [
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(34.95 * SCALE, 184.0 * SCALE, 4.75 * SCALE), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(34.95 * SCALE, 184.0 * SCALE, 15.25 * SCALE), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(-14.45 * SCALE, 184.0 * SCALE, 4.75 * SCALE), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(-14.45 * SCALE, 184.0 * SCALE, 15.25 * SCALE), App.Vector(0, 1, 0)),
    ]

    # 4x M3 Hex Nut / Screw Head Housing Pockets on the front face of the towers (Y in [185.0, 188.0mm]):
    hex_nut_housings = [
        make_hex_prism(2.9 * SCALE, 3.2 * SCALE, App.Vector(34.95 * SCALE, 184.8 * SCALE, 4.75 * SCALE), App.Vector(0, 1, 0)),
        make_hex_prism(2.9 * SCALE, 3.2 * SCALE, App.Vector(34.95 * SCALE, 184.8 * SCALE, 15.25 * SCALE), App.Vector(0, 1, 0)),
        make_hex_prism(2.9 * SCALE, 3.2 * SCALE, App.Vector(-14.45 * SCALE, 184.8 * SCALE, 4.75 * SCALE), App.Vector(0, 1, 0)),
        make_hex_prism(2.9 * SCALE, 3.2 * SCALE, App.Vector(-14.45 * SCALE, 184.8 * SCALE, 15.25 * SCALE), App.Vector(0, 1, 0)),
    ]

    # Slide-in lid retention channels along side walls
    groove_l = Part.makeBox(2.5 * SCALE, 56.0 * SCALE, 2.0 * SCALE)
    groove_l.translate(App.Vector(-18.5 * SCALE, 185.0 * SCALE, 13.4 * SCALE))
    groove_r = Part.makeBox(2.5 * SCALE, 56.0 * SCALE, 2.0 * SCALE)
    groove_r.translate(App.Vector(42.0 * SCALE, 185.0 * SCALE, 13.4 * SCALE))

    # Wire exit conduit through inner enclosure wall into interior cavity
    pocket_wire = Part.makeBox(14.0 * SCALE, 12.0 * SCALE, 10.0 * SCALE)
    pocket_wire.translate(App.Vector(36.0 * SCALE, 219.0 * SCALE, 2.0 * SCALE))

    cutters = [pocket_body, pocket_ears_slide, pocket_wire, groove_l, groove_r] + screw_holes + hex_nut_housings
    for c in cutters:
        frame = frame.cut(c).removeSplitter()

    # Re-apply bottom trim to guarantee 100% planar base at Z=0.0mm
    frame = frame.cut(trim_bot).removeSplitter()

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
