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
NUM_PARTICLES = 120000
PARTICLE_POS = np.random.uniform(-400, 400, (NUM_PARTICLES, 3))
PARTICLE_VEL = np.zeros((NUM_PARTICLES, 3))

def get_energy(pos):
    # Tight-binding model on a simple cubic lattice
    # Energy = cos(kx) + cos(ky) + cos(kz)
    k = pos * 0.015
    return np.cos(k[:, 0]) + np.cos(k[:, 1]) + np.cos(k[:, 2])

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(5, 5, 15)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global PARTICLE_POS, PARTICLE_VEL
    t = py5.frame_count
    
    py5.background(3, 3, 10)
    
    # Physics: Surface Attraction + Flow
    # Energy gradient is the attraction force
    k = PARTICLE_POS * 0.015
    # Gradient of cos(kx) is -sin(kx)
    grad = -np.sin(k)
    
    # Target energy level (Fermi Level)
    E_f = 0.5 * np.sin(t * 0.02) # Pulsing Fermi level
    E = np.cos(k[:, 0]) + np.cos(k[:, 1]) + np.cos(k[:, 2])
    force = grad * (E - E_f)[:, np.newaxis] * -0.5
    
    # Add some tangent flow (current)
    flow = np.cross(grad, [0, 1, 0])
    
    PARTICLE_VEL = PARTICLE_VEL * 0.85 + force * 0.1 + flow * 0.05
    PARTICLE_POS += PARTICLE_VEL
    
    # Wrapping
    PARTICLE_POS = (PARTICLE_POS + 500) % 1000 - 500
    
    # Rendering
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * 0.01)
    py5.rotate_x(t * 0.007)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    # Color mapping based on momentum (k)
    # Electric Cobalt (200-240), Solar Gold (40-60)
    k_mag = np.linalg.norm(k, axis=-1)
    
    num_bands = 8
    for b_idx in range(num_bands):
        mask = (k_mag >= b_idx * 0.5) & (k_mag < (b_idx + 1) * 0.5)
        if not np.any(mask): continue
        
        # Cobalt to Gold gradient
        blend = b_idx / num_bands
        r = int(50 * (1-blend) + 255 * blend)
        g = int(100 * (1-blend) + 200 * blend)
        b = int(255 * (1-blend) + 50 * blend)
        
        py5.stroke(r, g, b, 80)
        py5.points(PARTICLE_POS[mask])
        
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
