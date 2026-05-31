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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Branch:
    def __init__(self, x, y, angle, length, depth):
        self.x = x
        self.y = y
        self.angle = angle
        self.length = length
        self.depth = depth
        self.end_x = x + np.cos(angle) * length
        self.end_y = y + np.sin(angle) * length
        self.children = []
        self.growing = True
        self.current_length = 0.0

branches = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Initialize seed branches
    for i in range(6):
        angle = i * (py5.TWO_PI / 6)
        branches.append(Branch(0, 0, angle, py5.random(30, 80), 0))

def draw():
    py5.background(0)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_z(py5.frame_count * 0.005)
    
    active_branches = [b for b in branches if b.growing]
    
    # Grow and branch
    for b in active_branches:
        if b.current_length < b.length:
            b.current_length += 2.0
            if b.current_length >= b.length:
                b.current_length = b.length
                b.growing = False
                
                # Spawn children
                if b.depth < 8:
                    num_children = py5.random_int(1, 3)
                    for _ in range(num_children):
                        # Hexagonal branching angles (60 degrees)
                        angle_offset = py5.random_choice([-py5.PI/3, py5.PI/3, 0])
                        new_angle = b.angle + angle_offset + py5.random(-0.1, 0.1)
                        new_length = b.length * py5.random(0.6, 0.9)
                        branches.append(Branch(b.end_x, b.end_y, new_angle, new_length, b.depth + 1))
    
    # Draw branches
    py5.stroke_weight(2)
    for b in branches:
        depth_factor = b.depth / 8.0
        py5.stroke(200 + depth_factor * 20, 80 - depth_factor * 40, 60 + depth_factor * 40, 80)
        
        curr_x = b.x + np.cos(b.angle) * b.current_length
        curr_y = b.y + np.sin(b.angle) * b.current_length
        
        # Adding slight 3D perturbation to z based on noise
        z1 = py5.os_noise(b.x * 0.01, b.y * 0.01, 0) * 100 - 50
        z2 = py5.os_noise(curr_x * 0.01, curr_y * 0.01, 0) * 100 - 50
        
        py5.line(b.x, b.y, z1, curr_x, curr_y, z2)
        
        # Draw bright tips
        if b.growing:
            py5.stroke_weight(5)
            py5.stroke(210, 20, 100, 100)
            py5.point(curr_x, curr_y, z2)
            py5.stroke_weight(2)

    py5.pop_matrix()

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
