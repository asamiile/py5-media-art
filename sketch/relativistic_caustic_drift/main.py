from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation constants
NUM_PARTICLES = 180_000
NUM_STARS = 12_000

# State
particles = None
colors = None
stars = None
hubs = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, colors, stars, hubs
    
    # Initialize particles on a grid (source plane)
    res_x = 600
    res_y = 300
    x, y = np.meshgrid(np.linspace(-800, 800, res_x), np.linspace(-400, 400, res_y))
    particles_base = np.stack([x, y, np.zeros_like(x) - 400], axis=-1).reshape(-1, 3).astype(np.float32)
    particles = particles_base.copy()
    
    # Base colors (Glacial/Silver/Cyan)
    colors = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    colors[:, 0] = 190 + 20 * np.random.rand(NUM_PARTICLES) # Hue
    colors[:, 1] = 40 + 30 * np.random.rand(NUM_PARTICLES)  # Sat
    colors[:, 2] = 60 + 40 * np.random.rand(NUM_PARTICLES)  # Bri
    
    # Background stars
    stars = np.random.uniform(-1500, 1500, (NUM_STARS, 3)).astype(np.float32)
    
    # Gravitational hubs (positions and masses)
    hubs = np.random.uniform(-200, 200, (4, 3)).astype(np.float32)
    hubs[:, 2] = -100 # Closer to viewer than source

def draw():
    global particles, hubs
    if py5.frame_count % 50 == 0:
        print(f"Frame: {py5.frame_count}/{TOTAL_FRAMES}")
    
    t = py5.frame_count * 0.02
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    py5.camera(0, 0, 800, 0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(255, 120)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Hub motion
    hubs[0] = [300 * np.sin(t * 0.7), 150 * np.cos(t * 0.5), -100]
    hubs[1] = [-250 * np.cos(t * 0.4), -200 * np.sin(t * 0.8), -100]
    hubs[2] = [100 * np.sin(t * 1.2), -250 * np.cos(t * 0.6), -50]
    hubs[3] = [-150 * np.cos(t * 0.9), 300 * np.sin(t * 0.3), -150]
    
    # Deflection model: particles are rays from -400 to 800
    # For simplicity, we'll just warp the source plane
    res_x = 600
    res_y = 300
    x, y = np.meshgrid(np.linspace(-800, 800, res_x), np.linspace(-400, 400, res_y))
    p_pts = np.stack([x, y, np.zeros_like(x) - 400], axis=-1).reshape(-1, 3).astype(np.float32)
    
    # Vectorized deflection
    total_deflection = np.zeros_like(p_pts)
    for i in range(4):
        diff = p_pts - hubs[i]
        dist_sq = np.sum(diff**2, axis=1)[:, np.newaxis] + 1000 # Softening
        mag = 150000.0 / dist_sq
        total_deflection += diff * mag * 0.01
        
    particles = p_pts + total_deflection
    
    # Calculate "magnification" (intensity) based on local density
    # Or just use the magnitude of deflection as a proxy for caustic peaks
    infl = np.linalg.norm(total_deflection, axis=1)
    infl_norm = infl / np.max(infl) if np.max(infl) > 0 else 0
    
    # Additive Rendering
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Draw in bins based on influence (caustics)
    for i in range(5):
        m_low = i * 0.2
        m_high = (i + 1) * 0.2
        mask = (infl_norm >= m_low) & (infl_norm < m_high)
        if np.any(mask):
            # High influence = White/Gold, Low = Cyan/Silver
            h = 190 - i * 30
            if h < 0: h = 50 # Gold
            s = 60 - i * 10
            if s < 0: s = 80
            b = 30 + i * 15
            alpha = 20 + i * 20
            
            py5.stroke(h, s, b, alpha)
            py5.stroke_weight(1.0 + i * 0.5)
            py5.points(particles[mask])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run([
            "cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        ], check=True)

if __name__ == "__main__":
    py5.run_sketch()
