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
    py5.background(5, 0, 10) # very dark purple void
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Do not clear background, allow accumulation
    
    py5.translate(py5.width / 2, py5.height / 2, -1000)
    
    t_start = py5.frame_count * 0.1
    t_end = (py5.frame_count + 1) * 0.1
    t_vals = np.linspace(t_start, t_end, 500)
    
    # 3D Harmonograph equations (decaying sine waves)
    # x(t) = A_x * sin(f_x * t + p_x) * exp(-d_x * t) + ...
    # We will remove the decay to make it an infinite continuous drawing, 
    # and instead slowly shift frequencies.
    
    f1 = 2.01 + np.sin(py5.frame_count * 0.001) * 0.05
    f2 = 3.0 + np.cos(py5.frame_count * 0.002) * 0.05
    f3 = 1.99 + np.sin(py5.frame_count * 0.0015) * 0.05
    f4 = 4.02 + np.cos(py5.frame_count * 0.0025) * 0.05
    
    amp = py5.height * 0.8
    
    x = amp * (np.sin(f1 * t_vals) + 0.5 * np.sin(f2 * t_vals + np.pi/4))
    y = amp * (np.sin(f3 * t_vals) + 0.5 * np.sin(f4 * t_vals + np.pi/3))
    z = amp * 0.5 * (np.sin((f1+f2) * t_vals) + np.cos((f3+f4) * t_vals))
    
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_z(py5.frame_count * 0.002)
    
    py5.no_fill()
    py5.stroke_weight(4)
    
    # Color pulse
    r = 255 * (0.5 + 0.5 * np.sin(py5.frame_count * 0.05))
    g = 50
    b = 255 * (0.5 + 0.5 * np.cos(py5.frame_count * 0.03))
    
    py5.stroke(r, g, b, 150)
    
    py5.begin_shape(py5.LINE_STRIP)
    for i in range(len(t_vals)):
        py5.vertex(x[i], y[i], z[i])
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
