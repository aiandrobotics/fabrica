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
    Constructs the Flush Top Drop-In Enclosure Lid (Part 8) for the Motorized Module.
    Features:
      1. Main flush top plate (1.4mm thick, spanning X in [-17.5, 40.2mm], Y in [195.7, 236.8mm], Z in [19.8, 21.2mm]).
      2. Rear corner downward alignment tabs (extending Z in [18.0, 19.8mm]) for friction lock.
      3. Rear-left corner finger pry notch for toolless removal.
    """
    # 1. Main Flush Top Plate (sitting in frame top rebate at Z = 19.8 to 21.2mm, clearing servo top at Z=19.75mm)
    w_top = 57.7 * SCALE # X in [-17.5, 40.2mm]
    l_top = 41.1 * SCALE # Y in [195.7, 236.8mm]
    t_top = 1.4 * SCALE
    z_top_min = 19.8 * SCALE

    top_plate = Part.makeBox(w_top, l_top, t_top)
    top_plate.translate(App.Vector(-17.5 * SCALE, 195.7 * SCALE, z_top_min))

    # 2. Downward Alignment Tabs at Rear Corners (behind/beside the servo motor)
    tab_l = Part.makeBox(3.0 * SCALE, 3.5 * SCALE, 1.8 * SCALE)
    tab_l.translate(App.Vector(-17.0 * SCALE, 231.0 * SCALE, z_top_min - 1.8 * SCALE))

    tab_r = Part.makeBox(3.0 * SCALE, 3.5 * SCALE, 1.8 * SCALE)
    tab_r.translate(App.Vector(35.0 * SCALE, 231.0 * SCALE, z_top_min - 1.8 * SCALE))

    lid = top_plate.fuse([tab_l, tab_r]).removeSplitter()

    # 3. Finger Pry Notch at Rear-Left Corner
    notch = Part.makeCylinder(3.5 * SCALE, 3.0 * SCALE, App.Vector(-17.5 * SCALE, 236.8 * SCALE, z_top_min - 1.0))
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
