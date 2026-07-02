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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 30000
points = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points
    # Distribute points on sphere
    phi = np.arccos(1 - 2 * np.random.rand(NUM_POINTS))
    theta = 2 * np.pi * np.random.rand(NUM_POINTS)
    
    points = np.zeros((NUM_POINTS, 3))
    points[:, 0] = np.sin(phi) * np.cos(theta)
    points[:, 1] = np.sin(phi) * np.sin(theta)
    points[:, 2] = np.cos(phi)

def draw():
    global points
    
    py5.background(250)  # Stark white
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(280, 80, 80, -1, -1, -1) # purple light
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.frame_count * 0.005)
    
    py5.stroke_weight(5)
    
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    
    # Noise calculation for sharp spikes
    # We use multiple layers of absolute noise to make "ridges" and "spikes"
    n1 = np.array([py5.os_noise(p[0]*1.5, p[1]*1.5, p[2]*1.5 + t) for p in points])
    n2 = np.array([py5.os_noise(p[0]*3, p[1]*3, p[2]*3 - t) for p in points])
    
    # Sharpness
    spikes = np.abs(n1 - 0.5) * 2
    spikes = spikes ** 4  # power pushes it to be sharp peaks
    
    r = 200 + spikes * 200 + n2 * 50
    
    px = r * x
    py = r * y
    pz = r * z
    
    for i in range(NUM_POINTS):
        # Base color is jet black, tips get metallic/purple
        intensity = spikes[i]
        py5.stroke(280, 80*intensity, 10 + 90*intensity, 90)
        py5.point(px[i], py[i], pz[i])
        
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
            
        os._exit(0)

py5.run_sketch()
