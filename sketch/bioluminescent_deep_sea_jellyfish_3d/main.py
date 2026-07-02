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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(240, 90, 5) # Deep sea dark blue
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Gentle floating motion
    py5.translate(0, py5.sin(time * 0.5) * 100, 0)
    py5.rotate_x(py5.sin(time * 0.3) * 0.2)
    py5.rotate_z(py5.cos(time * 0.4) * 0.1)
    py5.rotate_y(time * 0.2)
    
    # Pulse animation
    pulse = 1.0 + py5.sin(time * 2.0) * 0.15
    
    # Draw Jellyfish Bell
    py5.push_matrix()
    py5.scale(1.0, pulse, 1.0)
    py5.no_fill()
    py5.stroke_weight(2)
    
    num_lat = 20
    num_lon = 40
    r = 300
    
    for i in range(num_lat):
        lat0 = py5.PI / 2 * i / num_lat
        lat1 = py5.PI / 2 * (i + 1) / num_lat
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(num_lon + 1):
            lon = py5.TWO_PI * j / num_lon
            
            # Ripple effect
            r0 = r + py5.sin(lat0 * 5 - time * 3) * 20
            r1 = r + py5.sin(lat1 * 5 - time * 3) * 20
            
            x0 = r0 * py5.cos(lat0) * py5.cos(lon)
            z0 = r0 * py5.cos(lat0) * py5.sin(lon)
            y0 = -r0 * py5.sin(lat0)
            
            x1 = r1 * py5.cos(lat1) * py5.cos(lon)
            z1 = r1 * py5.cos(lat1) * py5.sin(lon)
            y1 = -r1 * py5.sin(lat1)
            
            # Bioluminescent gradient
            hue = py5.remap(lat0, 0, py5.PI/2, 280, 180)
            alpha = py5.remap(lat0, 0, py5.PI/2, 60, 0)
            py5.stroke(hue, 80, 100, alpha)
            py5.vertex(x0, y0, z0)
            
            hue1 = py5.remap(lat1, 0, py5.PI/2, 280, 180)
            alpha1 = py5.remap(lat1, 0, py5.PI/2, 60, 0)
            py5.stroke(hue1, 80, 100, alpha1)
            py5.vertex(x1, y1, z1)
            
        py5.end_shape()
    py5.pop_matrix()
    
    # Draw tentacles
    num_tentacles = 15
    for i in range(num_tentacles):
        py5.push_matrix()
        angle = py5.TWO_PI * i / num_tentacles
        
        # Attach to the rim
        tx = py5.cos(angle) * (r * 0.8)
        tz = py5.sin(angle) * (r * 0.8)
        
        py5.translate(tx, 0, tz)
        
        py5.no_fill()
        py5.stroke(180 + py5.sin(time + i)*20, 80, 100, 40)
        py5.stroke_weight(3)
        
        py5.begin_shape()
        for j in range(20):
            ty = j * 40
            
            # Tentacle wave motion
            wave_x = py5.sin(time * 1.5 - j * 0.2 + i) * (j * 5)
            wave_z = py5.cos(time * 1.5 - j * 0.2 + i) * (j * 5)
            
            # Adjust y for pulse contraction
            ty *= (2.0 - pulse)
            
            py5.curve_vertex(wave_x, ty, wave_z)
            
        py5.end_shape()
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
            
        import os
        os._exit(0)

py5.run_sketch()
