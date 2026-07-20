from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

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

# Ribbon properties
NUM_RIBBONS = 20
RIBBON_LENGTH = 150
RIBBON_MAX_WIDTH = 60.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global ribbon_offsets, ribbon_colors
    ribbon_offsets = np.random.uniform(0, 1000, (NUM_RIBBONS, 2))
    # Warm colors: oranges, golds, corals
    ribbon_colors = np.random.uniform(20, 60, NUM_RIBBONS)

def draw():
    # Deep navy blue background with trail fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(220, 80, 15, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # We will use additive blending for the ribbons to make them glow
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    global ribbon_offsets, ribbon_colors
    
    for i in range(NUM_RIBBONS):
        # Base hue shifting slightly over time
        hue = (ribbon_colors[i] + t * 40) % 360
        py5.fill(hue, 90, 80, 60)
        
        offset_x, offset_y = ribbon_offsets[i]
        
        py5.begin_shape(py5.QUAD_STRIP)
        
        dx, dy = 1.0, 0.0 # Default tangent
        
        for j in range(RIBBON_LENGTH):
            # Calculate logical progression along the ribbon
            u = j / float(RIBBON_LENGTH - 1)
            
            # Use noise to calculate the spine's position
            noise_x = py5.noise(offset_x, u * 2.0, t * 3.0)
            noise_y = py5.noise(offset_y, u * 2.0, t * 3.0)
            
            # Map noise to screen coordinates, making it swoop across
            x = py5.width * 1.2 * noise_x - py5.width * 0.1
            y = py5.height * 1.2 * noise_y - py5.height * 0.1
            
            # To draw a quad strip, we need normal vectors to expand the ribbon.
            # We approximate the tangent using finite differences
            if j < RIBBON_LENGTH - 1:
                u_next = (j + 1) / float(RIBBON_LENGTH - 1)
                nx = py5.width * 1.2 * py5.noise(offset_x, u_next * 2.0, t * 3.0) - py5.width * 0.1
                ny = py5.height * 1.2 * py5.noise(offset_y, u_next * 2.0, t * 3.0) - py5.height * 0.1
                dx = nx - x
                dy = ny - y
                
            angle = math.atan2(dy, dx)
            
            # Calculate ribbon width modulated by sine to make it twist and pinch
            twist = math.sin(u * py5.TWO_PI * 3.0 + t * py5.TWO_PI * 5.0)
            w = RIBBON_MAX_WIDTH * twist
            
            # Normal angles
            nx_1 = x + math.cos(angle - py5.PI/2) * w
            ny_1 = y + math.sin(angle - py5.PI/2) * w
            nx_2 = x + math.cos(angle + py5.PI/2) * w
            ny_2 = y + math.sin(angle + py5.PI/2) * w
            
            # Add vertices
            py5.vertex(float(nx_1), float(ny_1))
            py5.vertex(float(nx_2), float(ny_2))
            
        py5.end_shape()
        
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
