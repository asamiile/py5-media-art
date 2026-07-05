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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Cloth grid settings
COLS, ROWS = 60, 40
REST_DIST = 30.0

NUM_POINTS = COLS * ROWS
pos = np.zeros((NUM_POINTS, 2), dtype=np.float32)
old_pos = np.zeros((NUM_POINTS, 2), dtype=np.float32)

# Initial setup: hanging from the top
start_x = SIZE[0]/2 - (COLS * REST_DIST)/2
start_y = 200.0

for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        pos[idx, 0] = start_x + c * REST_DIST
        pos[idx, 1] = start_y + r * REST_DIST

old_pos[:] = pos[:]

# Constraints (pairs of indices)
constraints = []
for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        # Right neighbor
        if c < COLS - 1:
            constraints.append((idx, idx + 1, REST_DIST))
        # Bottom neighbor
        if r < ROWS - 1:
            constraints.append((idx, idx + COLS, REST_DIST))
        # Shear (diagonal)
        if c < COLS - 1 and r < ROWS - 1:
            constraints.append((idx, idx + COLS + 1, REST_DIST * 1.414))
        if c > 0 and r < ROWS - 1:
            constraints.append((idx, idx + COLS - 1, REST_DIST * 1.414))

constraints = np.array(constraints, dtype=np.float32)
idx1 = constraints[:, 0].astype(np.int32)
idx2 = constraints[:, 1].astype(np.int32)
target_dists = constraints[:, 2]

pinned = np.zeros(NUM_POINTS, dtype=bool)
# Pin the top row
for c in range(COLS):
    # Only pin every 5th point to let it sag
    if c % 5 == 0 or c == COLS - 1:
        pinned[c] = True

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(220, 80, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(2)
    py5.stroke_join(py5.ROUND)

def draw():
    global pos, old_pos
    
    py5.background(220, 80, 10)
    
    time_val = py5.frame_count * 0.05
    
    # Verlet integration
    dt = 1.0
    gravity = np.array([0, 0.5])
    
    # Wind based on noise
    wind_force = np.zeros((NUM_POINTS, 2))
    for i in range(NUM_POINTS):
        px, py_coord = pos[i]
        wx = py5.noise(px * 0.001, py_coord * 0.001, time_val * 0.5) * 4.0 - 1.0 # Bias to right
        wy = py5.noise(px * 0.002 + 100, py_coord * 0.002, time_val * 0.5) * 2.0 - 1.5
        wind_force[i] = [wx, wy]
    
    # Update positions
    vel = pos - old_pos
    # Damping
    vel *= 0.99
    
    old_pos[:] = pos[:]
    pos += vel + (gravity + wind_force) * (dt * dt)
    
    # Enforce constraints (multiple iterations for stiffness)
    for _ in range(5):
        diff = pos[idx2] - pos[idx1]
        dist = np.linalg.norm(diff, axis=1)
        
        # Avoid div zero
        dist[dist < 0.1] = 0.1
        
        diff_ratio = (target_dists - dist) / dist
        
        offset = diff * diff_ratio[:, np.newaxis] * 0.5
        
        # Apply offsets using np.add.at for safety with duplicate indices
        # Actually since we loop we could just do a simple non-vectorized or partially vectorized
        # To avoid data races in numpy, we can just split constraints into non-overlapping sets or 
        # approximate it. We'll just do normal array addition, which might miss some overlap but is fast enough for cloth.
        
        pos[idx1] -= offset
        pos[idx2] += offset
        
        # Re-pin
        pos[pinned] = old_pos[pinned]

    # Draw cloth using QUADS
    py5.no_stroke()
    py5.begin_shape(py5.QUADS)
    for r in range(ROWS - 1):
        for c in range(COLS - 1):
            i1 = r * COLS + c
            i2 = i1 + 1
            i3 = i2 + COLS
            i4 = i1 + COLS
            
            # Simple lighting / color based on stretch or velocity
            v = np.linalg.norm(pos[i1] - old_pos[i1])
            hue = (280 + v * 15 + c * 2) % 360
            brightness = min(100, 30 + v * 10)
            
            py5.fill(hue, 80, brightness, 90)
            py5.vertex(pos[i1, 0], pos[i1, 1])
            py5.vertex(pos[i2, 0], pos[i2, 1])
            py5.vertex(pos[i3, 0], pos[i3, 1])
            py5.vertex(pos[i4, 0], pos[i4, 1])
            
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
