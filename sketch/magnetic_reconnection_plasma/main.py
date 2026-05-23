from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 150000

# Particle states
pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
age = np.zeros(NUM_PARTICLES, dtype=np.float32)
max_age = np.random.uniform(50, 150, NUM_PARTICLES).astype(np.float32)

def reset_particles(mask):
    count = np.sum(mask)
    if count == 0: return
    # Start particles near the current sheets (y ~ height/2, x spread out)
    pos[mask, 0] = np.random.uniform(0, SIZE[0], count)
    pos[mask, 1] = np.random.uniform(SIZE[1]*0.3, SIZE[1]*0.7, count)
    vel[mask, 0] = 0.0
    vel[mask, 1] = 0.0
    age[mask] = 0

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    reset_particles(np.ones(NUM_PARTICLES, dtype=bool))
    py5.background(5, 0, 10)

def get_magnetic_field(x, y, t):
    # Normalized coordinates
    nx = (x - SIZE[0]/2) / (SIZE[0]/2)
    ny = (y - SIZE[1]/2) / (SIZE[1]/2)
    
    # Reconnection dynamics
    # Before t=0.5: opposing fields
    # At t=0.5: reconnection event (X-point forms)
    # After t=0.5: reconfigured fields
    
    phase = np.clip((t - 0.5) * 5.0, -1.0, 1.0) # -1 to 1 transition
    
    # Background Harris sheet (opposing fields)
    B0 = 10.0
    a = 0.2
    
    # Sweet-Parker / Petschek like topology
    # Bx ~ tanh(y/a), By ~ x
    Bx = B0 * np.tanh(ny / a)
    By = -B0 * nx * 0.5 * (1.0 + phase) # As phase goes to 1, X-point deepens
    
    # Add noise for turbulence
    noise_x = py5.noise(nx*2.0, ny*2.0, t*2.0) - 0.5
    noise_y = py5.noise(nx*2.0 + 10, ny*2.0 + 10, t*2.0) - 0.5
    
    Bx += noise_x * 4.0
    By += noise_y * 4.0
    
    # Outflow jets along x-axis after reconnection
    jet = np.maximum(0.0, phase) * B0 * 2.0
    Bx += np.sign(nx) * jet * np.exp(-ny**2 / (0.1**2))
    
    return Bx, By

def draw():
    global pos, vel, age
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 0, 10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Update particles
    Bx, By = get_magnetic_field(pos[:, 0], pos[:, 1], t)
    
    # ExB drift + thermal motion
    # We treat B field directly as velocity for visualization
    vel[:, 0] = vel[:, 0] * 0.9 + Bx * 0.5
    vel[:, 1] = vel[:, 1] * 0.9 + By * 0.5
    
    pos += vel
    age += 1
    
    # Reset old or out of bounds particles
    out_of_bounds = (pos[:, 0] < 0) | (pos[:, 0] > SIZE[0]) | (pos[:, 1] < 0) | (pos[:, 1] > SIZE[1])
    dead = age > max_age
    reset_particles(out_of_bounds | dead)
    
    # Render
    py5.blend_mode(py5.ADD)
    
    # Speed-based coloring
    speed = np.sqrt(vel[:, 0]**2 + vel[:, 1]**2)
    
    # Gold for slow, Magenta for fast/hot
    # Normalize speed roughly 0 to 15
    norm_speed = np.clip(speed / 15.0, 0.0, 1.0)
    
    # We will draw points. Since we can't easily vectorize color array in pure py5.points() without NumPy pixel buffer,
    # we use a subset batching or simple loop. Since 150k is large, we map directly to pixels.
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Filter valid positions
    valid = (pos[:, 0] >= 0) & (pos[:, 0] < SIZE[0]) & (pos[:, 1] >= 0) & (pos[:, 1] < SIZE[1])
    px = pos[valid, 0].astype(int)
    py_coords = pos[valid, 1].astype(int)
    ns = norm_speed[valid]
    
    # Colors (ARGB)
    # Background is black. We add to existing pixels to simulate additive blending manually.
    
    # Gold: R=255, G=200, B=50
    # Magenta: R=255, G=0, B=255
    r_add = np.full(len(ns), 255, dtype=np.uint16)
    g_add = (200.0 * (1.0 - ns)).astype(np.uint16)
    b_add = (50.0 * (1.0 - ns) + 255.0 * ns).astype(np.uint16)
    
    # Extract current channels directly (shape is H, W, 4)
    # Channels are A, R, G, B
    curr_r = pixels[py_coords, px, 1]
    curr_g = pixels[py_coords, px, 2]
    curr_b = pixels[py_coords, px, 3]
    
    # Add and clip
    new_r = np.clip(curr_r.astype(np.float32) + r_add * 0.1, 0, 255).astype(np.uint8)
    new_g = np.clip(curr_g.astype(np.float32) + g_add * 0.1, 0, 255).astype(np.uint8)
    new_b = np.clip(curr_b.astype(np.float32) + b_add * 0.1, 0, 255).astype(np.uint8)
    
    pixels[py_coords, px, 0] = 255
    pixels[py_coords, px, 1] = new_r
    pixels[py_coords, px, 2] = new_g
    pixels[py_coords, px, 3] = new_b
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
