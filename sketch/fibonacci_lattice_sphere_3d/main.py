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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(time * 0.5)
    py5.rotate_y(time * 0.7)
    
    # Animated golden ratio parameter
    golden_ratio = (1 + np.sqrt(5)) / 2
    animated_ratio = golden_ratio + np.sin(time) * 0.05
    
    num_pts = 1000
    radius = 600 + np.sin(time * 2) * 100
    
    points = []
    
    # Calculate Fibonacci sphere points
    for i in range(num_pts):
        t = i / float(num_pts - 1)
        # y goes from 1 to -1
        y = 1 - (t * 2)
        r = np.sqrt(1 - y * y)
        theta = py5.PI * 2 * animated_ratio * i
        
        x = np.cos(theta) * r
        z = np.sin(theta) * r
        
        points.append(np.array([x * radius, y * radius, z * radius]))
    
    # Draw points and connections
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    
    for i in range(num_pts):
        p1 = points[i]
        
        # Color based on index and time
        hue = (i * 0.5 + time * 20) % 360
        py5.stroke(hue, 80, 100, 80)
        
        # Connect to a few neighbors in sequence
        # (Since points are sequentially close in spiral, connecting i to i+1..i+5 creates interesting meshes)
        for j in range(1, 6):
            if i + j < num_pts:
                p2 = points[i + j]
                py5.vertex(*p1)
                py5.vertex(*p2)
                
    py5.end_shape()
    
    # Draw glowing nodes
    py5.stroke_weight(6)
    py5.begin_shape(py5.POINTS)
    for i in range(num_pts):
        hue = (i * 0.5 + time * 20) % 360
        py5.stroke(hue, 50, 100, 100)
        py5.vertex(*points[i])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
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
