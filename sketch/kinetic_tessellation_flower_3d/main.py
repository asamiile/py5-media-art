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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 15, 20)  # Dark slate
    py5.ambient_light(50, 50, 50)
    py5.directional_light(255, 220, 150, 1, 1, -1)  # Warm gold light
    py5.directional_light(150, 220, 255, -1, -1, -1)  # Cool cyan light
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.2 + py5.PI / 4)
    py5.rotate_y(t * py5.TWO_PI)
    
    num_layers = 12
    num_petals = 8
    
    for i in range(num_layers):
        py5.push_matrix()
        
        radius = 200 + i * 80
        layer_t = (t + i / num_layers) % 1.0
        
        py5.rotate_y(layer_t * py5.TWO_PI * (1 if i % 2 == 0 else -1))
        
        for j in range(num_petals):
            py5.push_matrix()
            angle = j * py5.TWO_PI / num_petals
            py5.rotate_y(angle)
            py5.translate(radius, 0, 0)
            
            # Bloom effect
            bloom = py5.sin(layer_t * py5.PI)
            py5.rotate_z(bloom * py5.PI / 2)
            
            py5.fill(200, 170, 80) if i % 2 == 0 else py5.fill(80, 180, 200)
            py5.no_stroke()
            
            # Draw petal
            py5.begin_shape()
            py5.vertex(0, 0, 0)
            py5.vertex(40, -100 * bloom, 20)
            py5.vertex(80, -120 * bloom, 0)
            py5.vertex(40, -100 * bloom, -20)
            py5.end_shape(py5.CLOSE)
            
            py5.pop_matrix()
            
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
