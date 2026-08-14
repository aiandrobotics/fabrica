"""
assembly_follower_module.py — Passive Follower Module Sub-Assembly
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import os
import sys
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
    EXPORT_DIR,
)
from part_02_follower_frame import create_follower_frame
from part_03_follower_flap import create_follower_flap, PADDLE_THICKNESS
from part_10_frame_joiner import construct_frame_joiner

def build_follower_assembly():
    """
    Assembles the Passive Follower Module:
    1. Follower 3-Sided U-Frame (Green #2ecc71).
    2. Full-Size Rotating Follower Flap (Orange #e67e22) seated along hinge axis (X=0).
    3. 2x Frame Joiners (Blue #3498db) attached to outer Front (Y=0) and Right (X=240) dovetails.
    """
    for doc_name in list(App.listDocuments().keys()):
        App.closeDocument(doc_name)
    doc = App.newDocument("FollowerAssembly")
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    rail_w = 15.0 * SCALE
    bottom_thick = 3.0 * SCALE

    # 1. Base Follower Chassis Frame (Color: Green #2ecc71)
    frame_shape = create_follower_frame()
    frame_obj = doc.addObject("Part::Feature", "Part02FollowerFrame")
    frame_obj.Shape = frame_shape
    if hasattr(frame_obj, "ViewObject") and frame_obj.ViewObject:
        frame_obj.ViewObject.ShapeColor = (0.18, 0.8, 0.44)

    # 2. Full-Size Follower Flap with Ø14mm Drive Axle (Color: Orange #e67e22)
    # Flap axle is centered along hinge axis at X = 0, Z = t/2 = 7.5mm
    flap_shape = create_follower_flap()
    flap_obj = doc.addObject("Part::Feature", "Part03FollowerFlap")
    flap_obj.Shape = flap_shape
    flap_obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(flap_obj, "ViewObject") and flap_obj.ViewObject:
        flap_obj.ViewObject.ShapeColor = (0.9, 0.49, 0.13)

    # 3. Front Interlocking Bridge Joiner (Color: Blue #3498db)
    joiner_shape = construct_frame_joiner()
    joiner_front = doc.addObject("Part::Feature", "Part10FrameJoiner_Front")
    joiner_front.Shape = joiner_shape.copy()
    joiner_front.Placement = App.Placement(
        App.Vector(w / 2.0, - (MODULE_GAP / 2.0), bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(joiner_front, "ViewObject") and joiner_front.ViewObject:
        joiner_front.ViewObject.ShapeColor = (0.2, 0.6, 0.86)

    # 4. Right Interlocking Bridge Joiner (Color: Blue #3498db)
    joiner_right = doc.addObject("Part::Feature", "Part10FrameJoiner_Right")
    joiner_right.Shape = joiner_shape.copy()
    joiner_right.Placement = App.Placement(
        App.Vector(w + (MODULE_GAP / 2.0), h / 2.0, bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 90)
    )
    if hasattr(joiner_right, "ViewObject") and joiner_right.ViewObject:
        joiner_right.ViewObject.ShapeColor = (0.2, 0.6, 0.86)

    doc.recompute()
    return doc

def export_part():
    """Exports STEP and STL files to EXPORT_DIR."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    doc = build_follower_assembly()

    step_path = os.path.join(EXPORT_DIR, "assembly_follower_module.step")
    stl_path  = os.path.join(EXPORT_DIR, "assembly_follower_module.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shapes = [obj.Shape for obj in doc.Objects if hasattr(obj, "Shape")]
    compound = Part.makeCompound(shapes)
    compound.exportStep(step_path)
    compound.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()



