"""
end_pivot_pin.py — Captive Inner-Flanged Shoulder Pivot Pin
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.

Features:
1. Smooth Cylindrical Journal (Ø12.8mm x 15.0mm, Y in [0.0, 15.0mm]) rotating inside frame's 360° knuckle.
2. Inner Retaining Thrust Flange Disk (Ø16.0mm x 1.0mm, Y in [15.0, 16.0mm]) providing 100% pop-out-proof retention and low-friction thrust bearing action.
3. Male 8.0mm Hex Drive Peg (7.7mm AF x 9.0mm, Y in [16.0, 25.0mm]) with 1.5mm x 45° self-aligning nose cone.
4. Central Ø3.4mm driver access / weight-relief through-hole.
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
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    EXPORT_DIR,
)

def make_hexagon_wire(size_af, center_x, center_z, y_pos):
    """Generates an explicit closed hexagon wire in the XZ plane."""
    r = (size_af / 2.0) / math.cos(math.radians(30))
    pts = []
    for i in range(6):
        ang = math.radians(60 * i + 30)
        pts.append(App.Vector(center_x + r * math.cos(ang), y_pos, center_z + r * math.sin(ang)))
    pts.append(pts[0])
    return Part.makePolygon(pts)

def construct_end_pivot_pin():
    """
    Constructs the Captive Inner-Flanged Shoulder Pivot Pin.
    """
    pivot_z = PIVOT_Z                  # 15.00mm
    journal_d = DRIVE_SHAFT_DIAMETER   # 12.80mm
    journal_r = journal_d / 2.0        # 6.40mm
    journal_len = 15.0                 # 15.00mm (spans frame knuckle Y in [0.0, 15.0mm])
    
    disk_dia = 16.0                    # Ø16.0mm (larger than Ø13.7mm knuckle bore -> cannot pass through)
    disk_r = disk_dia / 2.0            # 8.00mm
    disk_thick = 1.0                   # 1.00mm (Y in [15.0, 16.0mm])
    
    hex_size = HEX_COUPLER_SIZE - 0.3  # 7.70mm flat-to-flat
    peg_len = 9.0                      # 9.00mm engagement depth (Y in [16.0, 25.0mm])

    # 1. Smooth Cylindrical Bearing Journal (Y in [0.0, 15.0mm])
    journal = Part.makeCylinder(journal_r, journal_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    
    # 0.8mm x 45° Lead-in entry chamfer on outer face (Y = 0.0mm)
    c_outer = Part.makeCone(journal_r, journal_r - 0.8, 0.8, App.Vector(0, 0, pivot_z), App.Vector(0, -1, 0))
    journal = journal.cut(c_outer).removeSplitter()

    # 2. Inner Retaining Thrust Flange Disk (Y in [15.0, 16.0mm])
    disk = Part.makeCylinder(disk_r, disk_thick, App.Vector(0, journal_len, pivot_z), App.Vector(0, 1, 0))

    # 3. Male 8.0mm Hex Drive Peg (Y in [16.0, 25.0mm])
    hex_wire = make_hexagon_wire(hex_size, 0, pivot_z, journal_len + disk_thick)
    hex_face = Part.Face(hex_wire)
    hex_peg = hex_face.extrude(App.Vector(0, peg_len, 0))

    # 1.5mm x 45° Self-aligning nose cone on hex peg tip (Y in [23.5, 25.0mm])
    c_tip = Part.makeCone(journal_r, journal_r - 1.5, 1.5, App.Vector(0, journal_len + disk_thick + peg_len, pivot_z), App.Vector(0, 1, 0))
    hex_peg = hex_peg.cut(c_tip).removeSplitter()

    # Fuse into monolithic shoulder pin
    pin = journal.fuse([disk, hex_peg]).removeSplitter()

    # 4. Central Ø3.4mm weight-relief / driver access through-hole
    center_hole = Part.makeCylinder(1.7, journal_len + disk_thick + peg_len + 2.0, App.Vector(0, -1.0, pivot_z), App.Vector(0, 1, 0))
    pin = pin.cut(center_hole).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "end_pivot_pin.step")
    stl_path  = os.path.join(EXPORT_DIR, "end_pivot_pin.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    pin.exportStep(step_path)
    pin.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return pin

def main():
    doc = App.ActiveDocument or App.newDocument("EndPivotPin")
    shape = construct_end_pivot_pin()
    feature = doc.addObject("Part::Feature", "EndPivotPin")
    feature.Shape = shape

def export_part():
    main()

export_part()
