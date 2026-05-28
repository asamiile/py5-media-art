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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 40000
positions = None
velocities = None
colors = None
ATTRACTORS = None

def setup():
    global positions, velocities, colors, ATTRACTORS
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 10, 26)  # Deep space navy
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.random.rand(NUM_PARTICLES, 2) * np.array(SIZE)
    velocities = np.zeros((NUM_PARTICLES, 2))
    
    hues = np.random.choice([0, 200, 300], NUM_PARTICLES, p=[0.1, 0.6, 0.3]) 
    colors = np.zeros((NUM_PARTICLES, 3))
    colors[:, 0] = hues
    
    attractors = []
    spacing = 600
    for y in range(-300, SIZE[1] + 300, int(spacing * np.sqrt(3) / 2)):
        for x in range(-300, SIZE[0] + 300, spacing):
            offset = spacing / 2 if (y // int(spacing * np.sqrt(3) / 2)) % 2 == 1 else 0
            sign = 1 if (int(x+y) % 2) == 0 else -1
            attractors.append([x + offset, y, sign])
    ATTRACTORS = np.array(attractors)

def draw():
    global positions, velocities
    
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 10, 26, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.01
    
    force = np.zeros_like(velocities)
    
    for ax, ay, asign in ATTRACTORS:
        dx = ax - positions[:, 0]
        dy = ay - positions[:, 1]
        dist_sq = dx**2 + dy**2
        dist_sq = np.maximum(dist_sq, 2000)
        
        tangent_x = -dy
        tangent_y = dx
        
        # Vary attractor strength with time
        magnitude = (600000.0 + np.sin(time + ax) * 200000) / dist_sq
        force[:, 0] += tangent_x * magnitude * asign
        force[:, 1] += tangent_y * magnitude * asign
        
        force[:, 0] += dx * magnitude * 0.05
        force[:, 1] += dy * magnitude * 0.05

    # Add some noise
    force[:, 0] += np.sin(positions[:, 1] * 0.01 + time) * 0.5
    force[:, 1] += np.cos(positions[:, 0] * 0.01 + time) * 0.5

    velocities = velocities * 0.95 + force * 0.08
    
    speeds = np.linalg.norm(velocities, axis=1)
    np.clip(speeds, 0, 12, out=speeds)
    norms = np.linalg.norm(velocities, axis=1, keepdims=True)
    norms[norms == 0] = 1
    velocities = (velocities / norms) * speeds.reshape(-1, 1)

    new_positions = positions + velocities
    
    py5.stroke_weight(2)
    
    for h_val, (r, g, b) in [(200, (0, 255, 255)), (300, (138, 43, 226)), (0, (255, 20, 147))]:
        mask = (colors[:, 0] == h_val)
        if not np.any(mask):
            continue
        py5.stroke(r, g, b, 60)
        lines = np.empty((np.sum(mask), 4))
        lines[:, 0:2] = positions[mask]
        lines[:, 2:4] = new_positions[mask]
        py5.lines(lines)
    
    new_positions[:, 0] = new_positions[:, 0] % py5.width
    new_positions[:, 1] = new_positions[:, 1] % py5.height
    
    positions = new_positions
    
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
