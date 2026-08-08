"""
part_10_frame_joiner.py — Click-Lock Hollow Dovetail Frame Joiner
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAD_DIR = os.path.dirname(SCRIPT_DIR)
if CAD_DIR not in sys.path:
    sys.path.insert(0, CAD_DIR)

import FreeCAD as App
import Part

from params import (
    SCALE,
    BASE_PANEL_THICKNESS,
    PRESS_FIT_CLEARANCE,
    JOINER_DETENT,
    EXPORT_DIR,
)

def construct_frame_joiner():
    """
    Constructs the Click-Lock Hollow Dovetail Frame Joiner shape.
    Double-sided dovetail key with flex detent bump and internal wire conduit tunnel.
    """
    clearance = PRESS_FIT_CLEARANCE
    dt_top_w = (16.0 * SCALE) - clearance
    dt_bot_w = (10.0 * SCALE) - clearance
    dt_depth = (8.0 * SCALE) - clearance
    dt_height = BASE_PANEL_THICKNESS - (2.0 * SCALE)

    # 1. Single Male Dovetail Key Profile (Trapezoid)
    poly_pts = [
        App.Vector(-dt_top_w / 2.0, 0, 0),
        App.Vector(dt_top_w / 2.0, 0, 0),
        App.Vector(dt_bot_w / 2.0, dt_depth, 0),
        App.Vector(-dt_bot_w / 2.0, dt_depth, 0),
        App.Vector(-dt_top_w / 2.0, 0, 0),
    ]
    wire_half = Part.makePolygon(poly_pts)
    face_half = Part.Face(wire_half)
    solid_half = face_half.extrude(App.Vector(0, 0, dt_height))

    # 2. Mirror and fuse to create double-sided dovetail joiner
    solid_half_2 = solid_half.copy()
    solid_half_2.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), 180))

    joiner_solid = solid_half.fuse(solid_half_2)

    # 3. Add 0.3mm Flex Detent Bumps on outer faces for click-lock retention
    detent_radius = JOINER_DETENT
    detent_1 = Part.makeCylinder(detent_radius, dt_top_w, App.Vector(-dt_top_w / 2.0, 0, dt_height / 2.0), App.Vector(1, 0, 0))

    joiner_solid = joiner_solid.fuse(detent_1)

    # 4. Model Hollow Internal Wire Conduit Tunnel (Center Hole for Servo/Power Wires)
    conduit_w = 6.0 * SCALE
    conduit_h = (dt_depth * 2.0) - (2.0 * SCALE)
    conduit = Part.makeBox(conduit_w, conduit_h, dt_height + 1.0, App.Vector(-conduit_w / 2.0, -conduit_h / 2.0, -0.5))

    joiner_solid = joiner_solid.cut(conduit)

    # 5. Apply 0.4mm Lead-In Chamfers to entry edges for smooth insertion
    try:
        vertical_edges = []
        for edge in joiner_solid.Edges:
            bb = edge.BoundBox
            if abs(bb.ZMax - bb.ZMin - dt_height) < 0.001:
                vertical_edges.append(edge)
        if vertical_edges:
            joiner_solid = joiner_solid.makeChamfer(0.4 * SCALE, vertical_edges)
    except Exception as e:
        print(f"Warning: Lead-in chamfer skipped on joiner: {e}")

    return joiner_solid

def export_part():
    """Exports STEP and STL files to EXPORT_DIR and adds shape to FreeCAD document."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    shape = construct_frame_joiner()

    doc = App.ActiveDocument or App.newDocument("Doc")
    obj = doc.addObject("Part::Feature", "Part10FrameJoiner")
    obj.Shape = shape
    doc.recompute()

    step_path = os.path.join(EXPORT_DIR, "part_10_frame_joiner.step")
    stl_path  = os.path.join(EXPORT_DIR, "part_10_frame_joiner.stl")

    shape.exportStep(step_path)
    shape.exportStl(stl_path)

    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()
