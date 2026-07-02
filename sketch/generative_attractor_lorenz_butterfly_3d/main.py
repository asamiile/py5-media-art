from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Lorenz Attractor Parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0

points = []
colors = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Precompute the attractor path
    x, y, z = 0.1, 0.0, 0.0
    dt = 0.015
    for i in range(10000):
        dx = (sigma * (y - x)) * dt
        dy = (x * (rho - z) - y) * dt
        dz = (x * y - beta * z) * dt
        x += dx
        y += dy
        z += dz
        points.append((x, y, z))
        colors.append((i * 0.1) % 360)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    
    py5.rotate_y(t * 0.3)
    py5.rotate_x(py5.PI / 8)
    py5.rotate_z(t * 0.1)
    
    scale = 18
    py5.scale(scale)
    
    py5.no_fill()
    py5.stroke_weight(0.5)
    
    # How much of the path is visible (animate drawing it, or animate the colors moving)
    # Let's draw the whole path but pulse the colors
    
    py5.begin_shape(py5.LINE_STRIP)
    for i in range(len(points)):
        p = points[i]
        
        # Color pulsing effect
        hue = (colors[i] + t * 20) % 360
        
        # Add a traveling bright spot
        bright_spot = (py5.frame_count * 30) % len(points)
        dist = abs(i - bright_spot)
        if dist > len(points) / 2:
            dist = len(points) - dist
            
        alpha = py5.remap(dist, 0, 1000, 100, 10)
        
        py5.stroke(hue, 90, 100, alpha)
        py5.vertex(p[0], p[1], p[2])
    py5.end_shape()


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
