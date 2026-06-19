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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 30000
particles = []

class Particle:
    def __init__(self):
        self.x = random.uniform(-1, 1)
        self.y = random.uniform(-1, 1)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    time_t = py5.frame_count * 0.01
    
    # Frequencies morphing over time
    n = 3.0 + 2.0 * np.sin(time_t * 0.5)
    m = 5.0 + 2.0 * np.cos(time_t * 0.4)
    
    py5.stroke(255, 220, 100, 150) # Golden sand color
    py5.stroke_weight(2)
    
    py5.begin_shape(py5.POINTS)
    
    scale = min(py5.width, py5.height) / 2.2
    
    for p in particles:
        # Calculate vibration amplitude at current position
        # Chladni equation
        chladni = np.sin(n * np.pi * p.x) * np.sin(m * np.pi * p.y) - np.sin(m * np.pi * p.x) * np.sin(n * np.pi * p.y)
        vibration = abs(chladni)
        
        # Random walk
        p.x += random.uniform(-0.01, 0.01) * vibration
        p.y += random.uniform(-0.01, 0.01) * vibration
        
        # Wrap
        if p.x < -1: p.x += 2
        if p.x > 1: p.x -= 2
        if p.y < -1: p.y += 2
        if p.y > 1: p.y -= 2
            
        py5.vertex(p.x * scale, p.y * scale)
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
            import os
            os._exit(1)

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
