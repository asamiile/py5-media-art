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

# Particle configuration
NUM_PARTICLES = 50000
P_POS = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
P_VEL = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
P_LIFE = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_ACCEL_MAG = np.zeros(NUM_PARTICLES, dtype=np.float32)

# Magnetic field configuration
NUM_DIPOLES = 4
DIPOLE_POS = np.zeros((NUM_DIPOLES, 2), dtype=np.float32)
DIPOLE_MOMENT = np.zeros((NUM_DIPOLES, 2), dtype=np.float32)
DIPOLE_ACTIVE = np.ones(NUM_DIPOLES, dtype=bool)

# Starfield
NUM_STARS = 2000
STARS_X = np.random.uniform(0, SIZE[0], NUM_STARS)
STARS_Y = np.random.uniform(0, SIZE[1], NUM_STARS)
STARS_SIZE = np.random.exponential(0.5, NUM_STARS) + 0.1

def init_particles(indices):
    P_POS[indices] = np.random.uniform(0, [SIZE[0], SIZE[1]], (len(indices), 2))
    P_VEL[indices] = 0
    P_LIFE[indices] = np.random.uniform(0.2, 1.0, len(indices))
    P_ACCEL_MAG[indices] = 0

def get_field(pos):
    # pos: (N, 2)
    b_total = np.zeros_like(pos)
    for i in range(NUM_DIPOLES):
        if not DIPOLE_ACTIVE[i]: continue
        r_vec = pos - DIPOLE_POS[i]
        r_mag_sq = np.sum(r_vec**2, axis=1, keepdims=True)
        r_mag = np.sqrt(r_mag_sq)
        r_hat = r_vec / (r_mag + 1e-6)
        
        m = DIPOLE_MOMENT[i]
        m_dot_r = np.sum(m * r_hat, axis=1, keepdims=True)
        
        # B = (3*(m.r_hat)*r_hat - m) / r^3
        b = (3 * m_dot_r * r_hat - m) / (r_mag_sq * r_mag + 100) # Soften center
        b_total += b
    
    # Normalize field
    b_mag = np.sqrt(np.sum(b_total**2, axis=1, keepdims=True))
    return b_total / (b_mag + 1e-6), b_mag

def setup():
    py5.size(*SIZE)
    py5.background(5, 5, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize dipoles
    for i in range(NUM_DIPOLES):
        DIPOLE_POS[i] = [SIZE[0]/2 + np.random.uniform(-300, 300), 
                         SIZE[1]/2 + np.random.uniform(-200, 200)]
        angle = np.random.uniform(0, py5.TWO_PI)
        DIPOLE_MOMENT[i] = [np.cos(angle) * 50000, np.sin(angle) * 50000]
    
    init_particles(np.arange(NUM_PARTICLES))

def update_field_topology(frame):
    # Periodically "reconnect" by flipping or moving dipoles
    if frame % 120 == 0:
        idx = np.random.randint(NUM_DIPOLES)
        angle = np.random.uniform(0, py5.TWO_PI)
        DIPOLE_MOMENT[idx] = [np.cos(angle) * 50000, np.sin(angle) * 50000]
        # Move it slightly
        DIPOLE_POS[idx] += np.random.uniform(-100, 100, 2)

def draw():
    update_field_topology(py5.frame_count)
    
    # Update particles
    b_dir, b_mag = get_field(P_POS)
    
    # Advect along field
    P_VEL[:] = b_dir * (2.0 + np.log1p(b_mag.flatten() * 0.001)[:, None])
    P_POS[:] += P_VEL
    P_LIFE[:] -= 0.005
    
    # Acceleration mag for coloring
    P_ACCEL_MAG[:] = b_mag.flatten()
    
    # Respawn dead or out of bounds
    dead = (P_LIFE <= 0) | (P_POS[:, 0] < 0) | (P_POS[:, 0] > SIZE[0]) | (P_POS[:, 1] < 0) | (P_POS[:, 1] > SIZE[1])
    if np.any(dead):
        init_particles(np.where(dead)[0])

    # Draw
    py5.no_stroke()
    py5.fill(5, 5, 15, 20) # Fade
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw stars (once or subtle every frame)
    if py5.frame_count == 1:
        py5.stroke(255, 150)
        for i in range(NUM_STARS):
            py5.stroke_weight(STARS_SIZE[i])
            py5.point(STARS_X[i], STARS_Y[i])
    
    # Draw particles
    # Optimization: Group particles by intensity bins and use py5.points()
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    num_bins = 20
    intensities = np.clip(P_ACCEL_MAG * 0.1, 0, 1)
    
    for b in range(num_bins):
        low = b / num_bins
        high = (b + 1) / num_bins
        mask = (intensities >= low) & (intensities < high)
        if not np.any(mask): continue
        
        # Representative color for the bin
        intensity = (low + high) / 2
        if intensity < 0.3:
            h = 240 - (intensity / 0.3) * 60 # 240 -> 180
            s = 80
            v = 40 + intensity * 100
        elif intensity < 0.7:
            h = 180 - ((intensity - 0.3) / 0.4) * 135 # 180 -> 45
            s = 80
            v = 80 + intensity * 20
        else:
            h = 45
            s = 80 - ((intensity - 0.7) / 0.3) * 80 # 80 -> 0 (White)
            v = 100
            
        py5.stroke(h, s, v, 30) # Fixed low alpha for trails
        py5.stroke_weight(1.0)
        # Convert P_POS[mask] to a list or array for points()
        py5.points(P_POS[mask])
    
    py5.color_mode(py5.RGB, 255, 255, 255, 255)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 60:
        py5.save(str(SKETCH_DIR / PREVIEW_FILENAME))

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
