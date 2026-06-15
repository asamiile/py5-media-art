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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw_branch(length, depth, max_depth, time):
    if depth > max_depth:
        return
        
    # Draw line
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 15, 1))
    
    hue = (depth * 25 + time * 30) % 360
    py5.stroke(hue, 80, 100, 80)
    
    py5.line(0, 0, 0, 0, -length, 0)
    
    # Move to end of branch
    py5.translate(0, -length, 0)
    
    # Branching angles driven by noise
    n_angle1 = py5.os_noise(depth * 0.1, time * 0.5) * py5.PI / 2
    n_angle2 = py5.os_noise(depth * 0.1 + 100, time * 0.5) * py5.PI / 2
    n_angle3 = py5.os_noise(depth * 0.1 + 200, time * 0.5) * py5.PI / 2
    
    shrink = 0.7
    
    # Branch 1
    py5.push_matrix()
    py5.rotate_y(time + n_angle1)
    py5.rotate_z(n_angle2)
    draw_branch(length * shrink, depth + 1, max_depth, time)
    py5.pop_matrix()
    
    # Branch 2
    py5.push_matrix()
    py5.rotate_y(-time + n_angle2)
    py5.rotate_z(-n_angle3)
    draw_branch(length * shrink, depth + 1, max_depth, time)
    py5.pop_matrix()
    
    # Branch 3 (adds 3D density)
    py5.push_matrix()
    py5.rotate_x(n_angle3)
    py5.rotate_z(n_angle1)
    draw_branch(length * shrink * 0.8, depth + 1, max_depth, time)
    py5.pop_matrix()

def draw():
    py5.background(10, 20, 10) # Very dark forest green
    
    time = py5.frame_count * 0.01
    
    # Camera orbits
    cam_radius = 1500
    cam_x = py5.sin(time * 0.3) * cam_radius
    cam_z = py5.cos(time * 0.3) * cam_radius
    cam_y = py5.sin(time * 0.5) * 500 - 500
    
    py5.camera(cam_x, cam_y, cam_z, 
               0, -500, 0, 
               0, 1, 0)
               
    py5.blend_mode(py5.ADD)
    
    # Center tree
    py5.translate(0, 500, 0)
    
    draw_branch(400, 0, 7, time)
    
    py5.blend_mode(py5.BLEND)

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
