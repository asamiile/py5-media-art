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

NUM_SEEDS = 3000
GOLDEN_ANGLE = 137.5077640500378546463487 * (np.pi / 180.0)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
def draw():
    py5.background(10)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Slowly rotate the entire sunflower
    py5.rotate_z(t * 0.1)
    # Give it a slight 3D tilt
    py5.rotate_x(py5.sin(t * 0.2) * 0.3)
    py5.rotate_y(py5.cos(t * 0.2) * 0.3)
    
    # We modulate the "divergence angle" slightly away from the exact golden angle
    # This causes the spiral arms to warp, twist, and form new interference patterns over time
    angle_offset = py5.sin(t * 0.5) * 0.005
    current_angle = GOLDEN_ANGLE + angle_offset
    
    # Scaling factor for the distance of seeds from the center
    c = 15.0 + py5.sin(t) * 2.0
    
    for i in range(1, NUM_SEEDS):
        # Phyllotaxis math: r = c * sqrt(n), theta = n * 137.5
        r = c * np.sqrt(i)
        theta = i * current_angle
        
        # Add a 3D Z-height based on distance and time to make it a dome/cone
        z = py5.sin(r * 0.01 - t * 2) * 100 - r * 0.2
        
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        # Color based on angle and radius
        hue = (i * 0.1 + r * 0.2 + t * 40) % 360
        
        # Size gets larger towards the edge
        size = 3 + (r / 200.0) * 4
        
        py5.push_matrix()
        py5.translate(x, y, z)
        # Point the seed outward and rotate it
        py5.rotate_z(theta + t)
        
        # Inner seeds glow brighter
        brightness = py5.remap(i, 0, NUM_SEEDS, 100, 40)
        py5.fill(hue, 80, brightness, 90)
        
        # Draw the "seed" as a small elongated diamond/petal
        py5.begin_shape()
        py5.vertex(0, -size)
        py5.vertex(size/2, 0)
        py5.vertex(0, size)
        py5.vertex(-size/2, 0)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

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
