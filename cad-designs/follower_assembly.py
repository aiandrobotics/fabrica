"""
follower_assembly.py — Passive Follower Module Sub-Assembly
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
    MODULE_GAP,
    EXPORT_DIR,
)
from follower_frame import construct_follower_frame
from follower_flap import construct_follower_flap
from frame_joiner import construct_frame_joiner
from hex_drive_coupler import construct_hex_drive_coupler

def build_follower_assembly():
    """
    Assembles the Passive Follower Module:
    1. Follower Chassis Frame (Green #2ecc71).
    2. Full-Size Rotating Follower Flap (Orange #e67e22) seated along hinge axis (X=0).
    3. 2x Frame Joiners (Blue #3498db) attached to outer Front (Y=0) and Right (X=240) dovetails.
    4. Modular Double-Male Hex Drive Coupler Pin (Purple #9b59b6) at bottom hinge port (Y=0).
    """
    for doc_name in list(App.listDocuments().keys()):
        App.closeDocument(doc_name)
    doc = App.newDocument("FollowerAssembly")
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    bottom_thick = 3.0

    # 1. Base Follower Chassis Frame (Color: Green #2ecc71)
    frame_shape = construct_follower_frame()
    frame_obj = doc.addObject("Part::Feature", "FollowerFrame")
    frame_obj.Shape = frame_shape
    if hasattr(frame_obj, "ViewObject") and frame_obj.ViewObject:
        frame_obj.ViewObject.ShapeColor = (0.18, 0.8, 0.44)

    # 2. Full-Size Follower Flap with Dual Female Hex Sockets (Color: Orange #e67e22)
    # Flap axle is centered along hinge axis at X = 0, Z = 8.0mm
    flap_shape = construct_follower_flap()
    flap_obj = doc.addObject("Part::Feature", "FollowerFlap")
    flap_obj.Shape = flap_shape
    flap_obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(flap_obj, "ViewObject") and flap_obj.ViewObject:
        flap_obj.ViewObject.ShapeColor = (0.9, 0.49, 0.13)

    # 3. Front Interlocking Bridge Joiner (Color: Blue #3498db)
    joiner_shape = construct_frame_joiner()
    joiner_front_shape = joiner_shape.copy()
    joiner_front_shape.translate(App.Vector(w / 2.0, - (MODULE_GAP / 2.0), bottom_thick))
    joiner_front = doc.addObject("Part::Feature", "FrameJoiner_Front")
    joiner_front.Shape = joiner_front_shape
    if hasattr(joiner_front, "ViewObject") and joiner_front.ViewObject:
        joiner_front.ViewObject.ShapeColor = (0.2, 0.6, 0.86)

    # 4. Right Interlocking Bridge Joiner (Color: Blue #3498db)
    joiner_right_shape = joiner_shape.copy()
    joiner_right_shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    joiner_right_shape.translate(App.Vector(w + (MODULE_GAP / 2.0), h / 2.0, bottom_thick))
    joiner_right = doc.addObject("Part::Feature", "FrameJoiner_Right")
    joiner_right.Shape = joiner_right_shape
    if hasattr(joiner_right, "ViewObject") and joiner_right.ViewObject:
        joiner_right.ViewObject.ShapeColor = (0.2, 0.6, 0.86)

    # 5. Modular Double-Male Hex Drive Coupler Pin (Color: Purple #9b59b6)
    coupler_shape = construct_hex_drive_coupler()
    coupler_obj = doc.addObject("Part::Feature", "HexDriveCoupler")
    coupler_obj.Shape = coupler_shape
    if hasattr(coupler_obj, "ViewObject") and coupler_obj.ViewObject:
        coupler_obj.ViewObject.ShapeColor = (0.6, 0.35, 0.71)

    doc.recompute()
    return doc

def export_part():
    """Exports STEP and STL files to EXPORT_DIR."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    doc = build_follower_assembly()

    step_path = os.path.join(EXPORT_DIR, "follower_assembly.step")
    stl_path  = os.path.join(EXPORT_DIR, "follower_assembly.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shapes = []
    for obj in doc.Objects:
        if hasattr(obj, "Shape"):
            s = obj.Shape.copy()
            if hasattr(obj, "Placement"):
                s.transformGeometry(obj.Placement.toMatrix())
            shapes.append(s)

    compound = Part.makeCompound(shapes)
    compound.exportStep(step_path)
    compound.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()



