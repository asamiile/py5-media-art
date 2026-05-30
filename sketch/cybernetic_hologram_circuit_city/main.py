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

GRID_SIZE = 15
buildings = []
pulses = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global buildings, pulses
    
    # Generate procedural city
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            if np.random.rand() > 0.3:
                # x, z, width, depth, height
                h = int(np.abs(py5.os_noise(x * 0.1, z * 0.1, 0)) * 400 + 50)
                if np.random.rand() > 0.8:
                    h += 200 # tall skyscrapers
                buildings.append({
                    "x": (x - GRID_SIZE/2) * 60,
                    "z": (z - GRID_SIZE/2) * 60,
                    "w": 40,
                    "d": 40,
                    "h": h
                })
                
    # Generate data pulses traveling up buildings
    for _ in range(300):
        b = np.random.choice(buildings)
        pulses.append({
            "b": b,
            "y": np.random.rand() * b["h"],
            "speed": np.random.rand() * 5 + 2
        })

def draw():
    global buildings, pulses
    
    # Trace effect background
    py5.push_style()
    py5.no_stroke()
    py5.fill(5, 10, 15, 20) # very dark cyan, semi transparent
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_style()
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.translate(py5.width/2, py5.height/2 + 200, 0)
    
    t = py5.frame_count * 0.01
    py5.rotate_x(py5.PI/4)
    py5.rotate_z(t * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    # Draw buildings
    py5.no_fill()
    py5.stroke(180, 100, 80, 40) # electric cyan
    py5.stroke_weight(1)
    
    for b in buildings:
        py5.push_matrix()
        py5.translate(b["x"], 0, b["z"])
        # box centers on the translate, so we need to shift Y by -h/2 (Z in py5 is depth, Y is up/down)
        # Wait, due to rotate_x, Z is up/down? Let's use standard Y up/down
        # Wait! Box draws from center.
        # If we just do py5.box(w, h, d), it will grow up and down.
        py5.translate(0, -b["h"]/2, 0)
        py5.box(b["w"], b["h"], b["d"])
        py5.pop_matrix()
        
    # Draw pulses
    py5.stroke_weight(4)
    for p in pulses:
        # update pulse
        p["y"] += p["speed"]
        if p["y"] > p["b"]["h"]:
            p["y"] = 0 # reset to bottom
            
        py5.push_matrix()
        py5.translate(p["b"]["x"], 0, p["b"]["z"])
        
        # We need to map y from 0 to h, but since Y is inverted or centered:
        y_pos = -p["y"]
        
        # Decide which corner of the building the pulse is on
        side_x = p["b"]["w"]/2 if p["speed"] > 4 else -p["b"]["w"]/2
        side_z = p["b"]["d"]/2 if p["speed"] < 3.5 else -p["b"]["d"]/2
        
        py5.translate(side_x, y_pos, side_z)
        py5.stroke(30, 100, 100, 100) # neon orange
        if np.random.rand() < 0.05:
            py5.stroke(0, 0, 100, 100) # pure white flash
        
        # Draw a small vertical line
        py5.line(0, 0, 0, 0, -20, 0)
        py5.pop_matrix()

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
