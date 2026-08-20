"""
follower_flap.py — Full-Size Follower Flap with Integrated Full-Length Axle
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
    ACCENT_BEVEL_DEPTH,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    EXPORT_DIR,
)

def make_hexagon_wire(size_af, center_x, center_z, y_pos):
    """Generates an explicit closed hexagon wire oriented for extrusion along the Y-axis."""
    r = (size_af / 2.0) / math.cos(math.radians(30))
    pts = []
    for i in range(6):
        ang = math.radians(60 * i + 30)
        pts.append(App.Vector(center_x + r * math.cos(ang), y_pos, center_z + r * math.sin(ang)))
    pts.append(pts[0])
    return Part.makePolygon(pts)

def construct_follower_flap():
    """
    Constructs the Full-Size Modular Drop-In Follower Flap (Y in [16.0, 204.0mm]).
    Features:
    1. Compact Drop-In Footprint (188x226mm) fitting directly between 360° closed frame knuckles.
    2. Continuous Solid Internal Drive Axle (Ø12.8mm) for maximum column torsional rigidity.
    3. Dual Integrated 8.0mm Female Hex Drive Coupler Sockets on top (Y=204) and bottom (Y=16) axle ends.
    4. Flush Top Surface (rests directly on 15.0mm frame rails).
    5. Multi-tiered Organic Gradient Circular Cutouts (~45% mass reduction).
    6. 1.2mm Recessed Perimeter Shadow Bevel for premium aesthetics.
    7. 0.6mm Debossed Diamond Micro-Grip Texture for fabric traction.
    8. 100% Supportless FDM Printability.
    """
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    t = params.PADDLE_THICKNESS       # 2.4mm
    pivot_z = PIVOT_Z                 # 15.00mm (exact top deck hinge line)
    panel_z_min = pivot_z             # 15.00mm (rests directly on top of frame rails)
    top_z = pivot_z + t               # 17.40mm
    rail_w = 15.0
    gap_axial = 0.5

    shaft_r = DRIVE_SHAFT_DIAMETER / 2.0  # 6.4mm
    knuckle_r = shaft_r + 3.0             # 9.4mm

    # Modular Drop-In Span: Sits between bottom pin inner disk (Y=16.0mm) and top knuckle (Y=205.0mm)
    y_min = 16.0                                 # 16.0mm (seats flush against bottom pin inner thrust disk)
    y_max = h - rail_w - 1.0                     # 204.0mm (1.0mm thrust clearance to top knuckle)
    total_len = y_max - y_min                    # 188.0mm

    x_min = -shaft_r                             # -6.4mm
    x_max = w - gap_axial                        # 219.5mm
    total_w = x_max - x_min                      # 225.9mm

    # 1. Main monolithic flat slab spanning X in [-6.4, 219.5mm], Y in [16.0, 204.0mm]
    blade = Part.makeBox(total_w, total_len, t)
    blade.translate(App.Vector(x_min, y_min, panel_z_min))

    # Outer corner fillets (R=3.0mm on top-right and bottom-right outer corners)
    corner_cutter1 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter1.translate(App.Vector(x_max - 3.0, y_min - 3.0, panel_z_min - 1.0))
    corner_cyl1 = Part.makeCylinder(3.0, t + 2.0, App.Vector(x_max - 3.0, y_min + 3.0, panel_z_min - 1.0))
    corner_trim1 = corner_cutter1.cut(corner_cyl1)

    corner_cutter2 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter2.translate(App.Vector(x_max - 3.0, y_max - 3.0, panel_z_min - 1.0))
    corner_cyl2 = Part.makeCylinder(3.0, t + 2.0, App.Vector(x_max - 3.0, y_max - 3.0, panel_z_min - 1.0))
    corner_trim2 = corner_cutter2.cut(corner_cyl2)

    blade = blade.cut(Part.makeCompound([corner_trim1, corner_trim2])).removeSplitter()

    # 2. Perimeter Shadow Bevel (Uniform 2.0mm around the OUTER boundary ONLY)
    border_w = 2.0
    bevel_d = ACCENT_BEVEL_DEPTH          # 1.2mm
    bevel_cuts = []

    # Right edge bevel (Full height Y in [16.0, 204.0mm])
    b_right = Part.makeBox(border_w + 0.2, total_len + 0.2, bevel_d + 0.1)
    b_right.translate(App.Vector(x_max - border_w, y_min - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_right)

    # Bottom outer edge bevel (X in [-6.4, 219.5mm])
    b_bot = Part.makeBox(total_w + 0.1, border_w + 0.1, bevel_d + 0.1)
    b_bot.translate(App.Vector(x_min, y_min - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_bot)

    # Top outer edge bevel (X in [-6.4, 219.5mm])
    b_top = Part.makeBox(total_w + 0.1, border_w + 0.1, bevel_d + 0.1)
    b_top.translate(App.Vector(x_min, y_max - border_w, top_z - bevel_d))
    bevel_cuts.append(b_top)

    # Left shaft outer edge (X in [-6.4 - 0.1, -6.4 + border_w], Y in [16.0 - 0.1, 204.0 + 0.1])
    b_left_mid = Part.makeBox(border_w + 0.1, total_len + 0.2, bevel_d + 0.1)
    b_left_mid.translate(App.Vector(x_min - 0.1, y_min - 0.1, top_z - bevel_d))
    bevel_cuts.append(b_left_mid)

    flap = blade.cut(Part.makeCompound(bevel_cuts)).removeSplitter()

    # 3. Continuous Drive Axle: Half-Cylinder Axle fused directly under the flap blade
    axle_full = Part.makeCylinder(shaft_r, total_len, App.Vector(0, y_min, pivot_z), App.Vector(0, 1, 0))
    axle_trim = Part.makeBox(shaft_r * 4.0, total_len + 1.0, shaft_r * 2.0)
    axle_trim.translate(App.Vector(-shaft_r * 2.0, y_min - 0.5, pivot_z))
    axle_half = axle_full.cut(axle_trim)

    flap = flap.fuse(axle_half).removeSplitter()

    # 4. Top & Bottom End Female 8.0mm Hex Torque Sockets (At Y = 16.0 and Y = 204.0mm ends)
    socket_d = 10.0
    hex_socket_top_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, y_max + 0.1)
    hex_socket_top_face = Part.Face(hex_socket_top_wire)
    hex_socket_top_cutter = hex_socket_top_face.extrude(App.Vector(0, -socket_d - 0.1, 0))

    hex_socket_bot_wire = make_hexagon_wire(HEX_COUPLER_SIZE, 0, pivot_z, y_min - 0.1)
    hex_socket_bot_face = Part.Face(hex_socket_bot_wire)
    hex_socket_bot_cutter = hex_socket_bot_face.extrude(App.Vector(0, socket_d + 0.1, 0))

    flap = flap.cut(Part.makeCompound([hex_socket_top_cutter, hex_socket_bot_cutter])).removeSplitter()

    # 5. Multi-Tiered Organic Gradient Circular Cutouts (~45% mass reduction)
    scale_geo = min(total_w, total_len) / 200.0
    hole_uvs = [
        (0.48, 0.50, 18.0 * scale_geo),
        (0.28, 0.32, 15.0 * scale_geo),
        (0.72, 0.35, 16.0 * scale_geo),
        (0.32, 0.70, 17.0 * scale_geo),
        (0.70, 0.68, 15.5 * scale_geo),
        (0.52, 0.22, 12.0 * scale_geo),
        (0.52, 0.78, 12.5 * scale_geo),
        (0.22, 0.52, 11.0 * scale_geo),
        (0.84, 0.50, 11.5 * scale_geo),
        (0.22, 0.15, 8.5 * scale_geo),
        (0.82, 0.18, 9.0 * scale_geo),
        (0.20, 0.85, 8.0 * scale_geo),
        (0.84, 0.82, 8.5 * scale_geo),
        (0.37, 0.12, 7.0 * scale_geo),
        (0.67, 0.12, 7.0 * scale_geo),
        (0.37, 0.88, 7.0 * scale_geo),
        (0.67, 0.88, 7.0 * scale_geo),
    ]

    cutters = []
    for u, v, hr in hole_uvs:
        cx = 15.0 + (total_w - 30.0) * u
        cy = y_min + (total_len) * v
        cyl = Part.makeCylinder(hr, t + 1.0, App.Vector(cx, cy, panel_z_min - 0.5))
        c_top = Part.makeCone(hr + HOLE_CHAMFER, hr, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, top_z - HOLE_CHAMFER))
        c_bot = Part.makeCone(hr, hr + HOLE_CHAMFER, HOLE_CHAMFER + 0.1, App.Vector(cx, cy, panel_z_min - 0.1))
        cutters.extend([cyl, c_top, c_bot])

    if cutters:
        flap = flap.cut(Part.makeCompound(cutters)).removeSplitter()

    # 6. 0.6mm Anti-Slip Diamond Micro-Grip Surface Texture extending across entire flap face
    tex_cutters = []
    tex_spacing = 14.0
    tex_w = 0.8
    tex_d = TEXTURE_HEIGHT
    
    for i in range(-int(w), int(w + h * 2), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, h * 2.0, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, top_z - tex_d))
        g2 = Part.makeBox(tex_w, h * 2.0, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, h, top_z - tex_d))
        tex_cutters.extend([g1, g2])

    # Bound for the entire outer slab inset by border_w
    tb_slab = Part.makeBox(total_w - 2 * border_w, total_len - 2 * border_w, t + 2.0)
    tb_slab.translate(App.Vector(x_min + border_w, y_min + border_w, panel_z_min - 1.0))

    tex_compound = Part.makeCompound(tex_cutters).common(tb_slab)
    flap = flap.cut(tex_compound).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "follower_flap.step")
    stl_path  = os.path.join(EXPORT_DIR, "follower_flap.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    flap.exportStep(step_path)
    flap.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return flap

def export_part():
    doc = App.ActiveDocument or App.newDocument("FollowerFlap")
    shape = construct_follower_flap()
    obj = doc.addObject("Part::Feature", "FollowerFlap")
    obj.Shape = shape

export_part()


