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
DURATION_SEC = 20
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
    py5.background(0)

def draw():
    # Keep background dark and clear it completely each frame for 3D
    py5.background(0, 0, 5)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Slowly rotate the entire 3D object
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.002)
    
    py5.blend_mode(py5.ADD)
    
    t_global = py5.frame_count * 0.05
    
    py5.stroke_weight(5)
    
    max_history = 1000
    pts = []
    
    for i in range(max_history + 1):
        t = t_global - (i * 0.015)
        if t < 0:
            break
            
        f1x = 3.0 + py5.sin(t * 0.01) * 0.2
        f2x = 1.5 + py5.cos(t * 0.02) * 0.2
        
        f1y = 2.0 + py5.cos(t * 0.015) * 0.2
        f2y = 4.5 + py5.sin(t * 0.01) * 0.2
        
        f1z = 2.5 + py5.sin(t * 0.02) * 0.2
        f2z = 1.0 + py5.cos(t * 0.03) * 0.2
        
        scale = 1000
        
        x = scale * (0.5 * py5.sin(t * f1x) + 0.5 * py5.sin(t * f2x + py5.PI/2))
        y = scale * (0.5 * py5.sin(t * f1y) + 0.5 * py5.sin(t * f2y + py5.PI/3))
        z = scale * (0.5 * py5.sin(t * f1z) + 0.5 * py5.sin(t * f2z + py5.PI/4))
        
        pts.append((x, y, z))
        
    for i in range(len(pts) - 1):
        p1 = pts[i]
        p2 = pts[i+1]
        
        hue = (t_global * 10 + i * 0.5) % 360
        alpha = py5.remap(i, 0, max_history, 100, 0)
        
        py5.stroke(hue, 80, 100, alpha)
        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
        import os
        os._exit(0)

py5.run_sketch()
