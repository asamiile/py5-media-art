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
NUM_PARTICLES = 150000
PARTICLE_POS = np.random.uniform(-SIZE[0]/2, SIZE[0]/2, (NUM_PARTICLES, 2))

# BEC Centers
CENTER1 = np.array([-200, 0])
CENTER2 = np.array([200, 0])

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(3, 3, 10)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global PARTICLE_POS
    t = py5.frame_count
    
    # Dark background
    py5.blend_mode(py5.BLEND)
    py5.background(3, 3, 10)
    
    # Interference Math
    rel_pos1 = PARTICLE_POS - CENTER1
    rel_pos2 = PARTICLE_POS - CENTER2
    d1 = np.linalg.norm(rel_pos1, axis=-1)
    d2 = np.linalg.norm(rel_pos2, axis=-1)
    
    # Phase evolution
    k = 0.08
    omega = 0.05
    phi1 = k * d1 - omega * t
    phi2 = k * d2 - omega * t + 0.5 * np.pi 
    
    # Amplitudes (Gaussian packets expanding)
    w = 100 + 2 * t
    amp1 = np.exp(-(d1**2) / (w**2))
    amp2 = np.exp(-(d2**2) / (w**2))
    
    # Interference pattern (Density)
    density = amp1**2 + amp2**2 + 2 * amp1 * amp2 * np.cos(phi1 - phi2)
    
    # Motion
    v1 = (rel_pos1 / (d1[:, np.newaxis] + 1)) * 1.5
    v2 = (rel_pos2 / (d2[:, np.newaxis] + 1)) * 1.5
    v = (v1 * amp1[:, np.newaxis] + v2 * amp2[:, np.newaxis]) / (amp1 + amp2 + 1e-6)[:, np.newaxis]
    PARTICLE_POS += v * 0.8
    
    # Reset
    off_screen = np.any(np.abs(PARTICLE_POS) > SIZE[0], axis=-1)
    PARTICLE_POS[off_screen] = np.random.uniform(-SIZE[0]/4, SIZE[0]/4, (np.sum(off_screen), 2))
    
    # Rendering
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    
    py5.blend_mode(py5.ADD)
    alpha_val = np.clip(density, 0, 1)
    
    # Quantize for color bands
    num_bands = 8
    for b_idx in range(num_bands):
        t_low = b_idx / num_bands
        t_high = (b_idx + 1) / num_bands
        mask = (alpha_val >= t_low) & (alpha_val < t_high)
        if not np.any(mask): continue
        
        if b_idx < 4:
            py5.stroke(30, 80, 200, 4)
        elif b_idx < 7:
            py5.stroke(50, 200, 180, 8)
        else:
            py5.stroke(200, 40, 60, 12)
            
        py5.stroke_weight(1.5 + b_idx * 0.2)
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
