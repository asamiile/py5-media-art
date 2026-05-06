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
MAX_PARTICLES = 160000
EMISSION_RATE = 2800 
JET_VEL = 38.0

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
    t_spin = py5.frame_count * 0.12 
    p_prec = py5.frame_count * 0.018 
    
    # Precessing axis
    axis = np.array([
        np.sin(p_prec) * np.cos(t_spin),
        np.cos(p_prec),
        np.sin(p_prec) * np.sin(t_spin)
    ], dtype=np.float32)
    
    inactive = np.where(age <= 0)[0]
    if len(inactive) > EMISSION_RATE:
        new_idx = inactive[:EMISSION_RATE]
        half = EMISSION_RATE // 2
        
        # Pole 1 & 2
        pos[new_idx] = 0.0
        # Add some scatter
        scatter = np.random.normal(0, 1.2, (EMISSION_RATE, 3))
        vel[new_idx[:half]] = axis * JET_VEL + scatter[:half]
        vel[new_idx[half:]] = -axis * JET_VEL + scatter[half:]
        
        age[new_idx] = np.random.uniform(60, 140, EMISSION_RATE)
    
    # 2. Physics: Magnetic Helicity & Expansion
    active = age > 0
    if np.any(active):
        v_act = vel[active]
        # v x axis for helical twist
        v_cross = np.cross(v_act, axis)
        vel[active] += v_cross * 0.12
        
        # Relativistic acceleration / expansion
        vel[active] *= 1.018
        
        pos[active] += vel[active]
        age[active] -= 1
    
    # 3. Render
    py5.background(0)
    
    # Starfield
    py5.push_matrix()
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[3], 45)
        py5.point(s[0], s[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1800)
    py5.rotate_y(py5.frame_count * 0.004)
    py5.rotate_x(0.3)
    
    # Neutron Star Core
    py5.push_matrix()
    py5.no_stroke()
    py5.fill(0, 0, 100, 100) # White
    py5.sphere(45)
    # Volumetric Glow
    for i in range(6):
        py5.fill(240, 50, 100, 12 - i*2)
        py5.sphere(55 + i*40)
    py5.pop_matrix()
    
    # Jet Particles
    p_act = pos[active]
    age_act = age[active]
    
    # Spectral mapping: Cobalt (core-near) to Magenta (tail)
    h = np.interp(age_act, [0, 140], [310, 240])
    
    # Efficient grouped rendering
    for hue_val in [240, 275, 310]:
        mask = (h >= hue_val - 20) & (h < hue_val + 20)
        if np.any(mask):
            py5.stroke(hue_val, 75, 100, 60)
            py5.stroke_weight(2.0 if hue_val == 240 else 1.5)
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
