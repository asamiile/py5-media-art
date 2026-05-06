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
NUM_PARTICLES = 80000
particles = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
velocities = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)

# Cymatic Parameters (Chladni Coefficients)
# Function: sin(pi*n*x)*sin(pi*m*y) - sin(pi*m*x)*sin(pi*n*y)
modes = [
    (3, 2), (5, 4), (7, 6), (2, 5)
]
weights = np.random.uniform(0.5, 1.5, len(modes))
phases = np.random.uniform(0, py5.TWO_PI, len(modes))

def chladni(x, y, t):
    z = 0
    for i, (n, m) in enumerate(modes):
        w = weights[i] * np.sin(phases[i] + t * 0.5)
        # Normalize x, y to [-1, 1]
        nx = (x / SIZE[0]) * 2 - 1
        ny = (y / SIZE[1]) * 2 - 1
        term = np.sin(np.pi * n * nx) * np.sin(np.pi * m * ny) - \
               np.sin(np.pi * m * nx) * np.sin(np.pi * n * ny)
        z += w * term
    return z

def get_gradient(x, y, t):
    eps = 1.0
    z0 = chladni(x, y, t)
    zx = chladni(x + eps, y, t)
    zy = chladni(x, y + eps, t)
    return (zx - z0) / eps, (zy - z0) / eps

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(5, 5, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles randomly
    global particles
    particles[:, 0] = np.random.uniform(0, SIZE[0], NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(0, SIZE[1], NUM_PARTICLES)

def draw():
    global particles, velocities
    
    # Motion and advection
    t = py5.frame_count / FPS
    
    # Vectorized gradient descent towards nodal lines (where |chladni| is small)
    # Actually, particles in cymatics tend to move to nodes where vibration is zero.
    # The gradient of the squared pressure field (z^2) points AWAY from nodes.
    # So we move in the direction of -grad(z^2).
    
    # To keep it performant, we'll use a subset of particles or just direct calculation
    # Since we have 80k, we must be careful with NumPy.
    
    px = particles[:, 0]
    py = particles[:, 1]
    
    # Clamp to bounds
    px = np.clip(px, 0, SIZE[0]-1)
    py = np.clip(py, 0, SIZE[1]-1)
    
    # Re-map to [-1, 1]
    nx = (px / SIZE[0]) * 2 - 1
    ny = (py / SIZE[1]) * 2 - 1
    
    z = np.zeros(NUM_PARTICLES, dtype=np.float32)
    dzdx = np.zeros(NUM_PARTICLES, dtype=np.float32)
    dzdy = np.zeros(NUM_PARTICLES, dtype=np.float32)
    
    for i, (n, m) in enumerate(modes):
        w = weights[i] * np.sin(phases[i] + t * 0.5)
        snx = np.sin(np.pi * n * nx)
        sny = np.sin(np.pi * m * ny)
        smx = np.sin(np.pi * m * nx)
        smy = np.sin(np.pi * n * ny)
        
        cnx = np.cos(np.pi * n * nx)
        cny = np.cos(np.pi * m * ny)
        cmx = np.cos(np.pi * m * nx)
        cmy = np.cos(np.pi * n * ny)
        
        term = snx * smy - smx * sny
        z += w * term
        
        dzdx += w * (np.pi * n * cnx * smy - np.pi * m * cmx * sny)
        dzdy += w * (np.pi * m * snx * cmy - np.pi * n * smx * cny)
        
    # Particles move towards nodes (z=0)
    # Acceleration = -sign(z) * grad(z)
    acc_x = -np.sign(z) * dzdx
    acc_y = -np.sign(z) * dzdy
    
    # Add some noise
    acc_x += np.random.normal(0, 0.05, NUM_PARTICLES)
    acc_y += np.random.normal(0, 0.05, NUM_PARTICLES)
    
    velocities += np.stack([acc_x, acc_y], axis=1) * 0.1
    velocities *= 0.92  # Friction
    
    particles += velocities
    
    # Boundary handling: wrap around or bounce
    mask_x = (particles[:, 0] < 0) | (particles[:, 0] >= SIZE[0])
    mask_y = (particles[:, 1] < 0) | (particles[:, 1] >= SIZE[1])
    particles[mask_x, 0] = np.random.uniform(0, SIZE[0], np.sum(mask_x))
    particles[mask_y, 1] = np.random.uniform(0, SIZE[1], np.sum(mask_y))
    
    # Rendering
    py5.no_stroke()
    
    # Fade background for trails
    py5.fill(5, 5, 15, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Draw particles
    py5.load_np_pixels()
    
    # Retina handling: get actual pixel buffer shape
    ph, pw = py5.np_pixels.shape[:2]
    scale_x = pw / SIZE[0]
    scale_y = ph / SIZE[1]
    
    # Convert particles to pixel coordinates
    idx_x = (particles[:, 0] * scale_x).astype(np.int32)
    idx_y = (particles[:, 1] * scale_y).astype(np.int32)
    
    # Filter out-of-bounds
    valid = (idx_x >= 0) & (idx_x < pw) & (idx_y >= 0) & (idx_y < ph)
    idx_x = idx_x[valid]
    idx_y = idx_y[valid]
    z_valid = z[valid]
    
    # Map intensity
    intensity = 1.0 / (1.0 + np.abs(z_valid) * 8.0)
    
    # Vectorized additive blending
    # target color based on val
    # Indigo: (75, 0, 130), Cyan: (0, 255, 255), Solar Gold: (255, 215, 0)
    tr = (intensity * 120 + 10).astype(np.uint16)
    tg = (intensity * 180 + 20).astype(np.uint16)
    tb = (intensity * 255 + 40).astype(np.uint16)
    
    # Get current pixels
    pixels_subset = py5.np_pixels[idx_y, idx_x].astype(np.uint16)
    
    # Additive blend (RGBA)
    pixels_subset[:, 0] = np.clip(pixels_subset[:, 0] + tr, 0, 255)
    pixels_subset[:, 1] = np.clip(pixels_subset[:, 1] + tg, 0, 255)
    pixels_subset[:, 2] = np.clip(pixels_subset[:, 2] + tb, 0, 255)
    pixels_subset[:, 3] = 255 # Alpha
    
    # Write back
    py5.np_pixels[idx_y, idx_x] = pixels_subset.astype(np.uint8)

    py5.update_np_pixels()
    
    # Add starfield occasionally
    if py5.frame_count == 1:
        for _ in range(200):
            x, y = np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])
            s = np.random.uniform(0.5, 2.0)
            py5.fill(255, 255, 255, np.random.uniform(50, 200))
            py5.circle(x, y, s)

    # Save frames and exit
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

py5.run_sketch()
