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
SPAWN_RATE = 8000 
JITTER_MAG = 6.0

# State
pos = None
age = None
max_age = None
starfield = None

def setup():
    global pos, age, max_age, starfield
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    pos = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)
    age = np.zeros(MAX_PARTICLES, dtype=np.float32)
    max_age = np.zeros(MAX_PARTICLES, dtype=np.float32)
    
    # Background Starfield
    num_stars = 4000
    sx = np.random.uniform(-py5.width*2.5, py5.width*2.5, num_stars)
    sy = np.random.uniform(-py5.height*2.5, py5.height*2.5, num_stars)
    sz = np.random.uniform(-4500, -1500, num_stars)
    sb = np.random.uniform(5, 55, num_stars)
    starfield = np.stack([sx, sy, sz, sb], axis=-1).astype(np.float32)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos, age, max_age
    
    # 1. Quantum Spawning
    inactive = np.where(age <= 0)[0]
    if len(inactive) > SPAWN_RATE:
        new_idx = inactive[:SPAWN_RATE]
        
        # Clumped positions using structured noise-like function
        t = py5.frame_count * 0.04
        # Generate candidates
        cx = np.random.uniform(-1200, 1200, SPAWN_RATE)
        cy = np.random.uniform(-1000, 1000, SPAWN_RATE)
        cz = np.random.uniform(-1000, 1000, SPAWN_RATE)
        
        # Probability field: interfering sine waves
        prob = (np.sin(cx * 0.001 + t) * np.cos(cy * 0.002 - t*0.5) * np.sin(cz * 0.0015 + t*0.3))
        # Structural mask
        mask = prob > -0.2 # Adjust for density
        
        spawned = new_idx[mask]
        if len(spawned) > 0:
            pos[spawned] = np.stack([cx[mask], cy[mask], cz[mask]], axis=-1)
            # Extremely short lived
            m_age = np.random.uniform(4, 18, len(spawned))
            age[spawned] = m_age
            max_age[spawned] = m_age
            
    # 2. Uncertainty Jitter
    active = age > 0
    if np.any(active):
        # Brownian-like jitter (quantum uncertainty)
        count = np.sum(active)
        pos[active] += np.random.normal(0, JITTER_MAG, (count, 3))
        age[active] -= 1
        
    # 3. Render
    py5.background(0)
    
    # Starfield
    py5.push_matrix()
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[3], 50)
        py5.point(s[0], s[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1500)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_z(py5.frame_count * 0.001)
    
    # Virtual Particles
    p_act = pos[active]
    age_act = age[active]
    max_act = max_age[active]
    
    # Life ratio
    life = age_act / max_act
    
    # Color: White (birth) -> Indigo (death)
    # High life -> White (0, 0, 100)
    # Low life -> Indigo (265, 80, 50)
    h = np.interp(life, [0, 1], [265, 0])
    s = np.interp(life, [0, 1], [80, 0])
    b = np.interp(life, [0, 1], [50, 100])
    
    # Split into 3 bands for rendering speed
    for i, h_target in enumerate([0, 265]):
        if i == 0: # White/Birth
            mask = life > 0.6
        else: # Indigo/Decay
            mask = life <= 0.6
            
        if np.any(mask):
            py5.stroke(h_target, s[mask].mean(), b[mask].mean(), 75)
            py5.stroke_weight(1.8 if i == 0 else 1.2)
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
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
