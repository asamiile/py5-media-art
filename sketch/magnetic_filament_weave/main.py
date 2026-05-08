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

# Simulation Parameters
N_PARTICLES = 150_000
N_DIPOLES = 5
STAR_COUNT = 12_000

# State
pos = np.zeros((N_PARTICLES, 3), dtype=np.float32)
age = np.zeros(N_PARTICLES, dtype=np.float32)
lifespan = np.zeros(N_PARTICLES, dtype=np.float32)

dipoles_pos = np.random.uniform(-400, 400, (N_DIPOLES, 3))
dipoles_axis = np.random.normal(0, 1, (N_DIPOLES, 3))
dipoles_axis /= np.linalg.norm(dipoles_axis, axis=1)[:, None]

stars_pos = np.zeros((STAR_COUNT, 3), dtype=np.float32)
stars_mag = np.zeros(STAR_COUNT, dtype=np.float32)

def init_particles(indices):
    n = len(indices)
    pos[indices] = np.random.uniform(-800, 800, (n, 3))
    age[indices] = 0
    lifespan[indices] = np.random.uniform(40, 100, n)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    init_particles(np.arange(N_PARTICLES))
    age[:] = np.random.uniform(0, lifespan, N_PARTICLES)
    
    # Init stars
    stars_pos[:, 0] = np.random.uniform(-SIZE[0]*1.5, SIZE[0]*1.5, STAR_COUNT)
    stars_pos[:, 1] = np.random.uniform(-SIZE[1]*1.5, SIZE[1]*1.5, STAR_COUNT)
    stars_pos[:, 2] = np.random.uniform(-2500, -1500, STAR_COUNT)
    stars_mag[:] = np.random.uniform(100, 255, STAR_COUNT)


def draw():
    global pos, age
    py5.background(0)
    
    # Camera
    t = py5.frame_count / TOTAL_FRAMES
    cam_dist = 1400
    cam_x = cam_dist * np.sin(t * 2 * np.pi * 0.08)
    cam_z = cam_dist * np.cos(t * 2 * np.pi * 0.08)
    py5.camera(cam_x, -400 * np.cos(t * 2 * np.pi * 0.04), cam_z, 0, 0, 0, 0, 1, 0)
    
    # 1. Stars
    py5.stroke_weight(1)
    for i in range(STAR_COUNT):
        twinkle = np.sin(py5.frame_count * 0.08 + i) * 60
        py5.stroke(stars_mag[i] + twinkle, 180)
        py5.point(stars_pos[i, 0], stars_pos[i, 1], stars_pos[i, 2])

    # 2. Magnetic Field Physics
    # Advect particles along B-field
    # B = sum(dipole_fields) + spiral_field
    
    b_field = np.zeros_like(pos)
    
    # Local dipoles
    for i in range(N_DIPOLES):
        r_vec = pos - dipoles_pos[i]
        r_mag_sq = np.sum(r_vec**2, axis=1)[:, None] + 1000
        r_mag = np.sqrt(r_mag_sq)
        
        # Simple dipole approximation: B = (3(m.r)r - m(r^2)) / r^5
        m = dipoles_axis[i]
        m_dot_r = np.sum(m * r_vec, axis=1)[:, None]
        
        dipole_b = (3 * m_dot_r * r_vec - m * r_mag_sq) / (r_mag**4 + 1000)
        b_field += dipole_b * 50000
        
    # Global spiral field
    rad = np.sqrt(pos[:, 0]**2 + pos[:, 2]**2)[:, None] + 1
    spiral_b = np.stack([-pos[:, 2], np.zeros(N_PARTICLES), pos[:, 0]], axis=1) / rad * 5
    b_field += spiral_b
    
    # Update positions
    step = 2.5
    pos += b_field * step
    age += 1
    
    # Recycle
    dead = (age >= lifespan) | (np.sum(pos**2, axis=1) > 1500**2)
    if np.any(dead):
        init_particles(np.where(dead)[0])
        
    # Rendering
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Colors: HSB mapping based on local field strength or position
    b_mag = np.linalg.norm(b_field, axis=1)
    hues = np.interp(b_mag, [0, 5], [180, 320]) # Cyan to Magenta
    sats = np.interp(b_mag, [0, 5], [40, 90])
    bris = np.interp(b_mag, [0, 5], [40, 100])
    
    py5.begin_shape(py5.POINTS)
    # Draw every 3rd for performance in Python
    for i in range(0, N_PARTICLES, 3):
        a = np.interp(age[i], [0, 15, lifespan[i]-20, lifespan[i]], [0, 70, 70, 0])
        py5.stroke(hues[i] % 360, sats[i], bris[i], a)
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
    py5.end_shape()
    
    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
