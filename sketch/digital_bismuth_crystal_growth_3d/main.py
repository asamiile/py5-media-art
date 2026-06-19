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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw():
    py5.background(10, 10, 15)
    
    # Lighting setup to enhance iridescent colors
    py5.ambient_light(50, 50, 50)
    py5.point_light(255, 255, 255, py5.width/2, -py5.height, 500)
    py5.directional_light(255, 100, 100, 1, 1, -1)
    
    time_t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Slow camera rotation
    py5.rotate_x(-py5.QUARTER_PI + np.sin(time_t * 0.2) * 0.2)
    py5.rotate_y(time_t * 0.5)
    
    num_steps = 300
    
    py5.no_stroke()
    
    # Hopper crystal growth simulation
    # Bismuth forms spiral staircases
    
    for i in range(num_steps):
        # Progress based on time to simulate growth
        growth = py5.constrain(py5.remap(py5.frame_count, i * 2, i * 2 + 60, 0, 1), 0, 1)
        
        if growth > 0:
            py5.push_matrix()
            
            # Spiral positioning
            angle = i * py5.HALF_PI * 0.98  # Slight offset from 90 degrees
            radius = 10 + i * 1.5
            height_y = i * 2 - num_steps
            
            py5.translate(np.cos(angle) * radius, height_y, np.sin(angle) * radius)
            py5.rotate_y(-angle)
            
            # Iridescent color shifting
            hue = (i * 2 + time_t * 50) % 360
            saturation = 80 + np.sin(i * 0.1) * 20
            brightness = 90
            
            py5.fill(hue, saturation, brightness)
            
            # Draw box segment
            box_width = 40 + i * 0.5
            box_height = 10
            box_depth = 15
            
            py5.scale(growth)
            py5.box(box_width, box_height, box_depth)
            
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
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
