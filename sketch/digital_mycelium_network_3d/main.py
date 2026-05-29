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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Mycelium network data
num_nodes = 800
nodes = np.zeros((num_nodes, 3))
connections = []
active_nodes = [0]
nodes[0] = [0, 0, 0]

# Generate points via 3D random walk / differential growth
for i in range(1, num_nodes):
    parent = np.random.choice(active_nodes)
    direction = np.random.randn(3)
    direction /= np.linalg.norm(direction)
    nodes[i] = nodes[parent] + direction * np.random.uniform(10, 50)
    connections.append((parent, i))
    active_nodes.append(i)
    if len(active_nodes) > 100:
        active_nodes.pop(0)

# Sort connections by distance from center for growth effect
distances = np.linalg.norm(nodes[1:], axis=1)
order = np.argsort(distances)
sorted_connections = [connections[i] for i in order]


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.sphere_detail(5)


def draw():
    py5.background(10, 80, 10)  # Very dark green/black void
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Rotate slowly over time
    angle = py5.TWO_PI * (py5.frame_count / TOTAL_FRAMES)
    py5.rotate_y(angle * 0.5)
    py5.rotate_x(angle * 0.25)
    
    # Breathing scale
    scale = 1.5 + 0.2 * np.sin(angle * 2)
    py5.scale(scale)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Calculate how many connections to draw based on time
    growth_ratio = min(1.0, py5.frame_count / (TOTAL_FRAMES * 0.8))
    visible_connections = int(growth_ratio * len(sorted_connections))
    
    py5.blend_mode(py5.ADD)
    
    # Draw connections (mycelium threads)
    for i in range(visible_connections):
        u, v = sorted_connections[i]
        p1 = nodes[u]
        p2 = nodes[v]
        
        # Color based on index and time
        hue = (120 + i * 0.1 + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 80, 80, 50)
        
        py5.begin_shape(py5.LINES)
        py5.vertex(*p1)
        py5.vertex(*p2)
        py5.end_shape()

    # Fail-safe
    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

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
