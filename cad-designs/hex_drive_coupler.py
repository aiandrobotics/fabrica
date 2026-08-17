"""
hex_drive_coupler.py — Compact 10mm Bridge Modular Hex Drive Coupler Pin
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
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
    HEX_COUPLER_DEPTH,
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

def construct_hex_drive_coupler():
    """
    Constructs the Compact 10mm Bridge Modular Double-Male Hex Drive Coupler Pin (Part 11).
    Connects adjacent flap drive shafts across column joints.
    """
    pivot_z = PIVOT_Z
    hex_size = HEX_COUPLER_SIZE - 0.3                 # 7.7mm flat-to-flat
    socket_depth = 10.5                               # 10.5mm hex engagement depth into flap
    bridge_len = MODULE_GAP                           # 10.0mm inter-module seam gap
    bridge_d = DRIVE_SHAFT_DIAMETER - 0.2             # 12.8mm cylinder
    bridge_r = bridge_d / 2.0                         # 6.4mm

    # 1. 10.0mm Inter-Module Smooth Bridge Cylinder (spanning Y = -bridge_len to Y = 0.0mm)
    bridge_cyl = Part.makeCylinder(bridge_r, bridge_len, App.Vector(0, -bridge_len, pivot_z), App.Vector(0, 1, 0))

    # 2. +Y Hex Drive Peg (inserts into top flap axle hex socket at Y = 0.0mm to Y = +10.5mm)
    hex_pos_wire = make_hexagon_wire(hex_size, 0, pivot_z, 0)
    hex_pos_face = Part.Face(hex_pos_wire)
    hex_pos_peg = hex_pos_face.extrude(App.Vector(0, socket_depth, 0))
    
    # 45° Lead-in nose chamfer on +Y tip
    c_pos = Part.makeCone(bridge_r, bridge_r - 2.0, 2.0, App.Vector(0, socket_depth, pivot_z), App.Vector(0, 1, 0))
    hex_pos_peg = hex_pos_peg.cut(c_pos).removeSplitter()

    # 3. -Y Hex Drive Peg (inserts into bottom flap axle hex socket at Y = -10.0mm to Y = -20.5mm)
    hex_neg_wire = make_hexagon_wire(hex_size, 0, pivot_z, -bridge_len)
    hex_neg_face = Part.Face(hex_neg_wire)
    hex_neg_peg = hex_neg_face.extrude(App.Vector(0, -socket_depth, 0))

    # 45° Lead-in nose chamfer on -Y tip
    c_neg = Part.makeCone(bridge_r, bridge_r - 2.0, 2.0, App.Vector(0, -bridge_len - socket_depth, pivot_z), App.Vector(0, -1, 0))
    hex_neg_peg = hex_neg_peg.cut(c_neg).removeSplitter()

    # Fuse into a smooth, 100% solid, compact coupler pin
    coupler = bridge_cyl.fuse(Part.makeCompound([hex_pos_peg, hex_neg_peg])).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "hex_drive_coupler.step")
    stl_path  = os.path.join(EXPORT_DIR, "hex_drive_coupler.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    coupler.exportStep(step_path)
    coupler.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return coupler

def export_part():
    construct_hex_drive_coupler()

export_part()

