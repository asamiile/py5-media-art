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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_COLS = 150
GRID_ROWS = 150
SPACING = 30

NUM_PILLARS = 20
pillars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pillars
    for _ in range(NUM_PILLARS):
        pillars.append({
            "x": np.random.randint(-GRID_COLS/2, GRID_COLS/2) * SPACING,
            "z": np.random.randint(-GRID_ROWS/2, GRID_ROWS/2) * SPACING,
            "height": np.random.rand() * 800 + 400
        })

def draw():
    py5.background(5, 10, 25) # Dark navy
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width/2, py5.height/2 + 200, 0)
    
    py5.rotate_x(py5.PI/3)
    py5.rotate_z(t * 0.2)
    
    py5.stroke_weight(3)
    
    # Draw ocean points
    py5.begin_shape(py5.POINTS)
    for x in range(-GRID_COLS//2, GRID_COLS//2):
        for z in range(-GRID_ROWS//2, GRID_ROWS//2):
            px = x * SPACING
            pz = z * SPACING
            
            # Complex noise for rolling waves
            noise_val = py5.os_noise(x * 0.05 + t, z * 0.05 + t*0.5, t * 0.2)
            noise_val += py5.os_noise(x * 0.02 - t, z * 0.02, 0) * 0.5
            
            py = -noise_val * 400
            
            # Distance fade
            dist = np.sqrt(px*px + pz*pz)
            alpha = max(0, 100 - (dist / (GRID_COLS * SPACING / 2) * 100))
            
            if py < -300:
                py5.stroke(180, 80, 100, alpha) # Bright turquoise peaks
            else:
                py5.stroke(200, 100, 80, alpha) # Bioluminescent cyan
                
            py5.vertex(px, pz, py) # Z is up/down when rotated
    py5.end_shape()
    
    # Draw pillars
    py5.stroke_weight(2)
    for p in pillars:
        # Distance fade for pillars too
        dist = np.sqrt(p["x"]**2 + p["z"]**2)
        alpha = max(0, 100 - (dist / (GRID_COLS * SPACING / 2) * 100))
        
        py5.stroke(0, 0, 100, alpha * 0.8) # Pure white
        
        # Pillars rise from deep below to high above
        py5.line(p["x"], p["z"], 500, p["x"], p["z"], -p["height"])

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
