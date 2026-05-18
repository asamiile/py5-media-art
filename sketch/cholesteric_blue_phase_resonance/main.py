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
PREVIEW_FILENAME = f"{WORK_NAME}_p2.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # Force 4K resolution (3840x2160)

# Simulation Parameters
NUM_PARTICLES = 200000  # Increased for ultra-dense 4K crystalline shine
LATTICE_SCALE = 300.0  # Unit cell size
TIME_STEP = 0.015
PITCH = 120.0  # Chiral pitch

# Initialize Particles
pos = np.random.uniform(-1000, 1000, (NUM_PARTICLES, 3))
colors = np.zeros((NUM_PARTICLES, 3))  # RGB
alpha = np.zeros(NUM_PARTICLES)

def get_director(p, t):
    """
    Approximation of BPI cubic symmetry (O8 minus).
    Double-twist cylinders along [100], [010], [001].
    """
    # Unit cell coordinates
    x, y, z = p[:, 0] / LATTICE_SCALE, p[:, 1] / LATTICE_SCALE, p[:, 2] / LATTICE_SCALE
    
    # Harmonic modes for O8- symmetry
    # n ~ sum A_h exp(i q_h . r)
    # Here we use a simplified sum of twist waves
    qx = 2 * np.pi * x + t * 0.2
    qy = 2 * np.pi * y + t * 0.3
    qz = 2 * np.pi * z + t * 0.1
    
    nx = np.sin(qy) * np.cos(qz)
    ny = np.sin(qz) * np.cos(qx)
    nz = np.sin(qx) * np.cos(qy)
    
    # Normalize
    mag = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-6
    return np.stack([nx/mag, ny/mag, nz/mag], axis=-1)

import shutil

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)  # Capping at 1x density prevents Retina-doubling lag on 4K renders
    py5.background(0)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial particle state
    global pos, colors, alpha
    pos = np.random.uniform(-1000, 1000, (NUM_PARTICLES, 3))

def draw():
    global pos, colors, alpha
    frame = py5.frame_count
    t = frame * TIME_STEP
    
    # Progress logs to prevent command timeouts
    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")
        
    py5.background(5, 5, 12)  # Deep indigo base
    
    # Update physics
    n = get_director(pos, t)
    
    # Advection: particles drift along director lines with a bit of noise
    pos += n * 2.5
    pos += np.random.normal(0, 0.5, pos.shape)
    
    # Boundary wrap
    pos = (pos + 1000) % 2000 - 1000
    
    # Iridescence: Bragg reflection intensity
    # Based on alignment with cubic lattice planes (110)
    # simplified: intensity depends on n orientation relative to fixed view
    view_dir = np.array([0, 0, 1])
    dot = np.abs(np.sum(n * view_dir, axis=-1))
    
    # HSB-like spectral mapping
    # Electric Cyan (180), Cobalt (220), Royal Violet (280), Pearl (300)
    hue = (180 + dot * 120) / 360.0
    
    # Intensity modulation: high near "lattice planes"
    # We use a periodic function of coordinates to simulate lattice reflection
    lattice_phase = np.sin(2 * np.pi * pos[:, 0] / LATTICE_SCALE) * \
                    np.sin(2 * np.pi * pos[:, 1] / LATTICE_SCALE) * \
                    np.sin(2 * np.pi * pos[:, 2] / LATTICE_SCALE)
    
    intensity = 0.2 + 0.8 * dot * (0.5 + 0.5 * lattice_phase)
    
    # Update alpha and decay
    alpha = 0.7 * alpha + 0.3 * intensity
    
    # Camera
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -500)
    py5.rotate_y(t * 0.1)
    py5.rotate_x(t * 0.05)
    
    # Rendering: Point system
    py5.stroke_weight(6.0)  # Thicker sparks for 4K canvas
    py5.blend_mode(py5.ADD)
    
    # Quantize colors into bands to use vectorized points()
    num_bands = 12
    for b_idx in range(num_bands):
        t_low = b_idx / num_bands
        t_high = (b_idx + 1) / num_bands
        
        mask = (dot >= t_low) & (dot < t_high) & (alpha > 0.02)
        if not np.any(mask):
            continue
            
        avg_dot = (t_low + t_high) / 2
        # Brighter, more spectral colors
        r = np.clip(avg_dot * 255, 100, 255)
        g = np.clip((1-avg_dot) * 255 + 100, 100, 255)
        b = 255
        
        avg_a = np.mean(alpha[mask])
        py5.stroke(r, g, b, np.clip(avg_a * 1200, 0, 255))
        py5.points(pos[mask])
        
    py5.pop_matrix()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into 4K video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "22",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Mirror output
        subprocess.run(["cp", str(SKETCH_DIR / f"{WORK_NAME}.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
