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
    BASE_PANEL_THICKNESS,
    WALL_THICKNESS,
)

# Local Dovetail & Flap Constants
DOVETAIL_MALE_WIDTH = 20.0 * SCALE
DOVETAIL_HEIGHT = 10.0 * SCALE
DOVETAIL_DEPTH = 6.0 * SCALE
DOVETAIL_MALE_NECK = 14.0 * SCALE
DOVETAIL_TOLERANCE = 0.2 * SCALE
PADDLE_PIVOT_DIAMETER = 5.0 * SCALE
BOTTOM_SHELL_THICKNESS = 3.0 * SCALE


def create_follower_frame():
    w = PANEL_WIDTH
    h = PANEL_HEIGHT
    t = BASE_PANEL_THICKNESS
    wall = 15.0 * SCALE
    bottom_thick = BOTTOM_SHELL_THICKNESS

    # 1. Main outer shell box
    outer_box = Part.makeBox(w, h, t)

    # 2. Main internal cavity cut
    cav_w = w - 2 * wall
    cav_h = h - 2 * wall
    cavity = Part.makeBox(cav_w, cav_h, t - bottom_thick + 0.1)
    cavity.translate(App.Vector(wall, wall, bottom_thick))
    frame = outer_box.cut(cavity)

    # 3. 4-Wall Symmetrical Click-Lock Dovetail Sockets
    dt_w = DOVETAIL_MALE_WIDTH + 2 * DOVETAIL_TOLERANCE
    dt_h = DOVETAIL_HEIGHT + 2 * DOVETAIL_TOLERANCE
    dt_d = DOVETAIL_DEPTH + DOVETAIL_TOLERANCE
    dt_neck = DOVETAIL_MALE_NECK + 2 * DOVETAIL_TOLERANCE

    dt_pts = [
        App.Vector(-dt_w / 2.0, 0, 0),
        App.Vector(dt_w / 2.0, 0, 0),
        App.Vector(dt_neck / 2.0, dt_d, 0),
        App.Vector(-dt_neck / 2.0, dt_d, 0),
        App.Vector(-dt_w / 2.0, 0, 0),
    ]
    dt_poly = Part.makePolygon(dt_pts)
    dt_face = Part.Face(dt_poly)
    dt_cutter_master = dt_face.extrude(App.Vector(0, 0, dt_h))

    dt_cutters = []

    # Front Wall (Y=0)
    c_front = dt_cutter_master.copy()
    c_front.translate(App.Vector(w / 2.0, -0.1, (t - dt_h) / 2.0))
    dt_cutters.append(c_front)

    # Back Wall (Y=H)
    c_back = dt_cutter_master.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h + 0.1, (t - dt_h) / 2.0))
    dt_cutters.append(c_back)

    # Left Wall (X=0)
    c_left = dt_cutter_master.copy()
    c_left.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -90)
    c_left.translate(App.Vector(-0.1, h / 2.0, (t - dt_h) / 2.0))
    dt_cutters.append(c_left)

    # Right Wall (X=W)
    c_right = dt_cutter_master.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w + 0.1, h / 2.0, (t - dt_h) / 2.0))
    dt_cutters.append(c_right)

    if dt_cutters:
        dt_compound = Part.makeCompound(dt_cutters)
        frame = frame.cut(dt_compound)

    # 4. 360° Closed Bearing Bores & Flex C-Snap Sockets for Flap Pivots
    pin_r = (PADDLE_PIVOT_DIAMETER / 2.0) + 0.25 * SCALE
    bore_cutters = []

    pivot_z = bottom_thick + 5.0 * SCALE
    pivot_positions = [
        App.Vector(wall - 0.1, h / 2.0 - 40.0 * SCALE, pivot_z),
        App.Vector(wall - 0.1, h / 2.0 + 40.0 * SCALE, pivot_z),
        App.Vector(w - wall + 0.1, h / 2.0 - 40.0 * SCALE, pivot_z),
        App.Vector(w - wall + 0.1, h / 2.0 + 40.0 * SCALE, pivot_z),
    ]

    for pos in pivot_positions:
        bore = Part.makeCylinder(pin_r, 8.0 * SCALE, pos, App.Vector(1 if pos.x < w / 2 else -1, 0, 0))
        snap_slot = Part.makeBox(2.0 * pin_r * 0.85, 8.0 * SCALE, pos.z + 0.1)
        snap_slot.translate(App.Vector(pos.x - (pin_r * 0.85), pos.y - 4.0 * SCALE, 0))
        bore_cutters.extend([bore, snap_slot])

    if bore_cutters:
        bore_compound = Part.makeCompound(bore_cutters)
        frame = frame.cut(bore_compound)

    # 5. Under-Frame Cable Management Clips
    clip_w = 4.0 * SCALE
    clip_d = 3.0 * SCALE
    clip_1 = Part.makeBox(clip_w, h - 2 * wall, clip_d)
    clip_1.translate(App.Vector(wall / 2.0 - clip_w / 2.0, wall, 0))
    clip_2 = Part.makeBox(clip_w, h - 2 * wall, clip_d)
    clip_2.translate(App.Vector(w - wall / 2.0 - clip_w / 2.0, wall, 0))
    frame = frame.cut(Part.makeCompound([clip_1, clip_2]))

    # 6. Apply 0.8mm Snag-Free Chamfers to outer top rim edges
    try:
        top_edges = [
            edge for edge in frame.Edges
            if abs(edge.BoundBox.ZMin - t) < 0.1 and abs(edge.BoundBox.ZMax - t) < 0.1
        ]
        if top_edges:
            frame = frame.makeChamfer(0.8 * SCALE, top_edges)
    except Exception as e:
        print(f"Notice: Top rim chamfer skipped: {e}")

    return frame


if __name__ == "__main__":
    doc = App.newDocument("FollowerFrame")
    obj = doc.addObject("Part::Feature", "Part02FollowerFrame")
    shape = create_follower_frame()
    obj.Shape = shape

    export_dir = os.path.join(os.path.dirname(__file__), "exports")
    os.makedirs(export_dir, exist_ok=True)
    step_path = os.path.join(export_dir, "part_02_follower_frame.step")
    stl_path = os.path.join(export_dir, "part_02_follower_frame.stl")

    shape.exportStep(step_path)
    shape.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")
