"""
Fabrica Cloth Folding Robot - Interface Case (Triple-Board Electronics Enclosure)
Part of Phase 5: Interface Module & Electronics Enclosure.

Houses 3 Circuit Boards:
1. Power Distribution Board (PDB) / 5V-6V Step-Down Buck Module with screw terminals (M3 standoffs @ 37.0 x 24.0 mm pitch)
2. ESP32 DevKit V1 / NodeMCU-32S (M3 standoffs @ 46.0 x 23.0 mm pitch + perimeter cradle)
3. PCA9685 16-Channel 12-Bit PWM Servo Driver Board (M2.5 standoffs @ 55.88 x 19.05 mm pitch)

Connectivity, Thermal & Mounting Features:
4. High-current DC Power Barrel Jack (Ø11.5mm) aligned directly with PDB input
5. ESP32 USB programming / debug port cutout (12.0 x 7.5mm)
6. Passive convection chimney cooling slots directly below all 3 boards
7. Internal zip-tie cable strain-relief saddles for clean wiring harnesses
8. Standard sliding dovetail sockets for seamless grid attachment & hidden wire routing
9. 4x M3 corner fastener bosses for interface top deck retention
10. 4x Anti-slip rubber foot sockets (Ø20.1 x 2.0mm)
"""

import os
import sys
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part
import params

def create_dovetail_socket_cutter(neck_w, flare_w, depth, height):
    """Creates a female dovetail socket cutting tool."""
    poly_pts = [
        App.Vector(-neck_w / 2.0, 0.1, 0),
        App.Vector(neck_w / 2.0, 0.1, 0),
        App.Vector(flare_w / 2.0, -depth, 0),
        App.Vector(-flare_w / 2.0, -depth, 0),
        App.Vector(-neck_w / 2.0, 0.1, 0),
    ]
    wire = Part.makePolygon(poly_pts)
    face = Part.Face(wire)
    return face.extrude(App.Vector(0, 0, height))

def construct_interface_case():
    """
    Constructs the monolithic 3D printable lower electronics chassis.
    """
    w = params.PANEL_WIDTH  # 220.0mm
    d = params.INTERFACE_PANEL_HEIGHT  # 120.0mm
    wall_t = params.WALL_THICKNESS  # 3.0mm
    floor_t = 3.0  # 3.0mm solid bottom floor
    
    # 15° Angled height profile:
    # Front (Y=0): Z = 15.0mm (matching base chassis rail height)
    # Rear (Y=120): Z = 15.0 + 120 * tan(15°) = ~47.15mm
    angle_deg = params.CONTROL_DECK_ANGLE  # 15.0°
    angle_rad = math.radians(angle_deg)
    z_front = params.BASE_PANEL_THICKNESS  # 15.0mm
    z_rear = z_front + d * math.tan(angle_rad)  # ~47.15mm
    
    # 1. Main outer wedge solid (Extruded along X):
    yz_pts = [
        App.Vector(0, 0, 0),
        App.Vector(0, d, 0),
        App.Vector(0, d, z_rear),
        App.Vector(0, 0, z_front),
        App.Vector(0, 0, 0)
    ]
    yz_wire = Part.makePolygon(yz_pts)
    yz_face = Part.Face(yz_wire)
    outer_wedge = yz_face.extrude(App.Vector(w, 0, 0))
    
    # 2. Hollow internal cavity (Offset by 3.0mm walls and 3.0mm floor):
    yz_inner_pts = [
        App.Vector(0, wall_t, floor_t),
        App.Vector(0, d - wall_t, floor_t),
        App.Vector(0, d - wall_t, z_rear + 2.0),
        App.Vector(0, wall_t, z_front + 2.0),
        App.Vector(0, wall_t, floor_t)
    ]
    yz_inner_wire = Part.makePolygon(yz_inner_pts)
    yz_inner_face = Part.Face(yz_inner_wire)
    inner_cavity = yz_inner_face.extrude(App.Vector(w - 2 * wall_t, 0, 0))
    inner_cavity.translate(App.Vector(wall_t, 0, 0))
    
    case_body = outer_wedge.cut(inner_cavity).removeSplitter()
    
    # 3. Four Corner M3 Screw Bosses:
    # Build bosses and trim them with outer_wedge so their top surface is 100% planar with the 15° rim!
    boss_r = 3.5  # Ø7.0mm boss
    pilot_r = 1.3  # Ø2.6mm core hole for M3 screw
    corner_bosses = []
    
    corner_locs = [
        (8.0, 8.0),
        (w - 8.0, 8.0),
        (8.0, d - 8.0),
        (w - 8.0, d - 8.0),
    ]
    
    for cx, cy in corner_locs:
        top_z = z_front + cy * math.tan(angle_rad)
        boss = Part.makeCylinder(boss_r, top_z + 5.0, App.Vector(cx, cy, 0))
        pilot = Part.makeCylinder(pilot_r, 16.0, App.Vector(cx, cy, top_z - 15.0))
        boss_trimmed = boss.common(outer_wedge).cut(pilot)
        corner_bosses.append(boss_trimmed)
        
    if corner_bosses:
        case_body = case_body.fuse(Part.makeCompound(corner_bosses)).removeSplitter()
        
    # 4. Internal Electronics Mounting (3 Distinct Functional Bays):
    # A) PCA9685 16-Channel PWM Servo Driver Standoffs (Right Bay):
    # PCB Footprint: 62.5 x 25.4mm, Hole pitch: 55.88 x 19.05mm
    pca_cx = w * 0.70  # ~154.0mm
    pca_cy = d * 0.50  # 60.0mm
    pca_pitch_x = 55.88
    pca_pitch_y = 19.05
    pca_standoff_h = 5.0
    pca_boss_r = 2.5  # Ø5.0mm boss
    pca_pilot_r = 1.1  # Ø2.2mm core hole for M2.5 screw
    
    pca_bosses = []
    for dx in [-pca_pitch_x / 2.0, pca_pitch_x / 2.0]:
        for dy in [-pca_pitch_y / 2.0, pca_pitch_y / 2.0]:
            bx = pca_cx + dx
            by = pca_cy + dy
            boss = Part.makeCylinder(pca_boss_r, floor_t + pca_standoff_h, App.Vector(bx, by, 0))
            pilot = Part.makeCylinder(pca_pilot_r, pca_standoff_h + 1.0, App.Vector(bx, by, floor_t))
            pca_bosses.append(boss.cut(pilot))
            
    # B) ESP32 DevKit Standoffs & Universal Retention Cradle (Lower-Left Bay):
    # PCB Footprint: 51.5 x 28.5mm, Hole pitch: 46.0 x 23.0mm
    esp_cx = 58.0  # positioned for ample clearance
    esp_cy = 44.0  # 44.0mm
    esp_pitch_x = 46.0
    esp_pitch_y = 23.0
    esp_standoff_h = 5.0
    esp_boss_r = 3.0  # Ø6.0mm boss
    esp_pilot_r = 1.3  # Ø2.6mm core hole for M3 screw
    
    esp_bosses = []
    for dx in [-esp_pitch_x / 2.0, esp_pitch_x / 2.0]:
        for dy in [-esp_pitch_y / 2.0, esp_pitch_y / 2.0]:
            bx = esp_cx + dx
            by = esp_cy + dy
            boss = Part.makeCylinder(esp_boss_r, floor_t + esp_standoff_h, App.Vector(bx, by, 0))
            pilot = Part.makeCylinder(esp_pilot_r, esp_standoff_h + 1.0, App.Vector(bx, by, floor_t))
            esp_bosses.append(boss.cut(pilot))
            
    # ESP32 Perimeter Alignment Cradle:
    cradle_box = Part.makeBox(54.0, 31.0, 3.5, App.Vector(esp_cx - 27.0, esp_cy - 15.5, floor_t))
    cradle_pocket = Part.makeBox(52.0, 29.0, 4.0, App.Vector(esp_cx - 26.0, esp_cy - 14.5, floor_t))
    esp_cradle = cradle_box.cut(cradle_pocket)
    
    # C) Power Distribution Board (PDB) Standoffs (Upper-Left Bay):
    # Footprint: 45.0 x 32.0mm, Hole pitch: 37.0 x 24.0mm (M3)
    pdb_cx = 38.0
    pdb_cy = 86.0
    pdb_pitch_x = 37.0
    pdb_pitch_y = 24.0
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
            
    # D) Cable Strain-Relief Zip-Tie Saddles:
    saddles = []
    for sx, sy in [(w * 0.50, d * 0.45), (pdb_cx + 28.0, pdb_cy)]:
        sad_b = Part.makeBox(6.0, 10.0, 4.0, App.Vector(sx - 3.0, sy - 5.0, floor_t))
        sad_slot = Part.makeBox(7.0, 3.0, 2.0, App.Vector(sx - 3.5, sy - 1.5, floor_t + 1.0))
        saddles.append(sad_b.cut(sad_slot))
        
    elec_mounts = pca_bosses + esp_bosses + [esp_cradle] + pdb_bosses + saddles
    case_body = case_body.fuse(Part.makeCompound(elec_mounts)).removeSplitter()
    
    # 5. External Port Cutouts:
    # A) ESP32 Micro-USB / USB-C Port Cutout on Left Wall (X=0):
    usb_w = 12.0
    usb_h = 7.5
    usb_z = floor_t + esp_standoff_h + 0.5
    usb_cut = Part.makeBox(wall_t + 2.0, usb_w, usb_h, App.Vector(-1.0, esp_cy - usb_w / 2.0, usb_z))
    
    # B) DC Power Barrel Jack (Ø11.5mm) on Left Wall directly feeding PDB input:
    dc_jack_r = params.DC_JACK_DIAMETER / 2.0  # 5.75mm
    dc_jack_y = pdb_cy  # 86.0mm (aligned directly with PDB)
    dc_jack_z = 12.0
    dc_jack_cut = Part.makeCylinder(dc_jack_r, wall_t + 2.0, App.Vector(-1.0, dc_jack_y, dc_jack_z), App.Vector(1, 0, 0))
    
    # C) ESP32 Header Pin Through-Floor Relief Slots:
    esp_pin_slot1 = Part.makeBox(42.0, 4.0, floor_t + 2.0, App.Vector(esp_cx - 21.0, esp_cy - 28.5 / 2.0 + 1.0 - 0.75, -1.0))
    esp_pin_slot2 = Part.makeBox(42.0, 4.0, floor_t + 2.0, App.Vector(esp_cx - 21.0, esp_cy + 28.5 / 2.0 - 3.5 - 0.75, -1.0))
    
    # D) Passive Convection Chimney Cooling Slots in Base Floor for all 3 boards:
    cooling_slots = [esp_pin_slot1, esp_pin_slot2]
    for i in [-1, 0, 1]:
        slot_e = Part.makeBox(36.0, 2.5, floor_t + 2.0, App.Vector(esp_cx - 18.0, esp_cy + i * 6.0 - 1.25, -1.0))
        cooling_slots.append(slot_e)
    for i in [-2, -1, 0, 1, 2]:
        slot_p = Part.makeBox(48.0, 2.5, floor_t + 2.0, App.Vector(pca_cx - 24.0, pca_cy + i * 5.0 - 1.25, -1.0))
        cooling_slots.append(slot_p)
    for i in [-1, 0, 1]:
        slot_pdb = Part.makeBox(28.0, 2.5, floor_t + 2.0, App.Vector(pdb_cx - 14.0, pdb_cy + i * 6.0 - 1.25, -1.0))
        cooling_slots.append(slot_pdb)
        
    # E) 4x Bottom Anti-Slip Rubber Feet Sockets (Ø20.1mm x 2.0mm):
    foot_r = params.FOOT_PAD_DIA / 2.0
    foot_d = params.FOOT_PAD_DEPTH
    foot_sockets = [
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(16.0, 16.0, -0.1)),
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(w - 16.0, 16.0, -0.1)),
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(16.0, d - 16.0, -0.1)),
        Part.makeCylinder(foot_r, foot_d + 0.1, App.Vector(w - 16.0, d - 16.0, -0.1)),
    ]
    
    # F) Dual Sliding Dovetail Sockets on Rear Mating Wall (Y = 120.0mm):
    dt_neck_w = params.DOVETAIL_NECK_WIDTH
    dt_flare_w = params.DOVETAIL_FLARE_WIDTH
    dt_depth = params.DOVETAIL_DEPTH
    dt_floor = params.DOVETAIL_FLOOR_THICKNESS
    dt_h = params.DOVETAIL_HEIGHT
    
    dt_cutter_proto = create_dovetail_socket_cutter(dt_neck_w, dt_flare_w, dt_depth, dt_h + 1.0)
    dt_cutters = []
    wire_ports = []
    pushout_holes = []
    
    for dt_x in [w * 0.25, w * 0.75]:  # 55.0mm and 165.0mm
        dt_c = dt_cutter_proto.copy()
        dt_c.translate(App.Vector(dt_x, d, dt_floor))
        dt_cutters.append(dt_c)
        
        # Wire pass-through conduit tunnel (12mm x 8mm)
        w_port = Part.makeBox(12.0, wall_t + dt_depth + 4.0, 8.0, App.Vector(dt_x - 6.0, d - dt_depth - 2.0, dt_floor + 2.0))
        wire_ports.append(w_port)
        
        # Push-out access hole through floor (Ø6.0mm)
        p_hole = Part.makeCylinder(3.0, dt_floor + 2.0, App.Vector(dt_x, d - dt_depth / 2.0, -1.0))
        pushout_holes.append(p_hole)
        
    # G) 0.4mm Elephant's Foot Bed Relief Chamfer on bottom outer perimeter:
    ef_cutter = Part.makeBox(w + 10.0, d + 10.0, params.ELEPHANTS_FOOT_CHAMFER + 0.1, App.Vector(-5.0, -5.0, -0.05))
    ef_inner = Part.makeBox(w - 2 * params.ELEPHANTS_FOOT_CHAMFER, d - 2 * params.ELEPHANTS_FOOT_CHAMFER, params.ELEPHANTS_FOOT_CHAMFER + 0.2, App.Vector(params.ELEPHANTS_FOOT_CHAMFER, params.ELEPHANTS_FOOT_CHAMFER, -0.1))
    ef_ring = ef_cutter.cut(ef_inner)
    
    all_cuts = [usb_cut, dc_jack_cut, ef_ring] + cooling_slots + foot_sockets + dt_cutters + wire_ports + pushout_holes
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
