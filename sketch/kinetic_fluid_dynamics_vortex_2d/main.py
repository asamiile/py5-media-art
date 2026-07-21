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
    global particles_x, particles_y, num_particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    num_particles = 40000
    particles_x = np.random.uniform(0, SIZE[0], num_particles)
    particles_y = np.random.uniform(0, SIZE[1], num_particles)
    
    py5.background(0)

def draw():
    global particles_x, particles_y
    
    # Fade background slightly for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    
    # Calculate vector field 
    s1 = 0.003
    s2 = 0.006
    time_factor = t * 0.3
    
    vx = np.sin(particles_x * s1 + time_factor) * np.cos(particles_y * s1 - time_factor) + \
         0.6 * np.cos(particles_y * s2)
    vy = -np.cos(particles_x * s1 - time_factor) * np.sin(particles_y * s1 + time_factor) + \
         0.6 * np.sin(particles_x * s2)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    dx = particles_x - cx
    dy = particles_y - cy
    dist = np.sqrt(dx*dx + dy*dy) + 1.0
    
    # Global rotation 
    vx -= (dy / dist) * 3.0 * np.exp(-dist * 0.0005)
    vy += (dx / dist) * 3.0 * np.exp(-dist * 0.0005)
    
    # Attraction to center slightly
    vx -= (dx / dist) * 0.5 * np.sin(t)
    vy -= (dy / dist) * 0.5 * np.sin(t)
    
    # Update positions
    speed = 8.0
    particles_x += vx * speed
    particles_y += vy * speed
    
    # Wrap around screen
    particles_x = np.mod(particles_x, SIZE[0])
    particles_y = np.mod(particles_y, SIZE[1])
    
    py5.stroke_weight(2.5)
    
    # Three color groups
    third = num_particles // 3
    g1 = slice(0, third)
    g2 = slice(third, third * 2)
    g3 = slice(third * 2, num_particles)
    
    # Deep oceanic blue
    py5.stroke(0, 120, 255, 60)
    py5.points(np.column_stack((particles_x[g1], particles_y[g1])))
    
    # Bright gold
    py5.stroke(255, 215, 0, 60)
    py5.points(np.column_stack((particles_x[g2], particles_y[g2])))
    
    # Cyan
    py5.stroke(0, 255, 255, 60)
    py5.points(np.column_stack((particles_x[g3], particles_y[g3])))

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
