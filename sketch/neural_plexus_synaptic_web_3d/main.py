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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Generate static random seeds for 300 nodes
num_nodes = 300
np.random.seed(42)
node_seeds = np.random.uniform(0, 1000, size=(num_nodes, 3))
pos = np.zeros((num_nodes, 3))

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(220, 80, 8) # Deep navy/teal background
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, -400)
    
    t_phase = (py5.frame_count / TOTAL_FRAMES) * py5.TWO_PI
    
    # Slowly rotate the entire network
    py5.rotate_x(t_phase * 0.5)
    py5.rotate_y(t_phase * 1.0)
    
    py5.blend_mode(py5.ADD)
    
    # Circular noise traversal ensures the node paths loop perfectly
    cx = np.cos(t_phase) * 1.2
    cy = np.sin(t_phase) * 1.2
    
    # Compute node positions
    for i in range(num_nodes):
        pos[i, 0] = py5.os_noise(node_seeds[i, 0], cx, cy) * 900
        pos[i, 1] = py5.os_noise(node_seeds[i, 1], cx, cy) * 900
        pos[i, 2] = py5.os_noise(node_seeds[i, 2], cx, cy) * 900
        
    # Draw Nodes
    py5.stroke(160, 90, 100, 90) # Electric cyan
    py5.stroke_weight(6)
    py5.begin_shape(py5.POINTS)
    for i in range(num_nodes):
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
    py5.end_shape()
    
    # Vectorized distance calculation
    # Pos shape is (N, 3). We want pairwise squared distances.
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :] # (N, N, 3)
    dist_sq = np.sum(diff**2, axis=-1) # (N, N)
    
    threshold = 280
    threshold_sq = threshold**2
    
    # Find all pairs of nodes within the distance threshold
    # Use np.triu to get upper triangle (avoid drawing lines twice, avoid self-lines)
    i_idx, j_idx = np.where(np.triu(dist_sq < threshold_sq, k=1))
    
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for idx in range(len(i_idx)):
        i = i_idx[idx]
        j = j_idx[idx]
        d_sq = dist_sq[i, j]
        
        # Opacity fades as nodes get further apart
        opacity = py5.remap(d_sq, 0, threshold_sq, 100, 0)
        
        # Hue shifts slightly from Green to Blue based on connection strength
        hue = 150 + (opacity * 0.4) 
        
        py5.stroke(hue, 90, 100, opacity)
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
        py5.vertex(pos[j, 0], pos[j, 1], pos[j, 2])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
