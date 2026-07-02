from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

stars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Generate background stars
    random.seed(42)
    for _ in range(1000):
        stars.append((
            random.uniform(-py5.width, py5.width * 2),
            random.uniform(-py5.height, py5.height),
            random.uniform(-1000, -200),
            random.uniform(1, 4)
        ))

def draw():
    py5.background(5, 20, 10) # Dark night sky
    
    # Draw stars
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 100, 200)
    for x, y, z, s in stars:
        py5.push_matrix()
        py5.translate(x, y, z)
        # Twinkle
        if py5.random(1) > 0.98:
            py5.scale(1.5)
        py5.rect(0, 0, s, s)
        py5.pop_matrix()

    # Draw Aurora
    py5.blend_mode(py5.ADD)
    time_t = py5.frame_count * 0.005
    
    num_ribbons = 6
    points_per_ribbon = 150
    ribbon_spacing = py5.width / points_per_ribbon
    
    py5.translate(0, py5.height * 0.3, -300)
    py5.rotate_x(py5.PI / 8)
    
    for r in range(num_ribbons):
        py5.begin_shape(py5.QUAD_STRIP)
        
        hue_base = (140 + r * 15 + time_t * 50) % 360
        z_offset = r * -150
        
        for i in range(points_per_ribbon + 1):
            x = i * ribbon_spacing * 1.5 - py5.width * 0.2
            
            # Complex noise for flowing ribbon motion
            noise_x = x * 0.002
            noise_y = r * 0.1
            
            n1 = py5.noise(noise_x, noise_y, time_t)
            n2 = py5.noise(noise_x + 10, noise_y + 10, time_t * 1.5)
            
            y_base = n1 * 400
            height_var = 300 + n2 * 400
            
            # Color
            alpha_bottom = 0
            alpha_top = py5.remap(n1, 0, 1, 50, 150)
            
            # Fade edges
            if i < 20:
                alpha_top *= i / 20.0
            elif i > points_per_ribbon - 20:
                alpha_top *= (points_per_ribbon - i) / 20.0
                
            # Top vertex
            py5.fill(hue_base, 80, 90, alpha_top)
            py5.vertex(x, y_base - height_var, z_offset + n1 * 100)
            
            # Bottom vertex
            py5.fill(hue_base + 30, 90, 50, alpha_bottom)
            py5.vertex(x, y_base, z_offset + n2 * 100)
            
        py5.end_shape()

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
