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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    global particles, num_particles, noise_scale, noise_z
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    num_particles = 15000
    noise_scale = 0.001
    noise_z = 0
    
    # Initialize particles
    particles = np.zeros((num_particles, 2))
    particles[:, 0] = np.random.uniform(0, SIZE[0], num_particles)
    particles[:, 1] = np.random.uniform(0, SIZE[1], num_particles)
    
    # Give them slightly different speeds and colors
    global speeds, color_r, color_g, color_b
    speeds = np.random.uniform(2, 8, num_particles)
    
    color_r = np.random.uniform(0, 50, num_particles)
    color_g = np.random.uniform(150, 255, num_particles)
    color_b = np.random.uniform(200, 255, num_particles)
    
    py5.background(5, 10, 20) # Deep dark indigo

def draw():
    global noise_z
    
    # Slight fade for trails using a black rect with low alpha
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 10, 20, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    for i in range(num_particles):
        x = particles[i, 0]
        y = particles[i, 1]
        
        # Calculate vector field angle using Perlin noise
        angle = py5.os_noise(x * noise_scale, y * noise_scale, noise_z) * py5.TWO_PI * 4
        
        # Move particle
        nx = x + np.cos(angle) * speeds[i]
        ny = y + np.sin(angle) * speeds[i]
        
        # Draw line segment for trail
        py5.stroke(color_r[i], color_g[i], color_b[i], 30)
        py5.line(x, y, nx, ny)
        
        # Wrap around edges gracefully (don't draw line across screen)
        if nx < 0:
            nx += SIZE[0]
            py5.point(nx, ny)
        elif nx >= SIZE[0]:
            nx -= SIZE[0]
            py5.point(nx, ny)
            
        if ny < 0:
            ny += SIZE[1]
            py5.point(nx, ny)
        elif ny >= SIZE[1]:
            ny -= SIZE[1]
            py5.point(nx, ny)
        
        particles[i, 0] = nx
        particles[i, 1] = ny
        
    noise_z += 0.003 # Animate the noise field slowly

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
        import os
        os._exit(0)

py5.run_sketch()
