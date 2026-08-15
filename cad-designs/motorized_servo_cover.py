"""
motorized_servo_cover.py — Full Enclosure Hood Cover for Horizontal MG996R Servo Bay
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
    Constructs the Full Enclosure Hood Cover for the Motorized Module.
    Features:
      1. Top plate covering X in [-17.0, 43.5mm], Y in [186.0, 240.0mm], Z in [15.0, 21.2mm].
      2. Rear face plate capping off the rear slide-in opening at Y in [237.5, 240.0mm], Z in [0.0, 21.2mm].
      3. Lateral slide retention tongues that engage with frame side grooves.
      4. Internal hollow pocket providing generous clearance around the MG996R motor body.
    """
    # 1. Top Face Plate (60.5mm wide x 54mm long x 6.2mm thick spanning Z=15.0..21.2mm, X in [-17.0, 43.5mm])
    top_plate = Part.makeBox(60.5 * SCALE, 54.0 * SCALE, 6.2 * SCALE)
    top_plate.translate(App.Vector(-17.0 * SCALE, 186.0 * SCALE, 15.0 * SCALE))

    # 2. Rear Face Cap (54.5mm wide x 2.5mm thick x 21.2mm tall spanning X in [-17.0, 37.5mm], Z=0..21.2mm)
    rear_cap = Part.makeBox(54.5 * SCALE, 2.5 * SCALE, 21.2 * SCALE)
    rear_cap.translate(App.Vector(-17.0 * SCALE, 237.5 * SCALE, 0.0))

    # 3. Lateral Retention Tongues (sliding into frame grooves at Z=13.6..14.8mm)
    tongue_l = Part.makeBox(1.5 * SCALE, 50.0 * SCALE, 1.2 * SCALE)
    tongue_l.translate(App.Vector(-18.5 * SCALE, 187.0 * SCALE, 13.6 * SCALE))

    tongue_r = Part.makeBox(1.5 * SCALE, 50.0 * SCALE, 1.2 * SCALE)
    tongue_r.translate(App.Vector(42.0 * SCALE, 187.0 * SCALE, 13.6 * SCALE))

    cover = top_plate.fuse([rear_cap, tongue_l, tongue_r]).removeSplitter()

    # 4. Underside clearance pocket for motor top casing (Z in [13.8, 20.0mm], X in [-17.0, 38.0mm], Y in [185.5, 230.5mm])
    pocket = Part.makeBox(56.0 * SCALE, 46.0 * SCALE, 6.2 * SCALE)
    pocket.translate(App.Vector(-17.5 * SCALE, 185.5 * SCALE, 13.8 * SCALE))

    cover = cover.cut(pocket).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_servo_cover.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_servo_cover.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    cover.exportStep(step_path)
    cover.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return cover

def main():
    doc = App.newDocument("MotorizedServoCover")
    shape = construct_motorized_servo_cover()
    feature = doc.addObject("Part::Feature", "MotorizedServoCover")
    feature.Shape = shape

main()
