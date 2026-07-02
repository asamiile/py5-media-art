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

NUM_PRISMS = 60
prisms = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global prisms
    for _ in range(NUM_PRISMS):
        prisms.append({
            "pos": (np.random.randn(3) * 350),
            "rot": (np.random.rand(3) * py5.TWO_PI),
            "rot_speed": (np.random.randn(3) * 0.02),
            "size": np.random.rand() * 100 + 50
        })

def draw_prism(size):
    # Draw a 3D triangular prism (tetrahedron)
    # Using 4 vertices
    v0 = (0, -size, 0)
    v1 = (size * 0.866, size/2, -size/2)
    v2 = (-size * 0.866, size/2, -size/2)
    v3 = (0, size/2, size)
    
    py5.begin_shape(py5.TRIANGLES)
    # Face 1
    py5.vertex(*v0); py5.vertex(*v1); py5.vertex(*v2)
    # Face 2
    py5.vertex(*v0); py5.vertex(*v2); py5.vertex(*v3)
    # Face 3
    py5.vertex(*v0); py5.vertex(*v3); py5.vertex(*v1)
    # Base
    py5.vertex(*v1); py5.vertex(*v2); py5.vertex(*v3)
    py5.end_shape()

def draw():
    py5.background(10) # Stark black
    # Using RGB for easy additive blending
    py5.color_mode(py5.RGB, 255)
    
    # We will simulate chromatic aberration by drawing everything 3 times
    # with slightly different camera offsets and pure RGB colors
    
    py5.blend_mode(py5.ADD)
    t = py5.frame_count * 0.02
    
    # Base global rotation
    base_rot_y = t * 0.5
    base_rot_x = t * 0.3
    
    # RGB offsets for aberration based on distance from center
    aberration = 15.0
    
    colors = [
        (255, 0, 0),   # Red
        (0, 255, 0),   # Green
        (0, 0, 255)    # Blue
    ]
    
    offsets = [
        (-aberration, 0, 0),
        (0, 0, 0),
        (aberration, 0, 0)
    ]
    
    for c_idx, col in enumerate(colors):
        py5.push_matrix()
        
        py5.translate(py5.width/2 + offsets[c_idx][0], py5.height/2 + offsets[c_idx][1], offsets[c_idx][2])
        py5.rotate_y(base_rot_y)
        py5.rotate_x(base_rot_x)
        
        py5.no_fill()
        py5.stroke(*col, 150) # Bright pure colors
        py5.stroke_weight(2)
        
        for p in prisms:
            py5.push_matrix()
            
            # Organic slow drift
            py5.translate(
                p["pos"][0] + np.sin(t + p["rot"][0])*50,
                p["pos"][1] + np.cos(t * 0.8 + p["rot"][1])*50,
                p["pos"][2] + np.sin(t * 1.2 + p["rot"][2])*50
            )
            
            py5.rotate_x(p["rot"][0] + t * 50 * p["rot_speed"][0])
            py5.rotate_y(p["rot"][1] + t * 50 * p["rot_speed"][1])
            py5.rotate_z(p["rot"][2] + t * 50 * p["rot_speed"][2])
            
            draw_prism(p["size"])
            
            py5.pop_matrix()
            
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
            
        os._exit(0)

py5.run_sketch()
