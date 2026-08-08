# Changelog

## 2026-08-08
- Created initial project scaffolding for `cad-designs`, `firmware`, `docs`, and `mobile-app` subdirectories.
- Added `specs/mission.md` detailing the project vision, high-level system architecture, four core deliverables, and roadmap.
- Added system reference images and CAD visuals under `specs/reference-images`.
- Refined CAD design specifications for Fabrica Cloth Folding Robot across `mission.md`, `tech-stack.md`, and `roadmap.md`.
- Implemented Phase 1 parametric foundation script (`params.py`), headless build script (`export_all.py`), executable shell entrypoint (`run.sh`), and standard directory layout.
- Optimized modular 4×3 grid architecture, consolidating the central column into a Monolithic Base Chassis Module and selecting Click-Lock Hollow Dovetail Frame Joiners for toolless assembly and hidden cable routing.
