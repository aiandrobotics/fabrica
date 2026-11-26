"""
end_pivot_pin.py — Outside-Headed Click-Lock Snap-Barb End Pivot Pin
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.

Features:
1. Outer End-Cap Head (Ø16.0mm x 2.5mm, Y in [-2.5, 0.0mm]) stopping flush against outer knuckle face,
   with a small +X orientation notch indicating the blade-side snap barb.
2. Smooth Cylindrical Bearing Journal (Ø12.8mm, Y in [0.0, 18.0mm]) sliding straight in from outside (Y=0).
3. Blade-Side (+X) Cantilever Click-Lock Snap Barb (R=9.1mm at Y in [15.2, 17.7mm]) on a stiffer 1.5mm thick,
   15.0mm long spring arm (Y in [3.0, 17.7mm]) that flexes 1.80mm inward through the Ø13.7mm frame knuckle bore
   and hooks 2.25mm behind the Y=15.0mm knuckle inner face (1.80mm positive lock even under full radial bore play).
   Uses a 45° support-free inner slot roof so the square peg base (r_clip=4.14mm) remains 100% solid at Y=18.0mm.
   Stays strictly in the upper hemisphere (0° -> 180°, Z >= 13.0mm) so it clears the uniform Ø13.7mm cradle trough.
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
    and clicks behind the Y=15.0mm knuckle inner face.
    """
    pivot_z = PIVOT_Z                  # 15.00mm
    journal_d = DRIVE_SHAFT_DIAMETER   # 12.80mm
    journal_r = journal_d / 2.0        # 6.40mm
    journal_len = 18.0                 # 18.00mm (spans 15mm frame knuckle + 3mm barb zone)

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

    # 3. Blade-Side (+X) Cantilever Click-Lock Snap Barb (Y in [15.2, 17.7mm], R = 9.1mm)
    #    Hooks 2.25mm past the Ø13.7mm (R=6.85mm) knuckle bore wall (still 1.80mm catch even under
    #    full 0.45mm radial play) on a stiffer 1.5mm thick spring beam (3.4x higher springback force).
    #    Positioned on +X (flap blade side) so across 0° -> 180° fold it sweeps strictly through Z >= 13.0mm.
    barb_h = 4.0                       # Z height of snap arm (pivot_z ± 2.0mm -> Z in [13.0, 17.0mm])
    barb_z0 = pivot_z - (barb_h / 2.0)
    pts = [
        App.Vector(journal_r - 1.5, 15.2, barb_z0),
        App.Vector(9.1,             15.2, barb_z0),  # 90° deep locking shoulder facing -Y (2.25mm hook)
        App.Vector(9.1,             15.6, barb_z0),  # 0.4mm crest
        App.Vector(journal_r - 0.1, 17.7, barb_z0),  # support-free insertion ramp
        App.Vector(journal_r - 1.5, 17.7, barb_z0),
        App.Vector(journal_r - 1.5, 15.2, barb_z0),
    ]
    barb_face = Part.Face(Part.makePolygon(pts))
    barb = barb_face.extrude(App.Vector(0, 0, barb_h))

    # 4. Male 45° Diamond Tapered Square Drive Peg (Y in [18.0, 30.0mm])
    sq_peg = make_tapered_diamond_peg(journal_len, 1.0, peg_len, pivot_z)

    # Fuse body before cutting cantilever flex slot
    pin = cap.fuse([journal, sq_peg, barb]).removeSplitter()

    # 5. Stiff Cantilever Flex Relief Slot on +X (15mm beam, 1.5mm thick, 1.95mm flex gap behind barb)
    #    Slopes out at 45° from (X=2.95, Y=16.4) to (X=4.15, Y=17.6) so the square peg base (r_clip=4.14mm)
    #    at Y=18.0mm sits on 100% solid plastic while giving full 1.80mm flex clearance behind the barb.
    slot_y0 = 3.0
    slot_z0 = pivot_z - (barb_h / 2.0) - 0.7
    slot_h = barb_h + 1.4
    inner_slot_pts = [
        App.Vector(2.95, slot_y0, slot_z0),
        App.Vector(4.90, slot_y0, slot_z0),
        App.Vector(4.90, 16.4,    slot_z0),
        App.Vector(6.10, 17.6,    slot_z0),  # trims inner ramp tip so it clears 45° roof at full flex
        App.Vector(6.10, 18.1,    slot_z0),
        App.Vector(4.15, 18.1,    slot_z0),  # strictly outside square peg (r_clip = 4.14mm)
        App.Vector(4.15, 17.6,    slot_z0),
        App.Vector(2.95, 16.4,    slot_z0),  # 45° support-free roof under square peg
        App.Vector(2.95, slot_y0, slot_z0),
    ]
    inner_slot = Part.Face(Part.makePolygon(inner_slot_pts)).extrude(App.Vector(0, 0, slot_h))

    # Top & bottom horizontal release slits freeing the cantilever arm all the way past Y=18.0mm
    slot_len = journal_len - slot_y0 + 0.1
    slit_top = Part.makeBox(5.5, slot_len, 0.7)
    slit_top.translate(App.Vector(4.15, slot_y0, pivot_z + (barb_h / 2.0)))
    slit_bot = Part.makeBox(5.5, slot_len, 0.7)
    slit_bot.translate(App.Vector(4.15, slot_y0, pivot_z - (barb_h / 2.0) - 0.7))

    # Subtle +X alignment tick on outer cap face (Y = -2.5mm) showing blade-side orientation
    align_tick = Part.makeBox(3.5, 0.6, 1.2)
    align_tick.translate(App.Vector(2.5, -cap_thick - 0.1, pivot_z - 0.6))

    pin = pin.cut(Part.makeCompound([inner_slot, slit_top, slit_bot, align_tick])).removeSplitter()

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
