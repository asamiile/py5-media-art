from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid Size
# Must be small enough to compute at 60fps, then we scale up for drawing
CELL_SIZE = 10
COLS = SIZE[0] // CELL_SIZE
ROWS = SIZE[1] // CELL_SIZE

NUM_BLOBS = 12
blobs = np.zeros((NUM_BLOBS, 4), dtype=np.float32) # x, y, vx, vy

# Pre-calculate a meshgrid
X_GRID, Y_GRID = np.meshgrid(np.arange(COLS + 1) * CELL_SIZE, np.arange(ROWS + 1) * CELL_SIZE)

# Marching squares lookup table for line segments
# Array of edges to draw. Each edge is a tuple of (start_point_index, end_point_index)
# Points: 0=top, 1=right, 2=bottom, 3=left
state_lines = {
    0: [],
    1: [(2, 3)],
    2: [(1, 2)],
    3: [(1, 3)],
    4: [(0, 1)],
    5: [(0, 1), (2, 3)], # ambiguous
    6: [(0, 2)],
    7: [(0, 3)],
    8: [(0, 3)],
    9: [(0, 2)],
    10: [(0, 3), (1, 2)], # ambiguous
    11: [(0, 1)],
    12: [(1, 3)],
    13: [(1, 2)],
    14: [(2, 3)],
    15: []
}

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize blobs
    for i in range(NUM_BLOBS):
        blobs[i, 0] = random.uniform(0, py5.width)
        blobs[i, 1] = random.uniform(0, py5.height)
        blobs[i, 2] = random.uniform(-10, 10)
        blobs[i, 3] = random.uniform(-10, 10)

def get_state(a, b, c, d):
    state = 0
    if a > 1.0: state |= 8
    if b > 1.0: state |= 4
    if c > 1.0: state |= 2
    if d > 1.0: state |= 1
    return state

def get_interp_point(val1, val2, p1, p2):
    # Linear interpolation for smoother edges
    if val1 == val2:
        return p1
    mu = (1.0 - val1) / (val2 - val1)
    return p1 + mu * (p2 - p1)

def draw():
    global blobs
    
    py5.background(270, 90, 15) # Deep violet
    py5.blend_mode(py5.ADD)
    
    # Update blobs
    for i in range(NUM_BLOBS):
        blobs[i, 0] += blobs[i, 2]
        blobs[i, 1] += blobs[i, 3]
        
        # Bounce
        if blobs[i, 0] < 0 or blobs[i, 0] > py5.width: blobs[i, 2] *= -1
        if blobs[i, 1] < 0 or blobs[i, 1] > py5.height: blobs[i, 3] *= -1
    
    # Calculate scalar field (Metaball energy function)
    # Energy = sum(r^2 / ((x-cx)^2 + (y-cy)^2))
    # We'll use a fast vectorized approach
    
    field = np.zeros_like(X_GRID, dtype=np.float32)
    radius_sq = (py5.height * 0.15) ** 2
    
    for i in range(NUM_BLOBS):
        dx = X_GRID - blobs[i, 0]
        dy = Y_GRID - blobs[i, 1]
        dist_sq = dx**2 + dy**2
        
        # Avoid div by zero
        dist_sq[dist_sq < 0.001] = 0.001
        
        field += radius_sq / dist_sq
        
    # Draw Marching Squares
    py5.stroke_weight(3)
    
    # We want glowing neon lines, so we draw it multiple times with varying opacity and weight
    for pass_idx in range(3):
        if pass_idx == 0:
            py5.stroke(320, 100, 100, 20)
            py5.stroke_weight(12)
        elif pass_idx == 1:
            py5.stroke(320, 80, 100, 50)
            py5.stroke_weight(6)
        else:
            py5.stroke(180, 50, 100, 100) # cyan core
            py5.stroke_weight(2)
            
        py5.begin_shape(py5.LINES)
        
        for i in range(COLS):
            for j in range(ROWS):
                x = i * CELL_SIZE
                y = j * CELL_SIZE
                
                a_val = field[j, i]
                b_val = field[j, i + 1]
                c_val = field[j + 1, i + 1]
                d_val = field[j + 1, i]
                
                state = get_state(a_val, b_val, c_val, d_val)
                lines = state_lines[state]
                
                if not lines: continue
                
                # Corner points
                a_pt = np.array([x, y])
                b_pt = np.array([x + CELL_SIZE, y])
                c_pt = np.array([x + CELL_SIZE, y + CELL_SIZE])
                d_pt = np.array([x, y + CELL_SIZE])
                
                # Edge points (interpolated)
                pts = [
                    get_interp_point(a_val, b_val, a_pt, b_pt), # 0 (top)
                    get_interp_point(b_val, c_val, b_pt, c_pt), # 1 (right)
                    get_interp_point(d_val, c_val, d_pt, c_pt), # 2 (bottom)
                    get_interp_point(a_val, d_val, a_pt, d_pt)  # 3 (left)
                ]
                
                for p1_idx, p2_idx in lines:
                    py5.vertex(pts[p1_idx][0], pts[p1_idx][1])
                    py5.vertex(pts[p2_idx][0], pts[p2_idx][1])
                    
        py5.end_shape()

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
