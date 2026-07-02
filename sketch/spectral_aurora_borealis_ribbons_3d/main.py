from pathlib import Path
import shutil
import subprocess
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.hint(py5.DISABLE_DEPTH_TEST) # Additive blending works better without depth testing
    py5.blend_mode(py5.ADD)

def draw():
    py5.background(220, 90, 5) # Dark night sky
    
    t = py5.frame_count * 0.015
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -500)
    py5.rotate_x(py5.PI / 6)
    
    num_ribbons = 5
    points_per_ribbon = 150
    radius = 600
    
    for i in range(num_ribbons):
        py5.begin_shape(py5.QUAD_STRIP)
        py5.no_stroke()
        for j in range(points_per_ribbon):
            angle = py5.remap(j, 0, points_per_ribbon - 1, 0, py5.TWO_PI * 1.5)
            
            # Base circle
            x_base = py5.cos(angle) * radius
            z_base = py5.sin(angle) * radius
            
            # Noise displacement
            n_val = py5.os_noise(x_base * 0.002, z_base * 0.002, i * 10 + t)
            n_val_top = py5.os_noise(x_base * 0.003, z_base * 0.003, i * 10 + t * 1.2 + 50)
            
            x = x_base + py5.cos(angle) * n_val * 300
            z = z_base + py5.sin(angle) * n_val * 300
            
            x_top = x_base + py5.cos(angle) * n_val_top * 400
            z_top = z_base + py5.sin(angle) * n_val_top * 400
            
            # Height of the ribbon
            y_bottom = 200 + n_val * 100
            y_top = -600 + n_val_top * 200
            
            # Color
            hue = (140 + i * 20 + n_val * 40) % 360
            py5.fill(hue, 80, 80, 15) # Emerald to violet, low alpha for additive
            py5.vertex(x_top, y_top, z_top)
            
            py5.fill(hue, 90, 60, 5) # Fade out at bottom
            py5.vertex(x, y_bottom, z)
            
        py5.end_shape()
    
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES*100):.1f}%)")

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
