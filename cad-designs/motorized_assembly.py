"""
motorized_assembly.py — Active Motorized Module Sub-Assembly
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
from motorized_frame import construct_motorized_frame
from motorized_flap import construct_motorized_flap
from motorized_servo_cover import construct_motorized_servo_cover
from frame_joiner import construct_frame_joiner
from hex_drive_coupler import construct_hex_drive_coupler

def build_motorized_assembly():
    """
    Assembles the Active Motorized Module:
    1. Motorized Chassis Frame (Yellow #f1c40f).
    2. Monolithic Active Folding Flap (Red #d93829) with integrated 25T horn socket.
    3. Toolless Snap-Latch Servo Cover (Dark Slate #2c3e50).
    4. 2x Frame Joiners (Blue #3498db) attached to outer Front (Y=0) and Right (X=240) dovetails.
    5. Modular Double-Male Hex Drive Coupler Pin (Purple #9b59b6) at bottom hinge port (Y=0).
    6. Standard MG996R Servo motor reference model (Dark Grey #34495e) inside motor bay.
    """
    for doc_name in list(App.listDocuments().keys()):
        App.closeDocument(doc_name)
    doc = App.newDocument("MotorizedAssembly")
    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    bottom_thick = 3.0 * SCALE

    # 1. Base Motorized Chassis Frame (Color: Yellow #f1c40f)
    frame_shape = construct_motorized_frame()
    frame_obj = doc.addObject("Part::Feature", "MotorizedFrame")
    frame_obj.Shape = frame_shape
    if hasattr(frame_obj, "ViewObject") and frame_obj.ViewObject:
        frame_obj.ViewObject.ShapeColor = (0.95, 0.77, 0.05)

    # 2. Monolithic Active Flap (Color: Red #d93829)
    flap_shape = construct_motorized_flap()
    flap_obj = doc.addObject("Part::Feature", "MotorizedFlap")
    flap_obj.Shape = flap_shape
    flap_obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(flap_obj, "ViewObject") and flap_obj.ViewObject:
        flap_obj.ViewObject.ShapeColor = (0.85, 0.22, 0.16)

    # 3. Toolless Snap-Latch Servo Cover (Color: Dark Slate #2c3e50)
    cover_shape = construct_motorized_servo_cover()
    cover_obj = doc.addObject("Part::Feature", "MotorizedServoCover")
    cover_obj.Shape = cover_shape
    if hasattr(cover_obj, "ViewObject") and cover_obj.ViewObject:
        cover_obj.ViewObject.ShapeColor = (0.17, 0.24, 0.31)

    # 4. Front Interlocking Bridge Joiner (Color: Blue #3498db)
    joiner_shape = construct_frame_joiner()
    joiner_front = doc.addObject("Part::Feature", "FrameJoiner_Front")
    joiner_front.Shape = joiner_shape.copy()
    joiner_front.Placement = App.Placement(
        App.Vector(w / 2.0, - (MODULE_GAP / 2.0), bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(joiner_front, "ViewObject") and joiner_front.ViewObject:
        joiner_front.ViewObject.ShapeColor = (0.2, 0.6, 0.86)

    # 5. Right Interlocking Bridge Joiner (Color: Blue #3498db)
    joiner_right = doc.addObject("Part::Feature", "FrameJoiner_Right")
    joiner_right.Shape = joiner_shape.copy()
    joiner_right.Placement = App.Placement(
        App.Vector(w + (MODULE_GAP / 2.0), h / 2.0, bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 90)
    )
    if hasattr(joiner_right, "ViewObject") and joiner_right.ViewObject:
        joiner_right.ViewObject.ShapeColor = (0.2, 0.6, 0.86)

    # 6. Modular Double-Male Hex Drive Coupler Pin (Color: Purple #9b59b6)
    coupler_shape = construct_hex_drive_coupler()
    coupler_obj = doc.addObject("Part::Feature", "HexDriveCoupler")
    coupler_obj.Shape = coupler_shape
    coupler_obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(coupler_obj, "ViewObject") and coupler_obj.ViewObject:
        coupler_obj.ViewObject.ShapeColor = (0.6, 0.35, 0.71)

    # 7. Standard MG996R Servo CAD reference body (Color: Dark Metallic Grey #34495e)
    # Body: 40.5 x 20.0 x 36.0mm, Flange at Z=10.0mm, Spline output at X=0, Z=8.0mm, Y=188.5mm
    servo_body = Part.makeBox(20.0 * SCALE, 40.5 * SCALE, 36.0 * SCALE)
    servo_body.translate(App.Vector(-10.0 * SCALE, 189.0 * SCALE, 0.0))
    servo_flange = Part.makeBox(20.0 * SCALE, 54.0 * SCALE, 2.5 * SCALE)
    servo_flange.translate(App.Vector(-10.0 * SCALE, 182.25 * SCALE, 10.0 * SCALE))
    servo_spline = Part.makeCylinder(3.0 * SCALE, 6.0 * SCALE, App.Vector(0, 183.0 * SCALE, 8.0 * SCALE), App.Vector(0, -1, 0))
    servo_full = servo_body.fuse(Part.makeCompound([servo_flange, servo_spline])).removeSplitter()
    
    servo_obj = doc.addObject("Part::Feature", "MG996R_Servo")
    servo_obj.Shape = servo_full
    if hasattr(servo_obj, "ViewObject") and servo_obj.ViewObject:
        servo_obj.ViewObject.ShapeColor = (0.22, 0.28, 0.35)

    doc.recompute()
    return doc

def export_part():
    """Exports STEP and STL files to EXPORT_DIR."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    doc = build_motorized_assembly()

    step_path = os.path.join(EXPORT_DIR, "motorized_assembly.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_assembly.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shapes = [obj.Shape for obj in doc.Objects if hasattr(obj, "Shape")]
    compound = Part.makeCompound(shapes)
    compound.exportStep(step_path)
    compound.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()
