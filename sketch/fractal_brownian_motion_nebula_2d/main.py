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

# Particle system using numpy for speed
num_particles = 20000
positions = np.zeros((num_particles, 2), dtype=np.float32)
hues = np.zeros(num_particles, dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    positions[:, 0] = np.random.uniform(0, SIZE[0], num_particles)
    positions[:, 1] = np.random.uniform(0, SIZE[1], num_particles)
    hues[:] = np.random.uniform(200, 320, num_particles) # Deep space colors (blues to magentas)
    
    py5.background(10, 80, 5) # Very dark blue space
    
def draw():
    # Fading background for trails
    py5.fill(10, 80, 5, 2)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    time = py5.frame_count * 0.005
    
    py5.stroke_weight(1)
    
    for i in range(num_particles):
        x = positions[i, 0]
        y = positions[i, 1]
        
        # Fractal Brownian Motion (fBm) flow field
        # 3 octaves
        n1 = py5.os_noise(x * 0.002, y * 0.002, time) * 1.0
        n2 = py5.os_noise(x * 0.004, y * 0.004, time + 100) * 0.5
        n3 = py5.os_noise(x * 0.008, y * 0.008, time + 200) * 0.25
        
        angle = (n1 + n2 + n3) * py5.TWO_PI * 4
        
        vx = py5.cos(angle) * 2
        vy = py5.sin(angle) * 2
        
        positions[i, 0] += vx
        positions[i, 1] += vy
        
        # Wrapping
        if positions[i, 0] < 0: positions[i, 0] += SIZE[0]
        if positions[i, 0] > SIZE[0]: positions[i, 0] -= SIZE[0]
        if positions[i, 1] < 0: positions[i, 1] += SIZE[1]
        if positions[i, 1] > SIZE[1]: positions[i, 1] -= SIZE[1]
        
        py5.stroke(hues[i], 80, 100, 10) # Faint glowing points
        py5.point(positions[i, 0], positions[i, 1])
        
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
