"""
Fabrica Cloth Folding Robot - Interface Control Faceplate (Compact Top Deck with Direct Wall Snap Legs)
Part of Phase 5: Interface Module & Electronics Enclosure.

Features:
1. Compact flat horizontal rectangular top deck (140.0 x 120.0 x 3.0mm, assembled Z = 45.0 to 48.0mm)
2. 4-Sided Toolless Direct Wall Snap Retention System:
   - 4x Cantilever Snap Legs (2 on Front Edge, 2 on Rear Edge @ X=35, 105mm)
   - 10.0mm wide x 1.6mm thick x 8.0mm reach cantilever legs with 1.2mm outward detent beads
   - Continuous 1.8mm side register down-ribs aligning against inner left/right chassis walls
3. Standardized Human-Machine Interface (HMI) Controls:
   - 4x Inline Ø16.0mm Tactile Push Button Cutouts (0.8mm chamfers, 24.0mm pitch, centered at X=70.0mm, Y=54.0mm)
   - Circular Round Ø6.0mm Status LED Window (0.8mm top chamfer, Ø8.5mm x 1.2mm underside retention lip @ X=70.0mm, Y=86.4mm)
4. Diamond Micro-Grip Surface Texture & 0.8mm Perimeter Chamfer
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
    Constructs the compact monolithic 3D printable flat horizontal top faceplate
    with direct wall cantilever snap legs and continuous side register down-ribs.
    """
    w = params.INTERFACE_PANEL_WIDTH  # 140.0mm
    d = params.INTERFACE_PANEL_HEIGHT  # 120.0mm
    t_panel = 3.0  # 3.0mm thick top faceplate
    h_case = 45.0  # 45.0mm case chassis height
    wall_t = params.WALL_THICKNESS  # 3.0mm
    
    # 1. Main flat horizontal top deck:
    deck = Part.makeBox(w, d, t_panel, App.Vector(0, 0, h_case))
    
    # 2. Continuous Side Register Down-Ribs (Left & Right inner wall alignment):
    rib_t = 1.8  # 1.8mm thick guide rib
    rib_h = 3.5  # 3.5mm downward protrusion
    rib_clearance = 0.25  # 0.25mm perimeter clearance
    
    left_rib = Part.makeBox(
        rib_t,
        d - 2 * wall_t - 2 * rib_clearance,
        rib_h,
        App.Vector(wall_t + rib_clearance, wall_t + rib_clearance, h_case - rib_h)
    )
    right_rib = Part.makeBox(
        rib_t,
        d - 2 * wall_t - 2 * rib_clearance,
        rib_h,
        App.Vector(w - wall_t - rib_t - rib_clearance, wall_t + rib_clearance, h_case - rib_h)
    )
    
    # 3. Direct Wall Snap Legs (4x: 2 Front, 2 Rear @ X=35, 105mm):
    snap_w = 10.0  # 10.0mm wide cantilever leg
    snap_t = 1.6  # 1.6mm thickness
    snap_reach = 8.0  # 8.0mm downward reach into chassis
    detent_w = snap_w
    detent_reach = 2.0  # 2.0mm vertical height of detent bead
    detent_h = 1.2  # 1.2mm outward projection into wall window
    
    snap_tabs = []
    for sx in [35.0, 105.0]:
        # Front Snap Tab (clicks into front wall window @ Y=0):
        f_leg = Part.makeBox(
            snap_w, snap_t, snap_reach,
            App.Vector(sx - snap_w / 2.0, wall_t + rib_clearance, h_case - snap_reach)
        )
        f_bead = Part.makeBox(
            detent_w, detent_h, detent_reach,
            App.Vector(sx - snap_w / 2.0, wall_t + rib_clearance - detent_h, h_case - 7.0)
        )
        snap_tabs.extend([f_leg, f_bead])
        
        # Rear Snap Tab (clicks into rear wall window @ Y=120):
        r_leg = Part.makeBox(
            snap_w, snap_t, snap_reach,
            App.Vector(sx - snap_w / 2.0, d - wall_t - rib_clearance - snap_t, h_case - snap_reach)
        )
        r_bead = Part.makeBox(
            detent_w, detent_h, detent_reach,
            App.Vector(sx - snap_w / 2.0, d - wall_t - rib_clearance, h_case - 7.0)
        )
        snap_tabs.extend([r_leg, r_bead])
        
    deck = deck.fuse(Part.makeCompound([left_rib, right_rib] + snap_tabs)).removeSplitter()
    
    # 4. 4x Standardized Ø16.0mm Tactile Push Button Cutouts:
    btn_r = params.BUTTON_HOLE_DIA / 2.0  # 8.0mm
    btn_pitch = 30.0  # 30.0mm pitch (14.0mm edge-to-edge gap between Ø16mm holes)
    btn_cx = w / 2.0  # 70.0mm
    btn_xs = [btn_cx - 1.5 * btn_pitch, btn_cx - 0.5 * btn_pitch, btn_cx + 0.5 * btn_pitch, btn_cx + 1.5 * btn_pitch]
    btn_y = d * 0.45  # 54.0mm
    
    btn_cuts = []
    for bx in btn_xs:
        cut = Part.makeCylinder(btn_r, t_panel + 2.0, App.Vector(bx, btn_y, h_case - 1.0))
        c_top = Part.makeCone(
            btn_r + params.HOLE_CHAMFER, btn_r, params.HOLE_CHAMFER,
            App.Vector(bx, btn_y, h_case + t_panel - params.HOLE_CHAMFER)
        )
        btn_cuts.extend([cut, c_top])
        
    # 5. Status LED Diffuser Window (Ø6.0mm round):
    led_r = 3.0  # Ø6.0mm round hole
    led_y = d * 0.72  # 86.4mm
    led_cut = Part.makeCylinder(led_r, t_panel + 2.0, App.Vector(btn_cx, led_y, h_case - 1.0))
    led_c_top = Part.makeCone(
        led_r + params.HOLE_CHAMFER, led_r, params.HOLE_CHAMFER,
        App.Vector(btn_cx, led_y, h_case + t_panel - params.HOLE_CHAMFER)
    )
    led_lip = Part.makeCylinder(4.25, 1.2, App.Vector(btn_cx, led_y, h_case - 0.1))
    
    # 6. Diamond Grip Surface Texture Grooves (0.6mm depth):
    tex_cuts = []
    tex_h = params.TEXTURE_HEIGHT
    num_grooves = 16
    g_step = (w - 30.0) / num_grooves
    for i in range(num_grooves + 1):
        gx = 15.0 + i * g_step
        g_box = Part.makeBox(0.8, d - 24.0, tex_h + 0.1, App.Vector(gx - 0.4, 12.0, h_case + t_panel - tex_h))
        tex_cuts.append(g_box)
        
    # 7. 0.8mm Perimeter Top Edge Chamfer:
    ef_cutter = Part.makeBox(w + 10.0, d + 10.0, 0.8, App.Vector(-5.0, -5.0, h_case + t_panel - 0.8))
    ef_inner = Part.makeBox(w - 1.6, d - 1.6, 1.0, App.Vector(0.8, 0.8, h_case + t_panel - 0.9))
    ef_ring = ef_cutter.cut(ef_inner)
    
    all_cuts = btn_cuts + [led_cut, led_c_top, led_lip, ef_ring] + tex_cuts
    deck = deck.cut(Part.makeCompound(all_cuts)).removeSplitter()
    
    return deck

construct_controller_panel = construct_interface_panel  # Backward compatibility alias

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
