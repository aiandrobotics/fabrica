"""
drive_coupler.py — Compact 10mm Bridge Modular Drive Coupler Pin
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import os
import sys
import math

# Add current directory to path for FreeCAD imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part
from params import (
    MODULE_GAP,
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

def construct_drive_coupler():
    """
    Constructs the Symmetric Inter-Module 45° Diamond Tapered Square Drive Coupler (Part 11).
    Spans the 10mm gap between adjacent modules and bridges their 360° knuckles:
    - Continuous smooth Ø12.6mm journal cylinder (Y in [-18.84, +18.84mm]) with 45° conical shoulders.
    - +Y / -Y 45° Diamond Tapered Square Pegs (6.35 -> 5.90mm x 12.0mm, corner-relieved + 45° nose chamfer).
    """
    pivot_z = PIVOT_Z
    peg_depth = SQUARE_DRIVE_PEG_DEPTH                # 12.0mm tapered square engagement depth into flap
    knuckle_len = 15.0                                # 15.0mm journal through frame knuckle
    gap_half = MODULE_GAP / 2.0                       # 5.0mm
    thrust_gap = 1.0                                  # 1.0mm thrust gap
    journal_d = DRIVE_SHAFT_DIAMETER - 0.2            # 12.6mm cylinder
    journal_r = journal_d / 2.0                       # 6.3mm
    r_clip = (SQUARE_DRIVE_BASE_SIZE / 2.0) * math.sqrt(2.0) - SQUARE_DRIVE_CORNER_CLIP  # 4.14mm

    # 1. Continuous Smooth Bearing Journal Cylinder spanning bridge + both frame knuckles
    shoulder_h = journal_r - r_clip  # ~2.16mm for 45° support-free cone
    y_peg_base = gap_half + knuckle_len + thrust_gap  # 21.0mm
    y_cone_start = y_peg_base - shoulder_h            # ~18.84mm
    main_shaft = Part.makeCylinder(journal_r, 2.0 * y_cone_start, App.Vector(0, -y_cone_start, pivot_z), App.Vector(0, 1, 0))

    # 2. +Y 45° Conical Shoulder & Tapered Diamond Square Peg (Y in [21.0, 33.0mm])
    pos_cone = Part.makeCone(journal_r, r_clip, shoulder_h, App.Vector(0, y_cone_start, pivot_z), App.Vector(0, 1, 0))
    sq_pos_peg = make_tapered_diamond_peg(y_peg_base, 1.0, peg_depth, pivot_z)

    # 3. -Y 45° Conical Shoulder & Tapered Diamond Square Peg (Y in [-33.0, -21.0mm])
    neg_cone = Part.makeCone(journal_r, r_clip, shoulder_h, App.Vector(0, -y_cone_start, pivot_z), App.Vector(0, -1, 0))
    sq_neg_peg = make_tapered_diamond_peg(-y_peg_base, -1.0, peg_depth, pivot_z)

    # Fuse into a smooth, 100% solid coupler pin
    coupler = main_shaft.fuse([pos_cone, sq_pos_peg, neg_cone, sq_neg_peg]).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "drive_coupler.step")
    stl_path  = os.path.join(EXPORT_DIR, "drive_coupler.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    coupler.exportStep(step_path)
    coupler.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return coupler

def export_part():
    doc = App.ActiveDocument or App.newDocument("DriveCoupler")
    shape = construct_drive_coupler()
    feature = doc.addObject("Part::Feature", "DriveCoupler")
    feature.Shape = shape

export_part()

