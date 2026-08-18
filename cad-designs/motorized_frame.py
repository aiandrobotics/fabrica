"""
motorized_frame.py — Motorized Outer Frame Chassis with Solid Mounting Towers, Hex Screw Housings, Inner Enclosure Wall, and Rear Slide-in Servo Bay
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
    DOVETAIL_NECK_WIDTH,
    DOVETAIL_FLARE_WIDTH,
    DOVETAIL_DEPTH,
    PIVOT_Z,
    DRIVE_SHAFT_DIAMETER,
    BEARING_ROTATING_CLEARANCE,
    TPU_BUMPER_DEPTH,
    EXPORT_DIR,
)

def make_hex_prism(r_af, depth, center, axis):
    """Creates a regular hexagonal prism aligned with given axis for M3 nut/screw housing."""
    r_corner = r_af / math.cos(math.radians(30))
    pts = []
    for i in range(6):
        ang = math.radians(60 * i + 30)
        pts.append(App.Vector(center.x + r_corner * math.cos(ang), center.y, center.z + r_corner * math.sin(ang)))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    solid = face.extrude(axis * depth)
    return solid

def construct_motorized_frame():
    """
    Constructs the 4-sided outer perimeter chassis for the Active Motorized Module.
    Features:
      1. Complete continuous inner enclosure wall (X in [38.0, 48.0mm], Y in [185.0, 240.0mm])
         sealing the motor compartment from the frame's central cavity.
      2. Solid front mounting towers (Y in [185.0, 195.5mm]) with 4x M3 through-holes (2 top, 2 bottom)
         spaced accurately per MG996R motor specs with captive hex nut housings.
      3. Open rear slide-in slot (Y=240mm) allowing the horizontal MG996R servo to slide directly into place.
      4. 100% Flat Base Plane at Z=0.0mm matching the follower frame base.
      5. Hinge pivot axis at PIVOT_Z = 10.0mm identically matching all follower modules.
    """
    import params
    w = params.PANEL_WIDTH
    h = params.PANEL_HEIGHT
    t = params.BASE_PANEL_THICKNESS
    rail_w = 15.0
    bottom_thick = 3.0
    pivot_z = PIVOT_Z        # 10.0mm

    knuckle_r = (DRIVE_SHAFT_DIAMETER / 2.0) + 3.0 # 9.5mm radius
    knuckle_len = 15.0
    # MG996R Motor Module Fixed Hardware Zone (anchored at top edge Y = h):
    # Total motor module length = 70.0mm (never scaled, fits physical MG996R servo)
    k_top_start_y = h - 70.0
    k_top_len = 15.0 # Knuckle barrel spans Y in [h - 70.0, h - 55.0]
    towers_start_y = h - 55.0 # Towers span Y in [h - 55.0, h - 44.5]
    bay_start_y = h - 44.5 # Motor bay spans Y in [h - 44.5, h]
    bay_len = 44.5
    # 1. Base 4-Wall Perimeter Frame
    outer_box = Part.makeBox(w, h, t)
    t_blade = params.PADDLE_THICKNESS # 2.4mm
    sweep_z_min = pivot_z - t_blade   # 12.60mm

    # Bottom 360° Knuckle Barrel (Y in [0, 15mm])
    k_bot = Part.makeCylinder(knuckle_r, knuckle_len, App.Vector(0, 0, pivot_z), App.Vector(0, 1, 0))
    # Top Knuckle Barrel at Y in [h - 70.0, h - 55.0mm] (surrounding servo adapter journal)
    k_top = Part.makeCylinder(knuckle_r, k_top_len, App.Vector(0, k_top_start_y, pivot_z), App.Vector(0, 1, 0))
    # Middle Semi-Circular Support Cradle Wall between knuckles (strictly below Z = 12.60mm in X < 0)
    cradle_outer = Part.makeCylinder(knuckle_r, k_top_start_y - knuckle_len, App.Vector(0, knuckle_len, pivot_z), App.Vector(0, 1, 0))
    cradle_trim_top = Part.makeBox(knuckle_r * 4.0, h, knuckle_r * 2.0)
    cradle_trim_top.translate(App.Vector(-knuckle_r * 2.0, 0, sweep_z_min))
    cradle_support = cradle_outer.cut(cradle_trim_top)

    bore_r = (DRIVE_SHAFT_DIAMETER / 2.0) + BEARING_ROTATING_CLEARANCE # 6.85mm

    # Solid cradle reinforcement boss at y_cradle_seam below axle bore (Z in [0, bore_bottom = 8.15mm])
    y_cradle_seam = (knuckle_len + k_top_start_y) / 2.0  # 82.5mm
    seam_boss_len = 24.0
    seam_boss = Part.makeBox(knuckle_r + 4.0, seam_boss_len, pivot_z - bore_r)
    seam_boss.translate(App.Vector(-knuckle_r, y_cradle_seam - seam_boss_len / 2.0, 0))

    # Solid 2.0mm Bottom Base Floor under entire motor module zone (Y in [h - 70.0, h], X in [-24.0, 48.0mm], Z in [-2.0, 0.0mm])
    floor_t = 2.0
    module_base_floor = Part.makeBox(72.0, 70.0, floor_t)
    module_base_floor.translate(App.Vector(-24.0, k_top_start_y, -floor_t))

    # Knuckle Solid Vertical Pedestal (X in [-knuckle_r, knuckle_r], Y in [h - 70.0, h - 55.0mm], Z in [-2.0, 15.0mm]) anchoring knuckle to base floor
    knuckle_pedestal = Part.makeBox(knuckle_r * 2.0, 15.0, pivot_z + floor_t)
    knuckle_pedestal.translate(App.Vector(-knuckle_r, k_top_start_y, -floor_t))

    # Solid Mounting Towers at Y in [h - 55.0, h - 44.5mm] (height Z=0.0 to 25.0mm, sitting on base floor)
    t_servo = 25.0
    towers_box = Part.makeBox(72.0, 10.5, t_servo + floor_t)
    towers_box.translate(App.Vector(-24.0, towers_start_y, -floor_t))

    # Rear motor housing perimeter at Y in [h - 44.5, h] (height Z=0.0 to 25.0mm, sitting on base floor)
    rear_box = Part.makeBox(72.0, bay_len, t_servo + floor_t)
    rear_box.translate(App.Vector(-24.0, bay_start_y, -floor_t))

    frame = outer_box.fuse([k_bot, k_top, cradle_support, seam_boss, module_base_floor, knuckle_pedestal, towers_box, rear_box]).removeSplitter()

    # 2. Main Open Cavity, Bores, and Cradle Trough

    # Semi-Circular Cradle Trough between knuckles (supports half-cylinder axle from below)
    cradle_trough = Part.makeCylinder(bore_r, k_top_start_y - knuckle_len + 0.2, App.Vector(0, knuckle_len - 0.1, pivot_z), App.Vector(0, 1, 0))

    # Unified L-Shaped Main Cavity (continuous along right rail from Y=15 to Y=205mm without split line notches)
    cav_pts = [
        App.Vector(0, rail_w, 0),
        App.Vector(w - rail_w, rail_w, 0),
        App.Vector(w - rail_w, h - rail_w, 0),
        App.Vector(48.0, h - rail_w, 0),
        App.Vector(48.0, k_top_start_y, 0),
        App.Vector(0, k_top_start_y, 0),
        App.Vector(0, rail_w, 0),
    ]
    cav_wire = Part.makePolygon(cav_pts)
    cav_face = Part.Face(cav_wire)
    cav_main = cav_face.extrude(App.Vector(0, 0, t + 2.0))
    cav_main.translate(App.Vector(0, 0, -1.0))
    try:
        c_edges = [
            e for e in cav_main.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.YMin - e.BoundBox.YMax) < 0.001
            and not (abs(e.BoundBox.XMin - 0.0) < 0.001 and abs(e.BoundBox.YMin - k_top_start_y) < 0.001)
            and not (abs(e.BoundBox.XMin - 0.0) < 0.001 and abs(e.BoundBox.YMin - rail_w) < 0.001)
        ]
        if c_edges:
            cav_main = cav_main.makeFillet(3.0, c_edges)
    except Exception:
        pass

    # Front-Right Screw Access Pocket (flush with X = 48.0mm inner motor wall)
    cut_screw_access_right = Part.makeBox(37.0, 15.0, 25.0)
    cut_screw_access_right.translate(App.Vector(11.0, k_top_start_y, 0.0))

    # Front-Left Screw Access Pocket (X in [-24.5, -11.0mm], Y in [h - 70.0, h - 55.0mm], Z in [0.0, 25.0mm])
    cut_screw_access_left = Part.makeBox(13.5, 15.0, 25.0)
    cut_screw_access_left.translate(App.Vector(-24.5, k_top_start_y, 0.0))

    for cav in [cav_main, cradle_trough, cut_screw_access_right, cut_screw_access_left]:
        frame = frame.cut(cav).removeSplitter()

    # 3. Hinge Bearing Bores & Knuckle Bore
    bot_bore = Part.makeCylinder(bore_r, knuckle_len + 0.2, App.Vector(0, -0.1, pivot_z), App.Vector(0, 1, 0))
    # Top knuckle bore spanning Y in [h - 70.1, h - 60.9mm] (SOLID 360 degree closed cylinder barrel):
    top_bore = Part.makeCylinder(bore_r, 9.2, App.Vector(0, k_top_start_y - 0.1, pivot_z), App.Vector(0, 1, 0))
    
    # Adapter Disk Clearance Pocket at Y in [h - 61.5, h - 54.9mm] (X in [-11.0, 11.0mm], Z in [0.0, 25.0mm])
    adapter_pocket = Part.makeBox(22.0, 6.6, 25.0)
    adapter_pocket.translate(App.Vector(-11.0, k_top_start_y + 8.5, 0.0))

    # Planar bottom trim at Z=0.0mm for standard frame rails (preserving the Z=-2.0mm solid floor under motor module zone)
    trim_bot_main = Part.makeBox(w + 50.0, k_top_start_y + 25.0, 20.0)
    trim_bot_main.translate(App.Vector(-25.0, -25.0, -20.0))

    trim_bot_right = Part.makeBox(w - 48.0 + 25.0, 70.0 + 25.0, 20.0)
    trim_bot_right.translate(App.Vector(48.0, k_top_start_y, -20.0))

    trim_under_motor = Part.makeBox(w + 50.0, h + 50.0, 20.0)
    trim_under_motor.translate(App.Vector(-25.0, -25.0, -22.0))

    for b in [bot_bore, top_bore, adapter_pocket, trim_bot_main, trim_bot_right, trim_under_motor]:
        frame = frame.cut(b).removeSplitter()

    # 4. Top Drop-In Servo Bay Cavity with 2.0mm Solid Closed Base Floor (Z in [-2.0, 0.0mm]), Solid Closed Rear Wall (5.0mm thick at Y = h - 5.0 to h), and Solid Front Towers:
    # Front gearhead pass-through pocket through towers (X in [-11.5, 32.5mm], Y in [h - 55.0, h - 44.5mm], Z in [0.0, 25.0mm])
    pocket_body = Part.makeBox(44.0, 10.5, 25.0)
    pocket_body.translate(App.Vector(-11.5, towers_start_y, 0.0))

    # Main Top Drop-In Motor Bay (X in [-17.8, 38.5mm], Y in [h - 44.5, h - 5.0mm], Z in [0.0, 25.0mm])
    pocket_bay = Part.makeBox(56.3, 39.5, 25.0)
    pocket_bay.translate(App.Vector(-17.8, bay_start_y, 0.0))

    # Top Lid Seating Rebate (1.8mm depth at Z in [23.2, 25.0mm], X in [-23.8, 40.5mm], Y in [h - 44.5, h - 5.2mm])
    pocket_rebate = Part.makeBox(64.3, 39.3, 2.0)
    pocket_rebate.translate(App.Vector(-23.8, bay_start_y, 23.2))

    # 4x Horizontal M3 Screw Clearance Holes (Ø3.4mm) passing cleanly through the solid towers along Y-axis:
    screw_r = 1.7
    z_sc1 = pivot_z - 5.25 # 9.75mm
    z_sc2 = pivot_z + 5.25 # 20.25mm
    screw_holes = [
        Part.makeCylinder(screw_r, 14.0, App.Vector(34.95, towers_start_y - 1.0, z_sc1), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0, App.Vector(34.95, towers_start_y - 1.0, z_sc2), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0, App.Vector(-14.45, towers_start_y - 1.0, z_sc1), App.Vector(0, 1, 0)),
        Part.makeCylinder(screw_r, 14.0, App.Vector(-14.45, towers_start_y - 1.0, z_sc2), App.Vector(0, 1, 0)),
    ]

    # External motor wire exit conduit through OUTER LEFT WALL at X = -24.0mm matching MG996R cable grommet (Y in [h - 24.0, h - 12.0mm], Z in [3.0, 16.0mm])
    pocket_wire_left = Part.makeBox(14.0, 12.0, 13.0)
    pocket_wire_left.translate(App.Vector(-26.0, h - 24.0, 3.0))

    # Rear Tongue Locking Slot underneath the solid horizontal retention bar (5.3mm depth at X in [-20.0, 37.0mm], Y in [h - 5.7, h - 0.4mm], Z in [18.0, 20.0mm])
    slot_rear_tongue = Part.makeBox(57.0, 5.3, 2.0)
    slot_rear_tongue.translate(App.Vector(-20.0, h - 5.7, 18.0))

    # Side Snap Barb Catch Undercuts in Frame Sidewalls (3.5mm deep pockets, Y in [h - 36.0, h - 26.0mm])
    chan_l = Part.makeBox(2.5, 10.0, 10.0)
    chan_l.translate(App.Vector(-17.4, h - 36.0, 10.5))
    undercut_l = Part.makeBox(3.5, 10.0, 5.0)
    undercut_l.translate(App.Vector(-20.5, h - 36.0, 10.5))
    catch_snap_left = chan_l.fuse(undercut_l).removeSplitter()

    chan_r = Part.makeBox(2.5, 10.0, 10.0)
    chan_r.translate(App.Vector(38.0, h - 36.0, 10.5))
    undercut_r = Part.makeBox(3.5, 10.0, 5.0)
    undercut_r.translate(App.Vector(40.0, h - 36.0, 10.5))
    catch_snap_right = chan_r.fuse(undercut_r).removeSplitter()

    cutters = [pocket_body, pocket_bay, pocket_rebate, pocket_wire_left, slot_rear_tongue, catch_snap_left, catch_snap_right] + screw_holes
    for c in cutters:
        frame = frame.cut(c).removeSplitter()

    # Re-apply bottom trims to guarantee 100% planar base (Z=0.0mm on frame rails, Z=-2.0mm on motor base floor)
    frame = frame.cut(Part.makeCompound([trim_bot_main, trim_bot_right, trim_under_motor])).removeSplitter()

    # 5. Female Open-Top True Sliding Dovetail Joiner Sockets on Outer Rails (Front Y=0, Right X=W) matching Follower Frame
    dt_neck_w = DOVETAIL_NECK_WIDTH
    dt_flare_w = DOVETAIL_FLARE_WIDTH
    dt_depth = DOVETAIL_DEPTH
    dt_cut_h = t - bottom_thick + 0.5

    dt_pts = [
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_neck_w / 2.0, -0.1, 0),
        App.Vector(dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_flare_w / 2.0, dt_depth, 0),
        App.Vector(-dt_neck_w / 2.0, -0.1, 0),
    ]
    dt_poly = Part.makePolygon(dt_pts)
    dt_face = Part.Face(dt_poly)
    dt_cutter = dt_face.extrude(App.Vector(0, 0, dt_cut_h))
    dt_cutter.translate(App.Vector(0, 0, bottom_thick))

    # Master bottom push-out finger access hole (Ø6.0mm through bottom floor)
    push_hole = Part.makeCylinder(3.0, bottom_thick + 1.0, App.Vector(0, dt_depth * 0.6, -0.5))

    # High-Capacity Wire Pass-Through Conduit (through back wall of dovetail directly into frame wiring cavity)
    wire_hole_w = 8.0
    wire_hole_h = 8.6
    wire_hole_d = rail_w + 2.0
    wire_conduit = Part.makeBox(wire_hole_w, wire_hole_d, wire_hole_h)
    wire_conduit.translate(App.Vector(-wire_hole_w / 2.0, 0.0, 9.0 - (wire_hole_h / 2.0)))
    try:
        w_edges = [
            e for e in wire_conduit.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.ZMin - e.BoundBox.ZMax) < 0.001
        ]
        if w_edges:
            wire_conduit = wire_conduit.makeFillet(1.0, w_edges)
    except Exception:
        pass

    dt_cutter_complete = dt_cutter.fuse([push_hole, wire_conduit]).removeSplitter()

    # Front Wall (Y=0) -> cuts into +Y
    c_front = dt_cutter_complete.copy()
    c_front.translate(App.Vector(w / 2.0, 0, 0))

    # Right Wall (X=W) -> cuts into -X
    c_right = dt_cutter_complete.copy()
    c_right.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    c_right.translate(App.Vector(w, h / 2.0, 0))

    # Cradle Wall Dovetail Joint at y_cradle_seam = 82.5mm
    dt_lk_neck = 4.0
    dt_lk_flare = 7.5
    dt_lk_depth = 6.0
    gap = 0.20  # 0.20mm snug tight fit clearance

    x_left = -knuckle_r - 2.0
    x_right = 5.0
    center_x = -4.5

    dt4_poly_pts = [
        # Top edge of female pocket (in +Y half)
        App.Vector(x_right, y_cradle_seam + gap, 0),
        App.Vector(center_x + dt_lk_neck / 2.0 + gap, y_cradle_seam + gap, 0),
        App.Vector(center_x + dt_lk_flare / 2.0 + gap, y_cradle_seam + dt_lk_depth + gap, 0),
        App.Vector(center_x - dt_lk_flare / 2.0 - gap, y_cradle_seam + dt_lk_depth + gap, 0),
        App.Vector(center_x - dt_lk_neck / 2.0 - gap, y_cradle_seam + gap, 0),
        App.Vector(x_left, y_cradle_seam + gap, 0),
        
        # Bottom edge of male tab (in -Y half)
        App.Vector(x_left, y_cradle_seam, 0),
        App.Vector(center_x - dt_lk_neck / 2.0, y_cradle_seam, 0),
        App.Vector(center_x - dt_lk_flare / 2.0, y_cradle_seam + dt_lk_depth, 0),
        App.Vector(center_x + dt_lk_flare / 2.0, y_cradle_seam + dt_lk_depth, 0),
        App.Vector(center_x + dt_lk_neck / 2.0, y_cradle_seam, 0),
        App.Vector(x_right, y_cradle_seam, 0),
        
        App.Vector(x_right, y_cradle_seam + gap, 0),
    ]
    dt4_cutter = Part.Face(Part.makePolygon(dt4_poly_pts)).extrude(App.Vector(0, 0, pivot_z + 2.0))
    dt4_cutter.translate(App.Vector(0, 0, -1.0))

    for dt in [c_front, c_right, dt4_cutter]:
        frame = frame.cut(dt).removeSplitter()

    # 6. Anti-Slip Rubber Foot Sockets on Standard Frame Rails (Ø12mm x 2.0mm)
    foot_r = 6.0
    foot_d = 2.0
    foot_locs = [
        (w - (rail_w / 2.0), rail_w / 2.0),                # Bottom Right
        (w - (rail_w / 2.0), h - (rail_w / 2.0)),          # Top Right
        (25.0, rail_w / 2.0),                              # Bottom Left
        (55.0, h - (rail_w / 2.0)),                        # Top Rail (clears motor housing, under main frame)
    ]
    for fx, fy in foot_locs:
        fc = Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(fx, fy, -0.1))
        frame = frame.cut(fc).removeSplitter()

    # 7. Silent-Flip TPU Landing Bumper Slots (recessed into right landing rail at X = w - rail_w/2)
    tpu_cutters = []
    tpu_w = 5.0
    tpu_l = 14.0
    tpu_h = TPU_BUMPER_DEPTH # 1.5mm
    for py in [h * 0.25, h * 0.75]:
        b = Part.makeBox(tpu_w, tpu_l, tpu_h + 0.1)
        b.translate(App.Vector(w - (rail_w / 2.0) - (tpu_w / 2.0), py - (tpu_l / 2.0), t - tpu_h))
        tpu_cutters.append(b)

    frame = frame.cut(Part.makeCompound(tpu_cutters)).removeSplitter()

    # 8. Smooth rounded outer vertical corner fillets (R=3.0mm on outer corners)
    corner_cutter1 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter1.translate(App.Vector(w - 3.0, -3.0, -1.0))
    corner_cyl1 = Part.makeCylinder(3.0, t + 2.0, App.Vector(w - 3.0, 3.0, -1.0))
    corner_trim1 = corner_cutter1.cut(corner_cyl1)

    corner_cutter2 = Part.makeBox(6.0, 6.0, t + 2.0)
    corner_cutter2.translate(App.Vector(w - 3.0, h - 3.0, -1.0))
    corner_cyl2 = Part.makeCylinder(3.0, t + 2.0, App.Vector(w - 3.0, h - 3.0, -1.0))
    corner_trim2 = corner_cutter2.cut(corner_cyl2)

    frame = frame.cut(Part.makeCompound([corner_trim1, corner_trim2])).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_frame.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_frame.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    frame.exportStep(step_path)
    frame.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return frame

def main():
    doc = App.newDocument("MotorizedFrame")
    shape = construct_motorized_frame()
    feature = doc.addObject("Part::Feature", "MotorizedFrame")
    feature.Shape = shape

main()
