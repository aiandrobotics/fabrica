"""
motorized_servo_adapter.py — Modular Circular Servo Horn Drive Adapter
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.

Bolts directly onto the standard circular servo horn disk (Ø20mm) included with MG996R,
and extends a male 45° diamond tapered square drive peg to anchor into the motorized folding flap shaft.
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

def make_tapered_diamond_peg(y_start, direction, straight_len, taper_len, pivot_z):
    """Builds a corner-relieved 45° diamond tapered square peg with a 45° nose chamfer."""
    chamf_len = 1.2
    y_taper_start = y_start + direction * straight_len
    y_chamf_start = y_taper_start + direction * (taper_len - chamf_len)
    y_tip = y_taper_start + direction * taper_len

    parts = []
    if straight_len > 0.0:
        w0 = make_diamond_square_wire(SQUARE_DRIVE_BASE_SIZE, 0, pivot_z, y_start)
        parts.append(Part.Face(w0).extrude(App.Vector(0, direction * straight_len, 0)))

    taper_body = Part.makeLoft([
        make_diamond_square_wire(SQUARE_DRIVE_BASE_SIZE, 0, pivot_z, y_taper_start),
        make_diamond_square_wire(SQUARE_DRIVE_TIP_SIZE, 0, pivot_z, y_chamf_start),
    ], True, True)
    nose_chamf = Part.makeLoft([
        make_diamond_square_wire(SQUARE_DRIVE_TIP_SIZE, 0, pivot_z, y_chamf_start),
        make_diamond_square_wire(SQUARE_DRIVE_TIP_SIZE - 2.0, 0, pivot_z, y_tip),
    ], True, True)
    parts.extend([taper_body, nose_chamf])

    peg = parts[0]
    for p in parts[1:]:
        peg = peg.fuse(p)
    peg = peg.removeSplitter()

    # Clip the 4 sharp outer corners slightly so FDM seam blobs never bind in socket corners
    r_clip = (SQUARE_DRIVE_BASE_SIZE / 2.0) * math.sqrt(2.0) - SQUARE_DRIVE_CORNER_CLIP
    total_len = straight_len + taper_len
    clip_cyl = Part.makeCylinder(
        r_clip,
        total_len + 0.2,
        App.Vector(0, y_start - direction * 0.1, pivot_z),
        App.Vector(0, direction, 0),
    )
    return peg.common(clip_cyl).removeSplitter()

def construct_motorized_servo_adapter():
    """
    Constructs the 3D-printed Servo Horn to Square Drive Adapter (Part 12).
    Features:
      1. Ø20.0mm Circular Flange Disk (7.5mm thickness spanning Y=156.3 to 163.8mm, centered at Z_pivot=15.0mm).
      2. 4x M2/M2.5 screw clearance through-holes (Ø2.5mm) on Ø14.0mm PCD for bolting to the standard round metal/plastic horn.
      3. 100% Solid Continuous Central Core for maximum torsional fatigue resistance under servo torque.
      4. Male 45° Diamond Tapered Square Drive Peg (6.35 -> 5.90mm flat-to-flat, 6.3mm straight span + 12.0mm tapered engagement)
         passing through frame top knuckle and engaging 12.0mm into flap shaft square socket (Y in [138.0, 150.0mm])
         with corner relief and a 1.2mm x 45° self-aligning lead-in nose chamfer.
    """
    pivot_z = PIVOT_Z                          # 15.0mm
    disk_r = 10.0                              # 10.0mm radius (Ø20.0mm circular flange matching round horn)
    y_front = 156.3                            # Front face at Y = 156.3mm (6.3mm span to flap top face at Y = 150.0mm)
    y_rear = 163.8                             # Rear face at Y = 163.8mm (seats flush against MG996R round horn)
    disk_t = y_rear - y_front                  # 7.5mm thickness (+2.0mm thicker so horn screws stay recessed)
    knuckle_span = 6.3                         # 6.3mm straight span from flange (156.3) to flap entry (150.0)
    taper_len = SQUARE_DRIVE_PEG_DEPTH         # 12.0mm tapered square engagement inside flap (150.0 -> 138.0mm)

    # 1. Main Circular Flange Disk (Y in [156.3, 163.8mm])
    flange = Part.makeCylinder(disk_r, disk_t, App.Vector(0, y_front, pivot_z), App.Vector(0, 1, 0))

    # 2. Male 45° Diamond Tapered Square Drive Peg (18.3mm total: 6.3mm span + 12.0mm tapered engagement)
    sq_peg = make_tapered_diamond_peg(y_front, -1.0, knuckle_span, taper_len, pivot_z)

    adapter = flange.fuse(sq_peg).removeSplitter()

    # 3. 4x M2/M2.5 Mounting Screw Clearance Holes (Ø2.5mm) on Ø14.0mm PCD (R = 7.0mm)
    pcd_r = 7.0
    screw_r = 1.25
    screw_holes = []
    for i in range(4):
        ang = math.radians(90.0 * i + 45.0)
        sx = pcd_r * math.cos(ang)
        sz = pivot_z + pcd_r * math.sin(ang)
        sh = Part.makeCylinder(screw_r, disk_t + 2.0, App.Vector(sx, y_front - 1.0, sz), App.Vector(0, 1, 0))
        screw_holes.append(sh)

    # 4. Central Horn Boss / Screw Head Relief Pocket on Rear Face (Ø8.0mm x 2.0mm deep at Y in [161.8, 163.8mm])
    center_relief = Part.makeCylinder(4.0, 2.5, App.Vector(0, y_rear - 2.0, pivot_z), App.Vector(0, 1, 0))

    adapter = adapter.cut(Part.makeCompound(screw_holes + [center_relief])).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_servo_adapter.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_servo_adapter.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    adapter.exportStep(step_path)
    adapter.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return adapter

def main():
    doc = App.ActiveDocument or App.newDocument("MotorizedServoAdapter")
    shape = construct_motorized_servo_adapter()
    feature = doc.addObject("Part::Feature", "MotorizedServoAdapter")
    feature.Shape = shape

def export_part():
    main()

export_part()
