import numpy as np
import py5
from pathlib import Path
import sys
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

N = 240_000
pos = np.zeros((N, 3), dtype=np.float32)
vel = np.zeros((N, 3), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize cylinder
    theta = np.random.uniform(0, 2 * np.pi, N).astype(np.float32)
    r = (np.random.uniform(0, 1, N)**0.5 * 150).astype(np.float32)
    y = np.random.uniform(-SIZE[1]*1.5, SIZE[1]*1.5, N).astype(np.float32)
    
    pos[:, 0] = r * np.cos(theta)
    pos[:, 1] = y
    pos[:, 2] = r * np.sin(theta)

def get_curl(p, t):
    freq = 0.003
    x = p[:, 0] * freq
    y = p[:, 1] * freq
    z = p[:, 2] * freq
    
    cx = np.sin(y + t) + np.cos(z - t)
    cy = np.sin(z + t) + np.cos(x - t)
    cz = np.sin(x + t) + np.cos(y - t)
    
    return np.column_stack((cx, cy, cz))

def draw():
    py5.background(5, 2, 10) # Dark obsidian night
    
    # Center camera
    py5.translate(SIZE[0]/2, SIZE[1]/2, -500)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Slow rotation
    py5.rotate_y(t * np.pi * 0.4)
    py5.rotate_x(0.15)
    
    global pos, vel
    
    # Instability envelope
    if t < 0.2:
        amp = (t / 0.2) * 0.1
    elif t < 0.6:
        amp = 0.1 + ((t - 0.2) / 0.4)**2 * 1.5
    else:
        amp = 1.6 + ((t - 0.6) / 0.4)**3 * 6.0
        
    phase = t * 40.0
    
    # Kink instability (m=1)
    k_kink = 0.004
    kink_x = np.cos(k_kink * pos[:, 1] + phase) * amp * 300.0
    kink_z = np.sin(k_kink * pos[:, 1] + phase) * amp * 300.0
    
    # Sausage instability (m=0)
    k_sausage = 0.008
    sausage = np.cos(k_sausage * pos[:, 1] - phase * 1.5)
    
    dx = pos[:, 0] - kink_x
    dz = pos[:, 2] - kink_z
    r = np.sqrt(dx**2 + dz**2) + 1.0
    
    # Target radius
    r0 = 150.0 * np.maximum(0.05, 1.0 - amp * 0.6 * sausage)
    
    # Confinement force
    f_r = (r0 - r) * 0.03
    
    fx = f_r * (dx / r)
    fz = f_r * (dz / r)
    fy = np.zeros_like(fx)
    
    # Jet force at pinches
    tightness = np.maximum(0.0, 150.0 - r0) / 150.0 
    jet_force = (tightness**5) * 60.0 * amp
    fy += jet_force * np.sign(pos[:, 1]) * np.random.uniform(0.8, 1.2, N)
    fx += jet_force * (dx / r) * 0.3
    fz += jet_force * (dz / r) * 0.3
    
    # Curl noise
    curl = get_curl(pos, t * 15) * (2.0 + amp * 8.0)
    
    vel[:, 0] += fx + curl[:, 0]
    vel[:, 1] += fy + curl[:, 1]
    vel[:, 2] += fz + curl[:, 2]
    
    damping = 0.92 + 0.06 * tightness
    vel *= damping[:, None]
    
    pos += vel
    
    # Boundary reset
    out_of_bounds = np.abs(pos[:, 1]) > SIZE[1] * 2.5
    if np.any(out_of_bounds):
        num_out = np.sum(out_of_bounds)
        pos[out_of_bounds, 0] = np.random.uniform(-150, 150, num_out)
        pos[out_of_bounds, 1] = np.random.uniform(-SIZE[1]*2, SIZE[1]*2, num_out) * np.sign(np.random.randn(num_out))
        pos[out_of_bounds, 2] = np.random.uniform(-150, 150, num_out)
        vel[out_of_bounds] = 0
    
    # Group by speed for fast py5.points drawing
    speed = np.linalg.norm(vel, axis=1)
    
    # Define speed bins
    bins = 10
    max_speed = 40.0
    
    for i in range(bins):
        s_min = i * (max_speed / bins)
        s_max = (i + 1) * (max_speed / bins)
        if i == bins - 1:
            mask = speed >= s_min
        else:
            mask = (speed >= s_min) & (speed < s_max)
            
        if not np.any(mask):
            continue
            
        ns = (i + 0.5) / bins
        
        # Deep Violet -> Electric Cyan -> White-Gold
        r_c = 80 + ns * 2 * (20 - 80) if ns < 0.5 else 20 + (ns - 0.5) * 2 * (255 - 20)
        g_c = 20 + ns * 2 * (220 - 20) if ns < 0.5 else 220 + (ns - 0.5) * 2 * (240 - 220)
        b_c = 220 + ns * 2 * (255 - 220) if ns < 0.5 else 255 + (ns - 0.5) * 2 * (150 - 255)
        a_c = 15 + ns * 200
        
        py5.stroke(r_c, g_c, b_c, a_c)
        py5.stroke_weight(2)
        py5.points(pos[mask])
    
    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print("Rendering MP4...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        print("Generating preview...")
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        print("Done.")

py5.run_sketch()
