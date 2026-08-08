import os
import sys
import FreeCAD as App
import Part

# Ensure cad-designs root is in path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from params import SCALE
from part_02_follower_frame import create_follower_frame
from part_03_follower_flap import create_follower_flap

BOTTOM_SHELL_THICKNESS = 3.0 * SCALE


def build_follower_assembly():
    doc = App.newDocument("FollowerAssembly")

    # 1. Base Follower Frame
    frame_shape = create_follower_frame()
    frame_obj = doc.addObject("Part::Feature", "Part02FollowerFrame")
    frame_obj.Shape = frame_shape

    # 2. Left Flap
    flap_1 = create_follower_flap()
    flap_1_obj = doc.addObject("Part::Feature", "Part03FollowerFlap_Left")
    flap_1_obj.Shape = flap_1
    flap_1_obj.Placement = App.Placement(
        App.Vector(26.0 * SCALE, 26.0 * SCALE, BOTTOM_SHELL_THICKNESS + 2.0 * SCALE),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )

    # 3. Right Flap
    flap_2 = create_follower_flap()
    flap_2_obj = doc.addObject("Part::Feature", "Part03FollowerFlap_Right")
    flap_2_obj.Shape = flap_2
    flap_2_obj.Placement = App.Placement(
        App.Vector(26.0 * SCALE, 126.0 * SCALE, BOTTOM_SHELL_THICKNESS + 2.0 * SCALE),
        App.Rotation(App.Vector(0, 0, 1), 0)
    )

    doc.recompute()
    return doc


if __name__ == "__main__":
    doc = build_follower_assembly()
    export_dir = os.path.join(os.path.dirname(__file__), "exports")
    os.makedirs(export_dir, exist_ok=True)

    step_path = os.path.join(export_dir, "assembly_follower_module.step")
    stl_path = os.path.join(export_dir, "assembly_follower_module.stl")

    shapes = [obj.Shape for obj in doc.Objects if hasattr(obj, "Shape")]
    compound = Part.makeCompound(shapes)
    compound.exportStep(step_path)
    compound.exportStl(stl_path)
    print(f"Successfully exported {os.path.basename(step_path)} and {os.path.basename(stl_path)}")
