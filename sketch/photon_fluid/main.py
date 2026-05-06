import numpy as np
from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
GRID_SIZE = 64
NUM_PARTICLES = 100000
DECAY = 0.99
VISCOSITY = 0.0001

# State
vel_x = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
vel_y = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
p_pos = None
p_vel = None
starfield = None

def setup():
    global p_pos, p_vel, starfield
    py5.size(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    p_pos = np.random.uniform(0, py5.width, (NUM_PARTICLES, 2)).astype(np.float32)
    p_pos[:, 1] *= (py5.height / py5.width)
    p_vel = np.zeros_like(p_pos)
    
    # Starfield
    num_stars = 2000
    sx = np.random.uniform(0, py5.width, num_stars)
    sy = np.random.uniform(0, py5.height, num_stars)
    sb = np.random.uniform(5, 50, num_stars)
    starfield = np.stack([sx, sy, sb], axis=-1)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global vel_x, vel_y, p_pos, p_vel
    
    # 1. Update Fluid Grid (Simplified)
    # Add noise / impulses
    t = py5.frame_count / TOTAL_FRAMES
    
    # Vortex sources
    angle = py5.frame_count * 0.05
    for i in range(3):
        ix = int(GRID_SIZE/2 + np.cos(angle + i*2) * GRID_SIZE/4)
        iy = int(GRID_SIZE/2 + np.sin(angle + i*2) * GRID_SIZE/4)
        ix = np.clip(ix, 0, GRID_SIZE-1)
        iy = np.clip(iy, 0, GRID_SIZE-1)
        vel_x[iy, ix] += np.cos(angle*2) * 2.0
        vel_y[iy, ix] += np.sin(angle*2) * 2.0
    
    # Central suction (condensation)
    cy, cx = np.indices((GRID_SIZE, GRID_SIZE))
    mid = GRID_SIZE / 2
    dx = mid - cx
    dy = mid - cy
    dist = np.sqrt(dx**2 + dy**2) + 1.0
    vel_x += (dx / dist) * 0.1 * t
    vel_y += (dy / dist) * 0.1 * t
    
    # Simple diffusion-like decay
    vel_x *= DECAY
    vel_y *= DECAY
    
    # 2. Advect Particles
    # Map particle pos to grid
    gx = (p_pos[:, 0] / py5.width * (GRID_SIZE - 1)).astype(int)
    gy = (p_pos[:, 1] / py5.height * (GRID_SIZE - 1)).astype(int)
    gx = np.clip(gx, 0, GRID_SIZE - 1)
    gy = np.clip(gy, 0, GRID_SIZE - 1)
    
    # Update particle velocity from grid
    p_vel[:, 0] = vel_x[gy, gx]
    p_vel[:, 1] = vel_y[gy, gx]
    
    p_pos += p_vel
    
    # Wrap
    p_pos[:, 0] %= py5.width
    p_pos[:, 1] %= py5.height
    
    # 3. Render
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Starfield
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[2], 40)
        py5.point(s[0], s[1])
    
    # Speed-based coloring for "photon" feel
    speed = np.sqrt(np.sum(p_vel**2, axis=-1))
    
    # Split into 4 bands
    for i, threshold in enumerate([8.0, 4.0, 1.0, 0.0]):
        mask = speed > threshold
        if i > 0:
            mask &= speed <= [8.0, 4.0, 1.0][i-1]
        
        if np.any(mask):
            # Mapping: High speed -> White/Gold, Med -> Cyan/Violet
            if i == 0: # Very High
                py5.stroke(45, 20, 100, 80)
                py5.stroke_weight(2.0)
            elif i == 1: # High
                py5.stroke(180, 70, 100, 60)
                py5.stroke_weight(1.5)
            elif i == 2: # Med
                py5.stroke(270, 60, 90, 40)
                py5.stroke_weight(1.2)
            else: # Low
                py5.stroke(240, 40, 60, 20)
                py5.stroke_weight(1.0)
            
            py5.points(p_pos[mask])

    # Central Core Glow (The "Super-Photon")
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    for r in range(4):
        py5.fill(45, 20, 100, (10 - r*2) * t)
        py5.circle(0, 0, 80 + r*40)
    py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
