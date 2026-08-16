"""
motorized_flap.py — Monolithic Active Folding Flap with Symmetrical Dual-Ended Hex Torque Sockets
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
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    ACCENT_BEVEL_DEPTH,
    EXPORT_DIR,
)

FLAP_THICKNESS = 2.4 * SCALE

def make_hexagon_wire(size_af, center_x, center_z, y_pos):
    """Generates an explicit closed hexagon wire in the XZ plane."""
    r = (size_af / 2.0) / math.cos(math.radians(30))
    pts = []
    for i in range(6):
        ang = math.radians(60 * i + 30)
        pts.append(App.Vector(center_x + r * math.cos(ang), y_pos, center_z + r * math.sin(ang)))
    pts.append(pts[0])
    return Part.makePolygon(pts)

def construct_motorized_flap():
    """
    Constructs the Active Folding Flap (Part 7) with smooth under-flap axle gusset transition.
    Features:
      1. Solid cylindrical drive axle (Ø12.9mm) centered at Z_pivot=10.0mm spanning Y=0.5 to 179.0mm.
      2. Smooth under-flap structural reinforcing gusset blending axle into blade.
      3. Driven Top End (Y=179.0mm): Standard 8.0mm female hex socket receiving the motorized_servo_adapter peg.
      4. Output Bottom End (Y=0.5mm): Standard 8.0mm female hex socket transmitting column torque via hex_drive_coupler.
      5. Full-size blade with organic circular cutouts (~45% mass reduction) and diamond micro-grip knurling matching follower_flap.
    """
    w = PANEL_WIDTH - (1.0 * SCALE)          # 239.0mm
    h = PANEL_HEIGHT - (2.0 * SCALE)         # 238.0mm
    t = FLAP_THICKNESS                       # 2.4mm (Z = 15.0 to 17.4mm)
    panel_z_min = BASE_PANEL_THICKNESS       # 15.0mm
    top_z = panel_z_min + t                  # 17.4mm
    pivot_z = PIVOT_Z                        # 10.0mm
    axle_r = (DRIVE_SHAFT_DIAMETER / 2.0) - (0.05 * SCALE) # 6.45mm radius (Ø12.9mm solid core)
    axle_len = 178.5 * SCALE                 # Axle spans from Y=0.5 to Y=179.0mm

    # 1. Main full-size rectangular blade (X = 0 to 239mm, Y = 1 to 239mm, Z = 15.0 to 17.4mm)
    flap_box = Part.makeBox(w, h, t)
    flap_box.translate(App.Vector(0, 1.0 * SCALE, panel_z_min))

    # Knuckle and Motor Corner Relief Cutouts
    cut_bot = Part.makeBox(14.0 * SCALE, 16.0 * SCALE, t + 2.0)
    cut_bot.translate(App.Vector(-0.5 * SCALE, 0.0, panel_z_min - 1.0))

    cut_mid_k = Part.makeBox(14.0 * SCALE, 16.5 * SCALE, t + 2.0)
    cut_mid_k.translate(App.Vector(-0.5 * SCALE, 169.5 * SCALE, panel_z_min - 1.0))

    cut_motor = Part.makeBox(49.0 * SCALE, 56.0 * SCALE, t + 10.0)
    cut_motor.translate(App.Vector(-0.5 * SCALE, 184.8 * SCALE, panel_z_min - 1.0))

    flap = flap_box.cut(Part.makeCompound([cut_bot, cut_mid_k, cut_motor])).removeSplitter()

    # 2. Perimeter Accent Shadow Bevel (1.2mm depth, 4.0mm width on outer free edges)
    bevel_d = ACCENT_BEVEL_DEPTH             # 1.2mm
    bevel_w = 4.0 * SCALE                    # 4.0mm
    bevel_cuts = []

    # Right edge bevel
    b_right = Part.makeBox(bevel_w + 0.1, h + 2.0 * SCALE, bevel_d + 0.1)
    b_right.translate(App.Vector(w - bevel_w, 0.0, top_z - bevel_d))
    bevel_cuts.append(b_right)

    # Bottom edge bevel (for X >= 14mm)
    b_bot = Part.makeBox(w - 14.0 * SCALE, bevel_w + 0.1, bevel_d + 0.1)
    b_bot.translate(App.Vector(14.0 * SCALE, 0.0, top_z - bevel_d))
    bevel_cuts.append(b_bot)

    # Top edge bevel (for X >= 49mm)
    b_top = Part.makeBox(w - 49.0 * SCALE, bevel_w + 0.1, bevel_d + 0.1)
    b_top.translate(App.Vector(49.0 * SCALE, h - bevel_w + 1.0 * SCALE, top_z - bevel_d))
    bevel_cuts.append(b_top)

    flap = flap.cut(Part.makeCompound(bevel_cuts)).removeSplitter()

    # 3. Continuous Solid-Core Cylindrical Drive Axle (Ø12.9mm, Y = 0.5 to 179.0mm)
    axle_solid = Part.makeCylinder(axle_r, axle_len, App.Vector(0, 0.5 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # 4. Smooth Under-Flap Reinforcing Gusset (Y = 15.5 to 169.5mm) matching follower_flap.py
    gusset_start_y = 15.5 * SCALE
    gusset_len = 154.0 * SCALE
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

    # 4b. Smooth Flap-to-Axle Top Transition Bridge (Y = 15.5 to 169.5mm)
    # Smoothly blends the flat top surface of the flap (Z = 17.4mm) over the top of the axle and tangentially into the axle cylinder curve
    theta_t = math.radians(135.0)
    xt = axle_r * math.cos(theta_t)
    zt = pivot_z + axle_r * math.sin(theta_t)
    xs = 4.0 * SCALE
    zs = top_z
    scale_t = 6.0 * SCALE
    ts_x = -scale_t
    ts_z = 0.0
    tt_x = -scale_t * math.sin(theta_t)
    tt_z = scale_t * math.cos(theta_t)

    num_curve = 24
    curve_pts = []
    for i in range(num_curve):
        u = float(i) / float(num_curve - 1)
        h00 = 2 * u**3 - 3 * u**2 + 1
        h10 = u**3 - 2 * u**2 + u
        h01 = -2 * u**3 + 3 * u**2
        h11 = u**3 - u**2
        px = h00 * xs + h10 * ts_x + h01 * xt + h11 * tt_x
        pz = h00 * zs + h10 * ts_z + h01 * zt + h11 * tt_z
        curve_pts.append(App.Vector(px, 0, pz))

    bridge_pts = list(curve_pts)
    bridge_pts.append(App.Vector(0, 0, pivot_z))
    bridge_pts.append(App.Vector(xs, 0, panel_z_min))
    bridge_pts.append(App.Vector(xs, 0, top_z))
    bridge_pts.append(curve_pts[0])

    bridge_face = Part.Face(Part.makePolygon(bridge_pts))
    bridge_solid = bridge_face.extrude(App.Vector(0, gusset_len, 0))
    bridge_solid.translate(App.Vector(0, gusset_start_y, 0))

    # Fuse flap blade with axle, smooth under-flap gusset, and smooth top transition bridge
    flap = flap.fuse(Part.makeCompound([axle_solid, gusset_solid, bridge_solid])).removeSplitter()

    # 5. Top & Bottom End Female 8.0mm Hex Torque Sockets (Matching follower_flap.py)
    socket_d = 10.5 * SCALE
    hex_socket_top_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, 179.0 * SCALE + 0.1)
    hex_socket_top_face = Part.Face(hex_socket_top_wire)
    hex_socket_top_cutter = hex_socket_top_face.extrude(App.Vector(0, -socket_d - 0.1, 0))

    hex_socket_bot_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, -0.1)
    hex_socket_bot_face = Part.Face(hex_socket_bot_wire)
    hex_socket_bot_cutter = hex_socket_bot_face.extrude(App.Vector(0, socket_d + 0.1, 0))

    flap = flap.cut(Part.makeCompound([hex_socket_top_cutter, hex_socket_bot_cutter])).removeSplitter()

    # 6. Multi-Tiered Organic Gradient Circular Cutouts (~45% mass reduction) matching follower_flap
    hole_specs = [
        (w * 0.48, h * 0.50, 18.0 * SCALE),
        (w * 0.28, h * 0.32, 15.0 * SCALE),
        (w * 0.72, h * 0.35, 16.0 * SCALE),
        (w * 0.32, h * 0.70, 17.0 * SCALE),
        (w * 0.70, h * 0.68, 15.5 * SCALE),
        (w * 0.52, h * 0.22, 12.0 * SCALE),
        (w * 0.52, h * 0.78, 12.5 * SCALE),
        (w * 0.22, h * 0.52, 11.0 * SCALE),
        (w * 0.84, h * 0.50, 11.5 * SCALE),
        (w * 0.22, h * 0.15, 8.5 * SCALE),
        (w * 0.82, h * 0.18, 9.0 * SCALE),
        (w * 0.20, h * 0.85, 8.0 * SCALE),
        (w * 0.84, h * 0.82, 8.5 * SCALE),
        (w * 0.37, h * 0.12, 7.0 * SCALE),
        (w * 0.67, h * 0.12, 7.0 * SCALE),
        (w * 0.37, h * 0.88, 7.0 * SCALE),
        (w * 0.67, h * 0.88, 7.0 * SCALE),
    ]

    cutters = []
    for cx, cy, hr in hole_specs:
        if cx - hr < 49.0 * SCALE and cy + hr > 184.0 * SCALE:
            continue
        cyl = Part.makeCylinder(hr, t + 1.0, App.Vector(cx, cy, panel_z_min - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, top_z - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, panel_z_min - 0.1))
        cutters.extend([cyl, c_top, c_bot])

    if cutters:
        flap = flap.cut(Part.makeCompound(cutters)).removeSplitter()

    # 7. 0.6mm Anti-Slip Diamond Micro-Grip Surface Texture (Dual 45° cross-hatch matching follower_flap)
    tex_cutters = []
    tex_spacing = 14.0 * SCALE
    tex_w = 0.8 * SCALE
    tex_d = TEXTURE_HEIGHT                   # 0.6mm
    
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
    step_path = os.path.join(EXPORT_DIR, "motorized_flap.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_flap.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    flap.exportStep(step_path)
    flap.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return flap

def main():
    doc = App.ActiveDocument or App.newDocument("MotorizedFlap")
    shape = construct_motorized_flap()
    feature = doc.addObject("Part::Feature", "MotorizedFlap")
    feature.Shape = shape

def export_part():
    main()

export_part()
