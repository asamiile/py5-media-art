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

grid_w, grid_h = SIZE

N_FLOCKS = 120
N_PER_FLOCK = 250
N_AGENTS = N_FLOCKS * N_PER_FLOCK

f_pos = np.zeros((N_FLOCKS, 2), dtype=np.float32)
f_vel = np.zeros((N_FLOCKS, 2), dtype=np.float32)
a_pos = np.zeros((N_AGENTS, 2), dtype=np.float32)
a_vel = np.zeros((N_AGENTS, 2), dtype=np.float32)
a_flock_idx = np.repeat(np.arange(N_FLOCKS), N_PER_FLOCK)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Init flocks
    f_pos[:, 0] = np.random.uniform(grid_w*0.3, grid_w*0.7, N_FLOCKS)
    f_pos[:, 1] = np.random.uniform(grid_h*0.3, grid_h*0.7, N_FLOCKS)
    f_vel[:] = np.random.randn(N_FLOCKS, 2) * 2.0
    
    # Init agents
    a_pos[:] = f_pos[a_flock_idx] + np.random.randn(N_AGENTS, 2) * 100
    a_vel[:] = f_vel[a_flock_idx] + np.random.randn(N_AGENTS, 2)
    
    py5.background(10, 15, 35) # Deep Indigo

def draw():
    global f_pos, f_vel, a_pos, a_vel
    
    # Fading background for trails
    py5.fill(10, 15, 35, 30)
    py5.no_stroke()
    py5.rect(0, 0, grid_w, grid_h)
    
    # Update Flocks (Leaders)
    diff = f_pos[:, np.newaxis, :] - f_pos[np.newaxis, :, :]
    dist = np.linalg.norm(diff, axis=2) + 1e-5
    
    # Repulsion
    rep_mask = dist < 250
    rep = np.sum((diff / dist[:, :, np.newaxis]) * rep_mask[:, :, np.newaxis] * (1.0/dist[:, :, np.newaxis]), axis=1)
    
    # Alignment
    align_mask = dist < 500
    align = np.sum(f_vel[np.newaxis, :, :] * align_mask[:, :, np.newaxis], axis=1)
    # Normalize alignment
    align_norm = np.linalg.norm(align, axis=1, keepdims=True) + 1e-5
    align = align / align_norm
    
    # Cohesion
    coh_mask = dist < 800
    # count neighbors
    coh_count = np.sum(coh_mask, axis=1, keepdims=True)
    # center of mass of neighbors
    com = np.sum(f_pos[np.newaxis, :, :] * coh_mask[:, :, np.newaxis], axis=1) / (coh_count + 1e-5)
    coh = com - f_pos
    coh_norm = np.linalg.norm(coh, axis=1, keepdims=True) + 1e-5
    coh = coh / coh_norm
    
    # Global center attraction
    t = py5.frame_count * 0.02
    target = np.array([grid_w/2 + np.cos(t*1.3)*400, grid_h/2 + np.sin(t*0.9)*300])
    center_dir = target - f_pos
    c_norm = np.linalg.norm(center_dir, axis=1, keepdims=True) + 1e-5
    center_dir = center_dir / c_norm
    
    # Wander
    wander = np.random.randn(N_FLOCKS, 2)
    
    # Apply forces to flocks
    f_acc = rep * 4.0 + align * 1.5 + coh * 1.0 + center_dir * 0.8 + wander * 0.5
    f_vel += f_acc
    
    # Speed limit for flocks
    speed = np.linalg.norm(f_vel, axis=1, keepdims=True) + 1e-5
    f_vel = (f_vel / speed) * np.clip(speed, 2.0, 10.0)
    
    f_pos += f_vel
    
    # Update Agents
    # Attraction to flock center
    to_center = f_pos[a_flock_idx] - a_pos
    dist_to_center = np.linalg.norm(to_center, axis=1, keepdims=True) + 1e-5
    to_center_dir = to_center / dist_to_center
    
    # Agents align with flock velocity, attract to flock center, and have some noise
    a_acc = to_center_dir * (dist_to_center * 0.01) + f_vel[a_flock_idx] * 0.5 + np.random.randn(N_AGENTS, 2) * 1.5
    
    a_vel += a_acc
    
    # Speed limit for agents
    a_speed = np.linalg.norm(a_vel, axis=1, keepdims=True) + 1e-5
    a_vel = (a_vel / a_speed) * np.clip(a_speed, 4.0, 14.0)
    
    a_pos += a_vel
    
    # Render
    py5.blend_mode(py5.ADD)
    
    py5.stroke(255, 180, 100, 120)
    py5.stroke_weight(2)
    py5.points(a_pos)
    
    py5.blend_mode(py5.BLEND)
    
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
