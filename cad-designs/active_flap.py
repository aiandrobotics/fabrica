"""
active_flap.py — Monolithic Active Folding Flap with Integrated 25T Servo Horn Socket & Drive Axle
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
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    HEX_COUPLER_DEPTH,
    ACCENT_BEVEL_DEPTH,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    ELEPHANTS_FOOT_CHAMFER,
    EXPORT_DIR,
)

PADDLE_THICKNESS = 2.4 * SCALE

def make_hexagon_wire(flat_to_flat, center_x, center_z, y_pos):
    """Generates a regular hexagon wire in the XZ plane at a given Y position."""
    r = (flat_to_flat / math.sqrt(3.0))
    pts = [
        App.Vector(center_x + r * math.cos(i * math.pi / 3.0), y_pos, center_z + r * math.sin(i * math.pi / 3.0))
        for i in range(7)
    ]
    return Part.makePolygon(pts)

def construct_active_flap():
    """
    Constructs the Monolithic Active Folding Flap with Integrated 25T Servo Horn Socket.
    """
    w = PANEL_WIDTH          # 240.0mm full module width
    h = PANEL_HEIGHT         # 240.0mm full module length
    t = PADDLE_THICKNESS     # 2.4mm panel thickness
    total_z = BASE_PANEL_THICKNESS # 15.0mm (frame top rail height)
    pivot_z = 8.0 * SCALE    # 8.0mm
    panel_z_min = total_z    # 15.0mm (rests directly on top of frame rails)
    top_z = panel_z_min + t  # 17.4mm (flush with knuckle top crown at 17.5mm)
    axle_end_y = 186.0 * SCALE # Axle spans from Y=0 to Y=186mm (boss at Y=178 to 186mm)

    # 1. Base solid flap slab (Extends from X=0 to X=240mm, Y=0 to Y=240mm, Z=15.0 to Z=17.4mm)
    flap_box = Part.makeBox(w, h, t)
    flap_box.translate(App.Vector(0, 0, panel_z_min))

    # Knuckle clearance corner cutout for bottom knuckle (Y <= 15.8mm)
    cut_bot = Part.makeBox(11.5 * SCALE, 15.8 * SCALE, t + 2.0)
    cut_bot.translate(App.Vector(-0.5, -0.5, panel_z_min - 0.5))

    # Top-Left Knuckle & Servo Bay Corner Relief Cutout (X in [0, 52.0mm], Y in [164.0, 240.0mm])
    servo_cut_w = 52.0 * SCALE
    servo_cut_l = h - (164.0 * SCALE) + 0.5 # 76.5mm (Y = 164.0 to 240.0mm)
    cut_servo = Part.makeBox(servo_cut_w + 0.5, servo_cut_l + 1.0, t + 2.0)
    cut_servo.translate(App.Vector(-0.5, 164.0 * SCALE, panel_z_min - 0.5))

    flap = flap_box.cut(Part.makeCompound([cut_bot, cut_servo])).removeSplitter()

    # 2. Dual-Tone Perimeter Shadow Bevel (1.2mm depth on outer free edges)
    bevel_d = ACCENT_BEVEL_DEPTH  # 1.2mm
    bevel_w = 3.0 * SCALE
    
    bevel_cuts = []
    # Right edge bevel
    b_right = Part.makeBox(bevel_w + 0.2, h + 0.2, bevel_d + 0.1)
    b_right.translate(App.Vector(w - bevel_w, -0.1, top_z - bevel_d))
    bevel_cuts.append(b_right)
    
    # Bottom edge bevel (for X >= 12mm)
    b_bot = Part.makeBox(w - 11.5 * SCALE, bevel_w + 0.1, bevel_d + 0.1)
    b_bot.translate(App.Vector(11.5 * SCALE, -0.1, top_z - bevel_d))
    bevel_cuts.append(b_bot)
    
    # Top edge bevel (for X >= 52mm)
    b_top = Part.makeBox(w - servo_cut_w, bevel_w + 0.1, bevel_d + 0.1)
    b_top.translate(App.Vector(servo_cut_w, h - bevel_w, top_z - bevel_d))
    bevel_cuts.append(b_top)
    
    # Inner corner shadow bevel step along the servo notch
    b_corner_x = Part.makeBox(bevel_w + 0.1, servo_cut_l, bevel_d + 0.1)
    b_corner_x.translate(App.Vector(servo_cut_w - bevel_w, 164.0 * SCALE, top_z - bevel_d))
    bevel_cuts.append(b_corner_x)

    flap = flap.cut(Part.makeCompound(bevel_cuts)).removeSplitter()

    # 3. Continuous Solid Drive Axle (Y = 0.0 to 178.0mm with shaft_r=6.5mm, boss at Y=178 to 186mm)
    shaft_r = DRIVE_SHAFT_DIAMETER / 2.0  # 6.5mm (Ø13.0mm in Ø13.5mm knuckle bores)
    axle_solid = Part.makeCylinder(shaft_r, 178.0 * SCALE, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))

    # Top Driven End Enlarged Boss for 25T Servo Horn Pocket (Y = 178 to 186mm, Outer Ø17.0mm in Ø24mm pocket)
    boss_r = 8.5 * SCALE
    boss_len = 8.0 * SCALE
    servo_boss = Part.makeCylinder(boss_r, boss_len, App.Vector(0, 178.0 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # 4. Under-Flap Structural Reinforcing Gusset (Y = 15.8mm to 164.0mm between knuckles)
    gusset_start_y = 15.8 * SCALE
    gusset_len = (164.0 - 15.8) * SCALE # 148.2mm (ends at Y = 164.0mm before top knuckle)
    gusset_pts = [
        App.Vector(0, gusset_start_y, pivot_z),
        App.Vector(3.25 * SCALE, gusset_start_y, pivot_z - 3.0 * SCALE),
        App.Vector(6.5 * SCALE, gusset_start_y, pivot_z - 1.0 * SCALE),
        App.Vector(14.0 * SCALE, gusset_start_y, panel_z_min),
        App.Vector(0, gusset_start_y, panel_z_min),
        App.Vector(0, gusset_start_y, pivot_z),
    ]
    gusset_wire = Part.makePolygon(gusset_pts)
    gusset_face = Part.Face(gusset_wire)
    gusset_solid = gusset_face.extrude(App.Vector(0, gusset_len, 0))

    # Fuse flap panel with continuous drive axle, servo boss, and reinforcing gusset
    flap = flap.fuse(Part.makeCompound([axle_solid, servo_boss, gusset_solid])).removeSplitter()

    # 5. Output End (Y = 0) Female 8.0mm Hex Torque Socket
    socket_d = 10.5 * SCALE
    hex_socket_bot_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, -0.1)
    hex_socket_bot_face = Part.Face(hex_socket_bot_wire)
    hex_socket_bot_cutter = hex_socket_bot_face.extrude(App.Vector(0, socket_d + 0.1, 0))

    # 6. Driven End (Y = 186mm) 25T Servo Horn Pocket & M3 Screw Retention Holes
    # 25T spline pocket: Ø6.0mm bore, 4.0mm deep entering into -Y from Y=186mm
    spline_bore = Part.makeCylinder(3.0 * SCALE, 4.2 * SCALE, App.Vector(0, axle_end_y - 4.1 * SCALE, pivot_z), App.Vector(0, 1, 0))
    
    # M3 Central Retention Screw Through-Hole (Ø3.2mm) through Y = 175 to 186mm
    m3_hole = Part.makeCylinder(1.6 * SCALE, 12.0 * SCALE, App.Vector(0, axle_end_y - 11.5 * SCALE, pivot_z), App.Vector(0, 1, 0))
    
    # M3 Screw Head Counterbore (Ø6.0mm x 2.5mm deep) entering from Y=175mm
    m3_counterbore = Part.makeCylinder(3.0 * SCALE, 2.6 * SCALE, App.Vector(0, axle_end_y - 11.5 * SCALE, pivot_z), App.Vector(0, 1, 0))

    flap = flap.cut(Part.makeCompound([hex_socket_bot_cutter, spline_bore, m3_hole, m3_counterbore])).removeSplitter()

    # 7. Multi-Tiered Organic Gradient Circular Cutouts (~45% mass reduction)
    hole_specs = [
        (w * 0.48, h * 0.45, 18.0 * SCALE),
        (w * 0.28, h * 0.30, 15.0 * SCALE),
        (w * 0.72, h * 0.35, 16.0 * SCALE),
        (w * 0.32, h * 0.58, 16.5 * SCALE),
        (w * 0.70, h * 0.68, 15.5 * SCALE),
        (w * 0.52, h * 0.20, 12.0 * SCALE),
        (w * 0.52, h * 0.72, 12.5 * SCALE),
        (w * 0.22, h * 0.46, 11.0 * SCALE),
        (w * 0.84, h * 0.50, 11.5 * SCALE),
        (w * 0.22, h * 0.15, 8.5 * SCALE),
        (w * 0.82, h * 0.18, 9.0 * SCALE),
        (w * 0.75, h * 0.85, 9.5 * SCALE),
        (w * 0.85, h * 0.82, 8.5 * SCALE),
        (w * 0.37, h * 0.12, 7.0 * SCALE),
        (w * 0.67, h * 0.12, 7.0 * SCALE),
        (w * 0.58, h * 0.88, 7.0 * SCALE),
        (w * 0.40, h * 0.70, 9.5 * SCALE),
    ]

    cutters = []
    for cx, cy, hr in hole_specs:
        cyl = Part.makeCylinder(hr, t + 1.0, App.Vector(cx, cy, panel_z_min - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, top_z - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, panel_z_min - 0.1))
        cutters.extend([cyl, c_top, c_bot])

    if cutters:
        flap = flap.cut(Part.makeCompound(cutters)).removeSplitter()

    # 8. 0.6mm Diamond Micro-Grip Surface Texture
    tex_cutters = []
    tex_spacing = 14.0 * SCALE
    tex_w = 0.8 * SCALE
    tex_d = TEXTURE_HEIGHT
    
    for i in range(-int(w), int(w + h), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, h * 1.5, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, top_z - tex_d))
        g2 = Part.makeBox(tex_w, h * 1.5, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, h, top_z - tex_d))
        tex_cutters.extend([g1, g2])

    if tex_cutters:
        tex_bound = Part.makeBox(w - 2 * bevel_w, h - 2 * bevel_w, t + 2.0)
        tex_bound.translate(App.Vector(bevel_w, bevel_w, panel_z_min - 1.0))
        tex_compound = Part.makeCompound(tex_cutters).common(tex_bound)
        flap = flap.cut(tex_compound).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "active_flap.step")
    stl_path  = os.path.join(EXPORT_DIR, "active_flap.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    flap.exportStep(step_path)
    flap.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return flap

def main():
    doc = App.newDocument("ActiveFlap")
    shape = construct_active_flap()
    feature = doc.addObject("Part::Feature", "ActiveFlap")
    feature.Shape = shape

main()
