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
    MODULE_GAP,
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    HEX_COUPLER_SIZE,
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
    Constructs the Symmetric Inter-Module Hex Drive Coupler (Part 11).
    Spans the 10mm gap between adjacent modules and bridges their 360° knuckles:
    - Central 10mm Bridge (Y in [-5.0, 5.0mm]) with Ø15mm centering collar.
    - +Y Smooth Journal (Ø12.8mm x 15mm, Y in [5.0, 20.0mm]) + Hex Peg (7.7mm AF x 9mm, Y in [21.0, 30.0mm]).
    - -Y Smooth Journal (Ø12.8mm x 15mm, Y in [-20.0, -5.0mm]) + Hex Peg (7.7mm AF x 9mm, Y in [-30.0, -21.0mm]).
    - Central Ø3.4mm driver access / weight-relief through-hole.
    """
    pivot_z = PIVOT_Z
    hex_size = HEX_COUPLER_SIZE - 0.3                 # 7.7mm flat-to-flat
    socket_depth = 9.0                                # 9.0mm hex engagement depth into flap
    knuckle_len = 15.0                                # 15.0mm journal through frame knuckle
    gap_half = MODULE_GAP / 2.0                       # 5.0mm
    thrust_gap = 1.0                                  # 1.0mm thrust gap
    journal_d = DRIVE_SHAFT_DIAMETER - 0.2            # 12.8mm cylinder
    journal_r = journal_d / 2.0                       # 6.4mm
    collar_r = 7.5                                    # Ø15.0mm central centering collar

    # 1. Central 10.0mm Inter-Module Bridge Cylinder (Y in [-5.0, 5.0mm])
    bridge_cyl = Part.makeCylinder(journal_r, 2 * gap_half, App.Vector(0, -gap_half, pivot_z), App.Vector(0, 1, 0))
    # Central centering collar (Ø15.0mm x 2.0mm at Y in [-1.0, 1.0mm])
    collar = Part.makeCylinder(collar_r, 2.0, App.Vector(0, -1.0, pivot_z), App.Vector(0, 1, 0))
    bridge = bridge_cyl.fuse(collar).removeSplitter()

    # 2. +Y Smooth Knuckle Journal (Y in [5.0, 20.0mm])
    pos_journal = Part.makeCylinder(journal_r, knuckle_len + thrust_gap, App.Vector(0, gap_half, pivot_z), App.Vector(0, 1, 0))
    # +Y Hex Drive Peg (Y in [21.0, 30.0mm])
    hex_pos_wire = make_hexagon_wire(hex_size, 0, pivot_z, gap_half + knuckle_len + thrust_gap)
    hex_pos_face = Part.Face(hex_pos_wire)
    hex_pos_peg = hex_pos_face.extrude(App.Vector(0, socket_depth, 0))
    c_pos = Part.makeCone(journal_r, journal_r - 1.5, 1.5, App.Vector(0, gap_half + knuckle_len + thrust_gap + socket_depth, pivot_z), App.Vector(0, 1, 0))
    hex_pos_peg = hex_pos_peg.cut(c_pos).removeSplitter()

    # 3. -Y Smooth Knuckle Journal (Y in [-20.0, -5.0mm])
    neg_journal = Part.makeCylinder(journal_r, knuckle_len + thrust_gap, App.Vector(0, -gap_half - knuckle_len - thrust_gap, pivot_z), App.Vector(0, 1, 0))
    # -Y Hex Drive Peg (Y in [-30.0, -21.0mm])
    hex_neg_wire = make_hexagon_wire(hex_size, 0, pivot_z, -gap_half - knuckle_len - thrust_gap)
    hex_neg_face = Part.Face(hex_neg_wire)
    hex_neg_peg = hex_neg_face.extrude(App.Vector(0, -socket_depth, 0))
    c_neg = Part.makeCone(journal_r, journal_r - 1.5, 1.5, App.Vector(0, -gap_half - knuckle_len - thrust_gap - socket_depth, pivot_z), App.Vector(0, -1, 0))
    hex_neg_peg = hex_neg_peg.cut(c_neg).removeSplitter()

    # Fuse into a smooth, 100% solid coupler pin
    coupler = bridge.fuse([pos_journal, hex_pos_peg, neg_journal, hex_neg_peg]).removeSplitter()

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
    doc = App.ActiveDocument or App.newDocument("HexDriveCoupler")
    shape = construct_hex_drive_coupler()
    feature = doc.addObject("Part::Feature", "HexDriveCoupler")
    feature.Shape = shape

export_part()

