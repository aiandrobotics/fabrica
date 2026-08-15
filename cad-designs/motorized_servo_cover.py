"""
motorized_servo_cover.py — Flush Low-Profile Slide-In Servo Cover for Real MG996R
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import os
import sys
import FreeCAD as App
import Part

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from params import SCALE, EXPORT_DIR

def construct_motorized_servo_cover():
    """
    Constructs the Flush Low-Profile Slide-In Servo Cover.
    Specifically sized to enclose the real MG996R standard servo horizontally with zero bumps ($Z = 15.0..17.8mm$).
    """
    cover_w = 60.0 * SCALE   # 60.0mm along X (X = -17.0 to 43.0mm)
    cover_l = 49.0 * SCALE   # 49.0mm along Y (Y = 187.0 to 236.0mm)
    z_base = 15.0 * SCALE    # 15.0mm (rests on top of frame rails)
    z_max = 17.8 * SCALE     # 17.8mm (flush with knuckle top crown)
    cover_t = z_max - z_base # 2.8mm

    # 1. Main flat flush top plate
    top_plate = Part.makeBox(cover_w, cover_l, cover_t)
    top_plate.translate(App.Vector(-17.0 * SCALE, 187.0 * SCALE, z_base))

    # 2. Side Retention Guide Tongues
    tongue_w = 1.4 * SCALE
    tongue_h = 1.3 * SCALE
    t_left = Part.makeBox(tongue_w, cover_l - 6.0 * SCALE, tongue_h)
    t_left.translate(App.Vector(-18.4 * SCALE, 190.0 * SCALE, 13.4 * SCALE))

    t_right = Part.makeBox(tongue_w, cover_l - 6.0 * SCALE, tongue_h)
    t_right.translate(App.Vector(43.0 * SCALE, 190.0 * SCALE, 13.4 * SCALE))

    cover = top_plate.fuse(Part.makeCompound([t_left, t_right])).removeSplitter()

    # 3. Internal Underside Clearance Pocket for the top of the real servo
    cav_w = 58.5 * SCALE
    cav_l = 50.0 * SCALE
    cav_h = 3.0 * SCALE
    cav_pocket = Part.makeBox(cav_w, cav_l, cav_h)
    cav_pocket.translate(App.Vector(-17.5 * SCALE, 186.0 * SCALE, z_base - 0.1))

    cover = cover.cut(cav_pocket).removeSplitter()

    # 4. Passive Heat Dissipation Ventilation Gills
    gills = []
    gill_w = 2.0 * SCALE
    gill_l = 28.0 * SCALE
    for gy in range(int(194 * SCALE), int(228 * SCALE), int(6 * SCALE)):
        slot = Part.makeBox(gill_l, gill_w, cover_t + 2.0)
        slot.translate(App.Vector(5.0 * SCALE, float(gy), z_base - 1.0))
        gills.append(slot)

    # 5. Push-Pull Finger Grip Texture
    grips = []
    grip_w = 1.5 * SCALE
    grip_l = 24.0 * SCALE
    for gy in [231.0 * SCALE, 233.5 * SCALE]:
        g = Part.makeBox(grip_l, grip_w, 0.5 * SCALE)
        g.translate(App.Vector(7.0 * SCALE, gy, z_max - 0.5 * SCALE))
        grips.append(g)

    # 6. Rear Cable Exit Notch
    cable_notch = Part.makeBox(10.0 * SCALE, 8.0 * SCALE, cover_t + 2.0)
    cable_notch.translate(App.Vector(25.0 * SCALE, 230.0 * SCALE, z_base - 1.0))

    cover = cover.cut(Part.makeCompound(gills + grips + [cable_notch])).removeSplitter()

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
