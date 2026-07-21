from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    py5.rect_mode(py5.CENTER)
    
def draw():
    # Background - dark night sky
    py5.background(270, 90, 10) 
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Draw Sun (Sunset gradient circle with cutouts)
    sun_x = py5.width / 2
    sun_y = py5.height * 0.45
    sun_radius = py5.height * 0.4
    
    # Draw sun base (using overlapping thin rects for gradient effect)
    py5.no_stroke()
    for i in range(100):
        fraction = i / 100.0
        # Yellow (60) at top, Pink (320) at bottom
        hue = py5.lerp(60, -40, fraction) 
        if hue < 0: hue += 360
        
        py5.fill(hue, 80, 100)
        
        # Calculate width of circle at this height
        dy = (fraction * 2 - 1) * sun_radius
        w = math.sqrt(max(0, sun_radius**2 - dy**2)) * 2
        
        # Add synthwave sun cutouts at bottom
        if fraction > 0.5:
            # Cutouts get thicker towards bottom
            cutout_thickness = py5.remap(fraction, 0.5, 1.0, 2, 25)
            cutout_spacing = py5.remap(fraction, 0.5, 1.0, 10, 40)
            if (i * sun_radius / 50.0) % cutout_spacing < cutout_thickness:
                continue # Skip drawing (cutout)
                
        py5.rect(sun_x, sun_y + dy, w, sun_radius / 50.0 + 1)
        
    # 2. Draw Mountains (using noise)
    horizon = py5.height * 0.6
    py5.fill(270, 90, 15) # Dark purple silhouettes
    py5.begin_shape()
    py5.vertex(0, py5.height)
    py5.vertex(0, horizon)
    for x in range(0, py5.width, 10):
        # Parallax scrolling noise
        n = py5.os_noise(x * 0.002 + t * 0.5, 0)
        y = horizon - (n * py5.height * 0.15)
        py5.vertex(x, y)
    py5.vertex(py5.width, horizon)
    py5.vertex(py5.width, py5.height)
    py5.end_shape(py5.CLOSE)
    
    # Draw mountains glowing edge
    py5.no_fill()
    py5.stroke(320, 80, 100) # Neon pink
    py5.stroke_weight(3)
    py5.begin_shape()
    for x in range(0, py5.width, 10):
        n = py5.os_noise(x * 0.002 + t * 0.5, 0)
        y = horizon - (n * py5.height * 0.15)
        py5.vertex(x, y)
    py5.end_shape()

    # 3. Draw Perspective Grid
    py5.stroke(180, 80, 100) # Neon cyan
    py5.stroke_weight(4)
    
    # Horizontal moving lines
    num_h_lines = 20
    for i in range(num_h_lines):
        # Progress 0.0 to 1.0, scrolling towards viewer
        # Use fract to loop
        p = (i / num_h_lines + t * 2.0) % 1.0 
        
        # Quadratic mapping to simulate perspective depth
        y_pos = horizon + (p ** 3) * (py5.height - horizon)
        
        # Fade out near horizon
        alpha = py5.remap(p, 0, 0.1, 0, 100)
        py5.stroke(180, 80, 100, alpha)
        py5.line(0, y_pos, py5.width, y_pos)
        
    # Vertical radiating lines
    num_v_lines = 30
    py5.stroke(180, 80, 100)
    for i in range(-num_v_lines, num_v_lines):
        x_pos_bottom = py5.width / 2 + i * (py5.width / 10)
        # Perspective line from vanishing point at horizon
        vanishing_x = py5.width / 2
        py5.line(vanishing_x, horizon, x_pos_bottom, py5.height)
        
    # Add a glowing overlay for atmosphere
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    for i in range(3):
        py5.fill(320, 100, 20, 20)
        py5.rect(py5.width / 2, horizon - 50, py5.width, py5.height * 0.3 + i * 50)
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
        import os
        os._exit(0)

py5.run_sketch()
