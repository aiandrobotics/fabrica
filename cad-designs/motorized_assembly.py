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
    PIVOT_Z,
    EXPORT_DIR,
)

from motorized_frame import construct_motorized_frame
from motorized_flap import construct_motorized_flap
from servo_drive_adapter import construct_servo_drive_adapter
from motorized_servo_cover import construct_motorized_servo_cover
from frame_joiner import construct_frame_joiner
from hex_drive_coupler import construct_hex_drive_coupler

def construct_servo_cad_reference():
    """
    Loads and positions the real MG996R STEP solid reference model in horizontal orientation.
    Spline output aligns directly with flap hinge axis at (X=0, Z=PIVOT_Z), protruding into adapter at Y=185.0mm.
    """
    step_paths = [
        os.path.join(SCRIPT_DIR, "..", "specs", "reference-images", "mg996r.step"),
        os.path.join(SCRIPT_DIR, "exports", "reference-models", "mg996r.step"),
    ]
    step_file = None
    for sp in step_paths:
        if os.path.exists(sp):
            step_file = sp
            break

    raw_servo = Part.Shape()
    if step_file:
        raw_servo.read(step_file)
        p1 = App.Placement(App.Vector(-30.25 * SCALE, -9.75 * SCALE, -14.19 * SCALE), App.Rotation(0,0,0,1))
        r1 = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(1,0,0), 90))
        r2 = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(0,1,0), 180))
        p2 = App.Placement(App.Vector(0.0, 185.0 * SCALE, PIVOT_Z), App.Rotation(0,0,0,1))

        full_placement = p2.multiply(r2).multiply(r1).multiply(p1)
        servo_solid = raw_servo.copy()
        servo_solid.Placement = full_placement
        return servo_solid
    else:
        # Fallback to parametric box if file missing
        body = Part.makeBox(36.0 * SCALE, 40.5 * SCALE, 16.8 * SCALE)
        body.translate(App.Vector(4.5 * SCALE, 192.5 * SCALE, -2.0 * SCALE))
        return body

def build_motorized_assembly():
    """
    Assembles the Active Motorized Module:
    1. Motorized Frame (Gold/Amber)
    2. Full-Size Active Flap (Crimson Red)
    3. Flush Slide-In Servo Cover (Slate Black)
    4. 2x Frame Joiners (Blue)
    5. Modular Hex Drive Coupler Pin (Purple)
    6. Modular Servo Drive Adapter (Orange)
    7. MG996R Horizontal Servo Motor Solid (Cyan)
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

    # 2. Active Folding Flap (Red)
    flap_shape = construct_motorized_flap()
    flap_obj = doc.addObject("Part::Feature", "MotorizedFlap")
    flap_obj.Shape = flap_shape
    if hasattr(flap_obj, "ViewObject") and flap_obj.ViewObject:
        flap_obj.ViewObject.ShapeColor = (0.85, 0.20, 0.20)

    # 3. Modular Circular Servo Horn Drive Adapter (Orange)
    adapter_shape = construct_servo_drive_adapter()
    adapter_obj = doc.addObject("Part::Feature", "ServoDriveAdapter")
    adapter_obj.Shape = adapter_shape
    if hasattr(adapter_obj, "ViewObject") and adapter_obj.ViewObject:
        adapter_obj.ViewObject.ShapeColor = (0.90, 0.50, 0.15)

    # 4. Flush Low-Profile Servo Cover (Purple/Slate)
    cover_shape = construct_motorized_servo_cover()
    cover_obj = doc.addObject("Part::Feature", "MotorizedServoCover")
    cover_obj.Shape = cover_shape
    if hasattr(cover_obj, "ViewObject") and cover_obj.ViewObject:
        cover_obj.ViewObject.ShapeColor = (0.50, 0.25, 0.60)

    # 5. Front Interlocking Bridge Joiner (Blue)
    joiner_shape = construct_frame_joiner()
    joiner_front = doc.addObject("Part::Feature", "FrameJoiner_Front")
    joiner_front.Shape = joiner_shape.copy()
    joiner_front.Placement = App.Placement(
        App.Vector(w / 2.0, - (MODULE_GAP / 2.0), bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(joiner_front, "ViewObject") and joiner_front.ViewObject:
        joiner_front.ViewObject.ShapeColor = (0.20, 0.40, 0.85)

    # 6. Right Interlocking Bridge Joiner (Blue)
    joiner_right = doc.addObject("Part::Feature", "FrameJoiner_Right")
    joiner_right.Shape = joiner_shape.copy()
    joiner_right.Placement = App.Placement(
        App.Vector(w + (MODULE_GAP / 2.0), h / 2.0, bottom_thick),
        App.Rotation(App.Vector(0, 0, 1), 90)
    )
    if hasattr(joiner_right, "ViewObject") and joiner_right.ViewObject:
        joiner_right.ViewObject.ShapeColor = (0.20, 0.40, 0.85)

    # 7. Modular Double-Male Hex Drive Coupler Pin (Yellow)
    coupler_shape = construct_hex_drive_coupler()
    coupler_obj = doc.addObject("Part::Feature", "HexDriveCoupler")
    coupler_obj.Shape = coupler_shape
    coupler_obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )
    if hasattr(coupler_obj, "ViewObject") and coupler_obj.ViewObject:
        coupler_obj.ViewObject.ShapeColor = (0.90, 0.85, 0.20)

    # 8. ServoMotor Reference Solid (Cyan)
    servo_shape = construct_servo_cad_reference()
    servo_obj = doc.addObject("Part::Feature", "ServoMotor")
    servo_obj.Shape = servo_shape
    if hasattr(servo_obj, "ViewObject") and servo_obj.ViewObject:
        servo_obj.ViewObject.ShapeColor = (0.20, 0.80, 0.90)

    # Compound and Export Assembly
    comp = Part.makeCompound([
        frame_shape,
        flap_shape,
        adapter_shape,
        cover_shape,
        joiner_front.Shape,
        joiner_right.Shape,
        coupler_shape,
        servo_shape
    ])
    step_path = os.path.join(EXPORT_DIR, "motorized_assembly.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_assembly.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    comp.exportStep(step_path)
    comp.exportStl(stl_path)
    print("Successfully exported motorized_assembly.step and motorized_assembly.stl")
    return doc

if __name__ == "__main__":
    build_motorized_assembly()
