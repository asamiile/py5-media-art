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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 5, 20)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    t = py5.frame_count * 0.02
    
    num_rings = 40
    points_per_ring = 30
    
    py5.no_fill()
    py5.stroke_weight(2)
    py5.blend_mode(py5.ADD)
    
    for i in range(num_rings, 0, -1):
        z = (i * 20 - (py5.frame_count * 5) % 20)
        if z <= 0: continue
        
        tz = z * 0.01
        offset_x = py5.os_noise(tz, t) * 400 - 200
        offset_y = py5.os_noise(tz + 100, t) * 400 - 200
        
        r = 300 + py5.os_noise(tz, t*2) * 100
        
        scale = 1000.0 / (z + 100)
        
        px = offset_x * scale
        py = offset_y * scale
        pr = r * scale
        
        c_r = int(py5.remap(py5.os_noise(tz, 0, t), 0, 1, 50, 255))
        c_g = int(py5.remap(py5.os_noise(tz, 10, t), 0, 1, 50, 255))
        c_b = int(py5.remap(py5.os_noise(tz, 20, t), 0, 1, 50, 255))
        
        alpha = int(py5.remap(z, 0, num_rings * 20, 255, 0))
        py5.stroke(c_r, c_g, c_b, alpha)
        
        py5.begin_shape()
        for j in range(points_per_ring):
            angle = py5.TWO_PI * j / points_per_ring + tz * 2 + t
            rx = np.cos(angle) * pr
            ry = np.sin(angle) * pr
            py5.vertex(px + rx, py + ry)
        py5.end_shape(py5.CLOSE)
        
        if i > 1:
            z_next = ((i-1) * 20 - (py5.frame_count * 5) % 20)
            tz_next = z_next * 0.01
            offset_x_next = py5.os_noise(tz_next, t) * 400 - 200
            offset_y_next = py5.os_noise(tz_next + 100, t) * 400 - 200
            r_next = 300 + py5.os_noise(tz_next, t*2) * 100
            scale_next = 1000.0 / (z_next + 100)
            px_next = offset_x_next * scale_next
            py_next = offset_y_next * scale_next
            pr_next = r_next * scale_next
            
            py5.stroke(c_r, c_g, c_b, alpha // 2)
            py5.begin_shape(py5.LINES)
            for j in range(0, points_per_ring, 3):
                angle = py5.TWO_PI * j / points_per_ring + tz * 2 + t
                rx = np.cos(angle) * pr
                ry = np.sin(angle) * pr
                
                angle_next = py5.TWO_PI * j / points_per_ring + tz_next * 2 + t
                rx_next = np.cos(angle_next) * pr_next
                ry_next = np.sin(angle_next) * pr_next
                
                py5.vertex(px + rx, py + ry)
                py5.vertex(px_next + rx_next, py_next + ry_next)
            py5.end_shape()
            
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
