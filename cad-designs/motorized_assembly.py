"""
motorized_assembly.py — Multi-Body Motorized Sub-Assembly with Horizontal Direct-Drive Servo
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
    MODULE_GAP,
    DOVETAIL_DEPTH,
    EXPORT_DIR,
)

from motorized_frame import construct_motorized_frame
from motorized_flap import construct_motorized_flap
from motorized_servo_cover import construct_motorized_servo_cover
from frame_joiner import construct_frame_joiner
from hex_drive_coupler import construct_hex_drive_coupler

def construct_servo_cad_reference():
    """
    Constructs a CAD reference solid of the standard MG996R metal-gear servo in horizontal orientation.
    Lies on its side along Y in the rear corner bay with spline centered at (X=0, Z=8.0mm),
    top face resting flush at Z = 14.8mm under the slide-in cover.
    """
    pivot_z = 8.0 * SCALE
    body_l = 40.5 * SCALE # along Y (192.5 to 233.0mm)
    body_w = 36.0 * SCALE # along X (4.5 to 40.5mm)
    body_h = 16.8 * SCALE # along Z (-2.0 to 14.8mm)

    # 1. Main Servo Body Block
    main_body = Part.makeBox(body_w, body_l, body_h)
    main_body.translate(App.Vector(4.5 * SCALE, 192.5 * SCALE, -2.0 * SCALE))

    # 2. Output Spline Collar (centered at X=0, Z=8.0mm, protruding into flap horn socket at Y=178..185mm)
    spline_gear = Part.makeCylinder(3.0 * SCALE, 7.0 * SCALE, App.Vector(0, 178.0 * SCALE, pivot_z), App.Vector(0, 1, 0))
    spline_collar = Part.makeCylinder(6.0 * SCALE, 7.5 * SCALE, App.Vector(0, 185.0 * SCALE, pivot_z), App.Vector(0, 1, 0))

    # 3. Flange Mounting Ears (spanning Y = 189.5 to 236.5mm at X = 29.5mm)
    flange_t = 2.5 * SCALE
    flange = Part.makeBox(flange_t, 47.0 * SCALE, body_h)
    flange.translate(App.Vector(29.0 * SCALE, 189.5 * SCALE, -2.0 * SCALE))

    servo_solid = main_body.fuse(Part.makeCompound([spline_gear, spline_collar, flange])).removeSplitter()
    return servo_solid

def build_motorized_assembly():
    """
    Assembles the Active Motorized Module:
    1. Motorized Frame (Gold/Amber)
    2. Full-Size Active Flap (Crimson Red)
    3. Flush Slide-In Servo Cover (Slate Black)
    4. 2x Frame Joiners (Blue)
    5. Modular Hex Drive Coupler Pin (Purple)
    6. MG996R Horizontal Servo Motor Solid (Cyan)
    """
    for doc_name in list(App.listDocuments().keys()):
        App.closeDocument(doc_name)
    doc = App.newDocument("MotorizedAssembly")

    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    t = BASE_PANEL_THICKNESS # 15.0mm
    bottom_thick = 3.0 * SCALE

    # 1. Base Motorized Chassis Frame
    frame_shape = construct_motorized_frame()
    frame_obj = doc.addObject("Part::Feature", "MotorizedFrame")
    frame_obj.Shape = frame_shape
    if hasattr(frame_obj, "ViewObject") and frame_obj.ViewObject:
        frame_obj.ViewObject.ShapeColor = (0.95, 0.78, 0.20)

    # 2. Active Folding Flap
    flap_shape = construct_motorized_flap()
    flap_obj = doc.addObject("Part::Feature", "MotorizedFlap")
    flap_obj.Shape = flap_shape
    if hasattr(flap_obj, "ViewObject") and flap_obj.ViewObject:
        flap_obj.ViewObject.ShapeColor = (0.85, 0.20, 0.20)

    # 3. Flush Low-Profile Servo Cover
    cover_shape = construct_motorized_servo_cover()
    cover_obj = doc.addObject("Part::Feature", "MotorizedServoCover")
    cover_obj.Shape = cover_shape
    if hasattr(cover_obj, "ViewObject") and cover_obj.ViewObject:
        cover_obj.ViewObject.ShapeColor = (0.20, 0.22, 0.25)

    # 4. Front Interlocking Bridge Joiner (Blue)
    joiner_shape = construct_frame_joiner()
    joiner_front = doc.addObject("Part::Feature", "FrameJoiner_Front")
    joiner_front.Shape = joiner_shape.copy()
    joiner_front.Placement = App.Placement(
        App.Vector(w / 2.0, - (MODULE_GAP / 2.0), bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(joiner_front, "ViewObject") and joiner_front.ViewObject:
        joiner_front.ViewObject.ShapeColor = (0.20, 0.40, 0.85)

    # 5. Right Interlocking Bridge Joiner (Blue)
    joiner_right = doc.addObject("Part::Feature", "FrameJoiner_Right")
    joiner_right.Shape = joiner_shape.copy()
    joiner_right.Placement = App.Placement(
        App.Vector(w + (MODULE_GAP / 2.0), h / 2.0, bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 90)
    )
    if hasattr(joiner_right, "ViewObject") and joiner_right.ViewObject:
        joiner_right.ViewObject.ShapeColor = (0.20, 0.40, 0.85)

    # 6. Modular Double-Male Hex Drive Coupler Pin (Purple)
    coupler_shape = construct_hex_drive_coupler()
    coupler_obj = doc.addObject("Part::Feature", "HexDriveCoupler")
    coupler_obj.Shape = coupler_shape
    coupler_obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(coupler_obj, "ViewObject") and coupler_obj.ViewObject:
        coupler_obj.ViewObject.ShapeColor = (0.60, 0.20, 0.80)

    # 7. ServoMotor Reference Solid (Cyan)
    servo_shape = construct_servo_cad_reference()
    servo_obj = doc.addObject("Part::Feature", "ServoMotor")
    servo_obj.Shape = servo_shape
    if hasattr(servo_obj, "ViewObject") and servo_obj.ViewObject:
        servo_obj.ViewObject.ShapeColor = (0.15, 0.65, 0.75)

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

def main():
    build_motorized_assembly()

main()
