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

NUM_PARTICLES = 60000

# Pre-generate random spherical coordinates for the electron cloud
phi = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
costheta = np.random.uniform(-1, 1, NUM_PARTICLES)
theta = np.arccos(costheta)
base_radius = np.random.uniform(10, 300, NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.2) * 0.2)
    
    # We simulate "Spherical Harmonics" standing waves which govern electron orbitals.
    # We transition smoothly between different orbital shapes (m, l quantum numbers) using time.
    
    m1, l1 = 3, 4
    m2, l2 = 5, 2
    
    # Smooth blend factor between two orbital states
    blend = (py5.sin(t) + 1.0) * 0.5 
    
    # Harmonic 1
    Y1 = np.cos(m1 * phi) * np.sin(l1 * theta)
    # Harmonic 2
    Y2 = np.sin(m2 * phi) * np.cos(l2 * theta)
    
    # Combined interference pattern
    interference = (Y1 * blend + Y2 * (1.0 - blend))
    
    # The probability density modifies the radius
    # Areas of high interference get pushed outward and glow brighter
    density = np.abs(interference)
    r = base_radius + density * 150.0
    
    # Convert back to Cartesian
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    py5.stroke_weight(2.0)
    
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        d = density[i]
        
        # Only draw particles where probability density is high enough, 
        # creating distinct orbital lobes and nodes (empty spaces).
        if d > 0.15:
            # Hue shifts based on the phase of the wavefunction
            phase = interference[i]
            hue = (180 + phase * 60 + t * 20) % 360
            
            # Brightness is proportional to density
            brightness = py5.remap(d, 0.15, 1.0, 30, 100)
            
            py5.stroke(hue, 80, brightness, 40)
            py5.vertex(x[i], y[i], z[i])
            
    py5.end_shape()

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
