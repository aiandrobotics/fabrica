SCALE = 1.0

import os

# Build plate dimensions (Default: 256 x 256 x 256 mm; scale down to 180mm using SCALE = 180.0 / 256.0)
BUILD_PLATE_X = 256.0 * SCALE
BUILD_PLATE_Y = 256.0 * SCALE
BUILD_PLATE_Z = 256.0 * SCALE
SCALE_180     = 180.0 / 256.0

# ==============================================================================
# SIZING PROFILES:
# Profile 1 (Default): 256mm Build Plate -> 220mm True Squares (Max part: 244mm <= 245mm)
# Profile 2 (Compact): 180mm Build Plate -> 145mm True Squares (Max part: 169mm <= 170mm)
# ==============================================================================
PANEL_WIDTH              = 220.0 * SCALE  # 220mm True Square
PANEL_HEIGHT             = 220.0 * SCALE  # 220mm True Square
PANEL_THICKNESS          = 12.0 * SCALE
FOLLOWER_PANEL_THICKNESS = 10.0 * SCALE
BASE_PANEL_THICKNESS     = 15.0 * SCALE
FLAP_THICKNESS           = 2.4 * SCALE
PADDLE_THICKNESS         = 2.4 * SCALE

INTERFACE_PANEL_WIDTH     = 240.0 * SCALE
INTERFACE_PANEL_HEIGHT    = 120.0 * SCALE
INTERFACE_PANEL_THICKNESS = 25.0 * SCALE

# FDM Clearances, Tolerances & Walls
FIT_CLEARANCE           = 0.4 * SCALE
PRESS_FIT_CLEARANCE     = 0.2 * SCALE
THREAD_CLEARANCE        = 0.6 * SCALE
WALL_THICKNESS          = 3.0 * SCALE
COSMETIC_WALL_THICKNESS = 2.0 * SCALE

# Aesthetics & Printability Parameters
TEXTURE_HEIGHT         = 0.6 * SCALE
HOLE_CHAMFER           = 0.8 * SCALE
ELEPHANTS_FOOT_CHAMFER = 0.4 * SCALE
CONTROL_DECK_ANGLE     = 15.0
ACCENT_BEVEL_DEPTH     = 1.2 * SCALE

# TPU Dampers, Alignment Reticles & Power Port
TPU_BUMPER_DEPTH     = 1.5 * SCALE
RETICLE_DEBOSS_DEPTH = 0.4 * SCALE
DC_JACK_DIAMETER     = 11.5 * SCALE

# Base Module & Joiner Optimizations (True Sliding Dovetail System)
FOOT_PAD_DIA      = 20.1 * SCALE
FOOT_PAD_DEPTH    = 2.0 * SCALE
JOINER_DETENT     = 0.3 * SCALE
WIRE_PORT_FILLET  = 1.5 * SCALE

# True Sliding Dovetail Geometry (Top-Slide Drop-In Lock)
DOVETAIL_FLOOR_THICKNESS = 3.0 * SCALE  # 3.0mm bottom floor drop stop
DOVETAIL_NECK_WIDTH      = 12.0 * SCALE  # Width at frame seam
DOVETAIL_FLARE_WIDTH     = 18.0 * SCALE  # Flared width inside pocket (locks horizontally)
DOVETAIL_DEPTH           = 12.0 * SCALE  # 12mm deep insertion into frame for high moment stiffness
DOVETAIL_CLEARANCE       = 0.20 * SCALE  # 0.20mm sliding tolerance per side (0.40mm total clearance for smooth FDM assembly)
DOVETAIL_HEIGHT          = BASE_PANEL_THICKNESS - DOVETAIL_FLOOR_THICKNESS  # Exactly 12.0mm for 100% flush deck

# Heavy-Duty Drive Axle & Hex Torque Coupler (Column Synchronous Folding)
PIVOT_Z                   = 10.0 * SCALE  # Axle & Hinge Pivot Center (10.0mm above tabletop for 100% flat bottom across all frames)
DRIVE_SHAFT_DIAMETER      = 13.0 * SCALE  # Ø13mm outer axle diameter (3.5mm ground clearance & 100% flush tabletop)
DRIVE_SHAFT_BORE          = 8.0 * SCALE   # Ø8mm inner weight-relief bore
HEX_COUPLER_SIZE          = 8.0 * SCALE   # 8.0mm Flat-to-Flat standard hex drive interface
HEX_COUPLER_DEPTH         = 12.0 * SCALE  # 12.0mm engagement depth for zero slip under 35kg-cm servo load
BEARING_ROTATING_CLEARANCE = 0.45 * SCALE  # 0.45mm radial clearance (Ø13.9mm frame knuckle bore for friction-free FDM 3D printing rotation)


# ==============================================================================
# MG996R SERVO HARDWARE CONSTANTS (Fixed Physical Dimensions - Never Scaled)
# ==============================================================================
SERVO_MODULE_LENGTH    = 70.0  # Total motor module zone length along Y
SERVO_MODULE_WIDTH     = 72.0  # Enclosure outer width (X = -24.0 to +48.0mm)
SERVO_SPLINE_Y_OFFSET  = 55.0  # Servo spline output axis offset from frame top edge (Y = H - 55.0mm)
SERVO_HORN_ADAPTER_DIA = 19.0  # Ø19mm flange disk for standard MG996R round horn
SERVO_HORN_ADAPTER_LEN = 16.5  # Total adapter length (7mm flange + 9.5mm hex)
SERVO_COVER_WIDTH      = 63.7  # Top snap lid width
SERVO_COVER_LENGTH     = 38.8  # Top snap lid length
SERVO_MOUNT_WIDTH      = 40.5  # MG996R body length
SERVO_MOUNT_DEPTH      = 20.0  # MG996R body width
SERVO_MOUNT_HEIGHT     = 38.0  # MG996R body height
SERVO_HOLE_SPACING_X   = 48.0  # Flange mounting screw pitch
SERVO_HOLE_SPACING_Y   = 10.0
SERVO_SCREW_RADIUS     = 1.7   # M3 screw clearance (Ø3.4mm)

# Standard 4x3 Folding Grid Assembly Layout & Inter-Module Gap
MODULE_GAP        = 10.0 * SCALE  # 10mm fabric relief and cable raceway bridge gap
GRID_ROWS         = 4
GRID_COLS         = 3
TOTAL_GRID_WIDTH  = (PANEL_WIDTH * GRID_COLS) + (MODULE_GAP * (GRID_COLS - 1))
TOTAL_GRID_HEIGHT = (PANEL_HEIGHT * GRID_ROWS) + (MODULE_GAP * (GRID_ROWS - 1))

# Directory Paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR  = os.path.join(PROJECT_DIR, "exports")

if __name__ == "__main__":
    print("=== Fabrica CAD Parameters loaded successfully ===")
    print(f"SCALE: {SCALE}")
    print(f"Build Plate: {BUILD_PLATE_X:.1f} x {BUILD_PLATE_Y:.1f} x {BUILD_PLATE_Z:.1f} mm")
    print(f"Modular Panel: {PANEL_WIDTH:.1f} x {PANEL_HEIGHT:.1f} x {PANEL_THICKNESS:.1f} mm")
    print(f"Interface Panel: {INTERFACE_PANEL_WIDTH:.1f} x {INTERFACE_PANEL_HEIGHT:.1f} x {INTERFACE_PANEL_THICKNESS:.1f} mm")
    print(f"Standard 4x3 Grid Size: {TOTAL_GRID_WIDTH:.1f} x {TOTAL_GRID_HEIGHT:.1f} mm")
    print(f"TPU Bumper Slot: {TPU_BUMPER_DEPTH:.1f} mm | Anti-Slip Feet Sockets: Ø{FOOT_PAD_DIA:.1f} x {FOOT_PAD_DEPTH:.1f} mm")
    print(f"Joiner Click Detent: {JOINER_DETENT:.1f} mm | Dual-Tone Accent Bevel: {ACCENT_BEVEL_DEPTH:.1f} mm")
    print(f"DC Power Jack Port: Ø{DC_JACK_DIAMETER:.1f} mm | Garment Reticle Deboss: {RETICLE_DEBOSS_DEPTH:.1f} mm")
    print(f"Fit Clearance: {FIT_CLEARANCE:.2f} mm | Press Fit Clearance: {PRESS_FIT_CLEARANCE:.2f} mm")
    print(f"Export Path: {EXPORT_DIR}")
