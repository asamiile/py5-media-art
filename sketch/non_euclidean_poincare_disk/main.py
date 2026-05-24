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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # We will do a pixel-shader style render directly manipulating np_pixels
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    H, W = pixels.shape[0], pixels.shape[1]
    
    # Create coordinate grid
    y, x = np.mgrid[0:H, 0:W]
    
    # Map to complex plane [-1.2, 1.2]
    # Center at 0,0
    scale = min(W, H) / 2.2
    cx = (x - W/2) / scale
    cy = (y - H/2) / scale
    
    # Complex coordinate z
    z = cx + 1j * cy
    
    # Inside unit disk mask
    r2 = np.abs(z)**2
    mask = r2 < 1.0
    
    # Apply Mobius transformation to translate in hyperbolic space
    # Translation parameter a
    # We animate a moving from center towards the boundary to simulate zooming
    # Let's make it a smooth oscillation or continuous movement
    # a = tanh(distance) * exp(i * angle)
    
    dist = (t * 10.0) % 2.0  # Just a continuous driving distance
    # To avoid snapping, we can make it a continuous loop if we carefully choose the transformation,
    # but since t goes from 0 to 1, we can just sweep.
    # Actually, a smooth path in the Poincare disk:
    a = np.tanh(t * 8.0 - 4.0) * np.exp(1j * (t * np.pi * 2.0))
    
    # z' = (z + a) / (1 + conj(a)*z)
    z_prime = (z + a) / (1.0 + np.conj(a) * z)
    
    # Now we use z_prime to evaluate a pattern
    # Convert z_prime back to polar
    r_prime = np.abs(z_prime)
    theta_prime = np.angle(z_prime)
    
    # To make a pattern that looks like a tessellation, we can use log(1-r_prime) or similar,
    # but a simple mapping is mapping the hyperbolic distance from origin:
    # d_H = argtanh(r_prime)
    d_H = np.arctanh(np.clip(r_prime, 0.0, 0.9999))
    
    # Pattern based on d_H and theta_prime
    # We create a pseudo-tessellation with sin waves
    val = np.sin(d_H * 20.0) * np.cos(theta_prime * 7.0 + d_H * 5.0)
    
    # Color mapping
    # Base background (outside disk)
    out_r = np.full((H, W), 5, dtype=np.uint8)
    out_g = np.full((H, W), 0, dtype=np.uint8)
    out_b = np.full((H, W), 10, dtype=np.uint8)
    
    # Map val [-1, 1] to colors for inside the disk
    # Cyan-Emerald-Violet
    v_norm = (val[mask] + 1.0) * 0.5 # 0 to 1
    
    r_in = (np.sin(v_norm * np.pi * 2.0 + 0.0) * 127 + 128).astype(np.uint8)
    g_in = (np.sin(v_norm * np.pi * 2.0 + 2.0) * 127 + 128).astype(np.uint8)
    b_in = (np.sin(v_norm * np.pi * 2.0 + 4.0) * 127 + 128).astype(np.uint8)
    
    # Add a glowing boundary
    boundary_glow = np.exp(-(1.0 - r2[mask]) * 20.0)
    
    r_in = np.clip(r_in + boundary_glow * 255, 0, 255).astype(np.uint8)
    g_in = np.clip(g_in + boundary_glow * 100, 0, 255).astype(np.uint8)
    b_in = np.clip(b_in + boundary_glow * 255, 0, 255).astype(np.uint8)
    
    out_r[mask] = r_in
    out_g[mask] = g_in
    out_b[mask] = b_in
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = out_r
    pixels[:, :, 2] = out_g
    pixels[:, :, 3] = out_b
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
