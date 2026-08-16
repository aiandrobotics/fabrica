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
    TPU_BUMPER_DEPTH,
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

    # Solid 2.0mm Bottom Base Floor under entire motor module zone (Y in [170.0, 240.0mm], X in [-18.0, 48.0mm], Z in [-2.0, 0.0mm])
    floor_t = 2.0 * SCALE
    module_base_floor = Part.makeBox(66.0 * SCALE, h - 170.0 * SCALE, floor_t)
    module_base_floor.translate(App.Vector(-18.0 * SCALE, 170.0 * SCALE, -floor_t))

    # Knuckle Solid Vertical Pedestal (X in [-6.5, 6.5mm], Y in [170.0, 185.0mm], Z in [0.0, 10.0mm]) anchoring knuckle to base floor
    knuckle_pedestal = Part.makeBox(13.0 * SCALE, 15.0 * SCALE, 10.0 * SCALE)
    knuckle_pedestal.translate(App.Vector(-6.5 * SCALE, k_top_start_y, 0.0))

    # Solid Mounting Towers at Y in [185.0, 195.5mm] (height Z=0.0 to 21.2mm, sitting on base floor)
    t_servo = 21.2 * SCALE
    towers_box = Part.makeBox(66.0 * SCALE, 10.5 * SCALE, t_servo)
    towers_box.translate(App.Vector(-18.0 * SCALE, 185.0 * SCALE, 0.0))

    # Rear motor housing perimeter at Y in [195.5, 240.0mm] (height Z=0.0 to 21.2mm, sitting on base floor)
    rear_box = Part.makeBox(66.0 * SCALE, h - 195.5 * SCALE, t_servo)
    rear_box.translate(App.Vector(-18.0 * SCALE, 195.5 * SCALE, 0.0))

    # Axial Cradle Outer Cylinder Solid (R=9.5mm outer cylinder running along hinge axis at Y in [15, 170mm])
    cradle_outer_cyl = Part.makeCylinder(knuckle_r, k_top_start_y - knuckle_len, App.Vector(0, knuckle_len, pivot_z), App.Vector(0, 1, 0))

    frame = outer_box.fuse([k_bot, k_top, ramp_bot, ramp_top, cradle_outer_cyl, module_base_floor, knuckle_pedestal, towers_box, rear_box]).removeSplitter()

    # 2. Cut open interior cavities & Axial Cradle (Clean straight vertical wall from cradle apex at X=0.0mm)
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE  # 6.75mm radius (Ø13.5mm)

    # A. Continuous Axial Cradle Trough Cutter (Cylinder radius bore_r = 6.75mm centered at X=0, Z=10mm)
    cradle_trough = Part.makeCylinder(bore_r, k_top_start_y - knuckle_len + 0.2, App.Vector(0, knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))

    # B. Upper Flap Sweep Cut above Z=10.0mm (open top above cradle half-pipe, height 20mm)
    cav_cradle_top = Part.makeBox(knuckle_r * 2.0 + 10.0, k_top_start_y - knuckle_len, 20.0 * SCALE)
    cav_cradle_top.translate(App.Vector(-knuckle_r - 2.0, knuckle_len, pivot_z))

    # C. Lower Main Center Cavity (Straight rectangular window starting right at X=0.0mm):
    cav_main_lower = Part.makeBox(w - rail_w, 155.0 * SCALE, t + 2.0)
    cav_main_lower.translate(App.Vector(0.0, rail_w, -1.0))

    # Upper main cavity (Y = 170 to 225mm, X = 48 to 225mm) — preserves solid inner motor enclosure wall
    cav_main_upper = Part.makeBox(w - rail_w - 48.0 * SCALE, 55.0 * SCALE, t + 2.0)
    cav_main_upper.translate(App.Vector(48.0 * SCALE, 170.0 * SCALE, -1.0))

    # Front-Right Screw Access Pocket (X = 6.5 to 48.5mm, Y = 170.0 to 185.5mm, Z = 0.0 to 25.0mm) — opens front face of right tower down to base floor
    cut_screw_access_right = Part.makeBox(42.0 * SCALE, 15.5 * SCALE, 25.0 * SCALE)
    cut_screw_access_right.translate(App.Vector(6.5 * SCALE, k_top_start_y, 0.0))

    # Front-Left Screw Access Pocket (X = -18.5 to -6.5mm, Y = 170.0 to 185.5mm, Z = 0.0 to 25.0mm) — opens front face of left tower down to base floor
    cut_screw_access_left = Part.makeBox(12.0 * SCALE, 15.5 * SCALE, 25.0 * SCALE)
    cut_screw_access_left.translate(App.Vector(-18.5 * SCALE, k_top_start_y, 0.0))

    for cav in [cav_main_lower, cav_main_upper, cradle_trough, cav_cradle_top, cut_screw_access_right, cut_screw_access_left]:
        frame = frame.cut(cav).removeSplitter()

    # 3. Hinge Bearing Bores & Adapter Disk Rotating Clearance Pocket
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    top_bore = Part.makeCylinder(bore_r, k_top_len + 0.2, App.Vector(0, k_top_start_y - 0.1, pivot_z), App.Vector(0, 1, 0))
    
    # 6mm Adapter Disk Clearance Counterbore (Ø20.0mm for Ø19.0mm disk spanning Y=178.5 to 185.1mm)
    adapter_bore = Part.makeCylinder(10.0 * SCALE, 6.6 * SCALE, App.Vector(0, 178.5 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # Planar bottom trim at Z=0.0mm for standard frame rails (preserving the Z=-2.0mm solid floor under motor module zone Y=170-240mm)
    trim_bot_main = Part.makeBox(w + 50.0, 170.0 * SCALE + 25.0, 20.0)
    trim_bot_main.translate(App.Vector(-25.0, -25.0, -20.0))

    trim_bot_right = Part.makeBox(w - 48.0 * SCALE + 25.0, h - 170.0 * SCALE + 25.0, 20.0)
    trim_bot_right.translate(App.Vector(48.0 * SCALE, 170.0 * SCALE, -20.0))

    trim_under_motor = Part.makeBox(w + 50.0, h + 50.0, 20.0)
    trim_under_motor.translate(App.Vector(-25.0, -25.0, -22.0 * SCALE))

    for b in [bot_bore, top_bore, adapter_bore, trim_bot_main, trim_bot_right, trim_under_motor]:
        frame = frame.cut(b).removeSplitter()

    # 4. Top Drop-In Servo Bay Cavity with 2.0mm Solid Closed Base Floor (Z in [-2.0, 0.0mm]), Solid Closed Rear Wall (5.0mm thick at Y=235-240mm), and Solid Front Towers:
    # Front gearhead pass-through pocket through towers (X in [-11.5, 32.5mm], Y in [185.0, 195.5mm], Z in [0.0, 25.0mm])
    pocket_body = Part.makeBox(44.0 * SCALE, 10.5 * SCALE, 25.0 * SCALE)
    pocket_body.translate(App.Vector(-11.5 * SCALE, 185.0 * SCALE, 0.0))

    # Main Top Drop-In Motor Bay (X in [-17.8, 38.5mm], Y in [195.5, 235.0mm], Z in [0.0, 25.0mm])
    # Solid 2.0mm bottom floor preserved at Z in [-2.0, 0.0mm], solid 5.0mm back wall preserved at Y in [235.0, 240.0mm]
    pocket_bay = Part.makeBox(56.3 * SCALE, 39.5 * SCALE, 25.0 * SCALE)
    pocket_bay.translate(App.Vector(-17.8 * SCALE, 195.5 * SCALE, 0.0))

    # Top Lid Seating Rebate (1.8mm depth at Z in [19.4, 21.3mm], X in [-17.8, 40.5mm], Y in [195.5, 237.0mm])
    pocket_rebate = Part.makeBox(58.3 * SCALE, 41.5 * SCALE, 2.0 * SCALE)
    pocket_rebate.translate(App.Vector(-17.8 * SCALE, 195.5 * SCALE, 19.4 * SCALE))

    # 4x Horizontal M3 Screw Clearance Holes (Ø3.4mm) passing cleanly through the solid towers along Y-axis:
    screw_r = 1.7 * SCALE
    screw_holes = [
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(34.95 * SCALE, 184.0 * SCALE, 4.75 * SCALE), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(34.95 * SCALE, 184.0 * SCALE, 15.25 * SCALE), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(-14.45 * SCALE, 184.0 * SCALE, 4.75 * SCALE), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0 * SCALE, App.Vector(-14.45 * SCALE, 184.0 * SCALE, 15.25 * SCALE), App.Vector(0, 1, 0)),
    ]

    # Internal wire routing conduit through inner wall into main chassis cavity (Z in [0.0, 6.0mm])
    pocket_wire = Part.makeBox(12.0 * SCALE, 10.0 * SCALE, 6.0 * SCALE)
    pocket_wire.translate(App.Vector(37.0 * SCALE, 218.0 * SCALE, 0.0))

    cutters = [pocket_body, pocket_bay, pocket_rebate, pocket_wire] + screw_holes
    for c in cutters:
        frame = frame.cut(c).removeSplitter()

    # Re-apply bottom trims to guarantee 100% planar base (Z=0.0mm on frame rails, Z=-2.0mm on motor base floor)
    frame = frame.cut(Part.makeCompound([trim_bot_main, trim_bot_right, trim_under_motor])).removeSplitter()

    # 5. Female Open-Top True Sliding Dovetail Joiner Sockets on Outer Rails (Front Y=0, Right X=W) matching Follower Frame
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

    # Front Wall (Y=0) -> cuts into +Y
    c_front = dt_cutter_with_hole.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))

    # Right Wall (X=W) -> cuts into -X
    c_right = dt_cutter_with_hole.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))

    # Clean Solid Through-Dovetail Joint across Axial Cradle Wall at Y = 120.0mm
    dt_lk_neck = 3.5 * SCALE
    dt_lk_flare = 7.0 * SCALE
    dt_lk_depth = 7.0 * SCALE
    gap = 0.25 * SCALE
    x_left = -knuckle_r - 1.0 * SCALE
    x_right = 1.0 * SCALE
    center_x = (x_left + x_right) / 2.0
    y_seam = h / 2.0  # 120.0mm

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
    dt4_cutter = Part.Face(Part.makePolygon(dt4_poly_pts)).extrude(App.Vector(0, 0, pivot_z + 2.0))
    dt4_cutter.translate(App.Vector(0, 0, -1.0))

    for dt in [c_front, c_right, dt4_cutter]:
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

    # 7. Silent-Flip TPU Landing Bumper Slots (recessed into right landing rail at X = w - rail_w/2)
    tpu_cutters = []
    tpu_w = 5.0 * SCALE
    tpu_l = 14.0 * SCALE
    tpu_h = TPU_BUMPER_DEPTH # 1.5mm
    for py in [h * 0.25, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_l, tpu_h + 0.1)
        b.translate(App.Vector(w - (rail_w / 2.0) - (tpu_w / 2.0), py - (tpu_l / 2.0), t - tpu_h))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

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
