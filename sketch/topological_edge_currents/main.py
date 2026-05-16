from pathlib import Path
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 60000
PARTICLE_POS = np.random.uniform(-SIZE[0]/2, SIZE[0]/2, (NUM_PARTICLES, 2))

# Geometry: Grid with holes
GRID_SIZE = 100
GRID_SCALE = SIZE[0] / GRID_SIZE
OCCUPANCY = np.ones((GRID_SIZE, GRID_SIZE))

# Cut out some holes
np.random.seed(42) # Consistent for this session's fix
for _ in range(6):
    cx, cy = np.random.randint(20, 80, 2)
    rw, rh = np.random.randint(5, 15, 2)
    OCCUPANCY[cx-rw:cx+rw, cy-rh:cy+rh] = 0

# Border
OCCUPANCY[:10, :] = 0
OCCUPANCY[-10:, :] = 0
OCCUPANCY[:, :10] = 0
OCCUPANCY[:, -10:] = 0

def get_flow(pos):
    gx = ((pos[:, 0] + SIZE[0]/2) / GRID_SCALE).astype(int)
    gy = ((pos[:, 1] + SIZE[1]/2) / GRID_SCALE).astype(int)
    gx = np.clip(gx, 1, GRID_SIZE-2)
    gy = np.clip(gy, 1, GRID_SIZE-2)
    
    grad_x = OCCUPANCY[gx+1, gy] - OCCUPANCY[gx-1, gy]
    grad_y = OCCUPANCY[gx, gy+1] - OCCUPANCY[gx, gy-1]
    
    vx = grad_y
    vy = -grad_x
    
    mask = (np.abs(grad_x) > 0) | (np.abs(grad_y) > 0)
    vx += np.random.normal(0, 0.1, len(vx))
    vy += np.random.normal(0, 0.1, len(vy))
    
    return np.stack([vx, vy], axis=-1), mask

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(3, 5, 15)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global PARTICLE_POS
    t = py5.frame_count
    
    # Background trail
    py5.blend_mode(py5.BLEND)
    py5.fill(3, 5, 15, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Physics
    flow, mask = get_flow(PARTICLE_POS)
    PARTICLE_POS[mask] += flow[mask] * 3.0
    
    # Reset
    reset_mask = ~mask | (np.random.rand(NUM_PARTICLES) < 0.01)
    PARTICLE_POS[reset_mask] = np.random.uniform(-SIZE[0]/2, SIZE[0]/2, (np.sum(reset_mask), 2))
    
    # Rendering
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    py5.blend_mode(py5.ADD)
    
    # Emerald
    py5.stroke(50, 255, 180, 2)
    py5.stroke_weight(1.2)
    py5.points(PARTICLE_POS[mask][::2])
    
    # Amber
    py5.stroke(255, 200, 50, 1)
    py5.stroke_weight(0.8)
    py5.points(PARTICLE_POS[mask][1::2])
    
    py5.pop_matrix()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
