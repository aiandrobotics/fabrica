"""
motorized_frame.py — Active Motorized Module Frame with Horizontal Inline MG996R Servo Bay
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

def construct_motorized_frame():
    """
    Constructs the Active Motorized Frame with horizontal inline MG996R servo mounting bay.
    Top deck is 100% flush (Z=15.0..17.5mm) with zero protruding motor bumps.
    """
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = BOTTOM_SHELL_THICKNESS
    tie_w = 14.0 * SCALE
    tie_h = 3.0 * SCALE
    tie_x = 11.0 * SCALE
    center_x = tie_x + (tie_w / 2.0) # 18.0mm
    y_seam = h / 2.0                 # 120.0mm
    pivot_z = 8.0 * SCALE            # Hinge axis at Z = 8.0mm

    # 1. Main outer shell block (240 x 240 x 15mm)
    outer_box = Part.makeBox(w, h, t)

    # 2. Knuckle Extension Barrels & C1-Continuous Smooth Concave Transition Ramps
    knuckle_r = (DRIVE_SHAFT_DIAMETER / 2.0) + (3.0 * SCALE)  # 9.5mm radius (Ø19.0mm outer barrel)
    knuckle_len = rail_w                                      # 15.0mm
    
    # Bottom Knuckle Barrel (Y = 0 to 15mm)
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    
    # Top Knuckle Barrel (Y = 170 to 185.5mm)
    k_top_start_y = 170.0 * SCALE
    k_top_len = 15.5 * SCALE
    k_top = Part.makeCylinder(knuckle_r, k_top_len, App.Vector(0, k_top_start_y, pivot_z), App.Vector(0, 1, 0))

    # Smooth C1-Continuous Tangent Concave Blend Ramp
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

    # Top-Left Horizontal Motor Housing Solid Box (X = -knuckle_r to 44mm, Y = 185.5 to 240mm, Z = 0 to 15mm)
    servo_housing_w = 44.0 * SCALE + knuckle_r # 53.5mm
    servo_housing_l = (h - 185.5 * SCALE)      # 54.5mm
    servo_housing_box = Part.makeBox(servo_housing_w, servo_housing_l, t)
    servo_housing_box.translate(App.Vector(-knuckle_r, 185.5 * SCALE, 0))

    frame = outer_box.fuse(Part.makeCompound([k_bot, k_top, ramp_bot, ramp_top, servo_housing_box])).removeSplitter()

    # 3. Open Interior Cavities (preserving 4th tie-bar at X in [11, 25mm], Z in [0, 3mm])
    cav_main = Part.makeBox(w - rail_w - tie_x - tie_w, h - 2 * rail_w, t + 4.0 * SCALE)
    cav_main.translate(App.Vector(tie_x + tie_w, rail_w, -2.0 * SCALE))

    cav_left = Part.makeBox(tie_x + 0.5, k_top_start_y - knuckle_len, t + 2.0)
    cav_left.translate(App.Vector(-0.5, knuckle_len, -1.0))

    cav_tie_top = Part.makeBox(tie_w + 2.0 * SCALE, k_top_start_y - knuckle_len, t - tie_h + 2.0)
    cav_tie_top.translate(App.Vector(tie_x - 1.0 * SCALE, knuckle_len, tie_h))

    frame = frame.cut(Part.makeCompound([cav_main, cav_left, cav_tie_top])).removeSplitter()

    # 4. Hinge Bearing Bores (Bottom Y=0..15mm, Top Y=170..185.5mm)
    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE  # 6.75mm radius (Ø13.5mm)

    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    top_bore = Part.makeCylinder(bore_r, k_top_len + 0.2, App.Vector(0, k_top_start_y - 0.1, pivot_z), App.Vector(0, 1, 0))

    # Knuckle planar bottom trim: 100% flat at Z=0.0mm
    trim_bot = Part.makeBox(knuckle_r * 4.0, h + 2.0, knuckle_r + 2.0)
    trim_bot.translate(App.Vector(-knuckle_r * 2.0, -1.0, -knuckle_r - 2.0))

    frame = frame.cut(Part.makeCompound([bot_bore, top_bore, trim_bot])).removeSplitter()

    # 5. Horizontal Inline MG996R Servo Bay Cavity (Y = 185.5 to 238mm, lying flat on 20mm side)
    # Motor body pocket: X = 3.0 to 42.0mm, Y = 192.0 to 234.0mm, Z = -3.0 to 18.5mm
    motor_pocket = Part.makeBox(39.0 * SCALE, 42.0 * SCALE, t + 6.0)
    motor_pocket.translate(App.Vector(3.0 * SCALE, 192.0 * SCALE, -3.0 * SCALE))

    # Output Spline & Shaft Clearance Tunnel (along X=0, Z=8.0mm from Y=185.0 to 192.5mm)
    spline_tunnel = Part.makeCylinder(8.5 * SCALE, 7.6 * SCALE, App.Vector(0, 185.0 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # Flange Mounting Ears Recesses (for M3 screws at X = 28.0 to 32.5mm, Y = 188.5 to 237.5mm)
    flange_recess = Part.makeBox(6.0 * SCALE, 50.0 * SCALE, t + 6.0)
    flange_recess.translate(App.Vector(27.5 * SCALE, 188.0 * SCALE, -3.0 * SCALE))

    # 2x M3 Mounting Screw Holes
    screw_r = 1.6 * SCALE
    screws = [
        Part.makeCylinder(screw_r, 20.0 * SCALE, App.Vector(30.5 * SCALE, 190.0 * SCALE, -2.0 * SCALE), App.Vector(0, 0, 1)),
        Part.makeCylinder(screw_r, 20.0 * SCALE, App.Vector(30.5 * SCALE, 236.0 * SCALE, -2.0 * SCALE), App.Vector(0, 0, 1)),
    ]

    # Cable Pass-Through Conduit (routing servo wire from rear into central open cavity)
    wire_conduit = Part.makeBox(14.0 * SCALE, 10.0 * SCALE, 10.0 * SCALE)
    wire_conduit.translate(App.Vector(tie_x + tie_w - 2.0 * SCALE, 210.0 * SCALE, 0))

    # Flush Cover Slide-In Retention Grooves at Z = 13.2mm (along Y in [186.0..238.0mm])
    cover_groove_l = Part.makeBox(2.0 * SCALE, 52.0 * SCALE, 2.0 * SCALE)
    cover_groove_l.translate(App.Vector(-0.5 * SCALE, 186.0 * SCALE, 13.2 * SCALE))
    
    cover_groove_r = Part.makeBox(2.0 * SCALE, 52.0 * SCALE, 2.0 * SCALE)
    cover_groove_r.translate(App.Vector(42.5 * SCALE, 186.0 * SCALE, 13.2 * SCALE))

    frame = frame.cut(Part.makeCompound([
        motor_pocket, spline_tunnel, flange_recess, wire_conduit, cover_groove_l, cover_groove_r
    ] + screws)).removeSplitter()

    # 6. Female Open-Top True Sliding Dovetail Joiner Sockets on Outer Walls (Front Y=0, Back Y=H, Right X=W)
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

    # Master bottom push-out finger access hole (Ø6.0mm through bottom floor)
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
    c_back.translate(App.Vector(w / 2.0 + 30.0 * SCALE, h, 0))
    dt_cutters.append(c_back)

    # Right Wall (X=W) -> cuts into -X
    c_right = dt_cutter_with_hole.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))
    dt_cutters.append(c_right)

    # 7. Clean Solid Through-Dovetail Joint on 4th Wall (3.0mm solid outer walls, 0 floating pieces, 0 supports)
    dt_lk_neck = 4.0 * SCALE
    dt_lk_flare = 8.0 * SCALE
    dt_lk_depth = 8.0 * SCALE
    gap = 0.25 * SCALE

    x_left = tie_x - (1.0 * SCALE)
    x_right = tie_x + tie_w + (1.0 * SCALE)

    dt4_poly_pts = [
        # Top edge of female pocket (in +Y half)
        App.Vector(x_right, y_seam + gap, 0),
        App.Vector(center_x + dt_lk_neck / 2.0 + gap, y_seam + gap, 0),
        App.Vector(center_x + dt_lk_flare / 2.0 + gap, y_seam + dt_lk_depth + gap, 0),
        App.Vector(center_x - dt_lk_flare / 2.0 - gap, y_seam + dt_lk_depth + gap, 0),
        App.Vector(center_x - dt_lk_neck / 2.0 - gap, y_seam + gap, 0),
        App.Vector(x_left, y_seam + gap, 0),
        
        # Bottom edge of male tab (in -Y half)
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
    dt_cutters.append(dt4_cutter)

    frame = frame.cut(Part.makeCompound(dt_cutters)).removeSplitter()

    # 8. Anti-Slip Foot Pad Recess Sockets (4x on bottom face of rails for Ø12mm x 2.0mm rubber feet)
    foot_r = 6.0 * SCALE
    foot_d = 2.0 * SCALE
    foot_locs = [
        (w - (rail_w / 2.0), rail_w / 2.0),          # Bottom Right
        (w - (rail_w / 2.0), h - (rail_w / 2.0)),      # Top Right
        (25.0 * SCALE, rail_w / 2.0),                  # Bottom Left (along front rail)
        (55.0 * SCALE, h - (rail_w / 2.0)),            # Top Left (along back rail)
    ]
    foot_cutters = [
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(fx, fy, -0.1))
        for fx, fy in foot_locs
    ]
    frame = frame.cut(Part.makeCompound(foot_cutters)).removeSplitter()

    # 9. TPU Silent-Flip Landing Bumper Slots (1.5mm recessed into top landing rail at X = w - rail_w/2)
    tpu_cutters = []
    tpu_w = 5.0 * SCALE
    tpu_l = 14.0 * SCALE
    tpu_h = TPU_BUMPER_DEPTH # 1.5mm
    for py in [h * 0.25, h * 0.5, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_l, tpu_h + 0.1)
        b.translate(App.Vector(w - (rail_w / 2.0) - (tpu_w / 2.0), py - (tpu_l / 2.0), t - tpu_h))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 10. Elephant's Foot Relief Chamfer along outer bottom bed edges
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
