"""
part_01_base_module.py — Monolithic Stationary Base Chassis Module
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import sys
import os
import math

# Ensure cad-designs root is in Python path for importing params.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import FreeCAD as App
import Part

from params import (
    SCALE,
    PANEL_WIDTH,
    PANEL_HEIGHT,
    BASE_PANEL_THICKNESS,
    WALL_THICKNESS,
    ELEPHANTS_FOOT_CHAMFER,
    FOOT_PAD_DIA,
    FOOT_PAD_DEPTH,
    RETICLE_DEBOSS_DEPTH,
    TPU_BUMPER_DEPTH,
    TEXTURE_HEIGHT,
    HOLE_CHAMFER,
    JOINER_DETENT,
    WIRE_PORT_FILLET,
    EXPORT_DIR,
)

def construct_base_module():
    """
    Constructs the 1-piece Monolithic Base Chassis Module shape using FreeCAD's Part API.
    """
    w = PANEL_WIDTH
    h = PANEL_HEIGHT
    t = BASE_PANEL_THICKNESS
    wall = WALL_THICKNESS

    # 1. Main outer solid box
    base_box = Part.makeBox(w, h, t, App.Vector(0, 0, 0))

    # 2. Hollow open-bottom cavity (leaves outer perimeter wall & top surface plate)
    top_plate_thick = wall
    cavity_w = w - (2.0 * wall)
    cavity_h = h - (2.0 * wall)
    cavity_z = t - top_plate_thick
    cavity = Part.makeBox(cavity_w, cavity_h, cavity_z, App.Vector(wall, wall, 0))
    main_shell = base_box.cut(cavity)

    # 3. Internal Hexagonal Web Lattice Ribbing inside bottom cavity (Wall-to-Wall Coverage)
    ribs = []
    hex_radius = 16.0 * SCALE
    hex_wall = 2.0 * SCALE
    dx = hex_radius * 1.5
    dy = hex_radius * math.sqrt(3)

    cols = int(math.ceil(cavity_w / dx)) + 2
    rows = int(math.ceil(cavity_h / dy)) + 2

    cavity_bounds = Part.makeBox(cavity_w, cavity_h, cavity_z, App.Vector(wall, wall, 0))

    # Store valid internal hex cell center coordinates for top cutouts
    internal_hex_centers = []

    for col in range(-1, cols):
        for row in range(-1, rows):
            cx = wall + (col * dx)
            cy = wall + (row * dy) + (0.5 * dy if (col % 2 != 0) else 0.0)

            outer_hex = Part.makePolygon([
                App.Vector(cx + hex_radius * math.cos(a), cy + hex_radius * math.sin(a), 0)
                for a in [i * math.pi / 3 for i in range(7)]
            ])
            inner_hex = Part.makePolygon([
                App.Vector(cx + (hex_radius - hex_wall) * math.cos(a), cy + (hex_radius - hex_wall) * math.sin(a), 0)
                for a in [i * math.pi / 3 for i in range(7)]
            ])
            outer_face = Part.Face(outer_hex)
            inner_face = Part.Face(inner_hex)
            rib_face = outer_face.cut(inner_face)
            rib_solid = rib_face.extrude(App.Vector(0, 0, cavity_z))
            
            # Crop hex cell cleanly within cavity boundary
            cropped = rib_solid.common(cavity_bounds)
            if cropped.Volume > 0.001:
                ribs.append(cropped)

            # Collect internal hex centers (margin check for clean top cutouts)
            margin = wall + hex_radius + (15.0 * SCALE)
            if (margin < cx < w - margin) and (margin < cy < h - margin):
                internal_hex_centers.append((col, row, cx, cy))

    if ribs:
        lattice_compound = Part.makeCompound(ribs)
        main_shell = main_shell.fuse(lattice_compound)

    # 4. Aligned Dense Organic Hexagonal Cutouts (Rich Organic Mesh, No Large Blank Spaces)
    top_hex_cutters = []
    top_hex_r = hex_radius - hex_wall - (0.5 * SCALE)

    # Rich 2D organic cluster selection (75% open cell ratio covering full X/Y span without blank margins)
    selected_centers = [
        item for item in internal_hex_centers
        if (item[0] * 3 + item[1] * 5 + 1) % 4 != 0
    ]

    for col, row, cx, cy in selected_centers:
        hex_poly = Part.makePolygon([
            App.Vector(cx + top_hex_r * math.cos(a), cy + top_hex_r * math.sin(a), t - top_plate_thick - 0.1)
            for a in [i * math.pi / 3 for i in range(7)]
        ])
        hex_face = Part.Face(hex_poly)
        hex_prism = hex_face.extrude(App.Vector(0, 0, top_plate_thick + 0.2))
        top_hex_cutters.append(hex_prism)

    if top_hex_cutters:
        top_hex_compound = Part.makeCompound(top_hex_cutters)
        main_shell = main_shell.cut(top_hex_compound)

    # Apply 0.8mm Snag-Free Chamfers to all top hex cutout edges
    try:
        top_hex_edges = []
        for edge in main_shell.Edges:
            bb = edge.BoundBox
            if abs(bb.ZMin - t) < 0.001 and abs(bb.ZMax - t) < 0.001:
                # Identify short hex segment edges on top surface
                if 5.0 * SCALE < bb.XLength < 20.0 * SCALE or 5.0 * SCALE < bb.YLength < 20.0 * SCALE:
                    if abs(bb.XMin - wall) > 5.0 and abs(bb.XMax - (w - wall)) > 5.0:
                        top_hex_edges.append(edge)
        if top_hex_edges:
            main_shell = main_shell.makeChamfer(HOLE_CHAMFER, top_hex_edges)
    except Exception as e:
        print(f"Warning: Top hex chamfer skipped on base module: {e}")

    # 4. Anti-Slip Foot Pad Recess Sockets (Bottom 4 corners)
    foot_radius = FOOT_PAD_DIA / 2.0
    foot_offset = wall + foot_radius + (2.0 * SCALE)
    foot_positions = [
        App.Vector(foot_offset, foot_offset, 0),
        App.Vector(w - foot_offset, foot_offset, 0),
        App.Vector(w - foot_offset, h - foot_offset, 0),
        App.Vector(foot_offset, h - foot_offset, 0),
    ]
    foot_cuts = []
    for pos in foot_positions:
        cylinder = Part.makeCylinder(foot_radius, FOOT_PAD_DEPTH, pos, App.Vector(0, 0, 1))
        foot_cuts.append(cylinder)
    foot_compound = Part.makeCompound(foot_cuts)
    main_shell = main_shell.cut(foot_compound)
    # 5. Female Dovetail Joiner Sockets with Detent Dimples (All 4 outer side walls)
    dt_top_w = 16.0 * SCALE
    dt_bot_w = 10.0 * SCALE
    dt_depth = 8.0 * SCALE
    dt_height = t - (2.0 * SCALE)

    # Create master dovetail cutter
    poly_pts = [
        App.Vector(-dt_top_w / 2.0, 0, 0),
        App.Vector(dt_top_w / 2.0, 0, 0),
        App.Vector(dt_bot_w / 2.0, dt_depth, 0),
        App.Vector(-dt_bot_w / 2.0, dt_depth, 0),
        App.Vector(-dt_top_w / 2.0, 0, 0),
    ]
    dt_wire = Part.makePolygon(poly_pts)
    dt_face = Part.Face(dt_wire)
    dt_cutter = dt_face.extrude(App.Vector(0, 0, dt_height))

    # Add detent locking dimple cutter to dovetail socket
    dimple = Part.makeCylinder(JOINER_DETENT * 1.5, dt_top_w, App.Vector(0, dt_depth / 2.0, dt_height / 2.0), App.Vector(1, 0, 0))
    dt_cutter = dt_cutter.fuse(dimple)

    # Place dovetail cutters on 4 side walls (Pointing INTO each wall)
    dovetail_cuts = []
    # Front wall (Y=0) -> cuts in +Y direction
    dt_front = dt_cutter.copy()
    dt_front.Placement = App.Placement(App.Vector(w / 2.0, -0.1, (t - dt_height) / 2.0), App.Rotation(0, 0, 0))
    dovetail_cuts.append(dt_front)

    # Back wall (Y=h) -> cuts in -Y direction
    dt_back = dt_cutter.copy()
    dt_back.Placement = App.Placement(App.Vector(w / 2.0, h + 0.1, (t - dt_height) / 2.0), App.Rotation(App.Vector(0, 0, 1), 180))
    dovetail_cuts.append(dt_back)

    # Left wall (X=0) -> cuts in +X direction
    dt_left = dt_cutter.copy()
    dt_left.Placement = App.Placement(App.Vector(-0.1, h / 2.0, (t - dt_height) / 2.0), App.Rotation(App.Vector(0, 0, 1), -90))
    dovetail_cuts.append(dt_left)

    # Right wall (X=w) -> cuts in -X direction
    dt_right = dt_cutter.copy()
    dt_right.Placement = App.Placement(App.Vector(w + 0.1, h / 2.0, (t - dt_height) / 2.0), App.Rotation(App.Vector(0, 0, 1), 90))
    dovetail_cuts.append(dt_right)

    dovetail_compound = Part.makeCompound(dovetail_cuts)
    main_shell = main_shell.cut(dovetail_compound)

    # 8. Elephant's Foot Relief Chamfer along bottom outer edges (0.4mm)
    try:
        bottom_edges = []
        for edge in main_shell.Edges:
            bb = edge.BoundBox
            if abs(bb.ZMin) < 0.001 and abs(bb.ZMax) < 0.001:
                bottom_edges.append(edge)
        if bottom_edges:
            main_shell = main_shell.makeChamfer(ELEPHANTS_FOOT_CHAMFER, bottom_edges)
    except Exception as e:
        print(f"Warning: Elephant foot chamfer skipped on base module: {e}")

    return main_shell

def export_part():
    """Exports STEP and STL files to EXPORT_DIR and adds shape to FreeCAD document."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    shape = construct_base_module()

    doc = App.ActiveDocument or App.newDocument("Doc")
    obj = doc.addObject("Part::Feature", "Part01BaseModule")
    obj.Shape = shape
    doc.recompute()

    step_path = os.path.join(EXPORT_DIR, "part_01_base_module.step")
    stl_path  = os.path.join(EXPORT_DIR, "part_01_base_module.stl")

    shape.exportStep(step_path)
    shape.exportStl(stl_path)

    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()
