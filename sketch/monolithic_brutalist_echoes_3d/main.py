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

NUM_BLOCKS = 60
blocks = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global blocks
    for i in range(NUM_BLOCKS):
        # Generate massive overlapping blocks
        blocks.append({
            "pos": (
                np.random.randn() * 400,
                np.random.randn() * 400,
                np.random.randn() * 600 - 300
            ),
            "size": (
                np.random.rand() * 300 + 50,
                np.random.rand() * 600 + 100,
                np.random.rand() * 300 + 50
            ),
            "rot_y": np.random.choice([0, py5.PI/2]) # Orthogonal aesthetic
        })

def draw():
    py5.background(20, 25, 30) # Dusty grey-blue void
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.01
    
    # Lighting setup - Chiaroscuro
    py5.ambient_light(10, 10, 15) # Very dim ambient
    
    # Single harsh yellow spotlight cutting across
    py5.directional_light(50, 60, 100, 0.8, 0.5, -0.6)
    
    # Very subtle blue rim light
    py5.directional_light(210, 40, 20, -1, -0.2, 0.5)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Slow, imposing cinematic tracking shot
    py5.translate(-py5.frame_count * 1.5, np.sin(t * 0.5) * 50, py5.frame_count * 2.5)
    
    py5.rotate_y(py5.PI/6)
    
    py5.no_stroke()
    py5.fill(0, 0, 50) # Matte concrete grey
    
    for b in blocks:
        py5.push_matrix()
        py5.translate(*b["pos"])
        py5.rotate_y(b["rot_y"])
        py5.box(*b["size"])
        py5.pop_matrix()

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
