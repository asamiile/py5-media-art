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
DURATION_SEC = 20
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
    py5.background(0) # Pure black
    
    time = py5.frame_count * 0.05
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    py5.rotate_x(time * 0.2)
    py5.rotate_y(time * 0.3)
    
    py5.blend_mode(py5.ADD)
    
    radius = 500
    details = 40
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Draw fragmented sphere
    for i in range(details):
        lat0 = py5.PI * (-0.5 + float(i - 1) / details)
        z0 = radius * py5.sin(lat0)
        zr0 = radius * py5.cos(lat0)

        lat1 = py5.PI * (-0.5 + float(i) / details)
        z1 = radius * py5.sin(lat1)
        zr1 = radius * py5.cos(lat1)

        for j in range(details):
            lng = py5.TWO_PI * float(j - 1) / details
            x0 = py5.cos(lng) * zr0
            y0 = py5.sin(lng) * zr0
            x1 = py5.cos(lng) * zr1
            y1 = py5.sin(lng) * zr1

            lng1 = py5.TWO_PI * float(j) / details
            x2 = py5.cos(lng1) * zr1
            y2 = py5.sin(lng1) * zr1
            x3 = py5.cos(lng1) * zr0
            y3 = py5.sin(lng1) * zr0
            
            # Glitchy fragmentation using noise
            n = py5.os_noise(i * 0.1, j * 0.1, time * 0.5)
            if n > 0.4:
                # Cyan and orange palette
                if n > 0.7:
                    py5.stroke(190, 100, 100, 80) # Cyan
                else:
                    py5.stroke(25, 100, 100, 80) # Orange
                    
                py5.begin_shape(py5.LINES)
                py5.vertex(x0, y0, z0)
                py5.vertex(x1, y1, z1)
                
                py5.vertex(x1, y1, z1)
                py5.vertex(x2, y2, z1)
                py5.end_shape()

    # Draw orbiting rings of data points
    py5.rotate_x(-time * 0.4)
    py5.rotate_z(time * 0.1)
    
    for r in range(3):
        ring_radius = radius + 200 + r * 150
        num_points = 100 + r * 50
        
        py5.stroke(190, 100, 100, 90) if r % 2 == 0 else py5.stroke(25, 100, 100, 90)
        py5.stroke_weight(4)
        
        py5.begin_shape(py5.POINTS)
        for p in range(num_points):
            angle = p * py5.TWO_PI / num_points + time * (0.05 + r * 0.02)
            
            # Add some jitter to points
            jitter = (py5.os_noise(p, r, time) - 0.5) * 50
            
            px = py5.cos(angle) * (ring_radius + jitter)
            py5.vertex(px, 0, py5.sin(angle) * (ring_radius + jitter))
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
