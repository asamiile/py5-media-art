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
MAX_PARTICLES = 150000
EMISSION_RATE = 3000 
SOLAR_WIND_VEL = np.array([18.0, 0.0, 0.0], dtype=np.float32)
SHIELD_RADIUS = 450.0

# State
pos = None
vel = None
age = None
starfield = None

def setup():
    global pos, vel, age, starfield
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    pos = np.full((MAX_PARTICLES, 3), -5000.0, dtype=np.float32)
    vel = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)
    age = np.zeros(MAX_PARTICLES, dtype=np.float32)
    
    # Starfield
    num_stars = 4000
    sx = np.random.uniform(-py5.width*2, py5.width*2, num_stars)
    sy = np.random.uniform(-py5.height*2, py5.height*2, num_stars)
    sz = np.random.uniform(-4000, 1000, num_stars)
    sb = np.random.uniform(10, 70, num_stars)
    starfield = np.stack([sx, sy, sz, sb], axis=-1)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos, vel, age
    
    # 1. Emission
    inactive = np.where(age <= 0)[0]
    if len(inactive) > EMISSION_RATE:
        new_idx = inactive[:EMISSION_RATE]
        pos[new_idx, 0] = -1500.0
        pos[new_idx, 1] = np.random.uniform(-1000, 1000, EMISSION_RATE)
        pos[new_idx, 2] = np.random.uniform(-1000, 1000, EMISSION_RATE)
        vel[new_idx] = SOLAR_WIND_VEL + np.random.normal(0, 1.0, (EMISSION_RATE, 3))
        age[new_idx] = np.random.uniform(150, 250, EMISSION_RATE)
    
    # 2. Physics: Magnetopause deflection
    r = np.linalg.norm(pos, axis=-1)
    active = age > 0
    
    # Magnetic deflection logic
    # Approximate magnetosphere shape: parabola-like
    # x = c - (y^2 + z^2)/k
    # If x > shield_x(y,z), particle is deflected
    # Simplification: if r < SHIELD_RADIUS, push out
    inside = (r < SHIELD_RADIUS) & active
    if np.any(inside):
        p_in = pos[inside]
        r_in = r[inside]
        # Repulsion from origin
        force = (SHIELD_RADIUS / (r_in + 1.0))[:, np.newaxis] * 1.5 * (p_in / r_in[:, np.newaxis])
        # Pushed specifically along the "magnetotail" (positive X)
        force[:, 0] += 2.0
        vel[inside] += force
        # Energy loss on contact
        vel[inside] *= 0.98
    
    # Global pressure
    vel[active] += np.array([0.2, 0, 0])
    
    # Move
    pos[active] += vel[active]
    age[active] -= 1
    
    # Kill
    age[pos[:, 0] > 1500] = 0
    
    # Render
    py5.background(0)
    
    # Starfield
    py5.push_matrix()
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[3], 50)
        py5.point(s[0], s[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1200)
    py5.rotate_y(-1.0 + py5.frame_count * 0.003)
    py5.rotate_x(0.3)
    
    # Earth
    py5.push_matrix()
    py5.no_stroke()
    # Dark side
    py5.fill(220, 90, 15)
    py5.sphere(100)
    # Atmospheric glow (Auroral)
    for i in range(4):
        py5.fill(140, 80, 100, 8 - i*2)
        py5.sphere(110 + i*20)
    py5.pop_matrix()
    
    # Particles
    p_act = pos[active]
    r_act = r[active]
    age_act = age[active]
    
    # Auroral Green (140) for trapped, Solar Gold (45) for wind
    h = np.interp(r_act, [100, 600], [140, 45])
    
    # Draw in chunks by hue for color variation
    for hue_val in [45, 90, 140]:
        mask = (h >= hue_val - 25) & (h < hue_val + 25)
        if np.any(mask):
            py5.stroke(hue_val, 70, 100, 60)
            py5.stroke_weight(1.8 if hue_val > 100 else 1.2)
            py5.points(p_act[mask])

    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "17",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
