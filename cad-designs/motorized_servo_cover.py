"""
motorized_servo_cover.py — Flush Top Drop-In Lid for Motorized Servo Enclosure
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
    BASE_PANEL_THICKNESS,
    PIVOT_Z,
    EXPORT_DIR,
)

def construct_motorized_servo_cover():
    """
    Constructs the Flush Top Snap-Lock Enclosure Lid (Part 8) for the Motorized Module.
    Features:
      1. Main flush top plate (1.4mm thick, spanning X in [-17.5, 40.2mm], Y in [195.7, 236.8mm], Z in [19.8, 21.2mm]).
      2. Full-width Rear Interlocking Tongue (Y in [236.8, 239.0mm], Z in [18.3, 19.8mm]) sliding into the frame back wall.
      3. Dual Heavy-Duty Front Cantilever Snap Legs with 30° insertion ramps and 90° locking shoulders (Y=195.7mm).
      4. Rear-left corner finger/tool pry notch for easy toolless maintenance.
    """
    # 1. Main Flush Top Plate (sitting in frame top rebate at Z = 19.8 to 21.2mm, clearing servo top at Z=19.75mm)
    w_top = 57.7 * SCALE # X in [-17.5, 40.2mm]
    l_top = 38.8 * SCALE # Y in [195.7, 234.5mm]
    t_top = 1.4 * SCALE
    z_top_min = 19.8 * SCALE

    top_plate = Part.makeBox(w_top, l_top, t_top)
    top_plate.translate(App.Vector(-17.5 * SCALE, 195.7 * SCALE, z_top_min))

    # 2. Continuous Rear Interlocking Tongue (Extending +3.5mm into the frame back wall slot under the solid bar)
    tongue_w = 51.0 * SCALE
    tongue_l = 3.5 * SCALE
    tongue_t = 1.5 * SCALE
    tongue = Part.makeBox(tongue_w, tongue_l, tongue_t)
    tongue.translate(App.Vector(-14.5 * SCALE, 234.5 * SCALE, z_top_min - tongue_t))

    # 3. Dual Heavy-Duty Side Cantilever Snap Legs with 30° lead-in ramps and 90° locking shoulders
    def make_side_snap_leg(is_left):
        leg_l = 8.0 * SCALE  # Y-length
        leg_t = 1.8 * SCALE  # X-thickness
        leg_h = 5.5 * SCALE  # Z-height
        y_start = 205.0 * SCALE
        
        if is_left:
            x_pos = -17.0 * SCALE
            # Barb projects in -X direction by 0.9mm
            pts = [
                App.Vector(x_pos, y_start, z_top_min - leg_h),
                App.Vector(x_pos - 0.9 * SCALE, y_start, z_top_min - leg_h + 2.0 * SCALE),
                App.Vector(x_pos, y_start, z_top_min - leg_h + 2.5 * SCALE),
                App.Vector(x_pos, y_start, z_top_min - leg_h),
            ]
            x_ext = leg_t
        else:
            x_pos = 38.4 * SCALE
            # Barb projects in +X direction by 0.9mm
            pts = [
                App.Vector(x_pos + leg_t, y_start, z_top_min - leg_h),
                App.Vector(x_pos + leg_t + 0.9 * SCALE, y_start, z_top_min - leg_h + 2.0 * SCALE),
                App.Vector(x_pos + leg_t, y_start, z_top_min - leg_h + 2.5 * SCALE),
                App.Vector(x_pos + leg_t, y_start, z_top_min - leg_h),
            ]
            x_ext = leg_t
            
        leg_box = Part.makeBox(x_ext, leg_l, leg_h)
        leg_box.translate(App.Vector(x_pos, y_start, z_top_min - leg_h))
        
        barb_wire = Part.makePolygon(pts)
        barb_face = Part.Face(barb_wire)
        barb_solid = barb_face.extrude(App.Vector(0, leg_l, 0))
        return leg_box.fuse(barb_solid).removeSplitter()

    leg_left = make_side_snap_leg(True)
    leg_right = make_side_snap_leg(False)

    lid = top_plate.fuse([tongue, leg_left, leg_right]).removeSplitter()

    # 4. Finger / Tool Pry Notch at Rear-Left Corner
    notch = Part.makeCylinder(3.5 * SCALE, 3.0 * SCALE, App.Vector(-17.5 * SCALE, 234.5 * SCALE, z_top_min - 1.0))
    lid = lid.cut(notch).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_servo_cover.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_servo_cover.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    lid.exportStep(step_path)
    lid.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return lid

def main():
    doc = App.ActiveDocument or App.newDocument("MotorizedServoCover")
    shape = construct_motorized_servo_cover()
    feature = doc.addObject("Part::Feature", "MotorizedServoCover")
    feature.Shape = shape

def export_part():
    main()

export_part()
