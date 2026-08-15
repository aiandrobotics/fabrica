"""
motorized_flap.py — Monolithic Active Folding Flap (Full Blade with Integrated Drive Axle)
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
    PANEL_THICKNESS,
    BASE_PANEL_THICKNESS,
    PIVOT_Z,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    ACCENT_BEVEL_DEPTH,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    PRESS_FIT_CLEARANCE,
    EXPORT_DIR,
)

FLAP_THICKNESS = 2.4 * SCALE

def construct_motorized_flap():
    """
    Constructs the Monolithic Active Folding Flap with integrated continuous drive axle,
    integrated 25T metal servo horn socket, female hex torque output socket,
    full rectangular blade geometry, circular cutouts, and micro-grip texture.
    """
    w = PANEL_WIDTH - (1.0 * SCALE)          # 239.0mm
    h = PANEL_HEIGHT - (2.0 * SCALE)         # 238.0mm
    flap_t = FLAP_THICKNESS                  # 2.4mm (Z = 15.0 to 17.4mm)
    z_deck = 15.0 * SCALE
    pivot_z = PIVOT_Z                        # Hinge axis at X=0, Z=10.0mm
    axle_r = (DRIVE_SHAFT_DIAMETER / 2.0) - (0.05 * SCALE) # 6.45mm radius (Ø12.9mm solid core)
    axle_len = 185.0 * SCALE                 # Reaches from Y=0.5 to Y=185.0mm (engages 25T horn at Y=185mm)

    # 1. Main full-size rectangular blade (X = 0 to 239mm, Y = 1 to 239mm, Z = 15.0 to 17.4mm)
    blade = Part.makeBox(w, h, flap_t)
    blade.translate(App.Vector(0, 1.0 * SCALE, z_deck))

    # Knuckle and Motor Corner Relief Cutouts
    cut_bot = Part.makeBox(14.0 * SCALE, 16.0 * SCALE, flap_t + 2.0)
    cut_bot.translate(App.Vector(-0.5 * SCALE, 0.0, z_deck - 1.0))

    cut_mid_k = Part.makeBox(14.0 * SCALE, 16.5 * SCALE, flap_t + 2.0)
    cut_mid_k.translate(App.Vector(-0.5 * SCALE, 169.5 * SCALE, z_deck - 1.0))

    cut_motor = Part.makeBox(44.5 * SCALE, 55.0 * SCALE, flap_t + 2.0)
    cut_motor.translate(App.Vector(-0.5 * SCALE, 185.5 * SCALE, z_deck - 1.0))

    blade = blade.cut(Part.makeCompound([cut_bot, cut_mid_k, cut_motor])).removeSplitter()

    # 2. Continuous Solid-Core Cylindrical Drive Axle (Ø12.9mm, Y = 0.5 to 185.0mm)
    axle = Part.makeCylinder(axle_r, axle_len - 0.5 * SCALE, App.Vector(0, 0.5 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # Structural Gusset Web bridging axle into blade between knuckles (X = 0 to 11mm, Y = 15.5 to 169.5mm, Z = 10.0 to 15.0mm)
    gusset = Part.makeBox(11.0 * SCALE, 154.0 * SCALE, z_deck - pivot_z + flap_t)
    gusset.translate(App.Vector(0, 15.5 * SCALE, pivot_z))

    flap = blade.fuse(Part.makeCompound([axle, gusset])).removeSplitter()

    # Smooth Outer Tangent Profile (Trimming outside cylinder arc X < 0)
    outer_trim = Part.makeBox(axle_r * 4.0, h + 4.0 * SCALE, z_deck + flap_t + 4.0)
    outer_trim.translate(App.Vector(-axle_r * 4.0, -2.0 * SCALE, -2.0 * SCALE))
    
    cyl_keep = Part.makeCylinder(axle_r, axle_len + 0.2, App.Vector(0, 0.4 * SCALE, pivot_z), App.Vector(0, 1, 0))
    outer_trim = outer_trim.cut(cyl_keep)

    # Bottom clearance trim (Z < 0)
    bot_trim = Part.makeBox(w + 10.0, h + 10.0, 10.0)
    bot_trim.translate(App.Vector(-5.0, -5.0, -10.0))

    flap = flap.cut(Part.makeCompound([outer_trim, bot_trim])).removeSplitter()

    # 3. Rear 25T Metal Servo Horn Drive Socket (at Y = 185.0mm)
    horn_od = 7.0 * SCALE + PRESS_FIT_CLEARANCE   # 7.2mm outer spline receiver radius (Ø14.4mm)
    horn_pocket_depth = 8.0 * SCALE
    horn_pocket = Part.makeCylinder(horn_od, horn_pocket_depth + 0.1, App.Vector(0, axle_len - horn_pocket_depth, pivot_z), App.Vector(0, 1, 0))

    # M3 Central Retention Screw Access Counterbore (through axle to lock horn onto servo)
    screw_hole = Part.makeCylinder(1.6 * SCALE, 20.0 * SCALE, App.Vector(0, axle_len - horn_pocket_depth - 15.0 * SCALE, pivot_z), App.Vector(0, 1, 0))
    screw_head_cb = Part.makeCylinder(3.2 * SCALE, 10.0 * SCALE, App.Vector(0, axle_len - horn_pocket_depth - 15.0 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # 4. Front Female Hex Torque Output Socket (at Y = 0.5mm, for HexDriveCoupler)
    hex_r = (HEX_COUPLER_SIZE / 2.0) / math.cos(math.radians(30)) + PRESS_FIT_CLEARANCE
    hex_depth = 10.5 * SCALE
    hex_pts = []
    for i in range(6):
        ang = math.radians(60 * i + 30)
        hex_pts.append(App.Vector(hex_r * math.cos(ang), 0.4 * SCALE, pivot_z + hex_r * math.sin(ang)))
    hex_pts.append(hex_pts[0])
    hex_wire = Part.makePolygon(hex_pts)
    hex_face = Part.Face(hex_wire)
    hex_socket = hex_face.extrude(App.Vector(0, hex_depth + 0.1, 0))

    # Lead-in Chamfer for smooth hex coupler alignment
    chamfer_cone = Part.makeCone(hex_r + 1.0 * SCALE, hex_r, 1.5 * SCALE, App.Vector(0, 0.4 * SCALE, pivot_z), App.Vector(0, 1, 0))
    hex_cutter = hex_socket.fuse(chamfer_cone)

    flap = flap.cut(Part.makeCompound([horn_pocket, screw_hole, screw_head_cb, hex_cutter])).removeSplitter()

    # 5. Multi-Tiered Organic Circular Weight-Reduction Cutouts (~45% mass reduction)
    cutout_specs = [
        # Center large circular windows
        (w * 0.40, h * 0.35, 18.0 * SCALE),
        (w * 0.70, h * 0.35, 18.0 * SCALE),
        (w * 0.40, h * 0.65, 18.0 * SCALE),
        (w * 0.70, h * 0.65, 18.0 * SCALE),
        (w * 0.55, h * 0.50, 20.0 * SCALE),
        # Intermediate perimeter windows
        (w * 0.22, h * 0.20, 12.0 * SCALE),
        (w * 0.55, h * 0.20, 13.0 * SCALE),
        (w * 0.85, h * 0.20, 12.0 * SCALE),
        (w * 0.55, h * 0.80, 13.0 * SCALE),
        (w * 0.85, h * 0.80, 12.0 * SCALE),
        (w * 0.22, h * 0.50, 13.0 * SCALE),
        (w * 0.88, h * 0.50, 13.0 * SCALE),
    ]

    cutters = []
    for cx, cy, hr in cutout_specs:
        cyl = Part.makeCylinder(hr, flap_t + 1.0, App.Vector(cx, cy, z_deck - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, z_deck + flap_t - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, z_deck - 0.1))
        cutters.extend([cyl, c_top, c_bot])

    flap = flap.cut(Part.makeCompound(cutters)).removeSplitter()

    # 6. Micro-Grip Diamond Surface Texture (0.6mm debossed grip knurling on top surface)
    tex_cutters = []
    tex_spacing = 14.0 * SCALE
    tex_w = 0.8 * SCALE
    tex_d = TEXTURE_HEIGHT # 0.6mm
    top_z = z_deck + flap_t

    for i in range(-int(w), int(w + h), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, h * 1.5, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, top_z - tex_d))
        g2 = Part.makeBox(tex_w, h * 1.5, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, h, top_z - tex_d))
        tex_cutters.extend([g1, g2])

    if tex_cutters:
        tex_bound = Part.makeBox(w - 2 * 3.0 * SCALE, h - 2 * 3.0 * SCALE, flap_t + 2.0)
        tex_bound.translate(App.Vector(3.0 * SCALE, 4.0 * SCALE, z_deck - 1.0))
        tex_compound = Part.makeCompound(tex_cutters).common(tex_bound)
        flap = flap.cut(tex_compound).removeSplitter()

    # 7. Perimeter Accent Shadow Bevel (1.2mm recessed aesthetic border)
    bevel_w = 1.2 * SCALE
    b1 = Part.makeBox(w + 2.0, bevel_w, ACCENT_BEVEL_DEPTH + 0.1)
    b1.translate(App.Vector(-1.0, 1.0 * SCALE, top_z - ACCENT_BEVEL_DEPTH))
    b2 = Part.makeBox(w + 2.0, bevel_w, ACCENT_BEVEL_DEPTH + 0.1)
    b2.translate(App.Vector(-1.0, h - bevel_w + 1.0 * SCALE, top_z - ACCENT_BEVEL_DEPTH))
    b3 = Part.makeBox(bevel_w, h + 2.0, ACCENT_BEVEL_DEPTH + 0.1)
    b3.translate(App.Vector(w - bevel_w, 0, top_z - ACCENT_BEVEL_DEPTH))

    flap = flap.cut(Part.makeCompound([b1, b2, b3])).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_flap.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_flap.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    flap.exportStep(step_path)
    flap.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return flap

def main():
    doc = App.newDocument("MotorizedFlap")
    shape = construct_motorized_flap()
    feature = doc.addObject("Part::Feature", "MotorizedFlap")
    feature.Shape = shape

main()
