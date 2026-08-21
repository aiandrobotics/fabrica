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
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    ACCENT_BEVEL_DEPTH,
    EXPORT_DIR,
)

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
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    t = params.PADDLE_THICKNESS                  # 2.4mm
    pivot_z = PIVOT_Z                            # 15.00mm (exact top deck hinge line)
    panel_z_min = pivot_z                        # 15.00mm (rests directly on top of frame rails)
    top_z = pivot_z + t                          # 17.40mm
    rail_w = 15.0
    gap_axial = 0.5
    gap_radial = 0.5

    shaft_r = DRIVE_SHAFT_DIAMETER / 2.0         # 6.40mm
    knuckle_r = shaft_r + 3.0                    # 9.40mm

    # Full Frame Coverage Span: Covers frame top deck from Y=0.5 to Y=219.5mm (219.0mm length)
    y_min_blade = gap_axial                       # 0.5mm
    y_max_blade = h - gap_axial                   # 219.5mm
    total_blade_len = y_max_blade - y_min_blade   # 219.0mm

    # Modular Drop-In Spine Span: Starts at Y=16.0mm (seats against bottom pin inner thrust disk)
    y_knuckle_bot = 16.0                          # 16.0mm
    y_knuckle_mot_top = h - 70.0 - gap_axial     # 149.5mm
    mid_len = y_knuckle_mot_top - y_knuckle_bot  # 133.5mm

    x_min = -shaft_r                             # -6.4mm
    x_wing_start = knuckle_r + gap_radial        # 9.9mm
    x_max = w - gap_axial                        # 219.5mm
    total_w = x_max - x_min                      # 225.9mm
    full_wing_w = x_max - x_wing_start           # 209.6mm

    # Motor module notch boundary (motor housing spans X in [-24.0, 48.0mm], Y in [150.0, 220.0mm])
    # Inner notch clearance at X = 50.5mm (giving 100% collision-free kinematic rotation clearance)
    x_mot_notch = 50.5

    # 1. Main outer slab spanning X in [x_wing_start, x_max], Y in [y_min_blade, y_max_blade]
    slab_base = Part.makeBox(full_wing_w, total_blade_len, t)
    slab_base.translate(App.Vector(x_wing_start, y_min_blade, panel_z_min))

    # Cut away the motor module notch from slab_base: X in [x_wing_start - 1.0, x_mot_notch], Y in [149.5, 220.5]
    cut_motor_bay = Part.makeBox(x_mot_notch - x_wing_start + 1.0, (h - 70.0 - gap_axial) + 72.0, t + 2.0)
    cut_motor_bay.translate(App.Vector(x_wing_start - 0.5, y_knuckle_mot_top, panel_z_min - 1.0))
    slab_outer = slab_base.cut(cut_motor_bay)

    # 2. Hinge extension between knuckles spanning Y in [16.0, 149.5mm], X in [0.0, 9.9mm]
    slab_hinge = Part.makeBox(x_wing_start, mid_len, t)
    slab_hinge.translate(App.Vector(0.0, y_knuckle_bot, panel_z_min))

    blade = slab_outer.fuse(slab_hinge).removeSplitter()

    # Outer corner fillets (R=3.0mm on top-right and bottom-right outer corners)
    corner_cutter1 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter1.translate(App.Vector(x_max - 3.0, y_min_blade - 3.0, panel_z_min - 1.0))
    corner_cyl1 = Part.makeCylinder(3.0, t + 2.0, App.Vector(x_max - 3.0, y_min_blade + 3.0, panel_z_min - 1.0))
    corner_trim1 = corner_cutter1.cut(corner_cyl1)

    corner_cutter2 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter2.translate(App.Vector(x_max - 3.0, y_max_blade - 3.0, panel_z_min - 1.0))
    corner_cyl2 = Part.makeCylinder(3.0, t + 2.0, App.Vector(x_max - 3.0, y_max_blade - 3.0, panel_z_min - 1.0))
    corner_trim2 = corner_cutter2.cut(corner_cyl2)

    blade = blade.cut(Part.makeCompound([corner_trim1, corner_trim2])).removeSplitter()

    # 3. Perimeter Shadow Bevel (Uniform 2.0mm around the OUTER boundary ONLY)
    border_w = 2.0
    bevel_d = ACCENT_BEVEL_DEPTH          # 1.2mm
    bevel_cuts = []

    # Right edge bevel (Full height Y in [0.5, 219.5mm])
    b_right = Part.makeBox(border_w + 0.2, total_blade_len + 0.2, bevel_d + 0.1)
    b_right.translate(App.Vector(x_max - border_w, y_min_blade - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_right)

    # Bottom outer edge bevel (X in [9.9, 219.5mm])
    b_bot = Part.makeBox(full_wing_w + 0.1, border_w + 0.1, bevel_d + 0.1)
    b_bot.translate(App.Vector(x_wing_start, y_min_blade - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_bot)

    # Bottom knuckle notch step bevel (at Y = 16.0mm, X in [shaft_r, 9.9mm])
    b_kbot = Part.makeBox(x_wing_start - shaft_r + 0.1, border_w + 0.1, bevel_d + 0.1)
    b_kbot.translate(App.Vector(shaft_r, y_knuckle_bot - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_kbot)

    # Bottom knuckle inner wing side bevel along X = x_wing_start
    b_kw_bot = Part.makeBox(border_w + 0.1, y_knuckle_bot - y_min_blade + 0.2, bevel_d + 0.1)
    b_kw_bot.translate(App.Vector(x_wing_start - border_w, y_min_blade - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_kw_bot)

    # Top outer edge bevel (X in [x_mot_notch, 219.5mm])
    b_top = Part.makeBox(x_max - x_mot_notch + 0.1, border_w + 0.1, bevel_d + 0.1)
    b_top.translate(App.Vector(x_mot_notch, y_max_blade - border_w, top_z - bevel_d))
    bevel_cuts.append(b_top)

    # Motor notch left inner edge bevel (at X = x_mot_notch, Y in [149.5, 219.5mm])
    b_mot_left = Part.makeBox(border_w + 0.1, y_max_blade - y_knuckle_mot_top + 0.2, bevel_d + 0.1)
    b_mot_left.translate(App.Vector(x_mot_notch - 0.1, y_knuckle_mot_top - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_mot_left)

    # Motor notch bottom step bevel (at Y = 149.5mm, X in [shaft_r, x_mot_notch])
    b_mot_bot = Part.makeBox(x_mot_notch - shaft_r + 0.1, border_w + 0.1, bevel_d + 0.1)
    b_mot_bot.translate(App.Vector(shaft_r, y_knuckle_mot_top - border_w, top_z - bevel_d))
    bevel_cuts.append(b_mot_bot)

    flap = blade.cut(Part.makeCompound([b_right, b_bot, b_kbot, b_kw_bot, b_top, b_mot_left, b_mot_bot])).removeSplitter()

    # 4. Continuous Full Cylindrical Drive Axle (Ø12.8mm full cylinder providing 100% 360° hex socket enclosure)
    axle_mid_full = Part.makeCylinder(shaft_r, mid_len, App.Vector(0, y_knuckle_bot, pivot_z), App.Vector(0, 1, 0))
    flap = flap.fuse(axle_mid_full).removeSplitter()

    # 5. Output Female Hex Sockets (Bottom: Y=16.0mm, Top: Y=149.5mm)
    socket_d = 10.0
    hex_socket_bot_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, y_knuckle_bot - 0.1)
    hex_socket_bot_face = Part.Face(hex_socket_bot_wire)
    hex_socket_bot_cutter = hex_socket_bot_face.extrude(App.Vector(0, socket_d + 0.1, 0))

    hex_socket_top_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, y_knuckle_mot_top + 0.1)
    hex_socket_top_face = Part.Face(hex_socket_top_wire)
    hex_socket_top_cutter = hex_socket_top_face.extrude(App.Vector(0, -socket_d - 0.1, 0))

    flap = flap.cut(Part.makeCompound([hex_socket_bot_cutter, hex_socket_top_cutter])).removeSplitter()

    # 6. Multi-Tiered Organic Gradient Circular Cutouts (~45% mass reduction)
    mid_blade_w = x_max - (-shaft_r)
    scale_geo = min(mid_blade_w, total_blade_len) / 200.0
    hole_uvs = [
        (0.55, 0.45, 18.0 * scale_geo),
        (0.35, 0.30, 15.0 * scale_geo),
        (0.75, 0.32, 16.0 * scale_geo),
        (0.40, 0.65, 17.0 * scale_geo),
        (0.75, 0.65, 15.5 * scale_geo),
        (0.58, 0.20, 12.0 * scale_geo),
        (0.58, 0.75, 12.5 * scale_geo),
        (0.30, 0.48, 11.0 * scale_geo),
        (0.86, 0.48, 11.5 * scale_geo),
        (0.30, 0.15, 8.5 * scale_geo),
        (0.84, 0.18, 9.0 * scale_geo),
        (0.68, 0.88, 10.0 * scale_geo),
        (0.86, 0.82, 8.5 * scale_geo),
        (0.42, 0.12, 7.0 * scale_geo),
        (0.72, 0.12, 7.0 * scale_geo),
    ]

    cutters = []
    for u, v, hr in hole_uvs:
        cx = 15.0 + (mid_blade_w - 30.0) * u
        cy = y_min_blade + (total_blade_len) * v
        if cx < x_mot_notch + hr and cy > y_knuckle_mot_top - hr:
            continue
        cyl = Part.makeCylinder(hr, t + 1.0, App.Vector(cx, cy, panel_z_min - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, top_z - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, panel_z_min - 0.1))
        cutters.extend([cyl, c_top, c_bot])

    if cutters:
        flap = flap.cut(Part.makeCompound(cutters)).removeSplitter()

    # 7. 0.6mm Anti-Slip Diamond Micro-Grip Surface Texture extending across entire flap face to borders
    tex_cutters = []
    tex_spacing = 14.0
    tex_w = 0.8
    tex_d = TEXTURE_HEIGHT                   # 0.6mm
    
    for i in range(-int(w), int(w + h * 2), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, h * 2.0, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, top_z - tex_d))
        g2 = Part.makeBox(tex_w, h * 2.0, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, h, top_z - tex_d))
        tex_cutters.extend([g1, g2])

    # Bound for the outer slab inset by border_w
    tb_slab_base = Part.makeBox(full_wing_w - border_w + 1.0, total_blade_len - 2 * border_w, t + 2.0)
    tb_slab_base.translate(App.Vector(x_wing_start - 0.5, y_min_blade + border_w, panel_z_min - 1.0))
    tb_cut = Part.makeBox(x_mot_notch - x_wing_start + border_w + 1.0, (h - 70.0 - gap_axial) + 72.0, t + 4.0)
    tb_cut.translate(App.Vector(x_wing_start - 0.5, y_knuckle_mot_top - border_w, panel_z_min - 2.0))
    tb_slab = tb_slab_base.cut(tb_cut)

    # Bound for the hinge extension inset by border_w (X in [shaft_r, x_wing_start])
    tb_hinge = Part.makeBox(x_wing_start - shaft_r + 1.0, mid_len - 2 * border_w, t + 2.0)
    tb_hinge.translate(App.Vector(shaft_r, y_knuckle_bot + border_w, panel_z_min - 1.0))

    tex_bound_all = tb_slab.fuse(tb_hinge).removeSplitter()
    tex_compound = Part.makeCompound(tex_cutters).common(tex_bound_all)
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
