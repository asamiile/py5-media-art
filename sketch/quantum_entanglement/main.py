from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Particle System Parameters
PARTICLE_COUNT = 150
MAX_SPEED = 4
DECOHERENCE = 0.1

particles = None
stars = None

def setup():
    global particles, stars
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles (System A)
    # x, y, vx, vy
    particles = np.random.uniform(0, 1, (PARTICLE_COUNT, 4))
    particles[:, 0] *= py5.width / 2
    particles[:, 1] *= py5.height
    particles[:, 2:] = (particles[:, 2:] - 0.5) * MAX_SPEED
    
    # Starfield
    stars = np.random.uniform(0, 1, (1000, 3))
    stars[:, 0] *= py5.width
    stars[:, 1] *= py5.height
    stars[:, 2] = np.random.uniform(0.5, 2.0)  # size

def draw_starfield():
    py5.stroke(255, 150)
    for i in range(len(stars)):
        py5.stroke_weight(stars[i, 2])
        py5.point(stars[i, 0], stars[i, 1])

def draw():
    # Persistence effect
    py5.fill(0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    draw_starfield()
    
    # Update and Draw Particles
    center = np.array([py5.width / 2, py5.height / 2])
    
    # Mirror line is center X
    mid_x = py5.width / 2
    
    for i in range(PARTICLE_COUNT):
        p = particles[i]
        
        # Attraction to center
        dir_to_center = center - p[:2]
        dist = np.linalg.norm(dir_to_center)
        if dist > 0:
            p[2:] += (dir_to_center / dist) * 0.1
        
        # Noise
        p[2:] += (np.random.uniform(-0.1, 0.1, 2))
        
        # Friction
        p[2:] *= 0.98
        
        # Move
        p[:2] += p[2:]
        
        # Bounce/Wrap (constrain to left half)
        if p[0] < 0 or p[0] > mid_x:
            p[2] *= -1
            p[0] = np.clip(p[0], 0, mid_x)
        if p[1] < 0 or p[1] > py5.height:
            p[3] *= -1
            p[1] = np.clip(p[1], 0, py5.height)
            
        # Draw System A (Cyan)
        py5.stroke(0, 255, 255, 180)
        py5.stroke_weight(2)
        py5.point(p[0], p[1])
        
        # Draw System B (Magenta - Mirrored)
        # B = Mirrored X, but with slight noise
        mirror_x = py5.width - p[0]
        mirror_y = p[1] + np.sin(py5.frame_count * 0.1 + i) * 5 * DECOHERENCE
        
        py5.stroke(255, 0, 255, 180)
        py5.point(mirror_x, mirror_y)
        
        # Draw Entanglement Threads (Subtle)
        if i % 10 == 0:
            py5.stroke(255, 255, 255, 20)
            py5.stroke_weight(0.5)
            py5.line(p[0], p[1], mirror_x, mirror_y)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
