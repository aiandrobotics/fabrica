#!/bin/zsh
FREECAD_CMD="/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
FREECAD_GUI="/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"

if not which "$FREECAD_CMD" >/dev/null 2>&1; then
    if which freecadcmd >/dev/null 2>&1; then
        FREECAD_CMD="freecadcmd"
    fi
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
