"""
motorized_servo_cover.py — Toolless Snap-Latch Servo Enclosure Cover
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
    WALL_THICKNESS,
    PRESS_FIT_CLEARANCE,
    EXPORT_DIR,
)

def construct_motorized_servo_cover():
    """
    Constructs the Toolless Snap-Latch Protective Servo Cover for MG996R.
    """
    wall = 2.0 * SCALE
    deck_z = BASE_PANEL_THICKNESS # 15.0mm
    cover_l = 50.0 * SCALE        # along Y (Y = 184 to 234mm)
    cover_w = 24.0 * SCALE        # along X (X = -2.0 to 22.0mm)
    cover_h = 22.0 * SCALE        # Z = 15.0 to 37.0mm
    start_y = 184.0 * SCALE
    start_x = -2.0 * SCALE

    # 1. Main outer shell box
    outer_box = Part.makeBox(cover_w, cover_l, cover_h)
    outer_box.translate(App.Vector(start_x, start_y, deck_z))

    # Outer top edge chamfers / fillets for ergonomic aesthetic
    try:
        top_edges = [
            e for e in outer_box.Edges
            if abs(e.BoundBox.ZMin - (deck_z + cover_h)) < 0.001 and e.Length > 5.0 * SCALE
        ]
        if top_edges:
            outer_box = outer_box.makeChamfer(1.5 * SCALE, top_edges).removeSplitter()
    except Exception:
        pass

    # 2. Inner hollow cavity (wall thickness = 2.0mm)
    cav_w = cover_w - (2 * wall)
    cav_l = cover_l - (2 * wall)
    cav_h = cover_h - wall + 1.0
    inner_cav = Part.makeBox(cav_w, cav_l, cav_h)
    inner_cav.translate(App.Vector(start_x + wall, start_y + wall, deck_z - 0.5))

    cover = outer_box.cut(inner_cav).removeSplitter()

    # 3. Cable Exit Relief Notch (X = start_x + cover_w - wall to start_x + cover_w, Y = 210mm)
    wire_notch = Part.makeBox(wall + 1.0, 10.0 * SCALE, 8.0 * SCALE)
    wire_notch.translate(App.Vector(start_x + cover_w - wall - 0.5, 209.0 * SCALE, deck_z - 0.5))

    # 4. Shaft Clearance Arch on Front Face (Y = start_y, X centered around X=0)
    shaft_arch = Part.makeCylinder(7.5 * SCALE, wall + 2.0, App.Vector(0, start_y - 1.0, 8.0 * SCALE), App.Vector(0, 1, 0))

    # 5. Passive Cooling Ventilation Gills on Top Face (Z = deck_z + cover_h - wall)
    gill_cutters = []
    gill_w = 2.0 * SCALE
    gill_l = 16.0 * SCALE
    gill_h = wall + 2.0
    for gy in [start_y + 10.0 * SCALE, start_y + 18.0 * SCALE, start_y + 26.0 * SCALE, start_y + 34.0 * SCALE, start_y + 42.0 * SCALE]:
        g = Part.makeBox(gill_l, gill_w, gill_h)
        g.translate(App.Vector(start_x + 4.0 * SCALE, gy - (gill_w / 2.0), deck_z + cover_h - wall - 0.5))
        gill_cutters.append(g)

    cover = cover.cut(Part.makeCompound([wire_notch, shaft_arch] + gill_cutters)).removeSplitter()

    # 6. Snap-Latch Flex Tabs (extending down from Z = deck_z to Z = 10.0mm at X = 22.0mm)
    tab_w = 6.0 * SCALE
    tab_thick = 1.4 * SCALE
    tab_len = 5.0 * SCALE
    detent_bump = 0.4 * SCALE

    tabs = []
    for ty in [195.5 * SCALE, 225.5 * SCALE]:
        # Flex arm (X in [22.0, 23.4mm])
        arm = Part.makeBox(tab_thick, tab_w, tab_len)
        arm.translate(App.Vector(start_x + cover_w, ty - (tab_w / 2.0), deck_z - tab_len))
        
        # Detent catch bump (protrudes outward in +X: X in [23.4, 23.8mm])
        bump = Part.makeBox(detent_bump, tab_w, 1.5 * SCALE)
        bump.translate(App.Vector(start_x + cover_w + tab_thick, ty - (tab_w / 2.0), deck_z - tab_len + 0.8 * SCALE))
        
        tabs.extend([arm, bump])

    cover = cover.fuse(Part.makeCompound(tabs)).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_servo_cover.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_servo_cover.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    cover.exportStep(step_path)
    cover.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return cover

construct_servo_cover = construct_motorized_servo_cover

def main():
    doc = App.newDocument("MotorizedServoCover")
    shape = construct_motorized_servo_cover()
    feature = doc.addObject("Part::Feature", "MotorizedServoCover")
    feature.Shape = shape

main()
