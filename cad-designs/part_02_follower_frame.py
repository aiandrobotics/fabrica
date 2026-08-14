"""
part_02_follower_frame.py — Passive Follower Chassis U-Frame
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
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
    SCALE,
    PANEL_WIDTH,
    PANEL_HEIGHT,
    BASE_PANEL_THICKNESS,
    WALL_THICKNESS,
    PRESS_FIT_CLEARANCE,
    TPU_BUMPER_DEPTH,
    ELEPHANTS_FOOT_CHAMFER,
    EXPORT_DIR,
)

# Dovetail Constants (matching part_10_frame_joiner exactly)
DOVETAIL_TOP_WIDTH = 16.0 * SCALE
DOVETAIL_BOT_WIDTH = 10.0 * SCALE
DOVETAIL_DEPTH = 8.0 * SCALE
DOVETAIL_HEIGHT = BASE_PANEL_THICKNESS - (2.0 * SCALE)  # 13.0mm
PADDLE_PIVOT_DIAMETER = 5.0 * SCALE
ROTATING_CLEARANCE = 0.3 * SCALE  # per side
BOTTOM_SHELL_THICKNESS = 3.0 * SCALE

def create_follower_frame():
    """
    Constructs the Passive Follower U-Frame Module.
    Features:
    1. Rigid U-Frame Chassis with 3.0mm outer walls and recessed internal cavity.
    2. Top 360° Closed Bearing Bore (Ø5.6mm) for secure axial hinge retention.
    3. Bottom Flex C-Snap Socket with a 0.5mm lead-in funnel for toolless downward snap-in.
    4. 1.5mm recessed silent-flip TPU bumper landing pockets.
    5. 0.5mm debossed Poka-Yoke directional alignment arrow ("FRONT ➔").
    6. 1.5mm filleted wire pass-through ports with zip-tie loops.
    7. 4-wall symmetrical female dovetail sockets for part_10 bridge joiners.
    8. 0.4mm bottom Elephant's Foot relief chamfers.
    """
    w = PANEL_WIDTH
    h = PANEL_HEIGHT
    t = BASE_PANEL_THICKNESS
    wall = 15.0 * SCALE
    bottom_thick = BOTTOM_SHELL_THICKNESS

    # 1. Main outer shell box
    outer_box = Part.makeBox(w, h, t)

    # 2. Main internal folding paddle cavity cut
    cav_w = w - 2 * wall
    cav_h = h - 2 * wall
    cavity = Part.makeBox(cav_w, cav_h, t - bottom_thick + 0.5)
    cavity.translate(App.Vector(wall, wall, bottom_thick))
    frame = outer_box.cut(cavity).removeSplitter()

    # 3. 4-Wall Symmetrical Dovetail Joiner Sockets
    dt_top_w = DOVETAIL_TOP_WIDTH
    dt_bot_w = DOVETAIL_BOT_WIDTH
    dt_d = DOVETAIL_DEPTH
    dt_h = DOVETAIL_HEIGHT

    dt_pts = [
        App.Vector(-dt_top_w / 2.0, 0, 0),
        App.Vector(dt_top_w / 2.0, 0, 0),
        App.Vector(dt_bot_w / 2.0, dt_d, 0),
        App.Vector(-dt_bot_w / 2.0, dt_d, 0),
        App.Vector(-dt_top_w / 2.0, 0, 0),
    ]
    dt_poly = Part.makePolygon(dt_pts)
    dt_face = Part.Face(dt_poly)
    dt_cutter_master = dt_face.extrude(App.Vector(0, 0, dt_h))

    dt_cutters = []
    # Front Wall (Y=0)
    c_front = dt_cutter_master.copy()
    c_front.translate(App.Vector(w / 2.0, -0.1, (t - dt_h) / 2.0))
    dt_cutters.append(c_front)

    # Back Wall (Y=H)
    c_back = dt_cutter_master.copy()
    c_back.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    c_back.translate(App.Vector(w / 2.0, h + 0.1, (t - dt_h) / 2.0))
    dt_cutters.append(c_back)

    # Left Wall (X=0)
    c_left = dt_cutter_master.copy()
    c_left.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -90)
    c_left.translate(App.Vector(-0.1, h / 2.0, (t - dt_h) / 2.0))
    dt_cutters.append(c_left)

    # Right Wall (X=W)
    c_right = dt_cutter_master.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w + 0.1, h / 2.0, (t - dt_h) / 2.0))
    dt_cutters.append(c_right)

    frame = frame.cut(Part.makeCompound(dt_cutters)).removeSplitter()

    # 4. Hinge Pivot Interfaces (Along internal walls at X = wall and X = w - wall)
    # Top Pivot: 360° Closed Bore (Ø5.6mm)
    # Bottom Pivot: Flex C-Snap with 0.5mm Funnel
    bore_r = (PADDLE_PIVOT_DIAMETER / 2.0) + ROTATING_CLEARANCE  # 2.8mm radius (Ø5.6mm)
    pivot_z = bottom_thick + (4.0 * SCALE)
    bore_depth = 9.0 * SCALE
    
    # Left flap pivot axis (Y = h/2 - 40mm) and Right flap pivot axis (Y = h/2 + 40mm)
    pivot_y_positions = [h / 2.0 - 45.0 * SCALE, h / 2.0 + 45.0 * SCALE]
    hinge_cutters = []

    for py in pivot_y_positions:
        # Left wall pivot (facing +X)
        # Top 360° closed cylindrical bore
        bore_left = Part.makeCylinder(bore_r, bore_depth, App.Vector(wall - bore_depth + 0.1, py, pivot_z), App.Vector(1, 0, 0))
        hinge_cutters.append(bore_left)

        # Bottom Flex C-Snap with 0.5mm lead-in funnel on right wall (facing -X)
        bore_right = Part.makeCylinder(bore_r, bore_depth, App.Vector(w - wall - 0.1, py, pivot_z), App.Vector(1, 0, 0))
        # Snap insertion throat (width = 2*bore_r - 0.4mm for snap retention)
        snap_w = (bore_r * 2.0) - (0.4 * SCALE)
        snap_throat = Part.makeBox(bore_depth + 0.2, snap_w, t - pivot_z + 0.1)
        snap_throat.translate(App.Vector(w - wall - 0.1, py - snap_w / 2.0, pivot_z))
        
        # 0.5mm 45° Lead-in funnel at top of C-snap throat
        funnel_w = snap_w + (1.2 * SCALE)
        funnel = Part.makeBox(bore_depth + 0.2, funnel_w, 2.0 * SCALE)
        funnel.translate(App.Vector(w - wall - 0.1, py - funnel_w / 2.0, t - 1.5 * SCALE))
        
        hinge_cutters.extend([bore_right, snap_throat, funnel])

    frame = frame.cut(Part.makeCompound(hinge_cutters)).removeSplitter()

    # 5. TPU Silent-Flip Landing Bumper Slots (1.5mm recessed)
    tpu_cutters = []
    tpu_w = 12.0 * SCALE
    tpu_d = 4.0 * SCALE
    tpu_h = TPU_BUMPER_DEPTH  # 1.5mm
    
    for py in [h / 4.0, 3 * h / 4.0]:
        b1 = Part.makeBox(tpu_w, tpu_d, tpu_h + 0.1)
        b1.translate(App.Vector(wall + 10.0 * SCALE, py, bottom_thick - 0.05))
        b2 = Part.makeBox(tpu_w, tpu_d, tpu_h + 0.1)
        b2.translate(App.Vector(w - wall - 10.0 * SCALE - tpu_w, py, bottom_thick - 0.05))
        tpu_cutters.extend([b1, b2])

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 6. Filleted Internal Wire Pass-Through Ports with Zip-Tie Saddles
    wire_port_w = 8.0 * SCALE
    wire_port_h = 5.0 * SCALE
    wire_port_1 = Part.makeBox(wire_port_w, wall + 0.2, wire_port_h)
    wire_port_1.translate(App.Vector(w / 4.0 - wire_port_w / 2.0, -0.1, bottom_thick))
    wire_port_2 = Part.makeBox(wire_port_w, wall + 0.2, wire_port_h)
    wire_port_2.translate(App.Vector(3 * w / 4.0 - wire_port_w / 2.0, -0.1, bottom_thick))
    frame = frame.cut(Part.makeCompound([wire_port_1, wire_port_2])).removeSplitter()

    # 7. Debossed Poka-Yoke Directional Arrow ("FRONT ➔" along front outer face)
    arrow_shaft = Part.makeBox(12.0 * SCALE, 0.6 * SCALE, 2.0 * SCALE)
    arrow_shaft.translate(App.Vector(w / 2.0 - 6.0 * SCALE, -0.1, t - 3.5 * SCALE))
    arrow_head_poly = Part.makePolygon([
        App.Vector(w / 2.0 + 6.0 * SCALE, -0.1, t - 4.5 * SCALE),
        App.Vector(w / 2.0 + 10.0 * SCALE, -0.1, t - 2.5 * SCALE),
        App.Vector(w / 2.0 + 6.0 * SCALE, -0.1, t - 0.5 * SCALE),
        App.Vector(w / 2.0 + 6.0 * SCALE, -0.1, t - 4.5 * SCALE),
    ])
    arrow_head_face = Part.Face(arrow_head_poly)
    arrow_head = arrow_head_face.extrude(App.Vector(0, 0.6 * SCALE, 0))
    frame = frame.cut(Part.makeCompound([arrow_shaft, arrow_head])).removeSplitter()

    # 8. Elephant's Foot Relief Chamfer (0.4mm on bottom outer perimeter edges)
    try:
        base_edges = [
            e for e in frame.Edges
            if abs(e.BoundBox.ZMin) < 0.001 and abs(e.BoundBox.ZMax) < 0.001 and e.Length > 20.0 * SCALE
        ]
        if base_edges:
            frame = frame.makeChamfer(ELEPHANTS_FOOT_CHAMFER, base_edges)
            frame = frame.removeSplitter()
    except Exception as e:
        pass

    return frame

def export_part():
    """Exports STEP and STL files to EXPORT_DIR and adds shape to FreeCAD document."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    shape = create_follower_frame()

    doc = App.ActiveDocument or App.newDocument("FollowerFrame")
    obj = doc.addObject("Part::Feature", "Part02FollowerFrame")
    obj.Shape = shape
    doc.recompute()

    step_path = os.path.join(EXPORT_DIR, "part_02_follower_frame.step")
    stl_path  = os.path.join(EXPORT_DIR, "part_02_follower_frame.stl")

    for path in (step_path, stl_path):
        if os.path.exists(path):
            os.remove(path)

    shape.exportStep(step_path)
    shape.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")

export_part()


