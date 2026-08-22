"""
Fabrica Cloth Folding Robot - Interface Panel (Flat Horizontal Top Faceplate with Direct Wall Snap-Lock Tabs)
Part of Phase 5: Interface Module & Electronics Enclosure.

Features:
1. Flat horizontal rectangular faceplate (220.0 x 120.0 x 3.0mm)
2. 4x Standardized Ø16.0mm round tactile push button cutouts with 0.8mm chamfers
3. Circular Round Status LED indicator window (Ø6.0mm with 0.8mm chamfer & Ø8.5mm underside retention pocket)
4. 0.6mm Diamond micro-grip surface texture
5. 4-Sided Toolless Snap-Lock System mating with Direct Wall Holes:
   - Front: 2x Cantilever Snap Tabs (clicking forward directly into front wall retention windows)
   - Rear: 2x Cantilever Snap Tabs (clicking backward directly into rear wall retention windows)
   - Left & Right: Continuous Perimeter Register Down-Ribs (preventing lateral bowing/gapping)
6. 100% screwless, clean top surface aesthetics
"""

import os
import sys
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part
import params

def construct_interface_panel():
    """
    Constructs the flat horizontal top control faceplate with direct wall snap-lock tabs.
    """
    w = params.PANEL_WIDTH  # 220.0mm
    d = params.INTERFACE_PANEL_HEIGHT  # 120.0mm
    h_case = 45.0  # 45.0mm base chassis height for spacious wiring
    plate_t = 3.0  # 3.0mm faceplate thickness
    
    # 1. Base flat plate at Z = h_case (45.0mm):
    flat_plate = Part.makeBox(w, d, plate_t, App.Vector(0, 0, h_case))
    
    # 2. 4x Standardized Ø16.0mm Tactile Push Button Cutouts:
    btn_r = (params.BUTTON_HOLE_DIA + 0.6) / 2.0  # 8.3mm (0.6mm clearance)
    btn_pitch = 28.0  # 28.0mm center-to-center pitch
    btn_cx = w / 2.0  # 110.0mm
    btn_y = d * 0.45  # 54.0mm
    btn_xs = [btn_cx - 1.5 * btn_pitch, btn_cx - 0.5 * btn_pitch, btn_cx + 0.5 * btn_pitch, btn_cx + 1.5 * btn_pitch]
    
    btn_cutters = []
    for bx in btn_xs:
        cyl = Part.makeCylinder(btn_r, plate_t + 4.0, App.Vector(bx, btn_y, h_case - 2.0))
        chamfer = Part.makeCone(btn_r, btn_r + params.HOLE_CHAMFER, params.HOLE_CHAMFER + 0.1, App.Vector(bx, btn_y, h_case + plate_t - params.HOLE_CHAMFER))
        btn_cutters.extend([cyl, chamfer])
        
    # 3. Circular Round Status LED Window (Ø6.0mm with 0.8mm top chamfer & Ø8.5mm underside retention pocket):
    led_y = d * 0.72  # 86.4mm
    led_r = 3.0  # Ø6.0mm hole (fits standard 5mm round LED / snap-in clip)
    led_cut = Part.makeCylinder(led_r, plate_t + 4.0, App.Vector(btn_cx, led_y, h_case - 2.0))
    led_chamfer = Part.makeCone(led_r, led_r + params.HOLE_CHAMFER, params.HOLE_CHAMFER + 0.1, App.Vector(btn_cx, led_y, h_case + plate_t - params.HOLE_CHAMFER))
    led_lip = Part.makeCylinder(4.25, 1.5, App.Vector(btn_cx, led_y, h_case - 0.1))
    led_cutters = [led_cut, led_chamfer, led_lip]
    
    # 4. 0.6mm Diamond Micro-Grip Surface Texture:
    tex_cutters = []
    tex_spacing = 14.0
    tex_w = 0.6
    tex_d = params.TEXTURE_HEIGHT
    for i in range(-int(w), int(w + d * 1.5), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, d * 1.5, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, h_case + plate_t - tex_d))
        g2 = Part.makeBox(tex_w, d * 1.5, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, d, h_case + plate_t - tex_d))
        tex_cutters.extend([g1, g2])
        
    tex_bound = Part.makeBox(w - 2 * 14.0, d - 2 * 14.0, plate_t + 2.0, App.Vector(14.0, 14.0, h_case - 1.0))
    tex_compound = Part.makeCompound(tex_cutters).common(tex_bound)
    
    all_cuts = btn_cutters + led_cutters + [tex_compound]
    panel = flat_plate.cut(Part.makeCompound(all_cuts)).removeSplitter()
    
    # 5. Snap Tabs Mating with Direct Wall Retention Windows:
    # Wall retention windows on case are located at X in {50.0, 170.0mm}, width 12.0mm, Z in [38.0, 41.5mm]
    tab_w = 10.0   # 10.0mm tab width inside 12.0mm hole (1.0mm side clearance)
    tab_t = 1.6    # 1.6mm cantilever thickness
    tab_reach = 8.0  # reaches from Z=45.0 down to Z=37.0mm
    bead_h = 2.5
    bead_protrusion = 1.2
    
    snap_tabs = []
    # Front Cantilever Snap Tabs (at Y = 3.2mm to 4.8mm, bead extending forward to Y = 2.0mm into front wall hole):
    for sx in [50.0, 170.0]:
        f_arm = Part.makeBox(tab_w, tab_t, tab_reach, App.Vector(sx - tab_w / 2.0, 3.2, h_case - tab_reach))
        f_bead = Part.makeBox(tab_w, bead_protrusion, bead_h, App.Vector(sx - tab_w / 2.0, 3.2 - bead_protrusion, h_case - 6.5))
        snap_tabs.extend([f_arm, f_bead])
        
    # Rear Cantilever Snap Tabs (at Y = 115.2mm to 116.8mm, bead extending backward to Y = 118.0mm into rear wall hole):
    for sx in [50.0, 170.0]:
        r_arm = Part.makeBox(tab_w, tab_t, tab_reach, App.Vector(sx - tab_w / 2.0, d - 3.2 - tab_t, h_case - tab_reach))
        r_bead = Part.makeBox(tab_w, bead_protrusion, bead_h, App.Vector(sx - tab_w / 2.0, d - 3.2, h_case - 6.5))
        snap_tabs.extend([r_arm, r_bead])
        
    # Left & Right Continuous Perimeter Register Down-Ribs:
    rib_l = Part.makeBox(1.5, d - 14.0, 2.5, App.Vector(3.8, 7.0, h_case - 2.5))
    rib_r = Part.makeBox(1.5, d - 14.0, 2.5, App.Vector(w - 5.3, 7.0, h_case - 2.5))
    side_ribs = [rib_l, rib_r]
    
    underside_features = snap_tabs + side_ribs
    return panel.fuse(Part.makeCompound(underside_features)).removeSplitter()

def main():
    doc = App.newDocument("InterfacePanelDoc")
    shape = construct_interface_panel()
    
    out_dir = params.EXPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    step_path = os.path.join(out_dir, "interface_panel.step")
    stl_path = os.path.join(out_dir, "interface_panel.stl")
    shape.exportStep(step_path)
    shape.exportStl(stl_path)
    print("=== Interface Panel Exported Successfully ===")
    print("STEP:", step_path)
    print("STL:", stl_path)
    print("BoundBox:", shape.BoundBox)
    print(f"Volume: {shape.Volume:.2f} mm3")
    
    feature = doc.addObject("Part::Feature", "InterfacePanel")
    feature.Shape = shape
    if hasattr(feature, "ViewObject") and feature.ViewObject:
        feature.ViewObject.ShapeColor = (0.95, 0.75, 0.15)
    return feature

main()
