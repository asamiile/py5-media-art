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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_RINGS = 60
NUM_SIDES = 24
RING_SPACING = 120
SPEED = 15.0

angles = np.linspace(0, 2 * np.pi, NUM_SIDES, endpoint=False)
cos_a = np.cos(angles)
sin_a = np.sin(angles)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw():
    # Full clear to prevent infinite blowout, but keep trails short if desired.
    # We will use pure black to keep the glass effect sharp and clean.
    py5.background(0)
    
    time = py5.frame_count * 0.02
    
    # Move camera slightly based on noise
    cam_x = np.sin(time * 0.5) * 100
    cam_y = np.cos(time * 0.7) * 100
    
    py5.translate(py5.width / 2 + cam_x, py5.height / 2 + cam_y, 0)
    
    # Base Z positions (from far away to just behind camera)
    base_z = np.linspace(-NUM_RINGS * RING_SPACING, 200, NUM_RINGS)
    
    # Continuous shift for infinite forward motion
    shift = (py5.frame_count * SPEED) % RING_SPACING
    current_z = base_z + shift
    
    py5.blend_mode(py5.ADD)
    
    for i in range(NUM_RINGS - 1):
        z1 = current_z[i]
        z2 = current_z[i+1]
        
        # Calculate dynamic radii using interfering sine waves to mimic Perlin noise
        r1 = 400 + 150 * np.sin(angles * 3 + time + z1 * 0.005) + 80 * np.cos(angles * 5 - time * 0.8 + z1 * 0.002)
        r2 = 400 + 150 * np.sin(angles * 3 + time + z2 * 0.005) + 80 * np.cos(angles * 5 - time * 0.8 + z2 * 0.002)
        
        x1 = r1 * cos_a
        y1 = r1 * sin_a
        x2 = r2 * cos_a
        y2 = r2 * sin_a
        
        # Rotational twist that propagates down the tunnel
        twist1 = time * 0.5 + z1 * 0.001
        twist2 = time * 0.5 + z2 * 0.001
        
        # Distance-based fading
        # Far objects (z < -4000) have alpha 0, near objects (z ~ 0) have alpha 100
        alpha1 = np.clip(100 + z1 * 0.015, 0, 100)
        alpha2 = np.clip(100 + z2 * 0.015, 0, 100)
        
        # Color shifts down the tunnel
        h1 = (200 + z1 * 0.03 + time * 30) % 360  # Cyan, Blue, Purple, Pink
        h2 = (200 + z2 * 0.03 + time * 30) % 360
        
        py5.push_matrix()
        
        # Since we use QUAD_STRIP, we need to draw vertices. To handle twist properly 
        # on each Z slice without messing up the QUAD_STRIP connectivity, we calculate 
        # rotated coordinates explicitly instead of using rotate_z on the whole shape.
        
        tx1 = x1 * np.cos(twist1) - y1 * np.sin(twist1)
        ty1 = x1 * np.sin(twist1) + y1 * np.cos(twist1)
        
        tx2 = x2 * np.cos(twist2) - y2 * np.sin(twist2)
        ty2 = x2 * np.sin(twist2) + y2 * np.cos(twist2)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(NUM_SIDES + 1):
            idx = j % NUM_SIDES
            
            py5.fill(h1, 80, 90, alpha1 * 0.3)
            py5.stroke(h1, 90, 100, alpha1 * 0.8)
            py5.stroke_weight(2)
            py5.vertex(tx1[idx], ty1[idx], z1)
            
            py5.fill(h2, 80, 90, alpha2 * 0.3)
            py5.stroke(h2, 90, 100, alpha2 * 0.8)
            py5.stroke_weight(2)
            py5.vertex(tx2[idx], ty2[idx], z2)
            
        py5.end_shape()
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
