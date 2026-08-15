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

def clear_exports():
    if os.path.exists(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    print(f"Cleared exports directory: {EXPORT_DIR}")

def run_script(script_path):
    rel_path = os.path.relpath(script_path, CURRENT_DIR)
    print(f"\n--- Building {rel_path} ---")
    sys.stdout.flush()
    try:
        env = os.environ.copy()
        # Strip python path overrides so child freecadcmd uses its own bundled python
        env.pop("PYTHONHOME", None)
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [FREECAD_CMD, script_path],
            env=env,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.stdout.flush()
        if result.returncode == 0:
            print(f"  [SUCCESS] {rel_path}")
            return True
        else:
            print(f"  [FAILED] {rel_path} (Exit code: {result.returncode})")
            return False
    except Exception as e:
        print(f"  [FAILED] {rel_path}: {e}")
        return False

def main():
    print("=== Starting Fabrica CAD Export All ===")
    clear_exports()
    
    all_py = sorted(glob.glob(os.path.join(CURRENT_DIR, "*.py")))
    excluded = {"params.py", "export_all.py"}
    
    part_files = [f for f in all_py if os.path.basename(f) not in excluded and not os.path.basename(f).startswith("assembly_")]
    assembly_files = [f for f in all_py if os.path.basename(f).startswith("assembly_")]
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
