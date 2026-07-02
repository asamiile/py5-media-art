from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Node:
    def __init__(self, x, y, z):
        self.base_x = x
        self.base_y = y
        self.base_z = z

num_nodes = 300
nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(num_nodes):
        nodes.append(Node(
            py5.random(-600, 600),
            py5.random(-600, 600),
            py5.random(-600, 600)
        ))

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.05
    py5.rotate_y(t * 0.2)
    py5.rotate_z(t * 0.1)
    
    # Calculate current positions based on noise
    current_positions = []
    for node in nodes:
        nx = py5.os_noise(node.base_x * 0.01, t * 0.2) * 400 - 200
        ny = py5.os_noise(node.base_y * 0.01 + 100, t * 0.2) * 400 - 200
        nz = py5.os_noise(node.base_z * 0.01 + 200, t * 0.2) * 400 - 200
        current_positions.append((node.base_x + nx, node.base_y + ny, node.base_z + nz))
        
    py5.stroke_weight(2)
    
    # Connect nearby nodes
    max_dist = 250
    for i in range(len(current_positions)):
        p1 = current_positions[i]
        
        # Draw the node itself
        py5.stroke(200, 80, 100, 80)
        py5.point(*p1)
        
        for j in range(i + 1, len(current_positions)):
            p2 = current_positions[j]
            d = py5.dist(*p1, *p2)
            
            if d < max_dist:
                # Color and alpha based on distance
                alpha = py5.remap(d, 0, max_dist, 100, 0)
                hue = (200 + d * 0.5 + t * 10) % 360
                
                py5.stroke(hue, 90, 100, alpha)
                py5.line(*p1, *p2)


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
