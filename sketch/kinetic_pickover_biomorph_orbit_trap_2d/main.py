from pathlib import Path
import math
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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Orbit grid parameters (number of complex planes sample points)
GRID_RES = 500

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(3, 5, 12)  # Deep obsidian space


def draw():
    t = py5.frame_count / 60.0
    w, h = float(SIZE[0]), float(SIZE[1])
    aspect = w / h
    
    # 1. Random sample points in the complex plane to prevent grid artifacts
    n_points = int(GRID_RES * GRID_RES * aspect)
    rx = np.random.uniform(-2.2 * aspect, 2.2 * aspect, n_points).astype(np.float32)
    ry = np.random.uniform(-2.2, 2.2, n_points).astype(np.float32)
    z = rx + 1j * ry
    
    # Dynamically morph the complex parameter c and power parameters
    c = -0.55 + 0.12 * math.sin(t * 0.4) + 1j * (0.62 + 0.08 * math.cos(t * 0.35))
    
    # Track orbit history
    n_iters = 11
    history = np.zeros((n_iters, len(z)), dtype=np.complex64)
    escaped = np.zeros(len(z), dtype=bool)
    
    # Iteration loop
    history[0] = z
    for i in range(n_iters - 1):
        # Continuous mathematical mapping (multiplications are 5x faster than complex exponentiation operator **)
        z2 = z * z
        z = np.sin(z) + z2 * math.cos(t * 0.3) + (z2 * z) * math.sin(t * 0.3) + c
        history[i + 1] = z
        # Escape condition (Pickover's biomorph boundary)
        escaped |= (np.abs(np.real(z)) > 7.0) | (np.abs(np.imag(z)) > 7.0)
        
    # 2. Filter orbits that escaped to draw bioluminescent filaments
    # (Leaving behind the classic biological biomorph structures in the interior)
    escaped_orbits = history[:, escaped].flatten()
    
    # Filter out orbits that are extremely far away to prevent int32 overflow during casting
    valid_box = (np.abs(np.real(escaped_orbits)) < 15.0) & (np.abs(np.imag(escaped_orbits)) < 15.0)
    escaped_orbits = escaped_orbits[valid_box]
    
    # Map complex coordinates back to screen pixel space
    sx = ((np.real(escaped_orbits) / (2.2 * aspect) + 1.0) / 2.0 * w).astype(np.int32)
    sy = ((np.imag(escaped_orbits) / 2.2 + 1.0) / 2.0 * h).astype(np.int32)
    
    # Keep only points inside the screen boundaries
    valid = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    sx = sx[valid]
    sy = sy[valid]
    
    # Accumulate hits into a 2D density map
    density_map = np.zeros((int(h), int(w)), dtype=np.float32)
    np.add.at(density_map, (sy, sx), 1.0)
    
    # Log compression and normalization for glow rendering
    density_map = np.log1p(density_map * 22.0)
    max_d = np.max(density_map) + 1e-5
    norm_d = density_map / max_d
    
    # 3. Bio-luminescent palette mapping:
    # Deep Blue-Gray -> Glowing Emerald Green -> Radiant Cyan -> Solar Gold -> Frost White
    r_chan = np.clip(255.0 * (norm_d ** 1.6 * 0.8 + norm_d ** 0.4 * 0.1), 0, 255)
    g_chan = np.clip(255.0 * (norm_d ** 1.1 * 1.5 - norm_d ** 3.0 * 0.6), 0, 255)
    b_chan = np.clip(255.0 * (norm_d ** 2.0 * 1.25), 0, 255)
    
    # Mix background color
    glow_r = 3.0 + 8.0 * norm_d
    glow_g = 5.0 + 12.0 * norm_d
    glow_b = 12.0 + 24.0 * norm_d
    
    r_chan = np.clip(r_chan + glow_r, 0, 255)
    g_chan = np.clip(g_chan + glow_g, 0, 255)
    b_chan = np.clip(b_chan + glow_b, 0, 255)
    
    img_array = np.dstack((r_chan.astype(np.uint8), g_chan.astype(np.uint8), b_chan.astype(np.uint8)))
    img = py5.create_image_from_numpy(img_array, 'RGB')
    
    # Draw image with transparency and overlay to enable smooth motion trails
    py5.tint(255, 35)
    py5.image(img, 0, 0, w, h)
    py5.no_tint()
    
    # Tiny trail dimming overlay
    py5.fill(3, 5, 12, 10)
    py5.no_stroke()
    py5.rect(0, 0, w, h)
    
    # Save frame as JPEG for fast writes
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.jpg")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
