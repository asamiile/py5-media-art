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

NUM_CRYSTALS = 100
crystals = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global crystals
    for _ in range(NUM_CRYSTALS):
        crystals.append({
            "pos": np.random.randn(3) * 300,
            "rot": np.random.rand(3) * py5.TWO_PI,
            "size": np.random.rand() * 150 + 50,
            "color_shift": np.random.rand() * 40
        })

def draw_crystal(size):
    # A simple sharp crystal shape (octahedron-like)
    py5.begin_shape(py5.TRIANGLES)
    
    # Top point
    top = (0, -size, 0)
    # Bottom point
    bottom = (0, size, 0)
    # Middle points
    m1 = (size/2, 0, size/2)
    m2 = (size/2, 0, -size/2)
    m3 = (-size/2, 0, -size/2)
    m4 = (-size/2, 0, size/2)
    
    # Top pyramid
    py5.vertex(*top); py5.vertex(*m1); py5.vertex(*m2)
    py5.vertex(*top); py5.vertex(*m2); py5.vertex(*m3)
    py5.vertex(*top); py5.vertex(*m3); py5.vertex(*m4)
    py5.vertex(*top); py5.vertex(*m4); py5.vertex(*m1)
    
    # Bottom pyramid
    py5.vertex(*bottom); py5.vertex(*m2); py5.vertex(*m1)
    py5.vertex(*bottom); py5.vertex(*m3); py5.vertex(*m2)
    py5.vertex(*bottom); py5.vertex(*m4); py5.vertex(*m3)
    py5.vertex(*bottom); py5.vertex(*m1); py5.vertex(*m4)
    
    py5.end_shape()

def draw():
    py5.background(255) # Stark white
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.ambient_light(40, 40, 100)
    
    t = py5.frame_count * 0.02
    
    # Sweeping lights
    lx1 = py5.width/2 + np.cos(t) * 1000
    lz1 = np.sin(t) * 1000
    py5.directional_light(0, 0, 100, -np.cos(t), 1, -np.sin(t))
    py5.point_light(200, 80, 100, lx1, 0, lz1) # glacier blue
    py5.point_light(280, 80, 100, -lx1, py5.height, -lz1) # violet
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_y(t * 0.2)
    py5.rotate_x(py5.PI/8)
    
    # Draw crystals
    for c in crystals:
        py5.push_matrix()
        
        # Organic slow drift
        py5.translate(
            c["pos"][0] + np.sin(t + c["rot"][0])*50,
            c["pos"][1] + np.cos(t * 0.8 + c["rot"][1])*50,
            c["pos"][2] + np.sin(t * 1.2 + c["rot"][2])*50
        )
        
        py5.rotate_x(c["rot"][0] + t * 0.1)
        py5.rotate_y(c["rot"][1] + t * 0.15)
        py5.rotate_z(c["rot"][2] + t * 0.05)
        
        # Translucent blue/violet
        h = 200 + c["color_shift"] + np.sin(t)*20
        if h > 360: h -= 360
        if h < 0: h += 360
        
        py5.fill(h, 60, 100, 40)
        py5.stroke(0, 0, 0, 80) # Pure black thin lines
        py5.stroke_weight(1.5)
        
        draw_crystal(c["size"])
        
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
            
        os._exit(0)

py5.run_sketch()
