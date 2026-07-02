"""
hyper_chromatic_glitch_fold
===========================
A high-density data matrix folding and tearing itself apart, bleeding brilliant 
spectral colors as its structural integrity collapses under recursive glitches.
"""

from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes
from lib.safety import apply_anti_flicker_filter

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_FRAME = TOTAL_FRAMES // 2


def make_data_matrix(W, H, t, fc):
    x = np.arange(W, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    
    np.random.seed(fc)
    
    # 1. Global warping field
    warp_x = np.sin(Y * 0.005 + t) * 80 * np.sin(t * 0.8)
    warp_y = np.cos(X * 0.007 - t * 1.2) * 60 * np.cos(t * 0.5)
    
    Xw = X + warp_x
    Yw = Y + warp_y
    
    # 2. Folding (structural displacement)
    fold = np.sin(Xw * 0.002 + Yw * 0.003) > 0
    Xw = np.where(fold, Xw + 100, Xw - 50)
    Yw = np.where(fold, Yw - 80, Yw + 40)
    
    # 3. Horizontal Tearing
    tear_intensity = np.clip(np.sin(t * 1.5) ** 7, 0, 1) * 400
    
    row_is_torn_thick = np.random.rand(H, 1) < (0.01 + 0.05 * tear_intensity / 400)
    row_shift_thick = (np.random.rand(H, 1) - 0.5) * tear_intensity * 2
    
    row_is_torn_thin = np.random.rand(H, 1) < (0.05 + 0.1 * tear_intensity / 400)
    row_shift_thin = (np.random.rand(H, 1) - 0.5) * tear_intensity * 0.5
    
    Xw = Xw + row_is_torn_thick * row_shift_thick + row_is_torn_thin * row_shift_thin
    
    # 4. Grid generation
    def grid_lines(x_c, y_c, scale, thickness):
        return ((x_c % scale) < thickness) | ((y_c % scale) < thickness)
    
    g1 = grid_lines(Xw, Yw, 150, 6).astype(np.float32)
    g2 = grid_lines(Xw + t*50, Yw - t*30, 60, 2).astype(np.float32)
    
    block_x = (Xw // 15).astype(np.int32)
    block_y = (Yw // 15).astype(np.int32)
    block_hash = (block_x * 73856093 ^ block_y * 19349663 ^ fc) % 100
    g3 = ((block_hash > 85) & ((Xw % 15) < 12) & ((Yw % 15) < 12)).astype(np.float32)
    
    # Attenuate matrix to create depth/shadows
    patch_mask = np.sin(Xw * 0.01) * np.cos(Yw * 0.01)
    attenuate = patch_mask > -0.2
    
    g1 = np.where(attenuate, g1, g1 * 0.1)
    g2 = np.where(attenuate, g2, g2 * 0.1)
    g3 = np.where(attenuate, g3, g3 * 0.1)
    
    return g1, g2, g3, tear_intensity


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    print(f"[{WORK_NAME}] Setup OK  canvas={SIZE[0]}x{SIZE[1]}")


def draw():
    W, H = SIZE
    fc = py5.frame_count
    t = fc / 60.0
    
    g1, g2, g3, tear_intensity = make_data_matrix(W, H, t, fc)
    
    # Chromatic aberration
    aberration_max = 5 + int((tear_intensity / 400) * 40)
    shift_r = np.random.randint(-aberration_max, aberration_max + 1)
    shift_b = np.random.randint(-aberration_max, aberration_max + 1)
    
    # Color mixing:
    # g1 -> Electric Cyan (0, 255, 255)
    # g2 -> Cyber Magenta (255, 0, 255)
    # g3 -> Solar Gold (255, 200, 0)
    
    R_base = g2 * 255 + g3 * 255
    G_base = g1 * 255 + g3 * 200
    B_base = g1 * 255 + g2 * 255
    
    R = np.roll(R_base, shift_r, axis=1).astype(np.int16)
    G = G_base.astype(np.int16)
    B = np.roll(B_base, shift_b, axis=1).astype(np.int16)
    
    # Background (Obsidian Black)
    R += 10
    G += 10
    B += 10
    
    # Glitch scanlines
    scanlines = (np.random.rand(H, 1) > 0.95) * (np.random.rand(1, W) > 0.5) * 50
    R += scanlines.astype(np.int16)
    G += scanlines.astype(np.int16)
    B += scanlines.astype(np.int16)
    
    R = np.clip(R, 0, 255).astype(np.uint8)
    G = np.clip(G, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)
    
    py5.load_np_pixels()
    # Handle both Retina and non-Retina sizes safely
    ah, aw = py5.np_pixels.shape[:2]
    
    # For safety, take minimum of screen array and generated array bounds
    bh = min(ah, H)
    bw = min(aw, W)
    
    py5.np_pixels[:bh, :bw, 0] = 255
    py5.np_pixels[:bh, :bw, 1] = R[:bh, :bw]
    py5.np_pixels[:bh, :bw, 2] = G[:bh, :bw]
    py5.np_pixels[:bh, :bw, 3] = B[:bh, :bw]
    py5.update_np_pixels()
    
    apply_anti_flicker_filter(0.5)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % FPS == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc == PREVIEW_FRAME:
        # Save a preview snapshot early
        # Note: ffmpeg will also save a mid frame but this ensures we have one immediately.
        # Actually py5-templates handles the mid snapshot via ffmpeg, but since we are doing
        # our own output.mp4, we can let py5 save the snapshot right now.
        pass

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")


py5.run_sketch()
