from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(1.5)
    py5.no_fill()
    
def draw_petal(u_res, v_res, bloom_factor, phase_offset):
    py5.begin_shape(py5.LINES)
    for i in range(u_res):
        u = i / u_res
        next_u = (i + 1) / u_res
        for j in range(v_res):
            v = (j / v_res) * py5.TWO_PI
            
            # Parametric equation for a curled petal
            # bloom_factor ranges from 0.2 to 1.0 to make it open up
            r = 300 * u * (1 - u) * (1 + 0.3 * np.sin(3 * v + phase_offset))
            
            curl = u * py5.PI * (1.5 - bloom_factor)
            
            x = r * np.cos(v)
            y = r * np.sin(v)
            z = -u * 400 * np.cos(curl)
            
            # Adjust y based on curl
            y += u * 200 * np.sin(curl)
            
            # Add points to draw lines
            py5.vertex(x, y, z)
            
            # Connect to next u
            r_next = 300 * next_u * (1 - next_u) * (1 + 0.3 * np.sin(3 * v + phase_offset))
            curl_next = next_u * py5.PI * (1.5 - bloom_factor)
            
            x_next = r_next * np.cos(v)
            y_next = r_next * np.sin(v)
            z_next = -next_u * 400 * np.cos(curl_next)
            y_next += next_u * 200 * np.sin(curl_next)
            
            py5.vertex(x_next, y_next, z_next)
            
    py5.end_shape()

def draw():
    py5.background(245, 245, 250) # Stark almost white
    
    py5.translate(py5.width / 2, py5.height / 2 + 100, 0)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_x(py5.PI/4 + np.sin(t*0.5)*0.1)
    py5.rotate_z(py5.frame_count * 0.005)
    
    num_petals = 5
    bloom = 0.5 + 0.5 * np.sin(t * 0.3) # Oscillates between 0 and 1
    
    # Outer petals
    py5.stroke(20, 20, 25, 180) # Carbon Black
    for i in range(num_petals):
        py5.push_matrix()
        angle = i * py5.TWO_PI / num_petals
        py5.rotate_z(angle)
        py5.rotate_x(py5.PI/6 * bloom)
        draw_petal(40, 20, bloom, i)
        py5.pop_matrix()
        
    # Inner petals
    py5.stroke(180, 130, 200, 200) # Pale Lilac
    for i in range(3):
        py5.push_matrix()
        angle = i * py5.TWO_PI / 3 + py5.PI/3
        py5.rotate_z(angle)
        py5.rotate_x(py5.PI/4 * bloom)
        py5.scale(0.6)
        draw_petal(30, 15, bloom * 1.2, i+10)
        py5.pop_matrix()
        
    # Stamen/Center
    py5.stroke(218, 165, 32, 255) # Gold
    py5.stroke_weight(3)
    py5.begin_shape(py5.LINES)
    for i in range(30):
        angle = py5.random(py5.TWO_PI)
        radius = py5.random(10, 40)
        h = py5.random(50, 150) * bloom
        
        # Flare outward
        out_x = np.cos(angle) * radius * 2
        out_y = np.sin(angle) * radius * 2
        
        py5.vertex(np.cos(angle)*radius, np.sin(angle)*radius, 0)
        py5.vertex(out_x, out_y, -h)
    py5.end_shape()
    py5.stroke_weight(1.5)

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
