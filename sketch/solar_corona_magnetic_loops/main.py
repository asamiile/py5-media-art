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

pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
life = np.zeros(NUM_PARTICLES, dtype=np.float32)

# Define magnetic dipoles (sunspots) on the surface (z=0)
poles = np.array([
    [-200, 0, 100],  # N
    [200, 0, -100],  # S
    [-150, -200, 150], # N
    [100, -300, -150], # S
    [250, 200, 50],   # N
    [-50, 300, -50],  # S
], dtype=np.float32)

charges = np.array([1, -1, 1, -1, 1, -1], dtype=np.float32)

def reset_particles(mask):
    count = np.sum(mask)
    if count == 0: return
    
    # Spawn on the surface mostly around the N poles
    # We select N poles randomly for each particle
    n_poles = poles[charges > 0]
    pole_idx = np.random.randint(0, len(n_poles), count)
    
    base_pos = n_poles[pole_idx]
    
    # Add random offset
    offset = np.random.randn(count, 3) * 30.0
    offset[:, 2] = np.abs(offset[:, 2]) # always above surface
    
    pos[mask] = base_pos + offset
    vel[mask] = 0.0
    life[mask] = np.random.uniform(0.0, 1.0, count)

def get_field(p, t):
    B = np.zeros_like(p)
    
    # Sum over all poles: B = sum( q * r / |r|^3 )
    for i in range(len(poles)):
        r = p - poles[i]
        r_mag = np.linalg.norm(r, axis=1, keepdims=True) + 1.0 # avoid div by zero
        B += charges[i] * r / (r_mag**3)
        
    # Add time-varying noise (turbulence)
    # Simple sine wave based on position
    scale = 0.01
    noise_x = np.sin(p[:, 1] * scale + t * 5.0) * np.cos(p[:, 2] * scale)
    noise_y = np.cos(p[:, 0] * scale - t * 3.0) * np.sin(p[:, 2] * scale)
    noise_z = np.sin(p[:, 0] * scale + t * 4.0) * np.cos(p[:, 1] * scale)
    
    noise = np.stack([noise_x, noise_y, noise_z], axis=-1)
    
    B += noise * 0.0001
    
    return B

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    reset_particles(np.ones(NUM_PARTICLES, dtype=bool))

def draw():
    global pos, vel, life
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Physics step
    B = get_field(pos, t)
    
    # Normalize B field for constant speed along field lines
    B_mag = np.linalg.norm(B, axis=1, keepdims=True) + 1e-6
    B_dir = B / B_mag
    
    speed = 10.0
    vel = vel * 0.5 + B_dir * speed * 0.5
    
    pos += vel
    life -= 0.005
    
    # Reset particles that are dead or hit the surface (z < 0)
    dead = (life < 0) | (pos[:, 2] < -10)
    reset_particles(dead)
    
    # Rotate camera
    rot_y = t * np.pi * 2.0
    rot_x = np.pi / 4 + np.sin(t * np.pi * 2.0) * 0.1
    
    cos_y, sin_y = np.cos(rot_y), np.sin(rot_y)
    cos_x, sin_x = np.cos(rot_x), np.sin(rot_x)
    
    # Y-axis rotation
    x1 = pos[:, 0] * cos_y - pos[:, 1] * sin_y
    y1 = pos[:, 0] * sin_y + pos[:, 1] * cos_y
    z1 = pos[:, 2]
    
    # X-axis rotation (tilt down)
    y2 = y1 * cos_x - z1 * sin_x
    z2 = y1 * sin_x + z1 * cos_x
    
    # Simple perspective projection
    scale = 800.0 / (800.0 + y2)
    
    px = x1 * scale + SIZE[0] / 2
    py = -z2 * scale + SIZE[1] / 2 + 100
    
    valid = (px >= 0) & (px < SIZE[0]) & (py >= 0) & (py < SIZE[1]) & (y2 > -700)
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    p_x = px[valid].astype(int)
    p_y = py[valid].astype(int)
    p_life = life[valid]
    
    # Crimson to Hot Orange to Gold
    # life=1: Gold (255, 200, 50)
    # life=0.5: Orange (255, 80, 0)
    # life=0: Crimson (100, 0, 0)
    
    c_r = (p_life * 155 + 100).astype(np.uint16)
    c_g = np.clip(p_life * 200 - 50, 0, 255).astype(np.uint16)
    c_b = np.clip(p_life * 100 - 50, 0, 255).astype(np.uint16)
    
    curr_r = pixels[p_y, p_x, 1]
    curr_g = pixels[p_y, p_x, 2]
    curr_b = pixels[p_y, p_x, 3]
    
    new_r = np.clip(curr_r.astype(np.float32) + c_r * 0.1, 0, 255).astype(np.uint8)
    new_g = np.clip(curr_g.astype(np.float32) + c_g * 0.1, 0, 255).astype(np.uint8)
    new_b = np.clip(curr_b.astype(np.float32) + c_b * 0.1, 0, 255).astype(np.uint8)
    
    pixels[p_y, p_x, 0] = 255
    pixels[p_y, p_x, 1] = new_r
    pixels[p_y, p_x, 2] = new_g
    pixels[p_y, p_x, 3] = new_b
    
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
            
        import os
        os._exit(0)

py5.run_sketch()
