from pathlib import Path
import shutil
import subprocess
import sys
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    # Blend mode ADD for glowing overlaps
    py5.blend_mode(py5.ADD)

def draw_fractal(length, depth, max_depth, t):
    if depth == 0:
        return
        
    hue = (depth * 20 + py5.frame_count * 0.5) % 360
    py5.fill(hue, 90, 80, 50)
    
    # Draw shape
    py5.circle(0, 0, length)
    
    # Recursion
    new_length = length * 0.5
    num_branches = 6
    
    # Base rotation that evolves
    base_rot = math.sin(t + depth * 0.2) * math.pi / 4
    
    for i in range(num_branches):
        py5.push_matrix()
        angle = i * (py5.TWO_PI / num_branches) + base_rot
        
        # Position offset
        offset_dist = length * 0.6 * math.cos(t * 0.5 + depth)
        py5.rotate(angle)
        py5.translate(offset_dist, 0)
        
        # Recursive rotation
        py5.rotate(t * 2)
        
        draw_fractal(new_length, depth - 1, max_depth, t)
        py5.pop_matrix()

def draw():
    py5.background(5, 80, 10)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width/2, py5.height/2)
    
    # Global rotation
    py5.rotate(t * 0.5)
    
    # Start recursive drawing
    # Decrease max_depth slightly to ensure smooth 60fps
    draw_fractal(py5.height * 0.4, 5, 5, t)

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
