"""
Fabrica Cloth Folding Robot - Interface Module Assembly (Compact High-Capacity Enclosure)
Part of Phase 5: Interface Module & Electronics Enclosure.

Integrates 3 Boards + User Interface Controls in a Compact Flat Horizontal Rectangular Box Enclosure:
1. Interface Case (interface_case.py) - Compact lower electronics chassis (140.0 x 120.0 x 45.0mm) with integrated male dovetail @ X=70.0mm
2. Interface Control Faceplate (interface_panel.py) - Compact top deck (140.0 x 120.0 x 3.0mm) with round LED window
3. Power Distribution Board (PDB) / Buck Converter (CAD Reference - Left Bay @ X=25mm, Y=60mm)
4. ESP32 DevKit V1 / NodeMCU-32S Microcontroller Board (CAD Reference - Front-Right Bay @ X=88mm, Y=32mm)
5. PCA9685 16-Channel 12-Bit PWM Servo Driver Board (CAD Reference - Rear-Right Bay @ X=88mm, Y=88mm)
6. 4x Standardized Ø16.0mm Round Tactile Push Buttons (CAD Reference - Inline row @ Y=54mm)
7. Circular Round Status LED Diffuser / Indicator (CAD Reference @ X=70mm, Y=86.4mm)
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
    Oriented along Y: 32.0mm (X) x 45.0mm (Y) x 1.6mm with 4x M3 mounting holes (24.0 x 37.0mm pitch).
    """
    w = 32.0
    d = 45.0
    t_pcb = 1.6
    
    pcb = Part.makeBox(w, d, t_pcb)
    pitch_x = 24.0
    pitch_y = 37.0
    holes = []
    for dx in [-pitch_x / 2.0, pitch_x / 2.0]:
        for dy in [-pitch_y / 2.0, pitch_y / 2.0]:
            h = Part.makeCylinder(1.5, t_pcb + 1.0, App.Vector(w / 2.0 + dx, d / 2.0 + dy, -0.5))
            holes.append(h)
    pcb = pcb.cut(Part.makeCompound(holes))
    
    ind = Part.makeBox(12.0, 12.0, 8.0, App.Vector(w / 2.0 - 6.0, d / 2.0 - 6.0, t_pcb))
    t_in = Part.makeBox(15.0, 10.0, 10.0, App.Vector((w - 15.0) / 2.0, 2.0, t_pcb))
    t_out = Part.makeBox(24.0, 10.0, 10.0, App.Vector((w - 24.0) / 2.0, d - 12.0, t_pcb))
    hs = Part.makeBox(10.0, 15.0, 12.0, App.Vector(w - 12.0, 15.0, t_pcb))
    
    return pcb.fuse([ind, t_in, t_out, hs]).removeSplitter()

def construct_button_16mm_cad_reference():
    """
    CAD Reference solid for standard 16mm momentary tactile push button switch.
    """
    bezel = Part.makeCylinder(9.0, 2.0, App.Vector(0, 0, 0))
    body = Part.makeCylinder(7.9, 15.0, App.Vector(0, 0, -15.0))
    actuator = Part.makeCylinder(6.5, 3.5, App.Vector(0, 0, 2.0))
    terminals = Part.makeBox(4.0, 1.0, 6.0, App.Vector(-2.0, -0.5, -21.0))
    return bezel.fuse([body, actuator, terminals]).removeSplitter()

def construct_led_diffuser_cad_reference():
    """
    CAD Reference solid for 5mm round LED / snap-in bezel diffuser.
    """
    lens = Part.makeCylinder(2.9, 4.0, App.Vector(0, 0, 0))
    dome = Part.makeSphere(2.9, App.Vector(0, 0, 4.0))
    flange = Part.makeCylinder(3.5, 1.2, App.Vector(0, 0, -1.2))
    legs = Part.makeBox(1.5, 0.6, 12.0, App.Vector(-0.75, -0.3, -13.2))
    return lens.fuse([dome, flange, legs]).removeSplitter()

def build_assembly():
    """
    Constructs and positions all parts for the Compact Interface Assembly.
    """
    doc = App.newDocument("InterfaceAssemblyDoc")
    w = params.INTERFACE_PANEL_WIDTH  # 140.0mm
    d = params.INTERFACE_PANEL_HEIGHT  # 120.0mm
    h_case = 45.0
    
    # 1. Interface Case (with integrated male dovetail key):
    case = construct_interface_case()
    
    # 2. Interface Panel (Compact Flat Horizontal Top Faceplate):
    deck = construct_interface_panel()
    
    # 3. PCA9685 Servo Driver Board (Rear-Right Bay @ X=88mm, Y=88mm):
    pca = construct_pca9685_cad_reference()
    pca.translate(App.Vector(88.0 - 62.5 / 2.0, 88.0 - 25.4 / 2.0, 8.0))
    
    # 4. ESP32 DevKit Board (Front-Right Bay @ X=88mm, Y=35mm):
    esp = construct_esp32_cad_reference()
    # Rotated so USB port faces front wall (Y=0):
    esp.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    esp.translate(App.Vector(88.0 + 28.5 / 2.0, 35.0 - 51.5 / 2.0, 8.0))
    
    # 5. Power Distribution Board (Left Bay @ X=25mm, Y=60mm):
    pdb = construct_pdb_cad_reference()
    pdb.translate(App.Vector(25.0 - 32.0 / 2.0, 60.0 - 45.0 / 2.0, 8.0))
    
    # 6. 4x Ø16.0mm Tactile Push Buttons:
    btn_pitch = 30.0  # 30.0mm pitch
    btn_cx = w / 2.0  # 70.0mm
    btn_xs = [btn_cx - 1.5 * btn_pitch, btn_cx - 0.5 * btn_pitch, btn_cx + 0.5 * btn_pitch, btn_cx + 1.5 * btn_pitch]
    btn_y = d * 0.45  # 54.0mm
    
    buttons = []
    for bx in btn_xs:
        btn = construct_button_16mm_cad_reference()
        btn.translate(App.Vector(bx, btn_y, h_case + 3.0))
        buttons.append(btn)
        
    # 7. Status LED Diffuser / Round Indicator:
    led = construct_led_diffuser_cad_reference()
    led_y = d * 0.72  # 86.4mm
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
    print("=== Compact Interface Assembly Exported Successfully ===")
    print("STEP:", step_path)
    print("STL:", stl_path)
    print("BoundBox:", assy_compound.BoundBox)
    print(f"Total Volume: {assy_compound.Volume:.2f} mm3")
    
    return doc

def main():
    build_assembly()

main()
