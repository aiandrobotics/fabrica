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
    SQUARE_DRIVE_BASE_SIZE,
    SQUARE_DRIVE_TIP_SIZE,
    SQUARE_DRIVE_PEG_DEPTH,
    SQUARE_DRIVE_CORNER_CLIP,
    EXPORT_DIR,
)

def make_diamond_square_wire(size_af, center_x, center_z, y_pos):
    """Generates a 45°-rotated diamond square wire in the XZ plane."""
    r = (size_af / 2.0) * math.sqrt(2.0)
    pts = [
        App.Vector(center_x + r, y_pos, center_z),
        App.Vector(center_x,     y_pos, center_z + r),
        App.Vector(center_x - r, y_pos, center_z),
        App.Vector(center_x,     y_pos, center_z - r),
        App.Vector(center_x + r, y_pos, center_z),
    ]
    return Part.makePolygon(pts)

def make_tapered_diamond_peg(y_start, direction, taper_len, pivot_z):
    """Builds a corner-relieved 45° diamond tapered square peg with a 45° nose chamfer."""
    chamf_len = 1.2
    y_chamf_start = y_start + direction * (taper_len - chamf_len)
    y_tip = y_start + direction * taper_len

    taper_body = Part.makeLoft([
        make_diamond_square_wire(SQUARE_DRIVE_BASE_SIZE, 0, pivot_z, y_start),
        make_diamond_square_wire(SQUARE_DRIVE_TIP_SIZE, 0, pivot_z, y_chamf_start),
    ], True, True)
    nose_chamf = Part.makeLoft([
        make_diamond_square_wire(SQUARE_DRIVE_TIP_SIZE, 0, pivot_z, y_chamf_start),
        make_diamond_square_wire(SQUARE_DRIVE_TIP_SIZE - 2.0, 0, pivot_z, y_tip),
    ], True, True)
    peg = taper_body.fuse(nose_chamf).removeSplitter()

    r_clip = (SQUARE_DRIVE_BASE_SIZE / 2.0) * math.sqrt(2.0) - SQUARE_DRIVE_CORNER_CLIP
    clip_cyl = Part.makeCylinder(
        r_clip,
        taper_len + 0.2,
        App.Vector(0, y_start - direction * 0.1, pivot_z),
        App.Vector(0, direction, 0),
    )
    return peg.common(clip_cyl).removeSplitter()

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
    disk_thick = 3.0                   # 3.00mm (Y in [15.0, 18.0mm], sturdy for 3D printing)
    
    peg_len = SQUARE_DRIVE_PEG_DEPTH   # 12.00mm tapered square engagement depth (Y in [18.0, 30.0mm])

    # 1. Smooth Cylindrical Bearing Journal (Y in [0.0, 15.0mm])
    journal = Part.makeCylinder(journal_r, journal_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    
    # 0.8mm x 45° Lead-in entry chamfer on outer face (Y = 0.0mm)
    c_outer = Part.makeCone(journal_r, journal_r - 0.8, 0.8, App.Vector(0, 0, pivot_z), App.Vector(0, -1, 0))
    journal = journal.cut(c_outer).removeSplitter()

    # 2. Inner Retaining Thrust Flange Disk (Y in [15.0, 18.0mm])
    disk = Part.makeCylinder(disk_r, disk_thick, App.Vector(0, journal_len, pivot_z), App.Vector(0, 1, 0))

    # 3. Male 45° Diamond Tapered Square Drive Peg (Y in [18.0, 30.0mm])
    sq_peg = make_tapered_diamond_peg(journal_len + disk_thick, 1.0, peg_len, pivot_z)

    # Fuse into monolithic solid shoulder pin
    pin = journal.fuse([disk, sq_peg]).removeSplitter()

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
