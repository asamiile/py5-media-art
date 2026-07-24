from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Plasma Simulation Parameters
NUM_PARTICLES = 500000
STEPS_PER_FRAME = 3
DT = 0.05
Q_M = 1.0 # Charge to mass ratio magnitude

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, q, W, H
    W, H = SIZE
    
    pos = np.random.uniform(0, max(W, H), (NUM_PARTICLES, 2)).astype(np.float32)
    pos[:, 0] = pos[:, 0] % W
    pos[:, 1] = pos[:, 1] % H
    
    vel = np.random.uniform(-1.0, 1.0, (NUM_PARTICLES, 2)).astype(np.float32)
    
    # +1 for half (Cyan), -1 for half (Magenta)
    q = np.ones(NUM_PARTICLES, dtype=np.float32)
    q[NUM_PARTICLES//2:] = -1.0
    
    # Set background to black
    py5.background(0)

def step_physics(t):
    global pos, vel
    
    x = pos[:, 0]
    y = pos[:, 1]
    
    # 1. Evaluate E(x, y) and B(x, y) at particle positions
    # Electric Field: E = -Grad(V). Let V be a slow undulating landscape
    # V(x, y) = sin(x*0.01 + t) * cos(y*0.01 - t*0.5)
    Ex = -0.01 * np.cos(x*0.005 + t) * np.cos(y*0.005 - t*0.5) * 10.0
    Ey =  0.01 * np.sin(x*0.005 + t) * np.sin(y*0.005 - t*0.5) * 10.0
    
    # Add a strong radial electric field pulling to the center so they don't all fly away
    cx, cy = W/2, H/2
    dx = cx - x
    dy = cy - y
    dist = np.sqrt(dx*dx + dy*dy) + 1.0
    Ex += (dx / dist) * 0.02
    Ey += (dy / dist) * 0.02
    
    # Magnetic Field: B_z(x, y)
    # A strong, complex magnetic field creating "magnetic mirrors" and drift channels
    Bz = 15.0 + 10.0 * np.sin(x*0.008) * np.cos(y*0.012 + t*0.2) + 5.0 * np.cos(x*0.02)
    
    # 2. Boris Algorithm for V update (Standard Plasma Physics Integrator)
    # Half-E acceleration
    q_m = q * Q_M
    v_minus_x = vel[:, 0] + q_m * Ex * (DT / 2.0)
    v_minus_y = vel[:, 1] + q_m * Ey * (DT / 2.0)
    
    # Rotation step
    t_z = q_m * Bz * (DT / 2.0)
    s_z = 2.0 * t_z / (1.0 + t_z * t_z)
    
    v_prime_x = v_minus_x + v_minus_y * t_z
    v_prime_y = v_minus_y - v_minus_x * t_z
    
    v_plus_x = v_minus_x + v_prime_y * s_z
    v_plus_y = v_minus_y - v_prime_x * s_z
    
    # Half-E acceleration
    vel[:, 0] = v_plus_x + q_m * Ex * (DT / 2.0)
    vel[:, 1] = v_plus_y + q_m * Ey * (DT / 2.0)
    
    # Friction (radiative cooling)
    vel *= 0.99
    
    # Thermal noise (Brownian motion)
    vel += np.random.uniform(-0.1, 0.1, (NUM_PARTICLES, 2))
    
    # 3. Position update
    pos += vel * DT
    
    # Wrap around screen (Toroidal topology)
    pos[:, 0] = pos[:, 0] % W
    pos[:, 1] = pos[:, 1] % H

def draw():
    global pos, vel
    
    t = py5.frame_count * 0.02
    
    # Physics steps
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 220 // 256).astype(np.uint8)
    
    sx = pos[:, 0].astype(np.int32)
    sy = pos[:, 1].astype(np.int32)
    
    # Ensure perfectly in bounds
    valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx = sx[valid]
    sy = sy[valid]
    q_valid = q[valid]
    
    # Positive charges are Cyan (0, 255, 255), Negative are Magenta (255, 0, 255)
    # Brightness based on kinetic energy
    v_mag = np.sqrt(vel[valid, 0]**2 + vel[valid, 1]**2)
    intensity = np.clip(v_mag * 30.0 + 50.0, 0, 255).astype(np.uint8)
    
    vr = np.where(q_valid < 0, intensity, 0).astype(np.uint8) # Magenta R
    vg = np.where(q_valid > 0, intensity, 0).astype(np.uint8) # Cyan G
    vb = intensity # Both have B
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    flat_pixels[flat_indices, 1] = np.clip(flat_pixels[flat_indices, 1].astype(np.uint16) + vr, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 2] = np.clip(flat_pixels[flat_indices, 2].astype(np.uint16) + vg, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 3] = np.clip(flat_pixels[flat_indices, 3].astype(np.uint16) + vb, 0, 255).astype(np.uint8)
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

py5.run_sketch()
