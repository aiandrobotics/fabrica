"""
Fabrica Cloth Folding Robot - Interface Case (Compact Triple-Board Enclosure with Integrated Dovetail)
Part of Phase 5: Interface Module & Electronics Enclosure.

Features:
1. Compact flat horizontal rectangular box chassis (140.0 x 120.0 x 45.0mm)
   - Width reduced to 140.0mm (41% narrower than 220mm frame width) by arranging PDB vertically alongside ESP32 & PCA9685
   - 45.0mm chassis height provides >25mm of generous overhead space for wire routing
2. Houses 3 Circuit Boards in Compact Spatial Layout:
   - Power Distribution Board (PDB) / 5V-6V Step-Down Buck Module (M3 standoffs @ 24.0 x 37.0mm pitch, Left Bay @ X=25mm)
   - ESP32 DevKit V1 / NodeMCU-32S (M3 standoffs @ 46.0 x 23.0mm pitch + perimeter cradle, Front-Right Bay @ X=88mm, Y=32mm)
   - PCA9685 16-Channel 12-Bit PWM Servo Driver Board (M2.5 standoffs @ 55.88 x 19.05mm pitch, Rear-Right Bay @ X=88mm, Y=88mm)
3. Direct Wall Snap-Lock Retention Windows (Zero Internal Boss Clutter):
   - 4x Retention windows cut directly through the front and rear perimeter walls (2 on Front, 2 on Rear @ X=35, 105mm)
   - 100% unobstructed, smooth interior chamber maximizing cable routing volume
4. 16 Discrete Motor Wire Slots (1 Slot Per Servo Motor):
   - 16x vertical wire ports (4.0mm wide x 16.0mm high, extending from Z=8.0mm to Z=24.0mm)
   - Solid 3.0mm structural pillars between adjacent slots (7.0mm pitch) aligned directly with PCA9685 pin headers
   - Leaves a solid 14.0mm header beam below snap windows
5. Integrated External Male Sliding Dovetail Key with Standard Wire Raceway (@ X = 70.0mm / Centered):
   - Flared male sliding dovetail key matching frame_joiner geometry (11.6mm neck -> 17.6mm flare, 12mm height)
   - High-capacity internal wire raceway conduit (6.8 x 8.6mm with 1.0mm fillets) passing directly through the dovetail arm into the enclosure
   - Slides directly into the female dovetail socket of any Fabrica robot base frame module without loose joiners
6. Ports & Thermal Management:
   - High-current DC Power Barrel Jack (Ø11.5mm) on Left Wall (X=0) feeding PDB input directly
   - ESP32 USB programming / debug port cutout (12.0 x 7.5mm) on Front Wall (Y=0)
   - Passive convection chimney cooling slots directly below all 3 boards
   - 4x Anti-slip rubber foot sockets (Ø20.1 x 2.0mm)
   - Continuous 100% flush top perimeter rim
"""

import os
import sys
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part
import params

def construct_interface_case():
    """
    Constructs the compact monolithic 3D printable high-capacity flat rectangular electronics chassis
    with an integrated external male sliding dovetail key and continuous internal wire raceway.
    """
    w = params.INTERFACE_PANEL_WIDTH  # 140.0mm compact width
    d = params.INTERFACE_PANEL_HEIGHT  # 120.0mm
    h = 45.0  # 45.0mm spacious height for wiring
    wall_t = params.WALL_THICKNESS  # 3.0mm
    floor_t = 3.0  # 3.0mm solid bottom floor
    
    # 1. Main outer rectangular solid:
    outer_box = Part.makeBox(w, d, h)
    
    # 2. Hollow internal cavity (Completely smooth walls, 100% solid floor and rear wall):
    inner_cavity = Part.makeBox(w - 2 * wall_t, d - 2 * wall_t, h - floor_t + 2.0, App.Vector(wall_t, wall_t, floor_t))
    case_body = outer_box.cut(inner_cavity).removeSplitter()
    
    # 3. Internal Electronics Mounting (3 Distinct Functional Bays):
    # A) Power Distribution Board (PDB) Standoffs (Left Bay - Oriented Vertically along Y):
    pdb_cx = 25.0
    pdb_cy = 60.0
    pdb_pitch_x = 24.0
    pdb_pitch_y = 37.0
    pdb_standoff_h = 5.0
    pdb_boss_r = 3.0
    pdb_pilot_r = 1.3
    
    pdb_bosses = []
    for dx in [-pdb_pitch_x / 2.0, pdb_pitch_x / 2.0]:
        for dy in [-pdb_pitch_y / 2.0, pdb_pitch_y / 2.0]:
            bx = pdb_cx + dx
            by = pdb_cy + dy
            boss = Part.makeCylinder(pdb_boss_r, floor_t + pdb_standoff_h, App.Vector(bx, by, 0))
            pilot = Part.makeCylinder(pdb_pilot_r, pdb_standoff_h + 1.0, App.Vector(bx, by, floor_t))
            pdb_bosses.append(boss.cut(pilot))
            
    # B) ESP32 DevKit Standoffs & Universal Retention Cradle (Front-Right Bay - Oriented along Y):
    esp_cx = 88.0
    esp_cy = 35.0
    esp_pitch_x = 23.0
    esp_pitch_y = 46.0
    esp_standoff_h = 5.0
    esp_boss_r = 3.0
    esp_pilot_r = 1.3
    
    esp_bosses = []
    for dx in [-esp_pitch_x / 2.0, esp_pitch_x / 2.0]:
        for dy in [-esp_pitch_y / 2.0, esp_pitch_y / 2.0]:
            bx = esp_cx + dx
            by = esp_cy + dy
            boss = Part.makeCylinder(esp_boss_r, floor_t + esp_standoff_h, App.Vector(bx, by, 0))
            pilot = Part.makeCylinder(esp_pilot_r, esp_standoff_h + 1.0, App.Vector(bx, by, floor_t))
            esp_bosses.append(boss.cut(pilot))
            
    # ESP32 Perimeter Alignment Cradle:
    cradle_box = Part.makeBox(31.0, 54.0, 3.5, App.Vector(esp_cx - 15.5, esp_cy - 27.0, floor_t))
    cradle_pocket = Part.makeBox(29.0, 52.0, 4.0, App.Vector(esp_cx - 14.5, esp_cy - 26.0, floor_t))
    esp_cradle = cradle_box.cut(cradle_pocket)
    
    # C) PCA9685 16-Channel PWM Servo Driver Standoffs (Rear-Right Bay):
    pca_cx = 88.0
    pca_cy = 88.0
    pca_pitch_x = 55.88
    pca_pitch_y = 19.05
    pca_standoff_h = 5.0
    pca_boss_r = 2.5
    pca_pilot_r = 1.1
    
    pca_bosses = []
    for dx in [-pca_pitch_x / 2.0, pca_pitch_x / 2.0]:
        for dy in [-pca_pitch_y / 2.0, pca_pitch_y / 2.0]:
            bx = pca_cx + dx
            by = pca_cy + dy
            boss = Part.makeCylinder(pca_boss_r, floor_t + pca_standoff_h, App.Vector(bx, by, 0))
            pilot = Part.makeCylinder(pca_pilot_r, pca_standoff_h + 1.0, App.Vector(bx, by, floor_t))
            pca_bosses.append(boss.cut(pilot))
            
    elec_mounts = pdb_bosses + esp_bosses + [esp_cradle] + pca_bosses
    case_body = case_body.fuse(Part.makeCompound(elec_mounts)).removeSplitter()
    
    # 4. Integrated External Male Dovetail Key on Rear Wall (Centered at X = w / 2 = 70.0mm):
    dt_clearance = params.DOVETAIL_CLEARANCE  # 0.20mm
    gap = params.MODULE_GAP  # 20.0mm
    neck_w = params.DOVETAIL_NECK_WIDTH - (2.0 * dt_clearance)  # 11.60mm
    flare_w = params.DOVETAIL_FLARE_WIDTH - (2.0 * dt_clearance)  # 17.60mm
    dt_depth = params.DOVETAIL_DEPTH - dt_clearance  # 11.80mm
    dt_height = params.DOVETAIL_HEIGHT  # 12.0mm (Z in [3.0, 15.0mm])
    bridge_w = params.DOVETAIL_FLARE_WIDTH  # 18.0mm
    
    dt_x = w / 2.0  # 70.0mm
    y_seam = d  # 120.0mm
    y_frame_face = y_seam + gap  # 140.0mm
    y_tip = y_frame_face + dt_depth  # 151.80mm
    
    dt_pts = [
        App.Vector(dt_x - bridge_w / 2.0, y_seam - 1.0, 0),
        App.Vector(dt_x - bridge_w / 2.0, y_frame_face - 2.0, 0),
        App.Vector(dt_x - neck_w / 2.0, y_frame_face, 0),
        App.Vector(dt_x - flare_w / 2.0, y_tip, 0),
        App.Vector(dt_x + flare_w / 2.0, y_tip, 0),
        App.Vector(dt_x + neck_w / 2.0, y_frame_face, 0),
        App.Vector(dt_x + bridge_w / 2.0, y_frame_face - 2.0, 0),
        App.Vector(dt_x + bridge_w / 2.0, y_seam - 1.0, 0),
        App.Vector(dt_x - bridge_w / 2.0, y_seam - 1.0, 0),
    ]
    dt_wire = Part.makePolygon(dt_pts)
    dt_face = Part.Face(dt_wire)
    dt_male_solid = dt_face.extrude(App.Vector(0, 0, dt_height))
    dt_male_solid.translate(App.Vector(0, 0, params.DOVETAIL_FLOOR_THICKNESS))
    
    # 45 deg Lead-in entry chamfers at male tip:
    c_cutter1 = Part.makeBox(flare_w + 4.0, 3.0, 3.0, App.Vector(dt_x - flare_w / 2.0 - 2.0, y_tip - 1.5, params.DOVETAIL_FLOOR_THICKNESS - 1.5))
    c_cutter1.rotate(App.Vector(dt_x, y_tip, params.DOVETAIL_FLOOR_THICKNESS), App.Vector(1, 0, 0), 45)
    
    c_cutter2 = Part.makeBox(flare_w + 4.0, 3.0, 3.0, App.Vector(dt_x - flare_w / 2.0 - 2.0, y_tip - 1.5, params.DOVETAIL_FLOOR_THICKNESS + dt_height - 1.5))
    c_cutter2.rotate(App.Vector(dt_x, y_tip, params.DOVETAIL_FLOOR_THICKNESS + dt_height), App.Vector(1, 0, 0), -45)
    
    dt_male_solid = dt_male_solid.cut(Part.makeCompound([c_cutter1, c_cutter2])).removeSplitter()
    case_body = case_body.fuse(dt_male_solid).removeSplitter()
    
    # High-Capacity Internal Wire Raceway Conduit (6.8mm x 8.6mm with 1.0mm Fillets) matching frame_joiner:
    raceway_w = 6.8
    raceway_h = 8.6
    center_z = params.DOVETAIL_FLOOR_THICKNESS + (dt_height / 2.0)
    raceway_box = Part.makeBox(
        raceway_w,
        (y_tip - y_seam) + wall_t + 6.0,
        raceway_h,
        App.Vector(dt_x - raceway_w / 2.0, y_seam - wall_t - 2.0, center_z - (raceway_h / 2.0))
    )
    try:
        y_edges = [
            e for e in raceway_box.Edges
            if abs(e.BoundBox.XMin - e.BoundBox.XMax) < 0.001 and abs(e.BoundBox.ZMin - e.BoundBox.ZMax) < 0.001
        ]
        if y_edges:
            raceway_box = raceway_box.makeFillet(1.0, y_edges)
    except Exception:
        pass
        
    # 5. External Port & Wall Cutouts:
    # A) Direct Wall Snap Retention Holes (4x: 2 on Front Wall, 2 on Rear Wall @ X=35, 105mm):
    snap_hole_w = 12.0
    snap_hole_h = 3.5
    snap_z = h - 7.0  # 38.0mm to 41.5mm
    
    wall_snap_holes = []
    for sx in [35.0, 105.0]:
        f_hole = Part.makeBox(snap_hole_w, wall_t + 2.0, snap_hole_h, App.Vector(sx - snap_hole_w / 2.0, -1.0, snap_z))
        r_hole = Part.makeBox(snap_hole_w, wall_t + 2.0, snap_hole_h, App.Vector(sx - snap_hole_w / 2.0, d - wall_t - 1.0, snap_z))
        wall_snap_holes.extend([f_hole, r_hole])
        
    # B) Ports:
    # DC Power Barrel Jack (Ø11.5mm) on Left Wall (X=0) feeding PDB:
    dc_jack_r = params.DC_JACK_DIAMETER / 2.0
    dc_jack_y = pdb_cy  # 60.0mm
    dc_jack_z = 14.0
    dc_jack_cut = Part.makeCylinder(dc_jack_r, wall_t + 2.0, App.Vector(-1.0, dc_jack_y, dc_jack_z), App.Vector(1, 0, 0))
    
    # ESP32 Micro-USB / USB-C Port Cutout on Front Wall (Y=0):
    usb_w = 12.0
    usb_h = 7.5
    usb_z = floor_t + esp_standoff_h + 0.5
    usb_cut = Part.makeBox(usb_w, wall_t + 2.0, usb_h, App.Vector(esp_cx - usb_w / 2.0, -1.0, usb_z))
    
    # C) Relief and Cooling Slots:
    cooling_slots = []
    # PDB Cooling Slots:
    for i in [-1, 0, 1]:
        cooling_slots.append(Part.makeBox(20.0, 2.5, floor_t + 2.0, App.Vector(pdb_cx - 10.0, pdb_cy + i * 8.0 - 1.25, -1.0)))
    # ESP32 Cooling Slots:
    for i in [-1, 0, 1]:
        cooling_slots.append(Part.makeBox(36.0, 2.5, floor_t + 2.0, App.Vector(esp_cx - 18.0, esp_cy + i * 6.0 - 1.25, -1.0)))
    # PCA9685 Cooling Slots:
    for i in [-1, 0, 1]:
        cooling_slots.append(Part.makeBox(45.0, 2.5, floor_t + 2.0, App.Vector(pca_cx - 22.5, pca_cy + i * 6.0 - 1.25, -1.0)))
        
    # D) 4x Bottom Anti-Slip Rubber Feet Sockets (Ø20.1mm x 2.0mm):
    foot_r = params.FOOT_PAD_DIA / 2.0
    foot_d = params.FOOT_PAD_DEPTH
    foot_sockets = [
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(16.0, 16.0, -0.1)),
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(w - 16.0, 16.0, -0.1)),
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(16.0, d - 16.0, -0.1)),
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(w - 16.0, d - 16.0, -0.1)),
    ]
    
    # E) Standardized 16 Discrete Motor Wire Slots (1 Slot Per Servo Motor):
    # 16 slots of 4.0mm width x 16.0mm height (Z in [8.0, 24.0mm]) on 6.0mm pitch (2.0mm solid pillars)
    # Total span = 15 * 6.0 + 4.0 = 94.0mm, centered at pca_cx = 88.0mm (X in [41.0, 135.0mm])
    slot_w = 4.0
    slot_h = 16.0
    slot_pitch = 6.0
    slot_z_start = 8.0
    slot_start_x = pca_cx - (15 * slot_pitch + slot_w) / 2.0  # 41.0mm
    
    motor_slots = []
    for i in range(16):
        sx = slot_start_x + i * slot_pitch
        slot_cut = Part.makeBox(slot_w, wall_t + 4.0, slot_h, App.Vector(sx, d - wall_t - 2.0, slot_z_start))
        motor_slots.append(slot_cut)
        
    # F) 0.4mm Elephant's Foot Bed Relief Chamfer on bottom outer perimeter:
    ef_cutter = Part.makeBox(w + 10.0, d + 10.0, params.ELEPHANTS_FOOT_CHAMFER + 0.1, App.Vector(-5.0, -5.0, -0.05))
    ef_inner = Part.makeBox(w - 2 * params.ELEPHANTS_FOOT_CHAMFER, d - 2 * params.ELEPHANTS_FOOT_CHAMFER, params.ELEPHANTS_FOOT_CHAMFER + 0.2, App.Vector(params.ELEPHANTS_FOOT_CHAMFER, params.ELEPHANTS_FOOT_CHAMFER, -0.1))
    ef_ring = ef_cutter.cut(ef_inner)
    
    all_cuts = [usb_cut, dc_jack_cut, ef_ring, raceway_box] + wall_snap_holes + motor_slots + cooling_slots + foot_sockets
    case_body = case_body.cut(Part.makeCompound(all_cuts)).removeSplitter()
    
    return case_body

construct_controller_case = construct_interface_case  # Backward compatibility alias

def main():
    doc = App.newDocument("InterfaceCaseDoc")
    shape = construct_interface_case()
    
    out_dir = params.EXPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    step_path = os.path.join(out_dir, "interface_case.step")
    stl_path = os.path.join(out_dir, "interface_case.stl")
    shape.exportStep(step_path)
    shape.exportStl(stl_path)
    print("=== Interface Case Exported Successfully ===")
    print("STEP:", step_path)
    print("STL:", stl_path)
    print("BoundBox:", shape.BoundBox)
    print(f"Volume: {shape.Volume:.2f} mm3")
    
    feature = doc.addObject("Part::Feature", "InterfaceCase")
    feature.Shape = shape
    if hasattr(feature, "ViewObject") and feature.ViewObject:
        feature.ViewObject.ShapeColor = (0.2, 0.65, 0.35)
    return feature

main()
