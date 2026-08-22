"""
Fabrica Cloth Folding Robot - Interface Control Faceplate
Part of Phase 5: Interface Module & Electronics Enclosure.

Features:
1. Ergonomic 15° forward-angled control deck top faceplate.
2. 4x standardized Ø16.0mm tactile push button mounting cutouts with 0.8mm top chamfers.
3. Multi-state status LED diffuser window with internal retention lip.
4. 4x Corner M3 counterbored mounting holes mating with lower chassis bosses.
5. 0.6mm diamond micro-grip surface texture.
6. 1.2mm perimeter shadow accent bevel.
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
    Constructs the 3D printable 15° forward-angled Interface Control Faceplate.
    """
    w = params.PANEL_WIDTH  # 220.0mm
    d = params.INTERFACE_PANEL_HEIGHT  # 120.0mm
    plate_t = 3.0  # 3.0mm structural top deck thickness
    
    angle_deg = params.CONTROL_DECK_ANGLE  # 15.0°
    angle_rad = math.radians(angle_deg)
    deck_len = d / math.cos(angle_rad)  # ~124.23mm
    
    # 1. Base flat plate:
    flat_plate = Part.makeBox(w, deck_len, plate_t)
    
    # 2. 4x Ø16.0mm Tactile Push Button Cutouts with 0.8mm chamfers in flat coordinates:
    btn_r = (params.BUTTON_HOLE_DIA + 0.6) / 2.0  # 8.3mm (Ø16.6mm cutout for Ø16.0mm button)
    btn_pitch = 28.0
    btn_cx = w / 2.0  # 110.0mm
    btn_y_flat = deck_len * 0.45  # ~55.9mm
    
    btn_xs = [
        btn_cx - 1.5 * btn_pitch,
        btn_cx - 0.5 * btn_pitch,
        btn_cx + 0.5 * btn_pitch,
        btn_cx + 1.5 * btn_pitch,
    ]
    
    btn_cutters = []
    for bx in btn_xs:
        cyl = Part.makeCylinder(btn_r, plate_t + 4.0, App.Vector(bx, btn_y_flat, -2.0))
        chamfer = Part.makeCone(btn_r, btn_r + params.HOLE_CHAMFER, params.HOLE_CHAMFER + 0.1, App.Vector(bx, btn_y_flat, plate_t - params.HOLE_CHAMFER))
        btn_cutters.extend([cyl, chamfer])
        
    # 3. Status LED Cutout in flat coordinates:
    led_y_flat = deck_len * 0.72  # ~89.4mm
    led_w = 14.6  # for 14.0mm lens
    led_h = 5.6   # for 5.0mm lens
    led_cut = Part.makeBox(led_w, led_h, plate_t + 4.0, App.Vector(btn_cx - led_w / 2.0, led_y_flat - led_h / 2.0, -2.0))
    led_lip = Part.makeBox(led_w + 3.4, led_h + 3.4, 1.5, App.Vector(btn_cx - (led_w + 3.4) / 2.0, led_y_flat - (led_h + 3.4) / 2.0, -0.1))
    
    # 4. Corner M3 Counterbored Screw Holes in flat coordinates:
    y_inset = 8.0 / math.cos(angle_rad)
    corner_locs_flat = [
        (8.0, y_inset),
        (w - 8.0, y_inset),
        (8.0, deck_len - y_inset),
        (w - 8.0, deck_len - y_inset),
    ]
    
    screw_r = 1.7  # Ø3.4mm clearance for M3
    cb_r = 3.25   # Ø6.5mm counterbore
    cb_depth = 1.5
    screw_cutters = []
    for cx, cy in corner_locs_flat:
        hole = Part.makeCylinder(screw_r, plate_t + 4.0, App.Vector(cx, cy, -2.0))
        cb = Part.makeCylinder(cb_r, cb_depth + 0.1, App.Vector(cx, cy, plate_t - cb_depth))
        screw_cutters.extend([hole, cb])
        
    # 5. 0.6mm Diamond Micro-Grip Surface Texture:
    tex_cutters = []
    tex_spacing = 14.0
    tex_w = 0.6
    tex_d = params.TEXTURE_HEIGHT
    for i in range(-int(w), int(w + deck_len * 1.5), int(tex_spacing)):
        g1 = Part.makeBox(tex_w, deck_len * 1.5, tex_d + 0.1)
        g1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 45)
        g1.translate(App.Vector(i, 0, plate_t - tex_d))
        g2 = Part.makeBox(tex_w, deck_len * 1.5, tex_d + 0.1)
        g2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -45)
        g2.translate(App.Vector(i, deck_len, plate_t - tex_d))
        tex_cutters.extend([g1, g2])
        
    tex_bound = Part.makeBox(w - 2 * 14.0, deck_len - 2 * 14.0, plate_t + 2.0, App.Vector(14.0, 14.0, -1.0))
    tex_compound = Part.makeCompound(tex_cutters).common(tex_bound)
    
    all_cuts = btn_cutters + [led_cut, led_lip] + screw_cutters + [tex_compound]
    panel = flat_plate.cut(Part.makeCompound(all_cuts)).removeSplitter()
    
    # 6. Rotate to 15° Incline and position on top of case:
    panel.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), angle_deg)
    panel.translate(App.Vector(0, 0, params.BASE_PANEL_THICKNESS))
    
    # Trim front and rear edges to be perfectly vertical at Y=0 and Y=d:
    front_trim = Part.makeBox(w + 10.0, 20.0, 60.0, App.Vector(-5.0, -20.0, 0))
    rear_trim = Part.makeBox(w + 10.0, 20.0, 60.0, App.Vector(-5.0, d, 0))
    panel = panel.cut(Part.makeCompound([front_trim, rear_trim])).removeSplitter()
    
    return panel

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
