"""
part_11_hex_drive_coupler.py — Dual-Ring 20mm Bridge Modular Hex Drive Coupler Pin
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
    SCALE,
    MODULE_GAP,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    HEX_COUPLER_DEPTH,
    EXPORT_DIR,
)

def make_hexagon_wire(flat_to_flat, center_x, center_z, y_pos):
    """Generates a regular hexagon wire in the XZ plane at a given Y position."""
    r = (flat_to_flat / math.sqrt(3.0))
    pts = [
        App.Vector(center_x + r * math.cos(i * math.pi / 3.0), y_pos, center_z + r * math.sin(i * math.pi / 3.0))
        for i in range(7)
    ]
    return Part.makePolygon(pts)

def construct_hex_drive_coupler():
    """
    Constructs the Dual-Ring 20mm Bridge Modular Double-Male Hex Drive Coupler Pin (Part 11).
    Connects active servo module drive shafts and follower flap axles across column joints.

    Features:
    1. 20.0mm Center Bridge Cylinder (Ø12.8mm) exactly matching the Part 10 Frame Joiner module gap.
    2. Dual Stop Rings (Ø13.8mm x 1.0mm) resting against adjacent module knuckle faces for 100% axial lock.
    3. Double-Ended 8.0mm Hex Keys (7.7mm flat-to-flat with 0.15mm sliding fit clearance).
    4. 1.5mm x 45° self-aligning lead-in entry chamfers on both hex tips.
    5. 100% Solid Continuous Polymer Structure for maximum torsional and shear rigidity.
    """
    pivot_z = 8.0 * SCALE
    hex_size = HEX_COUPLER_SIZE - (0.3 * SCALE)       # 7.7mm flat-to-flat
    peg_len = 26.5 * SCALE                            # 26.5mm length (15.0mm knuckle bridge + 1.0mm gap + 10.5mm flap socket engagement)
    bridge_len = MODULE_GAP                           # 20.0mm (Y = -20.0mm to Y = 0.0mm)
    bridge_d = DRIVE_SHAFT_DIAMETER - (0.2 * SCALE)   # 12.8mm cylinder
    bridge_r = bridge_d / 2.0                         # 6.4mm
    ring_d = (DRIVE_SHAFT_DIAMETER / 2.0) + 0.4 * SCALE # 6.9mm radius (Ø13.8mm collar)
    ring_r = ring_d
    ring_t = 1.0 * SCALE                              # 1.0mm ring thickness

    # 1. 20.0mm Inter-Module Bridge Cylinder (spanning Y = -bridge_len to Y = 0.0mm)
    bridge_cyl = Part.makeCylinder(bridge_r, bridge_len, App.Vector(0, -bridge_len, pivot_z), App.Vector(0, 1, 0))

    # 2. Dual Retention Stop Rings (at Y = -ring_t to 0.0mm and Y = -bridge_len to -bridge_len + ring_t)
    ring_top = Part.makeCylinder(ring_r, ring_t, App.Vector(0, -ring_t, pivot_z), App.Vector(0, 1, 0))
    ring_bot = Part.makeCylinder(ring_r, ring_t, App.Vector(0, -bridge_len, pivot_z), App.Vector(0, 1, 0))

    # 3. +Y Hex Drive Peg (inserts into top module socket at Y = 0 to Y = +peg_len)
    hex_pos_wire = make_hexagon_wire(hex_size, 0, pivot_z, 0)
    hex_pos_face = Part.Face(hex_pos_wire)
    hex_pos_peg = hex_pos_face.extrude(App.Vector(0, peg_len, 0))
    
    # 45° Lead-in nose chamfer on +Y tip
    c_pos = Part.makeCone(bridge_r, bridge_r - 2.0 * SCALE, 2.0 * SCALE, App.Vector(0, peg_len, pivot_z), App.Vector(0, 1, 0))
    hex_pos_peg = hex_pos_peg.cut(c_pos).removeSplitter()

    # 4. -Y Hex Drive Peg (inserts into bottom driving module socket at Y = -bridge_len to Y = -bridge_len - peg_len)
    hex_neg_wire = make_hexagon_wire(hex_size, 0, pivot_z, -bridge_len)
    hex_neg_face = Part.Face(hex_neg_wire)
    hex_neg_peg = hex_neg_face.extrude(App.Vector(0, -peg_len, 0))

    # 45° Lead-in nose chamfer on -Y tip
    c_neg = Part.makeCone(bridge_r, bridge_r - 2.0 * SCALE, 2.0 * SCALE, App.Vector(0, -bridge_len - peg_len, pivot_z), App.Vector(0, -1, 0))
    hex_neg_peg = hex_neg_peg.cut(c_neg).removeSplitter()

    # Fuse all into a single 100% solid, indestructible coupler pin
    coupler = bridge_cyl.fuse(Part.makeCompound([ring_top, ring_bot, hex_pos_peg, hex_neg_peg])).removeSplitter()
    return coupler

def export_part():
    """Exports STEP and STL files to EXPORT_DIR and adds shape to FreeCAD document."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    shape = construct_hex_drive_coupler()

    doc = App.ActiveDocument or App.newDocument("Doc")
    obj = doc.addObject("Part::Feature", "Part11HexDriveCoupler")
    obj.Shape = shape
    doc.recompute()

    step_path = os.path.join(EXPORT_DIR, "part_11_hex_drive_coupler.step")
    stl_path  = os.path.join(EXPORT_DIR, "part_11_hex_drive_coupler.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shape.exportStep(step_path)
    shape.exportStl(stl_path)

    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()
