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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 80, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    py5.rotate_x(t * 0.5)
    py5.rotate_y(t * 0.3)
    py5.rotate_z(t * 0.1)
    
    num_curves = 150
    points_per_curve = 500
    base_radius = 800
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    for c in range(num_curves):
        # Unique parameters for each curve based on its index and time
        freq_x = 3 + np.sin(t * 0.2 + c * 0.1) * 2
        freq_y = 4 + np.cos(t * 0.3 + c * 0.1) * 2
        freq_z = 5 + np.sin(t * 0.1 + c * 0.2) * 2
        
        phase_x = t * 2 + c * 0.05
        phase_y = t * 1.5 + c * 0.07
        phase_z = t * 1.8 + c * 0.03
        
        hue = (180 + c * 2 + t * 50) % 360
        
        # Fade out tails
        py5.begin_shape(py5.LINE_STRIP)
        for p in range(points_per_curve):
            # Parameter from 0 to 2PI
            theta = (p / points_per_curve) * py5.TWO_PI
            
            x = base_radius * np.sin(freq_x * theta + phase_x)
            y = base_radius * np.sin(freq_y * theta + phase_y)
            z = base_radius * np.sin(freq_z * theta + phase_z)
            
            # Vary radius slightly
            r_mod = 1.0 + np.sin(theta * 10 + t) * 0.1
            x *= r_mod
            y *= r_mod
            z *= r_mod
            
            alpha = py5.remap(p, 0, points_per_curve, 0, 40)
            py5.stroke(hue, 90, 100, alpha)
            
            py5.vertex(x, y, z)
            
        py5.end_shape()

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
