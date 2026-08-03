import math
import shutil
import subprocess
import sys
from pathlib import Path
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"

# 15 seconds @ 60 FPS (900 frames)
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Simulation scale (960x540 for optimized rendering performance, upscaled to 4K in hardware)
SIM_W, SIM_H = 960, 540

# Optical physics constants
N_IOR = 1.38  # Soap film refractive index
D_MIN = 120.0  # Minimum film thickness (nm)
D_MAX = 800.0  # Maximum film thickness (nm)

# Wavelength arrays (380 to 700 nm, 15 nm steps for optimized rendering speed)
WL_START, WL_END, WL_STEP = 380, 700, 15
WL = np.arange(WL_START, WL_END + WL_STEP, WL_STEP, dtype=np.float64)
N_WL = len(WL)

# Precomputed color matching functions approximation (CIE 1931)
def cie_gauss(wl):
    x = (
        1.056 * np.exp(-0.5 * ((wl - 599.8) / 37.9) ** 2)
        + 0.362 * np.exp(-0.5 * ((wl - 442.0) / 16.0) ** 2)
        - 0.065 * np.exp(-0.5 * ((wl - 501.1) / 20.4) ** 2)
    )
    y = 0.821 * np.exp(-0.5 * ((wl - 568.8) / 46.9) ** 2) + 0.286 * np.exp(
        -0.5 * ((wl - 530.9) / 16.3) ** 2
    )
    z = 1.217 * np.exp(-0.5 * ((wl - 437.0) / 11.8) ** 2) + 0.681 * np.exp(
        -0.5 * ((wl - 459.0) / 26.0) ** 2
    )
    return np.clip(x, 0, None), np.clip(y, 0, None), np.clip(z, 0, None)

CMF_X, CMF_Y, CMF_Z = cie_gauss(WL)

# XYZ to sRGB conversion matrix (D65 white point)
XYZ_TO_RGB = np.array([
    [ 3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [ 0.0557, -0.2040,  1.0570]
], dtype=np.float64)

# Precomputed pure spectrum RGB colors for HUD color bar
pure_wl_colors = []

# CIE 1931 horseshoe border points
cie_horseshoe_pts = []

# Meshgrid for vectorized calculations
grid_x, grid_y = np.meshgrid(
    np.linspace(-1.0, 1.0, SIM_W),
    np.linspace(-1.0, 1.0, SIM_H)
)
# Distances from center
bubble_r_sim = 0.72
dist_grid = np.hypot(grid_x, grid_y)
bubble_mask = dist_grid <= bubble_r_sim

def precompute_optics():
    global pure_wl_colors, cie_horseshoe_pts
    
    # 1. Precompute pure monochromatic colors
    for w in WL:
        x, y, z = cie_gauss(np.array([w]))
        white_sum = CMF_X.sum() + CMF_Y.sum() + CMF_Z.sum()
        xyz = np.array([x[0], y[0], z[0]]) / (white_sum / 3.0)
        rgb = XYZ_TO_RGB @ xyz
        # Clip negative out-of-gamut values to avoid power of negative warning
        rgb = np.clip(rgb, 0, None)
        # Gamma correction
        rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1.0 / 2.4) - 0.055)
        rgb = np.clip(rgb, 0, 1)
        pure_wl_colors.append((int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)))
        
    # 2. Precompute CIE 1931 horseshoe boundary coordinates
    for w in np.linspace(380, 700, 80):
        cx, cy, cz = cie_gauss(np.array([w]))
        total = cx[0] + cy[0] + cz[0] + 1e-9
        cie_horseshoe_pts.append((cx[0] / total, cy[0] / total))

# Resolution variables
pimg = None

def setup():
    global pimg
    py5.size(*SIZE)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Image buffer (always exactly 1920x1080 pixels on CPU heap, ignoring high-DPI scaling)
    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)
    precompute_optics()

def get_swirling_thickness(frame):
    # Vectorized plasma-convection flow field using domain-warped waves in NumPy
    t = frame * 0.022
    
    # Coordinate warping displacements (simulating fluid convection swirls)
    warp_x = grid_x * 2.2 + np.sin(grid_y * 2.4 + t) * 0.45 + np.cos(grid_x * 1.5 - t * 0.8) * 0.3
    warp_y = grid_y * 2.2 + np.cos(grid_x * 2.4 - t) * 0.45 + np.sin(grid_y * 1.5 + t * 0.8) * 0.3
    
    # Swirling thickness perturbations
    plasma = np.sin(warp_x * 2.5) * 0.35 + np.cos(warp_y * 2.0) * 0.35
    plasma += np.sin(np.hypot(warp_x, warp_y) * 4.0 - t * 2.0) * 0.2
    
    # Gravitational drainage thickness gradient: thin at top, thick at bottom
    # We map y from [-0.72, 0.72] to thickness
    d_base = D_MIN + (0.72 - grid_y) / (2.0 * 0.72) * (D_MAX - D_MIN)
    
    # Apply swirling disturbances
    d = d_base + plasma * 180.0
    return np.clip(d, D_MIN, D_MAX)

def draw():
    fc = py5.frame_count
    
    # 1. Compute dynamic thickness
    thickness = get_swirling_thickness(fc)
    
    # 2. Vectorized CIE Spectral Reflectance sRGB calculations
    # Convert thickness array to shape (H, W, 1) and broadcast over wavelengths
    d_3d = thickness[:, :, np.newaxis]
    opd = 2.0 * N_IOR * d_3d  # Shape (H, W, 1)
    
    # Wavelength broadcasting array: shape (1, 1, N_WL)
    wl_3d = WL[np.newaxis, np.newaxis, :]
    
    # Calculate phase difference including the pi phase shift at first reflection boundary
    phase = np.pi + 2.0 * np.pi * opd / wl_3d  # Shape (H, W, N_WL)
    intensity = np.cos(phase * 0.5) ** 2  # Shape (H, W, N_WL)
    
    # Integrate CIE matching channels over spectrum
    x_sum = np.sum(intensity * CMF_X, axis=2) / CMF_X.sum()
    y_sum = np.sum(intensity * CMF_Y, axis=2) / CMF_Y.sum()
    z_sum = np.sum(intensity * CMF_Z, axis=2) / CMF_Z.sum()
    
    # Combine XYZ channels
    xyz = np.stack([x_sum, y_sum, z_sum], axis=-1)  # Shape (H, W, 3)
    
    # Convert XYZ to sRGB
    rgb = xyz.reshape(-1, 3) @ XYZ_TO_RGB.T
    
    # Clip negative out-of-gamut values to avoid power of negative warning
    rgb = np.clip(rgb, 0, None)
    
    # sRGB Gamma Correction
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1.0 / 2.4) - 0.055)
    rgb = np.clip(rgb, 0, 1)
    rgb_img = rgb.reshape(SIM_H, SIM_W, 3)
    
    # Apply circular mask for the bubble membrane
    final_rgb = np.zeros_like(rgb_img)
    final_rgb[bubble_mask] = rgb_img[bubble_mask]
    
    # 3. Blit to Py5Image pixels (packed 32-bit ARGB values)
    r8 = (final_rgb[:, :, 0] * 255).astype(np.uint8)
    g8 = (final_rgb[:, :, 1] * 255).astype(np.uint8)
    b8 = (final_rgb[:, :, 2] * 255).astype(np.uint8)
    a8 = np.where(bubble_mask, 255, 0).astype(np.uint8)
    
    # Pack channels in Processing ARGB format: A << 24 | R << 16 | G << 8 | B
    argb = (
        (a8.astype(np.int32) << 24)
        | (r8.astype(np.int32) << 16)
        | (g8.astype(np.int32) << 8)
        | b8.astype(np.int32)
    )
    
    pimg.load_pixels()
    pimg.pixels[:] = argb.flatten()
    pimg.update_pixels()
    
    # 4. Draw to 4K Canvas
    py5.background(5, 5, 10)  # Deep Obsidian Void
    
    # Draw offscreen bubble image (py5 handles hardware upscaling)
    py5.image(pimg, 0, 0, py5.width, py5.height)
    
    # Scale calculations
    scale_x = py5.width / SIM_W
    scale_y = py5.height / SIM_H
    
    # 5. Physics scanning target radar (rotates on the bubble surface)
    scan_r = bubble_r_sim * 0.75
    scan_angle = fc * 0.015
    sx_sim = SIM_W/2 + math.cos(scan_angle) * scan_r * (SIM_H/2)
    sy_sim = SIM_H/2 + math.sin(scan_angle) * scan_r * (SIM_H/2)
    
    sx_4k = sx_sim * scale_x
    sy_4k = sy_sim * scale_y
    
    # Draw scan target crosshairs
    py5.stroke(255, 160, 20, 180)
    py5.stroke_weight(1.5)
    py5.no_fill()
    py5.circle(sx_4k, sy_4k, 24)
    py5.line(sx_4k - 20, sy_4k, sx_4k + 20, sy_4k)
    py5.line(sx_4k, sy_4k - 20, sx_4k, sy_4k + 20)
    
    # Sample scanned thickness
    sim_px = int(np.clip(sx_sim, 0, SIM_W - 1))
    sim_py = int(np.clip(sy_sim, 0, SIM_H - 1))
    scanned_d = thickness[sim_py, sim_px]
    
    # 6. Real-time Reflection Spectrometer Panel (top-right corner)
    spec_x, spec_y = py5.width - 450, 100
    spec_w, spec_h = 350, 180
    
    py5.fill(10, 12, 22, 180)
    py5.stroke(0, 220, 255, 60)
    py5.stroke_weight(2)
    py5.rect(spec_x - 15, spec_y - 35, spec_w + 30, spec_h + 105)
    
    py5.fill(0, 220, 255, 220)
    py5.text_size(14)
    py5.text("REFLECTANCE SPECTROMETER (380-700 nm)", spec_x, spec_y - 12)
    
    # Draw spectrometer grid lines
    py5.stroke(0, 220, 255, 30)
    py5.stroke_weight(1)
    for grid_idx in range(5):
        gy = spec_y + grid_idx * (spec_h / 4)
        py5.line(spec_x, gy, spec_x + spec_w, gy)
        gx = spec_x + grid_idx * (spec_w / 4)
        py5.line(gx, spec_y, gx, spec_y + spec_h)
        
    # Compute spectrometer reflectance curve for scanned point
    spec_opd = 2.0 * N_IOR * scanned_d
    spec_phase = np.pi + 2.0 * np.pi * spec_opd / WL
    spec_intensity = np.cos(spec_phase * 0.5) ** 2
    
    # Plot intensity curve
    py5.stroke(255, 160, 20, 240)
    py5.stroke_weight(2.5)
    py5.no_fill()
    py5.begin_shape()
    for idx, w in enumerate(WL):
        wx = spec_x + (w - WL_START) / (WL_END - WL_START) * spec_w
        wy = spec_y + spec_h - (spec_intensity[idx] * spec_h)
        py5.vertex(wx, wy)
    py5.end_shape()
    
    # Draw spectrum color bar below plot
    bar_y = spec_y + spec_h + 15
    bar_h = 16
    for idx, (r, g, b) in enumerate(pure_wl_colors):
        wx = spec_x + idx * (spec_w / N_WL)
        py5.fill(r, g, b)
        py5.no_stroke()
        py5.rect(wx, bar_y, (spec_w / N_WL) + 1, bar_h)
        
    # Spectrum border
    py5.stroke(0, 220, 255, 80)
    py5.stroke_weight(1)
    py5.no_fill()
    py5.rect(spec_x, bar_y, spec_w, bar_h)
    
    py5.fill(255, 200)
    py5.text_size(11)
    py5.text("380 nm", spec_x, bar_y + 30)
    py5.text("540 nm", spec_x + spec_w / 2 - 15, bar_y + 30)
    py5.text("700 nm", spec_x + spec_w - 40, bar_y + 30)

    # 7. CIE 1931 Chromaticity Panel (bottom-left corner)
    cie_x, cie_y = 100, py5.height - 380
    cie_w, cie_h = 240, 240
    
    py5.fill(10, 12, 22, 180)
    py5.stroke(0, 220, 255, 60)
    py5.stroke_weight(2)
    py5.rect(cie_x - 15, cie_y - 35, cie_w + 30, cie_h + 55)
    
    py5.fill(0, 220, 255, 220)
    py5.text_size(14)
    py5.text("CIE 1931 CHROMATICITY SPACE", cie_x, cie_y - 12)
    
    # Draw CIE horseshoe boundary
    py5.no_fill()
    py5.stroke(0, 220, 255, 120)
    py5.stroke_weight(1.5)
    py5.begin_shape()
    for hx, hy in cie_horseshoe_pts:
        # Map [0, 0.85] coordinates to panel size
        px = cie_x + (hx / 0.85) * cie_w
        py = cie_y + cie_h - (hy / 0.85) * cie_h
        py5.vertex(px, py)
    py5.end_shape(py5.CLOSE)
    
    # Compute active scan dot CIE coordinates
    scanned_x, scanned_y, scanned_z = cie_gauss(WL)
    scanned_X = np.sum(spec_intensity * scanned_x)
    scanned_Y = np.sum(spec_intensity * scanned_y)
    scanned_Z = np.sum(spec_intensity * scanned_z)
    
    cie_sum = scanned_X + scanned_Y + scanned_Z + 1e-9
    sc_x = scanned_X / cie_sum
    sc_y = scanned_Y / cie_sum
    
    # Draw scanned chromaticity coordinates inside horseshoe
    coord_x = cie_x + (sc_x / 0.85) * cie_w
    coord_y = cie_y + cie_h - (sc_y / 0.85) * cie_h
    
    py5.fill(255, 160, 20, 230)
    py5.no_stroke()
    py5.circle(coord_x, coord_y, 8)
    
    # Draw crosshair lines for coordinates
    py5.stroke(255, 160, 20, 80)
    py5.stroke_weight(1)
    py5.line(cie_x, coord_y, cie_x + cie_w, coord_y)
    py5.line(coord_x, cie_y, coord_x, cie_y + cie_h)

    # 8. Laboratory HUD Telemetry
    py5.stroke(0, 220, 255, 90)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.rect(40, 40, py5.width - 80, py5.height - 80)
    
    # Corner targets
    for tx, ty in [(40, 40), (py5.width - 40, 40), (40, py5.height - 40), (py5.width - 40, py5.height - 40)]:
        py5.stroke(0, 220, 255, 180)
        py5.stroke_weight(3)
        py5.line(tx - 20, ty, tx + 20, ty)
        py5.line(tx, ty - 20, tx, ty + 20)

    # Telemetry text (top-left)
    py5.fill(0, 220, 255, 220)
    py5.text_size(24)
    py5.text("SYSTEM: MONOCHROMATIC WAVE INTERFERENCE", 80, 100)
    
    py5.text_size(18)
    py5.fill(255, 200)
    py5.text(f"REFRACTIVE INDEX (n) : {N_IOR:.2f} (WATER/SOAP)", 80, 145)
    py5.text(f"MEMBRANE RADIUS (R)  : {int(bubble_r_sim*SIM_H/2)} nm (SIMULATED)", 80, 175)
    py5.text(f"SCANNED THICKNESS (d): {scanned_d:.1f} nm", 80, 205)
    py5.text(f"CIE CHROMATICITY (xy): ({sc_x:.3f}, {sc_y:.3f})", 80, 235)

    # Progress bar (top-right)
    bar_width = 300
    bar_x = py5.width - 80 - bar_width
    bar_y = py5.height - 90
    py5.no_fill()
    py5.stroke(0, 220, 255, 100)
    py5.stroke_weight(2)
    py5.rect(bar_x, bar_y, bar_width, 16)
    
    py5.fill(0, 220, 255, 180)
    py5.no_stroke()
    py5.rect(bar_x + 2, bar_y + 2, (bar_width - 4) * (fc / TOTAL_FRAMES), 12)
    
    py5.fill(255, 220)
    py5.text_size(18)
    py5.text(f"FRAME RENDER : {fc} / {TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)", bar_x, bar_y - 15)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if blank screen
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {fc} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress logging
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame has beautiful swirls)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
