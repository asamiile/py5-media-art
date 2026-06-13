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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_branch(length, depth, max_depth, t):
    if depth == max_depth:
        return
        
    hue1 = (py5.frame_count * 0.3 + depth * 40) % 360
    hue2 = (hue1 + 180) % 360 # Complementary
    
    py5.fill(hue1, 90, 80, 20)
    py5.stroke(hue2, 90, 100, 60)
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 6, 1))
    
    # Draw the branch as a crystalline shard (triangle strip cylinder approximation)
    py5.begin_shape(py5.TRIANGLE_STRIP)
    sides = 4
    for i in range(sides + 1):
        angle = (i / sides) * py5.TWO_PI
        r_bottom = py5.remap(depth, 0, max_depth, 40, 2)
        r_top = py5.remap(depth + 1, 0, max_depth, 40, 2)
        
        py5.vertex(py5.cos(angle) * r_bottom, 0, py5.sin(angle) * r_bottom)
        py5.vertex(py5.cos(angle) * r_top, -length, py5.sin(angle) * r_top)
    py5.end_shape()
    
    py5.translate(0, -length, 0)
    
    # Branches
    num_branches = 3
    for i in range(num_branches):
        py5.push_matrix()
        
        # Angles driven by time and noise to create organic folding motion
        rot_y = (i / num_branches) * py5.TWO_PI + py5.os_noise(depth * 0.1, t * 0.2) * py5.PI
        rot_z = py5.sin(t * 1.5 + depth * 0.5 + i) * py5.PI / 3 + py5.PI / 5
        
        py5.rotate_y(rot_y)
        py5.rotate_z(rot_z)
        
        draw_branch(length * 0.68, depth + 1, max_depth, t)
        py5.pop_matrix()

def draw():
    py5.background(5, 5, 10)
    py5.lights()
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height - 200, -600)
    
    # Slowly rotate the entire tree
    t = py5.frame_count * 0.01
    py5.rotate_y(t)
    
    max_depth = 8
    initial_length = 600
    draw_branch(initial_length, 0, max_depth, t)
    
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
