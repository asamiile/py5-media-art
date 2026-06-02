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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw():
    py5.background(0)
    
    # Enable additive blending
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_x(t * py5.TWO_PI)
    py5.rotate_y(t * py5.TWO_PI * 0.5)
    py5.rotate_z(t * py5.TWO_PI * 0.25)
    
    num_points = 25000
    
    R = py5.width * 0.3
    r = py5.width * 0.15
    
    # We want a closed loop that wraps p times around the torus longitudinally and q times poloidally
    p = 15
    q = 32
    
    # We will generate a phase shift over time so the knot "breathes" or moves
    phase_shift = t * py5.TWO_PI * 2
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    # Use points for particle-like look
    py5.begin_shape(py5.POINTS)
    
    # Array calculations for speed (although Python loop is fast enough for 25000 points)
    # Using numpy to calculate coordinates
    theta = np.linspace(0, py5.TWO_PI, num_points)
    
    u = p * theta + phase_shift
    v = q * theta
    
    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)
    
    # Color palette: Lime (75), Magenta (300), Cyan (180)
    hue_vals = (75 + (u / (py5.TWO_PI * 2)) * 300) % 360
    
    for i in range(num_points):
        py5.stroke(hue_vals[i], 80, 80, 150)
        py5.vertex(x[i], y[i], z[i])
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.", flush=True)
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.", flush=True)
            
        import os
        os._exit(0)

py5.run_sketch()
