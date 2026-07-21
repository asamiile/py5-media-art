from pathlib import Path
import shutil
import subprocess
import sys
import random
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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(10, 15, 20)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)

def draw_layer(radius, sides, t, depth):
    if depth <= 0 or radius < 10:
        return
        
    py5.push_matrix()
    
    # Rotate based on depth and time
    rot_speed = py5.noise(depth * 0.1, t * 0.5) * 4 - 2
    py5.rotate(t * rot_speed)
    
    # Draw shape
    py5.begin_shape()
    for i in range(sides):
        angle = py5.TWO_PI / sides * i
        
        # Add perlin noise distortion to vertices
        noise_val = py5.noise(
            np.cos(angle) * 2 + t, 
            np.sin(angle) * 2 + t,
            depth
        )
        r = radius * (0.8 + noise_val * 0.4)
        
        x = np.cos(angle) * r
        y = np.sin(angle) * r
        py5.vertex(x, y)
    py5.end_shape(py5.CLOSE)
    
    # Recursion
    num_branches = 6
    for i in range(num_branches):
        py5.push_matrix()
        angle = py5.TWO_PI / num_branches * i + (t * (1 if depth%2==0 else -1))
        
        # Shift outward
        offset = radius * 0.6
        py5.translate(np.cos(angle) * offset, np.sin(angle) * offset)
        
        # Recursive call with scaled down radius
        draw_layer(radius * 0.55, sides, t, depth - 1)
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    # Clear screen with alpha fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(190, 80, 5, 4) # Very dark blue/teal fade
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # Pulsing base color
    base_hue = 160 + py5.noise(t) * 60 # Cyans to greens
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw central recursive structure
    depth = 4
    base_radius = 400 + np.sin(t * 2) * 100
    sides = 6
    
    for d in range(depth, 0, -1):
        hue = (base_hue + d * 15) % 360
        py5.stroke(hue, 80, 100, 15)
        draw_layer(base_radius, sides, t, d)

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
