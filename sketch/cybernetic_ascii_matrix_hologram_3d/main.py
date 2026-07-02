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

CHARS = "0101010101#$%&@ABCDEF0123456789X<>*"
NUM_POINTS = 3500

def torus_knot(u, p=3, q=7, r1=450, r2=150):
    x = (r1 + r2 * np.cos(q * u)) * np.cos(p * u)
    y = (r1 + r2 * np.cos(q * u)) * np.sin(p * u)
    z = r2 * np.sin(q * u)
    return x, y, z

u_vals = np.random.uniform(0, 2*np.pi, NUM_POINTS)
points = np.zeros((NUM_POINTS, 3))
for i in range(NUM_POINTS):
    points[i] = torus_knot(u_vals[i])
    points[i] += np.random.normal(0, 25, 3)

font = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global font
    font = py5.create_font("Courier", 36)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)

def draw():
    py5.background(2, 4, 8)
    
    t = py5.frame_count / 60.0
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    py5.rotate_x(t * 0.25)
    py5.rotate_y(t * 0.45)
    py5.rotate_z(np.sin(t * 0.1) * 0.15)
    
    py5.blend_mode(py5.ADD)
    
    for i in range(NUM_POINTS):
        x, y, z = points[i]
        
        u = (u_vals[i] + t * 0.5) % (2*np.pi)
        
        bri = 100 + 155 * np.sin(u * 12 - t * 4)
        if bri < 0:
            bri = 0
            
        py5.fill(10, 255, max(0, bri * 0.8), bri)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        # Billboarding logic: reverse the camera rotation
        py5.rotate_z(-np.sin(t * 0.1) * 0.15)
        py5.rotate_y(-t * 0.45)
        py5.rotate_x(-t * 0.25)
        
        char_idx = int((u * 100 + i + t * 15) % len(CHARS))
        char = CHARS[char_idx]
        
        if bri > 220:
            py5.scale(1.4)
            py5.fill(180, 255, 255, bri)
        
        py5.text(char, 0, 0)
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

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
