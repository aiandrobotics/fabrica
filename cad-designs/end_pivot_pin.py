"""
end_pivot_pin.py — Outside-Headed Click-Lock Snap-Barb End Pivot Pin
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.

Features:
1. Outer End-Cap Head (Ø16.0mm x 2.5mm, Y in [-2.5, 0.0mm]) stopping flush against outer knuckle face.
2. Smooth Cylindrical Bearing Journal (Ø12.8mm, Y in [0.0, 18.0mm]) sliding straight in from outside (Y=0).
3. Dual Integrated Cantilever Click-Lock Snap Barbs (Ø14.4mm at Y in [15.3, 17.8mm]) that flex inward
   through the Ø13.7mm frame knuckle bore and snap open into the frame's Ø16.8mm inner recess (zero pull-out).
4. Male 45° Diamond Tapered Square Peg (6.35 -> 5.90mm x 12.0mm, Y in [18.0, 30.0mm]) with corner relief & 45° nose chamfer.
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
    Constructs the 1-piece Outside-Headed Click-Lock Snap-Barb End Pivot Pin.
    Installs straight from the outside (Y=0) through the Ø13.7mm frame knuckle bore
    and clicks permanently behind the knuckle into the Ø16.8mm inner recess.
    """
    pivot_z = PIVOT_Z                  # 15.00mm
    journal_d = DRIVE_SHAFT_DIAMETER   # 12.80mm
    journal_r = journal_d / 2.0        # 6.40mm
    journal_len = 18.0                 # 18.00mm (spans 15mm frame knuckle + 3mm inner recess)

    cap_dia = 16.0                     # Ø16.0mm outer end-cap head (stops flush at Y=0.0mm)
    cap_r = cap_dia / 2.0              # 8.00mm
    cap_thick = 2.5                    # 2.50mm (Y in [-2.5, 0.0mm])

    peg_len = SQUARE_DRIVE_PEG_DEPTH   # 12.00mm tapered square engagement depth (Y in [18.0, 30.0mm])

    # 1. Outer End-Cap Head (Y in [-2.5, 0.0mm]) with 0.8mm x 45° outer rim chamfer
    cap = Part.makeCylinder(cap_r, cap_thick, App.Vector(0, -cap_thick, pivot_z), App.Vector(0, 1, 0))
    c_cap_bound = Part.makeCylinder(cap_r + 0.1, 0.85, App.Vector(0, -cap_thick - 0.05, pivot_z), App.Vector(0, 1, 0))
    c_cap_keep = Part.makeCone(cap_r - 0.8, cap_r, 0.85, App.Vector(0, -cap_thick - 0.05, pivot_z), App.Vector(0, 1, 0))
    cap = cap.cut(c_cap_bound.cut(c_cap_keep)).removeSplitter()

    # 2. Smooth Cylindrical Bearing Journal (Y in [0.0, 18.0mm])
    journal = Part.makeCylinder(journal_r, journal_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))

    # 3. Dual Cantilever Click-Lock Snap Barbs on ±X (Y in [15.3, 17.8mm], R = 7.2mm -> Ø14.4mm)
    #    Flexes 0.4mm inward per side through Ø13.7mm knuckle bore, clicks open in Ø16.8mm recess
    barb_h = 4.2                       # Z height of snap arm (pivot_z ± 2.1mm)
    barb_z0 = pivot_z - (barb_h / 2.0)
    barbs = []
    for sign in (1.0, -1.0):
        pts = [
            App.Vector(sign * (journal_r - 0.6), 15.3, barb_z0),
            App.Vector(sign * 7.2,               15.3, barb_z0),  # 90° locking shoulder facing -Y
            App.Vector(sign * 7.2,               15.8, barb_z0),  # 0.5mm crest
            App.Vector(sign * (journal_r - 0.1), 17.8, barb_z0),  # ~22° support-free insertion ramp
            App.Vector(sign * (journal_r - 0.6), 17.8, barb_z0),
            App.Vector(sign * (journal_r - 0.6), 15.3, barb_z0),
        ]
        barb_face = Part.Face(Part.makePolygon(pts))
        barbs.append(barb_face.extrude(App.Vector(0, 0, barb_h)))

    # 4. Male 45° Diamond Tapered Square Drive Peg (Y in [18.0, 30.0mm])
    sq_peg = make_tapered_diamond_peg(journal_len, 1.0, peg_len, pivot_z)

    # Fuse body before cutting cantilever flex slots
    pin = cap.fuse([journal, sq_peg] + barbs).removeSplitter()

    # 5. Cantilever Flex Relief Slots (Y in [7.5, 18.0mm]) freeing both ±X snap arms to deflect inward
    slot_cutters = []
    slot_y0 = 7.5
    slot_len = journal_len - slot_y0 + 0.1  # extends to Y=18.1mm so arm tip is free from square peg
    for sign in (1.0, -1.0):
        # Inner flex clearance gap behind the 1.6mm thick cantilever beam (|X| in [3.4, 4.8mm])
        x_min = 3.4 if sign > 0 else -4.8
        inner_slot = Part.makeBox(1.4, slot_len, barb_h + 1.4)
        inner_slot.translate(App.Vector(x_min, slot_y0, pivot_z - (barb_h / 2.0) - 0.7))
        slot_cutters.append(inner_slot)

        # Top & bottom horizontal release slits (0.7mm tall) freeing the cantilever arm from cylinder walls
        x_slit = 3.4 if sign > 0 else -8.0
        slit_top = Part.makeBox(4.6, slot_len, 0.7)
        slit_top.translate(App.Vector(x_slit, slot_y0, pivot_z + (barb_h / 2.0)))
        slit_bot = Part.makeBox(4.6, slot_len, 0.7)
        slit_bot.translate(App.Vector(x_slit, slot_y0, pivot_z - (barb_h / 2.0) - 0.7))
        slot_cutters.extend([slit_top, slit_bot])

    pin = pin.cut(Part.makeCompound(slot_cutters)).removeSplitter()

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
