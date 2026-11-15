"""
motorized_servo_cover.py — Flush Top Drop-In Lid for Motorized Servo Enclosure
Parametric FreeCAD Python script for Fabrica Cloth Folding Robot.
"""

import os
import sys
import FreeCAD as App
import Part

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from params import (
    EXPORT_DIR,
)

def construct_motorized_servo_cover():
    """
    Constructs the Flush Top Snap-Lock Enclosure Lid (Part 8) for the Motorized Module.
    Features:
      1. Main flush top plate (1.4mm thick, sitting in frame top rebate at Z in [25.8, 27.2mm]).
      2. Dual Heavy-Duty Side Cantilever Snap Legs with 30° insertion ramps and 90° locking shoulders.
      3. Rear-left corner finger/tool pry notch for easy toolless maintenance.
    """
    import params
    h = params.PANEL_HEIGHT
    # 1. Main Flush Top Plate (sitting in frame top rebate at Z = 25.8 to 27.2mm, spanning Y in [173.4, 219.8mm], recessed inside left wall at X=-20.6mm)
    w_top = 60.8 # X in [-20.6, 40.2mm]
    l_top = 46.4 # Y in [173.4, 219.8mm]
    t_top = 1.4
    z_top_min = 25.8

    top_plate = Part.makeBox(w_top, l_top, t_top)
    top_plate.translate(App.Vector(-20.6, 173.4, z_top_min))

    # Rear End-Wall Retaining Lip (closes off the open rear slide-in bay at Y in [214.0, 219.8mm], Z in [5.5, 25.8mm])
    rear_lip = Part.makeBox(55.7, 5.8, 20.3)
    rear_lip.translate(App.Vector(-17.5, 214.0, 5.5))

    # 2x Vertical Alignment Pegs under rear_lip (Ø4.0mm x 3.5mm at Y=216.0mm, Z in [2.0, 5.5mm]) for zero-rattle rear seating
    peg_r = 2.0
    peg_h = 3.5
    peg_y = 216.0
    peg_xs = [-6.0, 26.7]
    rear_pegs = []
    for px in peg_xs:
        p_cyl = Part.makeCylinder(peg_r, peg_h + 0.5, App.Vector(px, peg_y, 5.5 - peg_h))
        p_chamf = Part.makeCone(peg_r + 0.5, peg_r - 0.5, 0.6, App.Vector(px, peg_y, 5.5 - peg_h - 0.1))
        # Trim bottom tip cleanly with a 45° lead-in chamfer
        c_outer = Part.makeCylinder(peg_r + 1.0, 0.6, App.Vector(px, peg_y, 5.5 - peg_h - 0.05))
        c_keep = Part.makeCone(peg_r - 0.5, peg_r, 0.55, App.Vector(px, peg_y, 5.5 - peg_h))
        p_cyl = p_cyl.cut(c_outer.cut(c_keep)).removeSplitter()
        rear_pegs.append(p_cyl)

    # 2. Dual Heavy-Duty Side Cantilever Snap Legs with locking anchors (Y in [191.0, 199.0mm], centered in frame's [190.0, 200.0mm] catch channels)
    def make_side_snap_leg(is_left):
        leg_l = 8.0   # Y-length
        leg_t = 1.8   # X-thickness
        leg_h = 6.5   # Z-height
        y_start = 191.0
        
        if is_left:
            x_pos = -17.0
            pts = [
                App.Vector(x_pos, y_start, z_top_min - leg_h),
                App.Vector(x_pos - 2.5, y_start, z_top_min - leg_h + 2.0),
                App.Vector(x_pos, y_start, z_top_min - leg_h + 2.8),
                App.Vector(x_pos, y_start, z_top_min - leg_h),
            ]
            x_ext = leg_t
        else:
            x_pos = 38.4
            pts = [
                App.Vector(x_pos + leg_t, y_start, z_top_min - leg_h),
                App.Vector(x_pos + leg_t + 2.5, y_start, z_top_min - leg_h + 2.0),
                App.Vector(x_pos + leg_t, y_start, z_top_min - leg_h + 2.8),
                App.Vector(x_pos + leg_t, y_start, z_top_min - leg_h),
            ]
            x_ext = leg_t
            
        leg_box = Part.makeBox(x_ext, leg_l, leg_h)
        leg_box.translate(App.Vector(x_pos, y_start, z_top_min - leg_h))
        
        barb_wire = Part.makePolygon(pts)
        barb_face = Part.Face(barb_wire)
        barb_solid = barb_face.extrude(App.Vector(0, leg_l, 0))
        return leg_box.fuse(barb_solid).removeSplitter()

    leg_left = make_side_snap_leg(True)
    leg_right = make_side_snap_leg(False)

    lid = top_plate.fuse([leg_left, leg_right, rear_lip] + rear_pegs).removeSplitter()

    # 4. Finger / Tool Pry Notch at Rear-Left Corner
    notch = Part.makeCylinder(3.5, 3.0, App.Vector(-20.6, 219.8, z_top_min - 1.0))
    lid = lid.cut(notch).removeSplitter()

    # Export STEP and STL
    step_path = os.path.join(EXPORT_DIR, "motorized_servo_cover.step")
    stl_path  = os.path.join(EXPORT_DIR, "motorized_servo_cover.stl")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    lid.exportStep(step_path)
    lid.exportStl(stl_path)
    print(f"Exported to {step_path} and {stl_path}")
    return lid

def main():
    doc = App.ActiveDocument or App.newDocument("MotorizedServoCover")
    shape = construct_motorized_servo_cover()
    feature = doc.addObject("Part::Feature", "MotorizedServoCover")
    feature.Shape = shape

def export_part():
    main()

export_part()
