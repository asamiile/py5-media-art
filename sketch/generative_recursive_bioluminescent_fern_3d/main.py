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

def branch(length, depth, noise_z):
    # Base case
    if depth == 0:
        # Draw glowing tip
        py5.no_stroke()
        py5.fill(100, 255, 255, 150) # Cyan glow
        py5.push_matrix()
        py5.translate(0, -length, 0)
        # Pulse size based on noise
        pulse = 1.0 + 0.5 * py5.os_noise(depth * 0.1, length * 0.1, noise_z * 2.0)
        py5.sphere(8 * pulse)
        py5.pop_matrix()
        return

    # Draw current branch
    py5.stroke(10, 100 + depth * 20, 50, 200) # Greenish
    py5.stroke_weight(depth * 1.5)
    py5.line(0, 0, 0, 0, -length, 0)
    
    # Move to the end of the branch
    py5.translate(0, -length, 0)
    
    # Branching logic (2 or 3 branches)
    num_branches = 3 if depth % 2 == 0 else 2
    
    for i in range(num_branches):
        py5.push_matrix()
        
        # Calculate dynamic swaying angles using noise
        # Use world coordinates roughly to offset noise
        noise_x = depth * 0.5 + i * 1.2
        noise_y = length * 0.1
        
        angle_x = py5.os_noise(noise_x, noise_y, noise_z) * np.pi / 3.0
        angle_z = py5.os_noise(noise_x + 10, noise_y + 10, noise_z) * np.pi / 3.0
        
        # Base spread
        spread = np.pi / 4.0 * (i - (num_branches - 1) / 2.0)
        
        py5.rotate_x(angle_x)
        py5.rotate_z(spread + angle_z * 0.5)
        
        # Recursive call
        branch(length * 0.75, depth - 1, noise_z)
        
        py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.sphere_detail(5) # Low detail for performance
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(5, 10, 20) # Deep ocean dark
    
    # Lighting for the glowing tips
    py5.ambient_light(20, 40, 50)
    py5.point_light(150, 255, 255, py5.width/2, py5.height/2, 200)
    
    py5.translate(py5.width / 2, py5.height - 200, -500)
    
    # Slowly rotate the whole plant
    py5.rotate_y(py5.frame_count * 0.005)
    
    # Additive blending makes the glowing tips pop
    py5.blend_mode(py5.ADD)
    
    noise_z = py5.frame_count * 0.015 # Time dimension for noise
    
    # Start recursive branching
    # High depth (e.g., 7 or 8) is very slow, so we keep it to 6 or 7
    # 3^(depth/2) * 2^(depth/2) roughly
    py5.push_matrix()
    branch(400, 7, noise_z)
    py5.pop_matrix()

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
