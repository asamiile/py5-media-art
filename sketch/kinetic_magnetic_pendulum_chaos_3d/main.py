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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Magnet:
    def __init__(self, x, y, hue):
        self.pos = np.array([x, y], dtype=float)
        self.hue = hue

class Pendulum:
    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([0.0, 0.0], dtype=float)
        self.history = []

magnets = []
pendulum = None

def setup():
    global pendulum
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Place magnets
    magnets.append(Magnet(0, -300, 0))
    magnets.append(Magnet(-260, 150, 120))
    magnets.append(Magnet(260, 150, 240))
    
    pendulum = Pendulum(200, 200)

def draw():
    py5.background(10)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Physics simulation (sub-stepping for accuracy)
    dt = 0.05
    for _ in range(10):
        acc = np.array([0.0, 0.0])
        
        # Gravity towards center
        acc += -pendulum.pos * 0.01
        
        # Magnetic forces
        for mag in magnets:
            d = mag.pos - pendulum.pos
            dist_sq = np.sum(d**2)
            dist = np.sqrt(dist_sq)
            if dist > 1:
                # Force is proportional to 1/dist^3 in this common approximation
                force = d / (dist_sq * dist) * 1000000.0
                acc += force
                
        # Friction
        acc -= pendulum.vel * 0.05
        
        pendulum.vel += acc * dt
        pendulum.pos += pendulum.vel * dt
        
    pendulum.history.append((pendulum.pos[0], pendulum.pos[1], py5.frame_count))
    if len(pendulum.history) > 300:
        pendulum.history.pop(0)
        
    # Draw magnets
    py5.no_stroke()
    for mag in magnets:
        py5.fill(mag.hue, 80, 80, 50)
        py5.circle(mag.pos[0], mag.pos[1], 40)
        
    # Draw trail
    py5.no_fill()
    py5.stroke_weight(4)
    py5.begin_shape()
    for i, (hx, hy, fc) in enumerate(pendulum.history):
        alpha = py5.remap(i, 0, len(pendulum.history), 0, 100)
        hue = (fc * 2) % 360
        py5.stroke(hue, 90, 100, alpha)
        py5.vertex(hx, hy)
    py5.end_shape()
    
    # Draw pendulum bob
    py5.fill(0, 0, 100)
    py5.no_stroke()
    py5.circle(pendulum.pos[0], pendulum.pos[1], 20)


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
