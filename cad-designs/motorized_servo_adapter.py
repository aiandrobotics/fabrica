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
    DRIVE_SHAFT_DIAMETER,
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
      1. Ø20.0mm Circular Flange Disk (4.3mm thickness spanning Y=159.5 to 163.8mm, centered at Z_pivot=15.0mm).
      2. 4x M2/M2.5 screw clearance through-holes (Ø2.5mm) on Ø14.0mm PCD for bolting to the standard round metal/plastic horn.
      3. 100% Solid Continuous Central Core for maximum torsional fatigue resistance under servo torque.
      4. Male 8.0mm Hex Drive Peg (7.7mm flat-to-flat, 18.0mm length extending along -Y from Y=159.5 to 141.5mm)
         passing through frame top knuckle (Y in [150.0, 158.5mm]) and engaging 8.0mm into flap shaft hex socket (Y in [141.5, 149.5mm])
         with generous 2.55–3.15mm radial clearance to screw heads and a 2.0mm x 45° self-aligning lead-in entry chamfer.
    """
    import params
    h = params.PANEL_HEIGHT
    pivot_z = PIVOT_Z                          # 15.0mm
    disk_r = 10.0                              # 10.0mm radius (Ø20.0mm circular flange matching round horn)
    y_front = 159.5                            # Front face at Y = 159.5mm (1.0mm axial clearance from frame knuckle)
    y_rear = 163.8                             # Rear face at Y = 163.8mm (seats flush against MG996R round horn)
    disk_t = y_rear - y_front                  # 4.3mm thickness
    hex_size = 7.7                             # 7.7mm flat-to-flat (8.0mm hex socket clearance)
    peg_len = 18.0                             # 18.0mm continuous hex peg length (Y=159.5 to 141.5mm)

    # 1. Main Circular Flange Disk (Y in [159.5, 163.8mm])
    flange = Part.makeCylinder(disk_r, disk_t, App.Vector(0, y_front, pivot_z), App.Vector(0, 1, 0))

    # 2. Male 8.0mm Hex Drive Peg (Continuous along -Y from Y = 159.5 to 141.5mm)
    hex_wire = make_hexagon_wire(hex_size, 0, pivot_z, y_front)
    hex_face = Part.Face(hex_wire)
    hex_peg = hex_face.extrude(App.Vector(0, -peg_len, 0))

    # 45° Lead-in nose chamfer on hex peg tip
    chamfer_cone = Part.makeCone(disk_r, disk_r - 2.0, 2.0, App.Vector(0, y_front - peg_len, pivot_z), App.Vector(0, -1, 0))
    hex_peg = hex_peg.cut(chamfer_cone).removeSplitter()

    adapter = flange.fuse(hex_peg).removeSplitter()

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

    adapter = adapter.cut(Part.makeCompound(screw_holes)).removeSplitter()

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
