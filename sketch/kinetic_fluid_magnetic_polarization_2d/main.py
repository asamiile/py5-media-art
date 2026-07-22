from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

particles = None
colors = None

def setup():
    global particles, colors
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    num_particles = 15000
    
    # [x, y, age, max_age, color_idx]
    particles = np.zeros((num_particles, 5), dtype=np.float32)
    particles[:, 0] = np.random.rand(num_particles) * SIZE[0]
    particles[:, 1] = np.random.rand(num_particles) * SIZE[1]
    particles[:, 2] = np.random.rand(num_particles) * 100
    particles[:, 3] = np.random.rand(num_particles) * 50 + 100
    particles[:, 4] = np.random.randint(0, 3, size=num_particles)
    
    colors = [
        (255, 192, 64, 60),  # Molten gold
        (176, 16, 32, 40),   # Crimson red
        (255, 255, 255, 50), # White
    ]

def draw():
    global particles
    
    if py5.frame_count == 1:
        py5.background(10, 8, 8) # Warm dark grey
        
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 8, 8, 15) # Fading trail
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    
    # Update particles
    px = particles[:, 0]
    py = particles[:, 1]
    
    # Vector field based on 2 offset noise fields representing magnetic poles
    # We use vector math
    # noise scale
    s = 0.003
    
    angles = np.zeros_like(px)
    for i in range(len(px)):
        n1 = py5.noise(px[i]*s, py[i]*s, t) * 4 * np.pi
        n2 = py5.noise(px[i]*s + 1000, py[i]*s + 1000, t) * 4 * np.pi
        # Combine angles
        angles[i] = n1 + np.sin(n2)
        
    vx = np.cos(angles) * 3.0
    vy = np.sin(angles) * 3.0
    
    particles[:, 0] += vx
    particles[:, 1] += vy
    particles[:, 2] += 1 # age++
    
    # Reset dead particles
    dead = (particles[:, 2] > particles[:, 3]) | (particles[:, 0] < 0) | (particles[:, 0] > SIZE[0]) | (particles[:, 1] < 0) | (particles[:, 1] > SIZE[1])
    num_dead = np.sum(dead)
    
    if num_dead > 0:
        particles[dead, 0] = np.random.rand(num_dead) * SIZE[0]
        particles[dead, 1] = np.random.rand(num_dead) * SIZE[1]
        particles[dead, 2] = 0
        particles[dead, 3] = np.random.rand(num_dead) * 50 + 100
    
    # Draw particles manually since py5.points is slow with per-point colors
    # We will loop through the 3 color groups
    py5.stroke_weight(2)
    for c_idx, c_val in enumerate(colors):
        mask = particles[:, 4] == c_idx
        pts = particles[mask]
        if len(pts) > 0:
            py5.stroke(*c_val)
            py5.begin_shape(py5.POINTS)
            for p in pts:
                py5.vertex(p[0], p[1])
            py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
