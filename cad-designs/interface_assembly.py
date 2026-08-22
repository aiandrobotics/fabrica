"""
Fabrica Cloth Folding Robot - Interface Module Assembly (Flat Rectangular Box Enclosure)
Part of Phase 5: Interface Module & Electronics Enclosure.

Integrates 3 Boards + User Interface Controls in a Flat Horizontal Rectangular Box Enclosure:
1. Interface Case (interface_case.py) - Flat lower electronics chassis (220.0 x 120.0 x 30.0mm) with 4-sided toolless snap retention
2. Interface Control Faceplate (interface_panel.py) - Flat horizontal top deck (220.0 x 120.0 x 3.0mm) with round LED window
3. Power Distribution Board (PDB) / Buck Converter (CAD Reference)
4. ESP32 DevKit V1 / NodeMCU-32S Microcontroller Board (CAD Reference)
5. PCA9685 16-Channel 12-Bit PWM Servo Driver Board (CAD Reference)
6. 4x Standardized Ø16.0mm Round Tactile Push Buttons (CAD Reference)
7. Circular Round Status LED Diffuser / Indicator (CAD Reference)
"""

import os
import sys
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part
import params
from interface_case import construct_interface_case
from interface_panel import construct_interface_panel

def construct_pca9685_cad_reference():
    """
    CAD Reference solid for PCA9685 16-Channel PWM Servo Driver Board.
    PCB Footprint: 62.5 x 25.4 x 1.6mm with 4x M2.5 mounting holes (55.88 x 19.05mm pitch).
    """
    w = 62.5
    d = 25.4
    t_pcb = 1.6
    
    pcb = Part.makeBox(w, d, t_pcb)
    pitch_x = 55.88
    pitch_y = 19.05
    holes = []
    for dx in [-pitch_x / 2.0, pitch_x / 2.0]:
        for dy in [-pitch_y / 2.0, pitch_y / 2.0]:
            h = Part.makeCylinder(1.25, t_pcb + 1.0, App.Vector(w / 2.0 + dx, d / 2.0 + dy, -0.5))
            holes.append(h)
    pcb = pcb.cut(Part.makeCompound(holes))
    
    term = Part.makeBox(10.0, 8.0, 10.0, App.Vector(2.0, d / 2.0 - 4.0, t_pcb))
    headers = Part.makeBox(52.0, 8.0, 9.0, App.Vector(w / 2.0 - 26.0, d - 9.0, t_pcb))
    ic = Part.makeBox(8.0, 8.0, 2.0, App.Vector(w / 2.0 - 4.0, 4.0, t_pcb))
    cap = Part.makeCylinder(3.5, 9.0, App.Vector(15.0, 8.0, t_pcb))
    
    return pcb.fuse([term, headers, ic, cap]).removeSplitter()

def construct_esp32_cad_reference():
    """
    CAD Reference solid for ESP32 DevKit V1 (WROOM-32 / ESP-32S).
    PCB Footprint: 51.5 x 28.5 x 1.6mm with 4x M3 mounting holes (46.0 x 23.0mm pitch).
    """
    w = 51.5
    d = 28.5
    t_pcb = 1.6
    
    pcb = Part.makeBox(w, d, t_pcb)
    pitch_x = 46.0
    pitch_y = 23.0
    holes = []
    for dx in [-pitch_x / 2.0, pitch_x / 2.0]:
        for dy in [-pitch_y / 2.0, pitch_y / 2.0]:
            h = Part.makeCylinder(1.5, t_pcb + 1.0, App.Vector(w / 2.0 + dx, d / 2.0 + dy, -0.5))
            holes.append(h)
    pcb = pcb.cut(Part.makeCompound(holes))
    
    shield = Part.makeBox(18.0, 25.5, 3.0, App.Vector(w - 20.0, (d - 25.5) / 2.0, t_pcb))
    usb = Part.makeBox(8.0, 6.0, 3.0, App.Vector(-1.5, (d - 6.0) / 2.0, t_pcb))
    h1 = Part.makeBox(38.0, 2.5, 4.5, App.Vector(6.0, 1.0, -4.5))
    h2 = Part.makeBox(38.0, 2.5, 4.5, App.Vector(6.0, d - 3.5, -4.5))
    btn1 = Part.makeBox(4.0, 3.5, 2.0, App.Vector(2.0, 3.0, t_pcb))
    btn2 = Part.makeBox(4.0, 3.5, 2.0, App.Vector(2.0, d - 6.5, t_pcb))
    
    return pcb.fuse([shield, usb, h1, h2, btn1, btn2]).removeSplitter()

def construct_pdb_cad_reference():
    """
    CAD Reference solid for 5V/6V High-Current Power Distribution Board with screw terminals.
    PCB Footprint: 45.0 x 32.0 x 1.6mm with 4x M3 mounting holes (37.0 x 24.0mm pitch).
    """
    w = 45.0
    d = 32.0
    t_pcb = 1.6
    
    pcb = Part.makeBox(w, d, t_pcb)
    pitch_x = 37.0
    pitch_y = 24.0
    holes = []
    for dx in [-pitch_x / 2.0, pitch_x / 2.0]:
        for dy in [-pitch_y / 2.0, pitch_y / 2.0]:
            h = Part.makeCylinder(1.5, t_pcb + 1.0, App.Vector(w / 2.0 + dx, d / 2.0 + dy, -0.5))
            holes.append(h)
    pcb = pcb.cut(Part.makeCompound(holes))
    
    # Input and output screw terminal blocks:
    term_in = Part.makeBox(8.0, 15.0, 10.0, App.Vector(2.0, d / 2.0 - 7.5, t_pcb))
    term_out = Part.makeBox(8.0, 24.0, 10.0, App.Vector(w - 10.0, d / 2.0 - 12.0, t_pcb))
    inductor = Part.makeCylinder(6.0, 7.0, App.Vector(w / 2.0, d / 2.0, t_pcb))
    heatsink = Part.makeBox(12.0, 16.0, 8.0, App.Vector(w / 2.0 - 6.0, d / 2.0 - 8.0, t_pcb))
    
    return pcb.fuse([term_in, term_out, inductor, heatsink]).removeSplitter()

def construct_button_16mm_cad_reference():
    """
    CAD Reference solid for standard Ø16.0mm round tactile push button.
    """
    barrel = Part.makeCylinder(7.9, 18.0, App.Vector(0, 0, -18.0))
    bezel = Part.makeCylinder(9.0, 2.5, App.Vector(0, 0, 0))
    cap = Part.makeCylinder(6.5, 4.0, App.Vector(0, 0, 0))
    terminals = Part.makeBox(4.0, 8.0, 5.0, App.Vector(-2.0, -4.0, -23.0))
    return barrel.fuse([bezel, cap, terminals]).removeSplitter()

def construct_led_diffuser_cad_reference():
    """
    CAD Reference solid for circular round status LED diffuser / 5mm round LED indicator.
    """
    body = Part.makeCylinder(2.5, 8.5, App.Vector(0, 0, -5.0))
    dome = Part.makeSphere(2.5, App.Vector(0, 0, 3.5))
    flange = Part.makeCylinder(3.0, 1.2, App.Vector(0, 0, -1.0))
    leads = Part.makeBox(0.6, 2.54, 15.0, App.Vector(-0.3, -1.27, -20.0))
    return body.fuse([dome, flange, leads]).removeSplitter()

def build_assembly():
    """
    Assembles all Phase 5 interface module components into a multi-body FreeCAD Document.
    """
    doc = App.newDocument("InterfaceModuleAssembly")
    
    # 1. Base Flat Controller Case (30.0mm height):
    case = construct_interface_case()
    
    # 2. Top Flat Control Faceplate (at Z = 30.0mm):
    deck = construct_interface_panel()
    
    # 3. PCA9685 Driver Board (Right Bay):
    pca = construct_pca9685_cad_reference()
    pca.translate(App.Vector(params.PANEL_WIDTH * 0.70 - 62.5 / 2.0, params.INTERFACE_PANEL_HEIGHT * 0.50 - 25.4 / 2.0, 8.0))
    
    # 4. ESP32 DevKit Board (Lower-Left Bay):
    esp = construct_esp32_cad_reference()
    esp.translate(App.Vector(58.0 - 51.5 / 2.0, 44.0 - 28.5 / 2.0, 8.0))
    
    # 5. Power Distribution Board (Upper-Left Bay):
    pdb = construct_pdb_cad_reference()
    pdb.translate(App.Vector(38.0 - 45.0 / 2.0, 86.0 - 32.0 / 2.0, 8.0))
    
    # 6. 4x Ø16.0mm Tactile Push Buttons:
    h_case = 30.0
    btn_pitch = 28.0
    btn_cx = params.PANEL_WIDTH / 2.0
    btn_xs = [btn_cx - 1.5 * btn_pitch, btn_cx - 0.5 * btn_pitch, btn_cx + 0.5 * btn_pitch, btn_cx + 1.5 * btn_pitch]
    btn_y = params.INTERFACE_PANEL_HEIGHT * 0.45
    
    buttons = []
    for bx in btn_xs:
        btn = construct_button_16mm_cad_reference()
        btn.translate(App.Vector(bx, btn_y, h_case + 3.0))
        buttons.append(btn)
        
    # 7. Status LED Diffuser / Round Indicator:
    led = construct_led_diffuser_cad_reference()
    led_y = params.INTERFACE_PANEL_HEIGHT * 0.72
    led.translate(App.Vector(btn_cx, led_y, h_case))
    
    # Add objects to document with standard aesthetic color palette:
    obj_case = doc.addObject("Part::Feature", "InterfaceCase")
    obj_case.Shape = case
    if hasattr(obj_case, "ViewObject") and obj_case.ViewObject:
        obj_case.ViewObject.ShapeColor = (0.2, 0.65, 0.35)  # Enclosure Green
        
    obj_deck = doc.addObject("Part::Feature", "InterfacePanel")
    obj_deck.Shape = deck
    if hasattr(obj_deck, "ViewObject") and obj_deck.ViewObject:
        obj_deck.ViewObject.ShapeColor = (0.95, 0.75, 0.15)  # Control Deck Yellow
        
    obj_pca = doc.addObject("Part::Feature", "PCA9685_Board")
    obj_pca.Shape = pca
    if hasattr(obj_pca, "ViewObject") and obj_pca.ViewObject:
        obj_pca.ViewObject.ShapeColor = (0.1, 0.3, 0.8)  # Driver PCB Blue
        
    obj_esp = doc.addObject("Part::Feature", "ESP32_DevKit")
    obj_esp.Shape = esp
    if hasattr(obj_esp, "ViewObject") and obj_esp.ViewObject:
        obj_esp.ViewObject.ShapeColor = (0.15, 0.15, 0.15)  # MCU PCB Black
        
    obj_pdb = doc.addObject("Part::Feature", "PowerDistributionBoard")
    obj_pdb.Shape = pdb
    if hasattr(obj_pdb, "ViewObject") and obj_pdb.ViewObject:
        obj_pdb.ViewObject.ShapeColor = (0.85, 0.25, 0.2)  # PDB Red/Copper
        
    btn_colors = [(0.2, 0.4, 0.8), (0.2, 0.7, 0.3), (0.9, 0.7, 0.1), (0.85, 0.2, 0.2)]
    for i, b in enumerate(buttons):
        obj_b = doc.addObject("Part::Feature", f"Button_{i+1}")
        obj_b.Shape = b
        if hasattr(obj_b, "ViewObject") and obj_b.ViewObject:
            obj_b.ViewObject.ShapeColor = btn_colors[i % len(btn_colors)]
            
    obj_led = doc.addObject("Part::Feature", "StatusLED")
    obj_led.Shape = led
    if hasattr(obj_led, "ViewObject") and obj_led.ViewObject:
        obj_led.ViewObject.ShapeColor = (0.2, 0.8, 0.9)  # Cyan Indicator
        
    doc.recompute()
    
    # Export full multi-body assembly compound:
    assy_compound = Part.makeCompound([case, deck, pca, esp, pdb] + buttons + [led])
    out_dir = params.EXPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    step_path = os.path.join(out_dir, "interface_assembly.step")
    stl_path = os.path.join(out_dir, "interface_assembly.stl")
    assy_compound.exportStep(step_path)
    assy_compound.exportStl(stl_path)
    print("=== Interface Assembly Exported Successfully ===")
    print("STEP:", step_path)
    print("STL:", stl_path)
    print("BoundBox:", assy_compound.BoundBox)
    print(f"Total Volume: {assy_compound.Volume:.2f} mm3")
    
    return doc

def main():
    build_assembly()

main()
