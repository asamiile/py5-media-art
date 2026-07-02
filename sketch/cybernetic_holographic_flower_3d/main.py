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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(10, 20, 10)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Rotate scene
    py5.rotate_x(py5.PI / 4 + np.sin(py5.frame_count * 0.01) * 0.2)
    py5.rotate_z(py5.frame_count * 0.015)
    
    bloom = (np.sin(py5.frame_count * 0.05) + 1.0) / 2.0  # 0 to 1
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    num_petals = 12
    layers = 4
    
    for layer in range(layers):
        layer_scale = 1.0 - (layer * 0.2)
        py5.push_matrix()
        
        # Stagger layer rotations
        py5.rotate_z(layer * py5.PI / num_petals)
        
        for i in range(num_petals):
            py5.push_matrix()
            py5.rotate_z(i * py5.TWO_PI / num_petals)
            
            # Petal curl
            curl = (layer + 1) * 0.5 + bloom * 1.5
            py5.rotate_x(py5.PI / 2 - curl)
            
            py5.begin_shape(py5.LINES)
            hue = (280 + layer * 30 + py5.frame_count * 0.5) % 360
            
            for v in np.linspace(0, 1, 40):
                # Parametric petal shape
                w = np.sin(v * py5.PI) * 150 * layer_scale
                h = v * 500 * layer_scale
                
                py5.stroke(hue, 90, 100, 80)
                py5.vertex(-w, -h, 0)
                py5.vertex(w, -h, 0)
                
                # Cross-hatching for holographic feel
                if v < 0.95:
                    h_next = (v + 0.05) * 500 * layer_scale
                    py5.vertex(-w, -h, 0)
                    py5.vertex(0, -h_next, 20 * layer_scale)
                    
                    py5.vertex(w, -h, 0)
                    py5.vertex(0, -h_next, 20 * layer_scale)

            py5.end_shape()
            py5.pop_matrix()
            
        py5.pop_matrix()
        
    # Core
    py5.push_matrix()
    py5.rotate_z(-py5.frame_count * 0.05)
    py5.stroke(60, 90, 100, 90)
    py5.stroke_weight(4)
    py5.sphere_detail(10)
    py5.sphere(80 + bloom * 30)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
