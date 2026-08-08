import math
import os
import sys
import FreeCAD as App
import Part

# Ensure script dir is in path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from params import (
    SCALE,
    PANEL_WIDTH,
    PANEL_HEIGHT,
)

# Local Flap Constants
PADDLE_THICKNESS = 6.0 * SCALE
PADDLE_PIVOT_DIAMETER = 5.0 * SCALE


def create_follower_flap():
    w = 188.0 * SCALE
    h = 88.0 * SCALE
    t = PADDLE_THICKNESS

    # 1. Base solid flap slab
    flap_box = Part.makeBox(w, h, t)

    # 2. Dual-Tone Perimeter Shadow Bevel (1.2mm depth along top perimeter)
    bevel_d = 1.2 * SCALE
    bevel_w = 2.5 * SCALE
    bevel_cutter = Part.makeBox(w + 0.2, h + 0.2, bevel_d)
    bevel_cutter.translate(App.Vector(-0.1, -0.1, t - bevel_d))
    bevel_inner = Part.makeBox(w - 2 * bevel_w, h - 2 * bevel_w, bevel_d + 0.2)
    bevel_inner.translate(App.Vector(bevel_w, bevel_w, t - bevel_d - 0.1))
    bevel_rim = bevel_cutter.cut(bevel_inner)
    flap = flap_box.cut(bevel_rim)

    # 3. Dual Male Pivot Pins with 45° Lead-in Chamfers
    pin_r = PADDLE_PIVOT_DIAMETER / 2.0
    pin_len = 6.0 * SCALE

    pin_left = Part.makeCylinder(pin_r, pin_len, App.Vector(-pin_len, h / 2.0, t / 2.0), App.Vector(1, 0, 0))
    pin_right = Part.makeCylinder(pin_r, pin_len, App.Vector(w, h / 2.0, t / 2.0), App.Vector(1, 0, 0))

    try:
        chamfer_edges = []
        for edge in pin_left.Edges:
            if abs(edge.BoundBox.XMin + pin_len) < 0.1:
                chamfer_edges.append(edge)
        for edge in pin_right.Edges:
            if abs(edge.BoundBox.XMax - (w + pin_len)) < 0.1:
                chamfer_edges.append(edge)
        if chamfer_edges:
            pin_left = pin_left.makeChamfer(0.8 * SCALE, [e for e in pin_left.Edges if abs(e.BoundBox.XMin + pin_len) < 0.1])
            pin_right = pin_right.makeChamfer(0.8 * SCALE, [e for e in pin_right.Edges if abs(e.BoundBox.XMax - (w + pin_len)) < 0.1])
    except Exception as e:
        print(f"Notice: Pin tip chamfer skipped: {e}")

    flap = flap.fuse(Part.makeCompound([pin_left, pin_right]))

    # 4. ~45% Gradient Mass Reduction Cutouts with 0.8mm Edge Chamfers
    cutters = []
    num_cols = 4
    num_rows = 2
    margin_x = 20.0 * SCALE
    margin_y = 15.0 * SCALE
    pitch_x = (w - 2 * margin_x) / num_cols
    pitch_y = (h - 2 * margin_y) / num_rows

    for c in range(num_cols):
        for r in range(num_rows):
            cx = margin_x + (c + 0.5) * pitch_x
            cy = margin_y + (r + 0.5) * pitch_y
            cut_r = (pitch_y * 0.38)
            hex_poly = Part.makePolygon([
                App.Vector(cx + cut_r * math.cos(a), cy + cut_r * math.sin(a), -0.1)
                for a in [i * math.pi / 3 for i in range(7)]
            ])
            hex_face = Part.Face(hex_poly)
            hex_prism = hex_face.extrude(App.Vector(0, 0, t + 0.2))
            cutters.append(hex_prism)

    if cutters:
        flap = flap.cut(Part.makeCompound(cutters))

    try:
        top_cutout_edges = [
            edge for edge in flap.Edges
            if abs(edge.BoundBox.ZMax - t) < 0.2 and 10.0 * SCALE < edge.BoundBox.XMin < w - 10.0 * SCALE
        ]
        if top_cutout_edges:
            flap = flap.makeChamfer(0.6 * SCALE, top_cutout_edges[:12])
    except Exception as e:
        print(f"Notice: Flap cutout chamfer skipped: {e}")

    # 5. 0.6mm Anti-Slip Diamond Surface Texture
    tex_cutters = []
    tex_spacing = 8.0 * SCALE
    tex_d = 0.6 * SCALE
    for x_pos in range(int(margin_x), int(w - margin_x), int(tex_spacing)):
        groove = Part.makeBox(1.2 * SCALE, h - 2 * margin_y, tex_d + 0.1)
        groove.translate(App.Vector(x_pos, margin_y, t - tex_d))
        tex_cutters.append(groove)

    if tex_cutters:
        flap = flap.cut(Part.makeCompound(tex_cutters))

    return flap


if __name__ == "__main__":
    doc = App.newDocument("FollowerFlap")
    obj = doc.addObject("Part::Feature", "Part03FollowerFlap")
    shape = create_follower_flap()
    obj.Shape = shape

    export_dir = os.path.join(os.path.dirname(__file__), "exports")
    os.makedirs(export_dir, exist_ok=True)
    step_path = os.path.join(export_dir, "part_03_follower_flap.step")
    stl_path = os.path.join(export_dir, "part_03_follower_flap.stl")

    shape.exportStep(step_path)
    shape.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")
