"""
motorized_servo_adapter.py — Modular Circular Servo Horn Drive Adapter
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.

Bolts directly onto the standard circular servo horn disk (Ø20mm) included with MG996R,
and extends a male 8.0mm hex drive peg to anchor into the motorized folding flap shaft.
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

def construct_motorized_servo_adapter():
    """
    Constructs the 3D-printed Servo Horn to Hex Drive Adapter (Part 12).
    Features:
      1. Ø19.0mm Circular Flange Disk (7.0mm thickness spanning Y=178.0 to 185.0mm, centered at Z_pivot=10.0mm).
      2. 4x M2/M2.5 screw clearance through-holes (Ø2.2mm) on Ø14.0mm PCD for bolting to the standard round horn.
      3. Central Ø6.5mm driver access counterbore for the M3 servo spline retention screw.
      4. Male 8.0mm Hex Drive Peg (7.7mm flat-to-flat, 10.5mm length extending along -Y from Y=178.0 to 167.5mm)
         with a 1.5mm x 45° self-aligning lead-in entry chamfer.
    """
    import params
    h = params.PANEL_HEIGHT
    pivot_z = PIVOT_Z                          # 10.0mm
    disk_r = 9.5                               # 9.5mm radius (Ø19.0mm)
    disk_t = 6.0                               # 6.0mm thickness
    y_rear = h - 55.0                          # Seats against servo horn at Y = h - 55.0mm
    y_front = y_rear - disk_t                  # h - 61.0mm
    hex_size = 7.7                             # 7.7mm flat-to-flat (8mm hex clearance)
    peg_len = 10.5                             # 10.5mm insertion length into flap

    # 1. Main Circular Flange Disk (Y in [h - 61.0, h - 55.0mm])
    flange = Part.makeCylinder(disk_r, disk_t, App.Vector(0, y_front, pivot_z), App.Vector(0, 1, 0))

    # 2. Male 8.0mm Hex Drive Peg (Extending along -Y from Y = h - 61.0 to h - 71.5mm)
    hex_wire = make_hexagon_wire(hex_size, 0, pivot_z, y_front)
    hex_face = Part.Face(hex_wire)
    hex_peg = hex_face.extrude(App.Vector(0, -peg_len, 0))

    # 45° Lead-in nose chamfer on hex peg tip at Y = y_front - peg_len
    chamfer_cone = Part.makeCone(disk_r, disk_r - 2.0, 2.0, App.Vector(0, y_front - peg_len, pivot_z), App.Vector(0, -1, 0))
    hex_peg = hex_peg.cut(chamfer_cone).removeSplitter()

    adapter = flange.fuse(hex_peg).removeSplitter()

    # 3. 4x M2/M2.5 Mounting Screw Clearance Holes (Ø2.2mm) on Ø14.0mm PCD (R = 7.0mm)
    pcd_r = 7.0
    screw_r = 1.1
    screw_holes = []
    for i in range(4):
        ang = math.radians(90.0 * i)
        sx = pcd_r * math.cos(ang)
        sz = pivot_z + pcd_r * math.sin(ang)
        sh = Part.makeCylinder(screw_r, disk_t + 2.0, App.Vector(sx, y_front - 1.0, sz), App.Vector(0, 1, 0))
        screw_holes.append(sh)

    # 4. Central 2.0mm Hub/Screw Clearance Pocket on Rear Contact Face (Ø8.5mm x 2.0mm deep)
    rear_pocket_r = 4.25
    rear_pocket_depth = 2.0
    rear_pocket = Part.makeCylinder(rear_pocket_r, rear_pocket_depth + 0.1, App.Vector(0, y_rear - rear_pocket_depth, pivot_z), App.Vector(0, 1, 0))

    cutters = screw_holes + [rear_pocket]
    adapter = adapter.cut(Part.makeCompound(cutters)).removeSplitter()

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
