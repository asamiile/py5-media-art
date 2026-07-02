from pathlib import Path
import shutil
import subprocess
import sys
import random
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle arrays for accretion disk
NUM_PARTICLES = 8000
angles = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
radii = np.random.uniform(160, 1500, NUM_PARTICLES)
speeds = 60000 / (radii ** 1.6)  # Keplerian velocity profile
z_offsets = np.random.normal(0, 10, NUM_PARTICLES)

# Starfield for gravitational lensing
NUM_STARS = 2000
star_x = np.random.uniform(-3000, 3000, NUM_STARS)
star_y = np.random.uniform(-3000, 3000, NUM_STARS)
star_z = np.random.uniform(-4000, -1000, NUM_STARS)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
def draw():
    py5.background(2)
    
    t = py5.frame_count / 60.0
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    # Camera wobble
    py5.rotate_x(py5.PI / 2.6 + np.sin(t * 0.2) * 0.08)
    py5.rotate_y(t * 0.08)
    
    # Draw background stars with pseudo gravitational lensing distortion
    py5.push_matrix()
    py5.no_stroke()
    for i in range(NUM_STARS):
        x, y, z = star_x[i], star_y[i], star_z[i]
        
        # Simple pseudo-lensing: push points away from the origin in XY plane
        r = np.sqrt(x**2 + y**2)
        if r > 10:
            lens_factor = 1.0 + (50000.0 / (r ** 2 + 1000))
            lx = x * lens_factor
            ly = y * lens_factor
            
            py5.push_matrix()
            py5.translate(lx, ly, z)
            brightness = 30 + 70 * np.sin(t * 2 + i)
            py5.fill(220, 10, brightness)
            py5.box(6)
            py5.pop_matrix()
    py5.pop_matrix()
    
    # Draw accretion disk
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.5)
    
    global angles
    angles += speeds * 0.05
    
    # Vectorized computation for better performance
    r_current = radii - (t * 25)
    r_current = 160 + (r_current % 1340)
    
    x = r_current * np.cos(angles)
    y = r_current * np.sin(angles)
    z = z_offsets * (r_current / 400.0)
    
    speed_factor = speeds * 60
    prev_x = (r_current + 3) * np.cos(angles - speed_factor)
    prev_y = (r_current + 3) * np.sin(angles - speed_factor)
    
    for i in range(NUM_PARTICLES):
        r_c = r_current[i]
        
        if r_c < 300:
            hue = 195 # Ice blue/cyan
            sat = min(100, 20 + (r_c - 160) * 0.6)
            bri = 255
            alpha = 220
        else:
            hue = (25 + (r_c - 300) * 0.02) % 360 # Shifts to orange/red
            sat = 85
            bri = max(0, 220 - (r_c - 300) * 0.15)
            alpha = max(0, 180 - (r_c - 300) * 0.12)
            
        py5.stroke(hue, sat, bri, alpha)
        py5.line(x[i], y[i], z[i], prev_x[i], prev_y[i], z[i])

    py5.blend_mode(py5.BLEND)
    
    # Draw Event Horizon (Black Hole)
    py5.no_stroke()
    py5.fill(0)
    py5.push_matrix()
    py5.sphere_detail(40)
    py5.sphere(155)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
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
