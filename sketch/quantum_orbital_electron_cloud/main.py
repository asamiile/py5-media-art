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

NUM_ELECTRONS = 50000

# We use spherical coordinates (r, theta, phi) to model the electron cloud
radii = np.random.normal(300, 100, NUM_ELECTRONS).astype(np.float32)
thetas = np.random.uniform(0, np.pi * 2, NUM_ELECTRONS).astype(np.float32)
phis = np.random.uniform(0, np.pi, NUM_ELECTRONS).astype(np.float32)

# Rotational velocities for the electrons
d_theta = np.random.normal(0, 0.05, NUM_ELECTRONS).astype(np.float32)
d_phi = np.random.normal(0, 0.02, NUM_ELECTRONS).astype(np.float32)
d_r = np.random.normal(0, 1.5, NUM_ELECTRONS).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Subtle motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.2) * 0.5)
    
    global radii, thetas, phis
    
    # Quantum probability update (electrons jitter and orbit)
    thetas += d_theta
    phis += d_phi
    radii += d_r
    
    # Add a spherical harmonic-like probability density bias
    # We modulate the radius based on theta and phi to create lobed shapes (like p or d orbitals)
    prob_bias = np.abs(np.cos(thetas * 2) * np.sin(phis * 3)) * 50
    effective_radii = radii + prob_bias
    
    # Keep radii constrained
    radii = np.clip(radii, 50, 600)
    
    # Convert spherical to Cartesian
    x = effective_radii * np.sin(phis) * np.cos(thetas)
    y = effective_radii * np.sin(phis) * np.sin(thetas)
    z = effective_radii * np.cos(phis)
    
    # Color depends on distance from nucleus
    colors = (effective_radii * 0.8 + t * 50) % 360
    
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    
    for i in range(NUM_ELECTRONS):
        py5.stroke(colors[i], 80, 100, 30)
        py5.vertex(x[i], y[i], z[i])
        
    py5.end_shape()
    
    # Draw the nucleus
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 100, 100)
    py5.sphere_detail(12)
    py5.sphere(15)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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
            
        import os
        os._exit(0)

py5.run_sketch()
