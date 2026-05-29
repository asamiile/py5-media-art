from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spherical harmonics nodes
NUM_POINTS = 50000
points = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 8, 8)  # Very dark warm grey
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global points
    points = np.zeros((NUM_POINTS, 3))
    # Random spherical coordinates
    theta = np.random.rand(NUM_POINTS) * 2 * np.pi
    phi = np.arccos(2 * np.random.rand(NUM_POINTS) - 1)
    
    # Base radius 1
    points[:, 0] = np.sin(phi) * np.cos(theta)
    points[:, 1] = np.sin(phi) * np.sin(theta)
    points[:, 2] = np.cos(phi)

def draw():
    global points
    
    # Slight clear to build trails
    py5.push_style()
    py5.no_stroke()
    py5.fill(10, 8, 8, 20)
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_style()
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count * 0.015
    
    # Slow rotation
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.002)
    py5.rotate_z(np.sin(t*0.5) * 0.2)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    # We map spherical harmonics
    m = int(py5.remap(np.sin(t*0.5), -1, 1, 0, 5))
    m2 = int(py5.remap(np.cos(t*0.3), -1, 1, 0, 7))
    
    # Quick spherical to cartesian update based on time
    # This is a stylized chaotic mapping rather than strict physics
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    
    r = np.abs(np.sin(m * x * t) * np.cos(m2 * y * t) + np.sin(z * t)) * 200 + 100
    
    px = r * x
    py = r * y
    pz = r * z
    
    for i in range(0, NUM_POINTS, 2):
        # Color gradient based on radius
        h = py5.remap(r[i], 100, 300, 10, 40) # crimson to amber
        s = 80
        b = py5.remap(r[i], 100, 300, 40, 100)
        alpha = 15
        
        if np.random.rand() < 0.01:
            h = 0
            s = 0
            b = 100 # white sparks
            alpha = 50
            
        py5.stroke(h, s, b, alpha)
        py5.point(px[i], py[i], pz[i])
            
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)

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
            
        os._exit(0)

py5.run_sketch()
