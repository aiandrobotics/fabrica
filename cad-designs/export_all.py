import os
import sys
import glob
import shutil
import subprocess

FREECAD_CMD = "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
if not os.path.exists(FREECAD_CMD):
    FREECAD_CMD = "freecadcmd"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(CURRENT_DIR, "exports")
PARTS_DIR = os.path.join(CURRENT_DIR, "parts")
ASSEMBLIES_DIR = os.path.join(CURRENT_DIR, "assemblies")

def clear_exports():
    if os.path.exists(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    print(f"Cleared exports directory: {EXPORT_DIR}")

def run_script(script_path):
    rel_path = os.path.relpath(script_path, CURRENT_DIR)
    print(f"\n--- Building {rel_path} ---")
    try:
        result = subprocess.run(
            [FREECAD_CMD, script_path],
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout + result.stderr
        for line in output.splitlines():
            if any(k in line for k in ["Exported", "Error", "Exception", "Traceback", "Warning"]):
                print(f"  {line}")
        if result.returncode == 0 and "Traceback" not in output:
            print(f"  [SUCCESS] {rel_path}")
            return True
        else:
            print(f"  [FAILED] {rel_path} (Exit code: {result.returncode})")
            return False
    except Exception as e:
        print(f"  [ERROR] Failed to run {rel_path}: {e}")
        return False

def main():
    print("=== Starting Fabrica CAD Export All ===")
    clear_exports()
    
    part_files = sorted(glob.glob(os.path.join(PARTS_DIR, "part_*.py")))
    assembly_files = sorted(glob.glob(os.path.join(ASSEMBLIES_DIR, "assembly_*.py")))
    all_scripts = part_files + assembly_files
    
    if not all_scripts:
        print("No part or assembly scripts found to process.")
        return
    
    passed = 0
    total = len(all_scripts)
    
    for script in all_scripts:
        if run_script(script):
            passed += 1
            
    print(f"\n==========================================")
    print(f"Export All Summary: {passed}/{total} scripts built successfully.")
    print(f"==========================================")
    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
