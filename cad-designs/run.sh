#!/usr/bin/env bash
set -e

# Discover FreeCAD CLI binary
if [ -n "$FREECAD_CMD" ] && command -v "$FREECAD_CMD" >/dev/null 2>&1; then
    : # Use environment variable
elif command -v freecadcmd >/dev/null 2>&1; then
    FREECAD_CMD="freecadcmd"
elif command -v FreeCADCmd >/dev/null 2>&1; then
    FREECAD_CMD="FreeCADCmd"
elif command -v freecad >/dev/null 2>&1; then
    FREECAD_CMD="freecad"
else
    FREECAD_CMD="freecadcmd"
fi

# Discover FreeCAD GUI binary
if [ -n "$FREECAD_GUI" ] && command -v "$FREECAD_GUI" >/dev/null 2>&1; then
    : # Use environment variable
elif command -v freecad >/dev/null 2>&1; then
    FREECAD_GUI="freecad"
elif command -v FreeCAD >/dev/null 2>&1; then
    FREECAD_GUI="FreeCAD"
else
    FREECAD_GUI="freecad"
fi

if [[ $# -eq 0 ]]; then
    echo "Usage:"
    echo "  ./run.sh <part_file.py>   Run a part script headlessly"
    echo "  ./run.sh export_all       Regenerate all parts"
    echo "  ./run.sh assembly         Build full assembly"
    echo "  ./run.sh open <name>      Open exports/<name>.step in GUI"
    exit 1
fi

case "$1" in
    open)
        [[ -z "$2" ]] && { echo "Error: specify a name"; exit 1; }
        "$FREECAD_GUI" "exports/$2.step" ;;
    assembly)   "$FREECAD_CMD" assembly.py ;;
    export_all) python3 export_all.py ;;
    *.py)       "$FREECAD_CMD" "$1" ;;
    *)          echo "Unknown command: $1"; exit 1 ;;
esac
