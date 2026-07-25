from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.spatial import cKDTree

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

# Differential Growth Parameters
REPULSION_RADIUS = 15.0
MAX_EDGE_LEN = 10.0
MIN_EDGE_LEN = 2.0
REPULSION_FORCE = 0.5
SPRING_FORCE = 0.1
MAX_NODES = 15000 # Keep it reasonable so KDTree doesn't lag too much

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos
    
    W, H = SIZE
    
    # Initialize a small circle of nodes
    num_initial = 100
    theta = np.linspace(0, py5.TWO_PI, num_initial, endpoint=False)
    r = 50.0
    
    x = W/2 + r * np.cos(theta)
    y = H/2 + r * np.sin(theta)
    
    pos = np.column_stack((x, y))

def draw():
    global pos
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # --- Differential Growth Simulation ---
    N = len(pos)
    
    # 1. Subdivision
    if N < MAX_NODES:
        # Calculate distances to next neighbors (wrap around for closed loop)
        next_pos = np.roll(pos, -1, axis=0)
        dists = np.linalg.norm(next_pos - pos, axis=1)
        
        # Find edges that are too long
        too_long = np.where(dists > MAX_EDGE_LEN)[0]
        
        if len(too_long) > 0:
            # We insert one node at a time to avoid complex array resizing math, 
            # or we can do it batched. Batched is much faster.
            # Create a list of new nodes to insert
            new_nodes = (pos[too_long] + next_pos[too_long]) / 2.0
            
            # We add slight noise to new nodes to break symmetry
            new_nodes += np.random.uniform(-1.0, 1.0, new_nodes.shape)
            
            # Insert them into the array
            # numpy insert is slow, so we build a new array
            insert_indices = too_long + 1
            # We use np.insert which can take multiple indices
            # But wait, np.insert with multiple indices inserts BEFORE the index.
            # E.g., insert at too_long+1 puts it between i and i+1
            pos = np.insert(pos, insert_indices, new_nodes, axis=0)
            N = len(pos)
    
    # We do a few physics steps per frame for speed
    for _ in range(3):
        # 2. Spring Force (attraction to immediate neighbors)
        next_pos = np.roll(pos, -1, axis=0)
        prev_pos = np.roll(pos, 1, axis=0)
        
        # Move towards midpoint of neighbors
        midpoints = (next_pos + prev_pos) / 2.0
        spring_vec = (midpoints - pos) * SPRING_FORCE
        
        # 3. Repulsion Force (push away from any nearby nodes)
        tree = cKDTree(pos)
        pairs = tree.query_pairs(REPULSION_RADIUS)
        
        repulse_vec = np.zeros_like(pos)
        
        if len(pairs) > 0:
            pairs = np.array(list(pairs))
            i = pairs[:, 0]
            j = pairs[:, 1]
            
            diff = pos[i] - pos[j]
            dist = np.linalg.norm(diff, axis=1, keepdims=True)
            
            # Avoid divide by zero
            dist[dist < 0.1] = 0.1
            
            # Repulsion strength (stronger when closer)
            force_mag = REPULSION_FORCE * (1.0 - dist / REPULSION_RADIUS)
            force = (diff / dist) * force_mag
            
            # Accumulate forces (using np.add.at)
            np.add.at(repulse_vec, i, force)
            np.add.at(repulse_vec, j, -force)
            
        # Update positions
        pos += spring_vec + repulse_vec
        
    # --- Rendering ---
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Dynamic hue based on frame count
    hue = (py5.frame_count * 0.5) % 360
    py5.stroke(hue, 90, 100, 200)
    
    py5.begin_shape()
    for i in range(N):
        py5.vertex(pos[i, 0], pos[i, 1])
    # Close the loop
    py5.vertex(pos[0, 0], pos[0, 1])
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
