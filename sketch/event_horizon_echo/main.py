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
NUM_PARTICLES = 130000
GM = 60000.0
EVENT_HORIZON = 90.0
PHOTON_RING = 135.0

# State
pos = None
vel = None
starfield = None

def setup():
    global pos, vel, starfield
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Accretion Disk Initialization
    r = np.random.uniform(EVENT_HORIZON * 1.5, 900, NUM_PARTICLES)
    theta = np.random.uniform(0, 2*np.pi, NUM_PARTICLES)
    z = np.random.normal(0, 18, NUM_PARTICLES)
    
    px = r * np.cos(theta)
    py = r * np.sin(theta)
    pos = np.stack([px, py, z], axis=-1).astype(np.float32)
    
    # Keplerian speed
    v_mag = np.sqrt(GM / (r + 1.0))
    vx = -v_mag * np.sin(theta)
    vy = v_mag * np.cos(theta)
    vz = np.random.normal(0, 0.2, NUM_PARTICLES)
    vel = np.stack([vx, vy, vz], axis=-1).astype(np.float32)
    
    # Starfield
    num_stars = 4000
    sx = np.random.uniform(-py5.width*2.5, py5.width*2.5, num_stars)
    sy = np.random.uniform(-py5.height*2.5, py5.height*2.5, num_stars)
    sz = np.random.uniform(-5000, -1500, num_stars)
    sb = np.random.uniform(10, 65, num_stars)
    starfield = np.stack([sx, sy, sz, sb], axis=-1).astype(np.float32)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos, vel
    
    # 1. Physics: Schwarzschild-ish Attraction & Accretion
    r_vec = -pos
    r_mag = np.linalg.norm(r_vec, axis=-1, keepdims=True)
    r_mag_s = np.clip(r_mag, EVENT_HORIZON, 3000)
    
    # Gravitational force
    acc = (r_vec / r_mag_s**3) * GM
    
    # Accretion drag (energy loss)
    drag = -vel * (120000.0 / (r_mag_s**4 + 1.0))
    
    vel += acc + drag
    pos += vel
    
    # Annihilate inside EH
    dead = (r_mag[:, 0] < EVENT_HORIZON)
    pos[dead] = np.array([-5000.0, -5000.0, -5000.0])
    
    # 2. Render
    py5.background(0)
    
    # Starfield
    py5.push_matrix()
    py5.stroke_weight(1.2)
    for s in starfield:
        py5.stroke(0, 0, s[3], 50)
        py5.point(s[0], s[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1400)
    # Tilted view for Accretion Disk
    py5.rotate_x(1.3)
    py5.rotate_z(py5.frame_count * 0.008)
    
    # Event Horizon Shadow
    py5.no_stroke()
    py5.fill(0, 0, 0, 100)
    py5.sphere(EVENT_HORIZON)
    
    # Photon Ring Glow
    for i in range(4):
        py5.fill(45, 60, 100, 12 - i*3)
        py5.sphere(PHOTON_RING + i*20)
    
    # Doppler Beaming
    # With rotate_x(1.3), positive Y in disk is roughly "towards" camera
    v_y = vel[:, 1]
    
    # Map v_y to Blue/Red shift
    # Positive v_y -> Cyan (185), Negative -> Amber (45)
    h = np.interp(v_y, [-18, 18], [45, 185])
    b = np.interp(v_y, [-18, 18], [30, 100]) # Beaming effect
    
    # Grouped Rendering
    p_act_mask = (pos[:, 0] > -4000)
    p_act = pos[p_act_mask]
    h_act = h[p_act_mask]
    b_act = b[p_act_mask]
    
    # Toward band
    mask_to = h_act >= 115
    if np.any(mask_to):
        py5.stroke(185, 80, b_act[mask_to].mean(), 65)
        py5.stroke_weight(1.8)
        py5.points(p_act[mask_to])
        
    # Away band
    mask_aw = h_act < 115
    if np.any(mask_aw):
        py5.stroke(45, 75, b_act[mask_aw].mean(), 40)
        py5.stroke_weight(1.4)
        py5.points(p_act[mask_aw])

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
