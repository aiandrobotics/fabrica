"""
part_11_hex_drive_coupler.py — Smooth Cylindrical Journal Bearing Hex Drive Coupler Pin
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
    Constructs the Full-Journal Bearing Modular Double-Male Hex Drive Coupler Pin (Part 11).
    Connects active servo module drive shafts and follower flap axles across column joints.

    Features:
    1. Continuous Ø12.8mm Smooth Cylindrical Journal Bearing Shaft spanning through both 360° closed
       frame knuckles and the 20.0mm inter-module gap (Y = -36.0mm to Y = +16.0mm, length = 52.0mm).
       Provides true low-friction rotating journal support inside the Ø13.5mm knuckle bores.
    2. Dual 8.0mm Male Hex Drive Pegs (7.7mm flat-to-flat) starting exactly where the flap drive axles begin
       (+Y peg at Y = 16.0 to 26.5mm, -Y peg at Y = -36.0 to -46.5mm).
    3. 1.5mm x 45° self-aligning lead-in entry chamfers on both hex tips.
    4. 100% Solid Continuous Polymer Structure for maximum torsional and shear rigidity.
    """
    pivot_z = 8.0 * SCALE
    hex_size = HEX_COUPLER_SIZE - (0.3 * SCALE)       # 7.7mm flat-to-flat
    socket_depth = (HEX_COUPLER_DEPTH - 1.5) * SCALE  # 10.5mm hex engagement depth into flap
    knuckle_len = 15.0 * SCALE                        # 15.0mm knuckle barrel length
    gap_len = 1.0 * SCALE                             # 1.0mm axial clearance between knuckle and flap
    bridge_len = MODULE_GAP                           # 20.0mm inter-module seam gap

    # Journal cylindrical section spans through Knuckle A + Module Gap + Knuckle B + Clearance Gaps
    # From Y = -(bridge_len + knuckle_len + gap_len) to Y = +(knuckle_len + gap_len)
    journal_start_y = -(bridge_len + knuckle_len + gap_len) # -36.0mm
    journal_end_y   = +(knuckle_len + gap_len)              # +16.0mm
    journal_total_len = journal_end_y - journal_start_y     # 52.0mm

    journal_d = DRIVE_SHAFT_DIAMETER - (0.2 * SCALE)   # 12.8mm cylinder (0.35mm radial clearance in Ø13.5mm knuckle)
    journal_r = journal_d / 2.0                         # 6.4mm

    # 1. Continuous Ø12.8mm Smooth Cylindrical Journal Bearing Shaft (Y = -36.0mm to +16.0mm)
    journal_cyl = Part.makeCylinder(journal_r, journal_total_len, App.Vector(0, journal_start_y, pivot_z), App.Vector(0, 1, 0))

    # 2. +Y Hex Drive Peg (inserts into top flap hex socket at Y = 16.0mm to Y = 26.5mm)
    hex_pos_start_y = journal_end_y
    hex_pos_end_y   = hex_pos_start_y + socket_depth
    hex_pos_wire = make_hexagon_wire(hex_size, 0, pivot_z, hex_pos_start_y)
    hex_pos_face = Part.Face(hex_pos_wire)
    hex_pos_peg = hex_pos_face.extrude(App.Vector(0, socket_depth, 0))
    
    # 45° Lead-in nose chamfer on +Y tip
    c_pos = Part.makeCone(journal_r, journal_r - 2.0 * SCALE, 2.0 * SCALE, App.Vector(0, hex_pos_end_y, pivot_z), App.Vector(0, 1, 0))
    hex_pos_peg = hex_pos_peg.cut(c_pos).removeSplitter()

    # 3. -Y Hex Drive Peg (inserts into bottom flap hex socket at Y = -36.0mm to Y = -46.5mm)
    hex_neg_start_y = journal_start_y
    hex_neg_end_y   = hex_neg_start_y - socket_depth
    hex_neg_wire = make_hexagon_wire(hex_size, 0, pivot_z, hex_neg_start_y)
    hex_neg_face = Part.Face(hex_neg_wire)
    hex_neg_peg = hex_neg_face.extrude(App.Vector(0, -socket_depth, 0))

    # 45° Lead-in nose chamfer on -Y tip
    c_neg = Part.makeCone(journal_r, journal_r - 2.0 * SCALE, 2.0 * SCALE, App.Vector(0, hex_neg_end_y, pivot_z), App.Vector(0, -1, 0))
    hex_neg_peg = hex_neg_peg.cut(c_neg).removeSplitter()

    # Fuse into a single 100% solid, smooth journal bearing coupler pin
    coupler = journal_cyl.fuse(Part.makeCompound([hex_pos_peg, hex_neg_peg])).removeSplitter()
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
