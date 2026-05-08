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
N_PARTICLES = 120_000
SHOCK_RADIUS = 280
EXTENT = 1200
STAR_COUNT = 8_000

# State
pos = np.zeros((N_PARTICLES, 3), dtype=np.float32)
vel = np.zeros((N_PARTICLES, 3), dtype=np.float32)
age = np.zeros(N_PARTICLES, dtype=np.float32)
lifespan = np.zeros(N_PARTICLES, dtype=np.float32)

stars_pos = np.zeros((STAR_COUNT, 3), dtype=np.float32)
stars_mag = np.zeros(STAR_COUNT, dtype=np.float32)


def init_particles(indices):
    n = len(indices)
    # Emit from center
    pos[indices] = np.random.normal(0, 2, (n, 3))
    
    # Radial velocity
    angles = np.random.uniform(0, 2 * np.pi, n)
    phi = np.arccos(np.random.uniform(-1, 1, n))
    
    v_mag = np.random.uniform(12, 18, n)
    vel[indices, 0] = v_mag * np.sin(phi) * np.cos(angles)
    vel[indices, 1] = v_mag * np.sin(phi) * np.sin(angles)
    vel[indices, 2] = v_mag * np.cos(phi)
    
    age[indices] = 0
    lifespan[indices] = np.random.uniform(40, 120, n)


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Init all particles
    init_particles(np.arange(N_PARTICLES))
    # Randomize initial ages so they don't all die at once
    age[:] = np.random.uniform(0, lifespan, N_PARTICLES)
    
    # Init stars
    stars_pos[:, 0] = np.random.uniform(-SIZE[0]*1.5, SIZE[0]*1.5, STAR_COUNT)
    stars_pos[:, 1] = np.random.uniform(-SIZE[1]*1.5, SIZE[1]*1.5, STAR_COUNT)
    stars_pos[:, 2] = np.random.uniform(-2000, -1000, STAR_COUNT)
    stars_mag[:] = np.random.uniform(100, 255, STAR_COUNT)


def draw():
    global pos, vel, age
    
    py5.background(0)
    
    # Camera
    t = py5.frame_count / TOTAL_FRAMES
    cam_dist = 1200 + 200 * np.sin(t * 2 * np.pi)
    cam_x = cam_dist * np.sin(t * 2 * np.pi * 0.1)
    cam_z = cam_dist * np.cos(t * 2 * np.pi * 0.1)
    py5.camera(cam_x, -300 * np.sin(t * 2 * np.pi * 0.05), cam_z, 0, 0, 0, 0, 1, 0)
    
    # Draw Stars (as a separate pass)
    py5.stroke_weight(1)
    for i in range(STAR_COUNT):
        twinkle = np.sin(py5.frame_count * 0.05 + i) * 60
        py5.stroke(stars_mag[i] + twinkle, 150)
        py5.point(stars_pos[i, 0], stars_pos[i, 1], stars_pos[i, 2])

    # Update Physics
    age += 1
    
    # Distance from center
    r_sq = np.sum(pos**2, axis=1)
    r = np.sqrt(r_sq)
    
    # 1. Wind region (r < SHOCK_RADIUS)
    in_wind = r < SHOCK_RADIUS
    
    # 2. Shock region (r >= SHOCK_RADIUS)
    at_shock = ~in_wind
    
    # Apply turbulence at shock
    if np.any(at_shock):
        # Noise-driven turbulence using simple harmonic approximation
        ns = 0.003
        ph = py5.frame_count * 0.015
        
        # Swirling turbulence
        vel[at_shock, 0] += np.sin(pos[at_shock, 1] * ns + ph) * 0.6
        vel[at_shock, 1] += np.cos(pos[at_shock, 0] * ns - ph * 1.2) * 0.6
        vel[at_shock, 2] += np.sin(pos[at_shock, 0] * ns + ph * 0.8) * 0.6
        
        # Helical component
        vel[at_shock, 0] -= pos[at_shock, 1] * 0.002
        vel[at_shock, 1] += pos[at_shock, 0] * 0.002
        
        # Drag in shock region
        vel[at_shock] *= 0.97
        
    # Update positions
    pos += vel
    
    # Recycle particles
    dead = (age >= lifespan) | (r > EXTENT)
    if np.any(dead):
        init_particles(np.where(dead)[0])
    
    # Rendering Particles
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Color mapping
    h = np.zeros(N_PARTICLES)
    s = np.zeros(N_PARTICLES)
    b = np.zeros(N_PARTICLES)
    
    # Core to Shock: Cyan to Violet
    mask1 = in_wind
    h[mask1] = np.interp(r[mask1], [0, SHOCK_RADIUS], [190, 270])
    s[mask1] = np.interp(r[mask1], [0, SHOCK_RADIUS], [20, 80])
    b[mask1] = 100
    
    # Shock to Outer: Violet to Gold/Amber
    mask2 = at_shock
    h[mask2] = np.interp(r[mask2], [SHOCK_RADIUS, EXTENT], [270, 390])
    s[mask2] = np.interp(r[mask2], [SHOCK_RADIUS, EXTENT], [80, 100])
    b[mask2] = np.interp(r[mask2], [SHOCK_RADIUS, EXTENT], [100, 30])
    
    h %= 360
    
    # Draw points
    py5.begin_shape(py5.POINTS)
    # Draw every 2nd for speed in Python, still plenty for "silken" feel
    for i in range(0, N_PARTICLES, 2):
        a = np.interp(age[i], [0, 15, lifespan[i]-20, lifespan[i]], [0, 80, 80, 0])
        # Brightness pulse at core
        bri = b[i]
        if r[i] < 40:
            bri = 100
            a = 100
        
        py5.stroke(h[i], s[i], bri, a)
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
    py5.end_shape()
    
    # Core Glow (Blink/Pulse)
    py5.push_matrix()
    py5.stroke_weight(2)
    py5.stroke(190, 20, 100, 50 + 50 * np.sin(py5.frame_count * 0.3))
    py5.point(0, 0, 0)
    py5.pop_matrix()
    
    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
