import os
import sys
import math

# Add current directory to path for FreeCAD imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part
from params import (
    SCALE,
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
    Constructs the Modular Double-Male Hex Drive Coupler Pin (Part 11).
    Connects active servo module drive shafts and follower flap axles across column joints.

    Features:
    1. Double-Ended 8.0mm Hex Keys (7.7mm flat-to-flat with 0.15mm sliding fit clearance).
    2. Center Stop Flange (Ø13.8mm x 1.0mm) to maintain exact centering between module knuckles.
    3. 1.5mm x 45° self-aligning lead-in entry chamfers on both hex tips.
    4. Ø3.2mm internal through-hole for weight relief or optional M3 reinforcing tension rod.
    5. Modular, easily replaceable wear-part architecture.
    """
    pivot_z = 8.0 * SCALE
    hex_size = HEX_COUPLER_SIZE - (0.3 * SCALE) # 7.7mm flat-to-flat
    peg_len = 10.5 * SCALE                      # 10.5mm insertion depth into each socket
    flange_d = DRIVE_SHAFT_DIAMETER - (0.2 * SCALE) # 13.8mm
    flange_t = 1.0 * SCALE                      # 1.0mm center stop flange
    flange_r = flange_d / 2.0

    # 1. Center Stop Flange (sits at Y = -flange_t to Y = 0.0mm between modules)
    flange = Part.makeCylinder(flange_r, flange_t, App.Vector(0, -flange_t, pivot_z), App.Vector(0, 1, 0))

    # 2. +Y Hex Drive Peg (inserts into top module socket at Y = 0 to Y = peg_len)
    hex_pos_wire = make_hexagon_wire(hex_size, 0, pivot_z, 0)
    hex_pos_face = Part.Face(hex_pos_wire)
    hex_pos_peg = hex_pos_face.extrude(App.Vector(0, peg_len, 0))
    
    # 45° Lead-in nose chamfer on +Y tip
    c_pos = Part.makeCone(flange_r, flange_r - 2.0 * SCALE, 2.0 * SCALE, App.Vector(0, peg_len, pivot_z), App.Vector(0, 1, 0))
    hex_pos_peg = hex_pos_peg.cut(c_pos).removeSplitter()

    # 3. -Y Hex Drive Peg (inserts into bottom driving module socket at Y = -flange_t to Y = -flange_t - peg_len)
    hex_neg_wire = make_hexagon_wire(hex_size, 0, pivot_z, -flange_t)
    hex_neg_face = Part.Face(hex_neg_wire)
    hex_neg_peg = hex_neg_face.extrude(App.Vector(0, -peg_len, 0))

    # 45° Lead-in nose chamfer on -Y tip
    c_neg = Part.makeCone(flange_r, flange_r - 2.0 * SCALE, 2.0 * SCALE, App.Vector(0, -flange_t - peg_len, pivot_z), App.Vector(0, -1, 0))
    hex_neg_peg = hex_neg_peg.cut(c_neg).removeSplitter()

    coupler = flange.fuse(Part.makeCompound([hex_pos_peg, hex_neg_peg])).removeSplitter()

    # 4. Ø3.2mm Center Through-Hole
    total_len = peg_len * 2.0 + flange_t + 2.0
    bore_r = 1.6 * SCALE
    bore = Part.makeCylinder(bore_r, total_len, App.Vector(0, -peg_len - flange_t - 1.0, pivot_z), App.Vector(0, 1, 0))
    coupler = coupler.cut(bore).removeSplitter()

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

    shape.exportStep(step_path)
    shape.exportStl(stl_path)

    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()
