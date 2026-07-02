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

NUM_RINGS = 40
TUNNEL_DEPTH = 5000
SPEED = 30

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0) # Pitch black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2, 500)
    
    # Slight camera wobble
    py5.rotate_x(np.sin(t*0.5) * 0.1)
    py5.rotate_y(np.cos(t*0.3) * 0.1)
    
    # We loop Z from -TUNNEL_DEPTH to 0
    # Modulo math makes the rings loop endlessly towards the camera
    z_offset = (py5.frame_count * SPEED) % (TUNNEL_DEPTH / NUM_RINGS)
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    py5.blend_mode(py5.ADD)
    
    for i in range(NUM_RINGS):
        z = -TUNNEL_DEPTH + i * (TUNNEL_DEPTH / NUM_RINGS) + z_offset
        
        # Calculate color based on depth
        depth_ratio = abs(z) / TUNNEL_DEPTH
        alpha = py5.remap(depth_ratio, 0, 1, 100, 0) # Fade to black in distance
        
        # Rotate the tunnel over time and depth
        rot_z = t * 0.2 + depth_ratio * py5.TWO_PI
        
        py5.push_matrix()
        py5.translate(0, 0, z)
        py5.rotate_z(rot_z)
        
        # Color: Cyan (180) to Magenta (300)
        hue = py5.remap(np.sin(i*0.5 - t), -1, 1, 180, 300)
        py5.stroke(hue, 90, 100, alpha)
        
        # Draw Hexagon
        py5.begin_shape()
        for a in range(6):
            angle = py5.TWO_PI / 6 * a
            r = 600 + np.sin(t*2 + i*0.1)*50 # slight breathing effect
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            py5.vertex(x, y, 0)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

    # Draw data lines connecting the rings for speed illusion
    py5.stroke(0, 0, 100, 60) # White data packets
    py5.stroke_weight(2)
    num_lines = 12
    for l in range(num_lines):
        angle = py5.TWO_PI / num_lines * l + t
        r = 600
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        
        # Lines shoot forward
        py5.line(x, y, 0, x, y, -TUNNEL_DEPTH)

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
