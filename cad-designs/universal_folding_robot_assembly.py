"""
universal_folding_robot_assembly.py — Full-Scale 6-Module Universal Garment Folding Robot
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.

Kinematic Architecture:
  1. Left Active Folding Wing (486mm long):
     - Top-Left: Motorized Module with MG996R Direct-Drive Servo
     - Bottom-Left: Follower Module synchronously driven via Modular Hex Drive Coupler
     - Revolute Joint: 0° to 180° inward folding around Hinge Axis (X=0.0mm, Z=10.0mm)
  2. Center Stationary Base Platform (486mm x 220mm):
     - 2x Monolithic Base Modules with Garment Alignment Reticles and Silent-Flip TPU Dampers
     - Provides rigid static torso/body support
  3. Right Active Folding Wing (486mm long):
     - Top-Right: Motorized Module with MG996R Direct-Drive Servo (Mirrored Inward Fold)
     - Bottom-Right: Follower Module synchronously driven via Modular Hex Drive Coupler (Mirrored)
     - Revolute Joint: 0° to 180° inward folding around Hinge Axis (X=680.0mm, Z=10.0mm)
  4. 7x Heavy-Duty Sliding Dovetail Bridge Joiners:
     - Rigidly locks the 6 modules into a monolithic 680mm x 486mm chassis.

# @joint Left_Motorized_Flap.Axle -> Left_Motorized_Frame.Bore type=revolute axis=(0,1,0) center=(0,0,10)
# @joint Left_Follower_Flap.Axle -> Left_Follower_Frame.Bore type=revolute axis=(0,1,0) center=(0,0,10)
# @joint Left_HexCoupler -> Left_Motorized_Flap type=rigid
# @joint Left_HexCoupler -> Left_Follower_Flap type=rigid
# @joint Right_Motorized_Flap.Axle -> Right_Motorized_Frame.Bore type=revolute axis=(0,1,0) center=(680,0,10)
# @joint Right_Follower_Flap.Axle -> Right_Follower_Frame.Bore type=revolute axis=(0,1,0) center=(680,0,10)
# @joint Right_HexCoupler -> Right_Motorized_Flap type=rigid
# @joint Right_HexCoupler -> Right_Follower_Flap type=rigid
# @joint FrameJoiners -> Chassis_Frames type=rigid
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
    PIVOT_Z,
    EXPORT_DIR,
)

from motorized_frame import construct_motorized_frame
from motorized_flap import construct_motorized_flap
from motorized_servo_adapter import construct_motorized_servo_adapter
from motorized_servo_cover import construct_motorized_servo_cover
from follower_frame import construct_follower_frame
from follower_flap import construct_follower_flap
from base_module import construct_base_module
from frame_joiner import construct_frame_joiner
from hex_drive_coupler import construct_hex_drive_coupler

def construct_servo_cad_reference():
    """Loads and positions the real MG996R STEP solid reference model in horizontal orientation."""
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
        body = Part.makeBox(36.0 * SCALE, 40.5 * SCALE, 16.8 * SCALE)
        body.translate(App.Vector(4.5 * SCALE, 192.5 * SCALE, -2.0 * SCALE))
        return body

def build_universal_folding_robot_assembly():
    """Constructs the full 6-module universal garment folding robot assembly."""
    for doc_name in list(App.listDocuments().keys()):
        App.closeDocument(doc_name)
    doc = App.newDocument("UniversalFoldingRobotAssembly")

    w = PANEL_WIDTH          # 240.0mm
    h = PANEL_HEIGHT         # 240.0mm
    gap = MODULE_GAP         # 10.0mm
    pitch_x = w + gap        # 250.0mm
    pitch_y = h + gap        # 250.0mm
    bottom_thick = 3.0 * SCALE

    # Master parts dictionary for STEP compound export
    export_shapes = []

    # ==========================================
    # 1. LEFT FOLDING WING (Column 0: X = 0.0mm)
    # ==========================================
    # Top-Left: Motorized Module at Y = 250.0mm
    tl_frame = construct_motorized_frame()
    tl_frame.translate(App.Vector(0, pitch_y, 0))
    obj_tl_frame = doc.addObject("Part::Feature", "Left_Motorized_Frame")
    obj_tl_frame.Shape = tl_frame
    if hasattr(obj_tl_frame, "ViewObject") and obj_tl_frame.ViewObject:
        obj_tl_frame.ViewObject.ShapeColor = (0.20, 0.55, 0.40) # Forest Green
    export_shapes.append(tl_frame)

    tl_flap = construct_motorized_flap()
    tl_flap.translate(App.Vector(0, pitch_y, 0))
    obj_tl_flap = doc.addObject("Part::Feature", "Left_Motorized_Flap")
    obj_tl_flap.Shape = tl_flap
    if hasattr(obj_tl_flap, "ViewObject") and obj_tl_flap.ViewObject:
        obj_tl_flap.ViewObject.ShapeColor = (0.85, 0.50, 0.20) # Amber Ochre
    export_shapes.append(tl_flap)

    tl_adapter = construct_motorized_servo_adapter()
    tl_adapter.translate(App.Vector(0, pitch_y, 0))
    obj_tl_adapter = doc.addObject("Part::Feature", "Left_Servo_Adapter")
    obj_tl_adapter.Shape = tl_adapter
    if hasattr(obj_tl_adapter, "ViewObject") and obj_tl_adapter.ViewObject:
        obj_tl_adapter.ViewObject.ShapeColor = (0.75, 0.25, 0.75) # Magenta
    export_shapes.append(tl_adapter)

    tl_cover = construct_motorized_servo_cover()
    tl_cover.translate(App.Vector(0, pitch_y, 0))
    obj_tl_cover = doc.addObject("Part::Feature", "Left_Servo_Cover")
    obj_tl_cover.Shape = tl_cover
    if hasattr(obj_tl_cover, "ViewObject") and obj_tl_cover.ViewObject:
        obj_tl_cover.ViewObject.ShapeColor = (0.75, 0.25, 0.35) # Crimson
    export_shapes.append(tl_cover)

    tl_servo = construct_servo_cad_reference()
    tl_servo.translate(App.Vector(0, pitch_y, 0))
    obj_tl_servo = doc.addObject("Part::Feature", "Left_Servo_Motor")
    obj_tl_servo.Shape = tl_servo
    if hasattr(obj_tl_servo, "ViewObject") and obj_tl_servo.ViewObject:
        obj_tl_servo.ViewObject.ShapeColor = (0.20, 0.75, 0.85) # Cyan
    export_shapes.append(tl_servo)

    # Bottom-Left: Follower Module at Y = 0.0mm
    bl_frame = construct_follower_frame()
    obj_bl_frame = doc.addObject("Part::Feature", "Left_Follower_Frame")
    obj_bl_frame.Shape = bl_frame
    if hasattr(obj_bl_frame, "ViewObject") and obj_bl_frame.ViewObject:
        obj_bl_frame.ViewObject.ShapeColor = (0.20, 0.55, 0.40)
    export_shapes.append(bl_frame)

    bl_flap = construct_follower_flap()
    obj_bl_flap = doc.addObject("Part::Feature", "Left_Follower_Flap")
    obj_bl_flap.Shape = bl_flap
    if hasattr(obj_bl_flap, "ViewObject") and obj_bl_flap.ViewObject:
        obj_bl_flap.ViewObject.ShapeColor = (0.85, 0.50, 0.20)
    export_shapes.append(bl_flap)

    # Left Column Hex Drive Coupler at Y = 250.0mm (bridges Top-Left Flap to Bottom-Left Flap)
    l_coupler = construct_hex_drive_coupler()
    l_coupler.translate(App.Vector(0, pitch_y, 0))
    obj_l_coupler = doc.addObject("Part::Feature", "Left_Hex_Coupler")
    obj_l_coupler.Shape = l_coupler
    if hasattr(obj_l_coupler, "ViewObject") and obj_l_coupler.ViewObject:
        obj_l_coupler.ViewObject.ShapeColor = (0.90, 0.85, 0.20)
    export_shapes.append(l_coupler)

    # ===============================================
    # 2. CENTER STATIONARY PLATFORM (Column 1: X = 250)
    # ==========================================
    # Top-Center: Base Module at (X = 250, Y = 250)
    tc_base = construct_base_module()
    tc_base.translate(App.Vector(pitch_x, pitch_y, 0))
    obj_tc_base = doc.addObject("Part::Feature", "Center_Top_Base")
    obj_tc_base.Shape = tc_base
    if hasattr(obj_tc_base, "ViewObject") and obj_tc_base.ViewObject:
        obj_tc_base.ViewObject.ShapeColor = (0.30, 0.45, 0.60) # Slate Blue
    export_shapes.append(tc_base)

    # Bottom-Center: Base Module at (X = 250, Y = 0)
    bc_base = construct_base_module()
    bc_base.translate(App.Vector(pitch_x, 0, 0))
    obj_bc_base = doc.addObject("Part::Feature", "Center_Bottom_Base")
    obj_bc_base.Shape = bc_base
    if hasattr(obj_bc_base, "ViewObject") and obj_bc_base.ViewObject:
        obj_bc_base.ViewObject.ShapeColor = (0.30, 0.45, 0.60)
    export_shapes.append(bc_base)

    # ===========================================
    # 3. RIGHT FOLDING WING (Column 2: X = 500)
    # Mirrored so hinge axis is at X = 740mm (inward fold)
    # ===========================================
    total_w = (3 * w) + (2 * gap) # 740.0mm

    def mirror_x(shape):
        """Mirrors shape across X=0 and places it at total_w=740.0mm."""
        s = shape.copy()
        mat = App.Matrix()
        mat.scale(-1, 1, 1)
        s.transformShape(mat)
        s.translate(App.Vector(total_w, 0, 0))
        return s

    # Top-Right: Motorized Module (Mirrored) at Y = 250.0mm
    tr_frame = mirror_x(construct_motorized_frame())
    tr_frame.translate(App.Vector(0, pitch_y, 0))
    obj_tr_frame = doc.addObject("Part::Feature", "Right_Motorized_Frame")
    obj_tr_frame.Shape = tr_frame
    if hasattr(obj_tr_frame, "ViewObject") and obj_tr_frame.ViewObject:
        obj_tr_frame.ViewObject.ShapeColor = (0.20, 0.55, 0.40)
    export_shapes.append(tr_frame)

    tr_flap = mirror_x(construct_motorized_flap())
    tr_flap.translate(App.Vector(0, pitch_y, 0))
    obj_tr_flap = doc.addObject("Part::Feature", "Right_Motorized_Flap")
    obj_tr_flap.Shape = tr_flap
    if hasattr(obj_tr_flap, "ViewObject") and obj_tr_flap.ViewObject:
        obj_tr_flap.ViewObject.ShapeColor = (0.85, 0.50, 0.20)
    export_shapes.append(tr_flap)

    tr_adapter = mirror_x(construct_motorized_servo_adapter())
    tr_adapter.translate(App.Vector(0, pitch_y, 0))
    obj_tr_adapter = doc.addObject("Part::Feature", "Right_Servo_Adapter")
    obj_tr_adapter.Shape = tr_adapter
    if hasattr(obj_tr_adapter, "ViewObject") and obj_tr_adapter.ViewObject:
        obj_tr_adapter.ViewObject.ShapeColor = (0.75, 0.25, 0.75)
    export_shapes.append(tr_adapter)

    tr_cover = mirror_x(construct_motorized_servo_cover())
    tr_cover.translate(App.Vector(0, pitch_y, 0))
    obj_tr_cover = doc.addObject("Part::Feature", "Right_Servo_Cover")
    obj_tr_cover.Shape = tr_cover
    if hasattr(obj_tr_cover, "ViewObject") and obj_tr_cover.ViewObject:
        obj_tr_cover.ViewObject.ShapeColor = (0.75, 0.25, 0.35)
    export_shapes.append(tr_cover)

    tr_servo = mirror_x(construct_servo_cad_reference())
    tr_servo.translate(App.Vector(0, pitch_y, 0))
    obj_tr_servo = doc.addObject("Part::Feature", "Right_Servo_Motor")
    obj_tr_servo.Shape = tr_servo
    if hasattr(obj_tr_servo, "ViewObject") and obj_tr_servo.ViewObject:
        obj_tr_servo.ViewObject.ShapeColor = (0.20, 0.75, 0.85)
    export_shapes.append(tr_servo)

    # Bottom-Right: Follower Module (Mirrored) at Y = 0.0mm
    br_frame = mirror_x(construct_follower_frame())
    obj_br_frame = doc.addObject("Part::Feature", "Right_Follower_Frame")
    obj_br_frame.Shape = br_frame
    if hasattr(obj_br_frame, "ViewObject") and obj_br_frame.ViewObject:
        obj_br_frame.ViewObject.ShapeColor = (0.20, 0.55, 0.40)
    export_shapes.append(br_frame)

    br_flap = mirror_x(construct_follower_flap())
    obj_br_flap = doc.addObject("Part::Feature", "Right_Follower_Flap")
    obj_br_flap.Shape = br_flap
    if hasattr(obj_br_flap, "ViewObject") and obj_br_flap.ViewObject:
        obj_br_flap.ViewObject.ShapeColor = (0.85, 0.50, 0.20)
    export_shapes.append(br_flap)

    # Right Column Hex Coupler at X = 740mm, Y = 250mm
    r_coupler = mirror_x(construct_hex_drive_coupler())
    r_coupler.translate(App.Vector(0, pitch_y, 0))
    obj_r_coupler = doc.addObject("Part::Feature", "Right_Hex_Coupler")
    obj_r_coupler.Shape = r_coupler
    if hasattr(obj_r_coupler, "ViewObject") and obj_r_coupler.ViewObject:
        obj_r_coupler.ViewObject.ShapeColor = (0.90, 0.85, 0.20)
    export_shapes.append(r_coupler)

    # ====================================================
    # 4. INTER-MODULE FRAME DOVETAIL JOINERS (7x Joiners)
    # ====================================================
    base_joiner = construct_frame_joiner()

    def make_joiner_instance(name, pos_x, pos_y, rotate_deg):
        j = base_joiner.copy()
        if rotate_deg != 0:
            j.rotate(App.Vector(0,0,0), App.Vector(0,0,1), rotate_deg)
        j.translate(App.Vector(pos_x, pos_y, bottom_thick))
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = j
        if hasattr(obj, "ViewObject") and obj.ViewObject:
            obj.ViewObject.ShapeColor = (0.20, 0.40, 0.85) # Royal Blue
        export_shapes.append(j)
        return obj

    # 4.1 Vertical Column Seams (Col 0 <-> Col 1 at X = 245.0mm)
    make_joiner_instance("Joiner_Left_Bottom", w + (gap / 2.0), h / 2.0, 90)
    make_joiner_instance("Joiner_Left_Top", w + (gap / 2.0), pitch_y + (h / 2.0), 90)

    # 4.2 Vertical Column Seams (Col 1 <-> Col 2 at X = 495.0mm)
    make_joiner_instance("Joiner_Right_Bottom", (2 * w) + gap + (gap / 2.0), h / 2.0, 90)
    make_joiner_instance("Joiner_Right_Top", (2 * w) + gap + (gap / 2.0), pitch_y + (h / 2.0), 90)

    # 4.3 Horizontal Row Seams (Row 0 <-> Row 1 at Y = 245.0mm)
    make_joiner_instance("Joiner_Row_Left", w / 2.0, h + (gap / 2.0), 0)
    make_joiner_instance("Joiner_Row_Center", pitch_x + (w / 2.0), h + (gap / 2.0), 0)
    make_joiner_instance("Joiner_Row_Right", (2 * pitch_x) + (w / 2.0), h + (gap / 2.0), 0)

    # ==========================================
    # 5. STEP and STL Export
    # ==========================================
    comp = Part.makeCompound(export_shapes)
    step_path = os.path.join(EXPORT_DIR, "universal_folding_robot_assembly.step")
    stl_path  = os.path.join(EXPORT_DIR, "universal_folding_robot_assembly.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    comp.exportStep(step_path)
    comp.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")
    return doc

def export_part():
    """Exports assembly STEP and STL files."""
    build_universal_folding_robot_assembly()

build_universal_folding_robot_assembly()
