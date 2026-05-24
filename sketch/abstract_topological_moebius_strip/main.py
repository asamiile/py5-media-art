from pathlib import Path
import shutil
import subprocess
import sys
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Pre-calculate a dense grid for parametric surface evaluation
u_res = 300
v_res = 100
U = np.linspace(0, 2 * np.pi, u_res)
V = np.linspace(-1, 1, v_res)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    py5.rotate_y(t * 0.3)
    py5.rotate_x(py5.sin(t * 0.2) * 0.5)
    py5.rotate_z(t * 0.1)
    
    # Base radius of the Moebius strip
    R = 400.0
    
    # Twist frequency (standard Moebius is 0.5 twists per loop)
    # We animate it slightly to make the topology warp over time
    twist = 0.5 + py5.sin(t * 0.5) * 0.1
    
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # We will draw it as a series of connected line strips along the U-axis
    for i in range(v_res):
        v = V[i]
        
        # We only draw certain V lines to make it look like a wireframe track
        if i % 4 != 0:
            continue
            
        py5.begin_shape(py5.LINE_STRIP)
        for j in range(u_res):
            u = U[j]
            
            # Parametric equations for a generalized Moebius Strip
            # x(u,v) = [R + v * cos(twist * u)] * cos(u)
            # y(u,v) = [R + v * cos(twist * u)] * sin(u)
            # z(u,v) = v * sin(twist * u)
            
            # We scale V by a width factor that pulsates
            width = 150.0 + py5.sin(t + u * 2) * 50.0
            v_scaled = v * width
            
            cx = (R + v_scaled * np.cos(twist * u)) * np.cos(u)
            cy = (R + v_scaled * np.cos(twist * u)) * np.sin(u)
            cz = v_scaled * np.sin(twist * u)
            
            # Add some high-frequency noise to make it look like energy
            noise_val = py5.noise(u * 5.0, v * 5.0, t * 2.0)
            cx += py5.cos(u * 10) * noise_val * 20
            cy += py5.sin(u * 10) * noise_val * 20
            cz += py5.sin(v * 10) * noise_val * 20
            
            # Color is based on U parameter and time
            hue = (py5.degrees(u) + t * 40 + v * 30) % 360
            
            # Brightness pulsates
            brightness = 60 + 40 * py5.sin(u * 8 - t * 4)
            
            py5.stroke(hue, 80, brightness, 50)
            py5.vertex(cx, cy, cz)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
