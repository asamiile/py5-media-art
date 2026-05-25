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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 2500
NUM_COLORS = 4

pos = None
vel = None
species = None

colors = [
    (255, 60, 100),   # Neon Pink / Red
    (60, 255, 120),   # Neon Green
    (60, 150, 255),   # Neon Blue
    (255, 220, 60)    # Neon Yellow
]

def setup():
    global pos, vel, species
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    pos = np.random.rand(NUM_PARTICLES, 2)
    pos[:, 0] *= SIZE[0]
    pos[:, 1] *= SIZE[1]
    vel = np.zeros((NUM_PARTICLES, 2))
    species = np.random.randint(0, NUM_COLORS, NUM_PARTICLES)

def draw():
    global pos, vel, species
    
    # Motion blur / trails
    py5.fill(10, 15, 20, 80)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Evolving interaction matrix
    G = np.zeros((NUM_COLORS, NUM_COLORS))
    for i in range(NUM_COLORS):
        for j in range(NUM_COLORS):
            noise_val = py5.os_noise(i * 10.0, j * 10.0, t * 2.0)
            G[i, j] = (noise_val - 0.5) * 2.5 # Range [-1.25, 1.25]
    
    dx = pos[:, 0, np.newaxis] - pos[:, 0] # (N, N)
    dy = pos[:, 1, np.newaxis] - pos[:, 1] # (N, N)
    
    # Wrap around boundaries
    dx = dx - np.round(dx / py5.width) * py5.width
    dy = dy - np.round(dy / py5.height) * py5.height
    
    dist_sq = dx**2 + dy**2
    dist = np.sqrt(dist_sq)
    dist[dist == 0] = 1.0
    
    R_MAX = 80.0
    R_MIN = 15.0
    
    mask = dist < R_MAX
    np.fill_diagonal(mask, False)
    
    repel = (dist / R_MIN - 1.0)
    repel_mask = mask & (dist < R_MIN)
    
    G_map = G[species[:, np.newaxis], species] # (N, N) mapping
    attr = G_map * (1.0 - np.abs(dist - (R_MAX + R_MIN)/2.0) / ((R_MAX - R_MIN)/2.0))
    attr_mask = mask & (dist >= R_MIN)
    
    F = np.zeros_like(dist)
    F[repel_mask] = repel[repel_mask] * 2.0
    F[attr_mask] = attr[attr_mask]
    
    Fx = (dx / dist) * F
    Fy = (dy / dist) * F
    
    forces_x = np.sum(Fx, axis=1)
    forces_y = np.sum(Fy, axis=1)
    
    vel[:, 0] += forces_x * 0.1
    vel[:, 1] += forces_y * 0.1
    
    vel *= 0.7 # Friction
    
    pos += vel
    
    pos[:, 0] %= py5.width
    pos[:, 1] %= py5.height
    
    py5.blend_mode(py5.ADD)
    for i in range(NUM_COLORS):
        mask_i = (species == i)
        py5.fill(colors[i][0], colors[i][1], colors[i][2], 220)
        pts = pos[mask_i]
        for p in pts:
            py5.circle(p[0], p[1], 4)
            
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
