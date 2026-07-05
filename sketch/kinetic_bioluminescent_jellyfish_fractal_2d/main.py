from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 10, 20)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_tentacle(x, y, length, angle, depth, max_depth, time_val):
    if depth == 0:
        return
    
    # Calculate end point
    # Apply a noise-based curve to the angle
    noise_val = py5.noise(x * 0.005, y * 0.005, time_val * 0.5)
    angle_offset = (noise_val - 0.5) * py5.PI * 0.5
    current_angle = angle + angle_offset
    
    # Breathing effect on length
    breath = math.sin(time_val * 2.0 + depth * 0.5) * 0.2 + 1.0
    current_length = length * breath * (0.8 + noise_val * 0.2)
    
    ex = x + math.cos(current_angle) * current_length
    ey = y + math.sin(current_angle) * current_length
    
    # Draw segment
    weight = max(1.0, depth * 1.5)
    py5.stroke_weight(weight)
    
    # Color depends on depth and time
    hue = (180 + depth * 15 + time_val * 20) % 360
    py5.stroke(hue, 80, 90, 40)
    
    py5.line(x, y, ex, ey)
    
    # Recursive branches
    if depth > 1:
        # Branch 1
        draw_tentacle(ex, ey, length * 0.75, current_angle - 0.2, depth - 1, max_depth, time_val)
        # Branch 2
        draw_tentacle(ex, ey, length * 0.75, current_angle + 0.2, depth - 1, max_depth, time_val)

def draw():
    # Subtle fade for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(220, 80, 5, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    time_val = py5.frame_count * 0.02
    
    # Center position with gentle bobbing
    cx = py5.width / 2.0
    cy = py5.height * 0.3 + math.sin(time_val * 1.5) * 100
    
    # Draw core
    py5.no_stroke()
    for i in range(5, 0, -1):
        py5.fill(300, 70, 100, 15)
        py5.circle(cx, cy, i * 40 + math.sin(time_val * 4) * 20)
        
    # Draw tentacles
    num_tentacles = 12
    for i in range(num_tentacles):
        base_angle = py5.PI * 0.5 + (i - num_tentacles/2.0) * 0.15
        draw_tentacle(cx, cy, py5.height * 0.15, base_angle, 8, 8, time_val)

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
