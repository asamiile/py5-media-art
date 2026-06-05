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
    py5.no_stroke()
    
def draw():
    py5.background(240, 240, 245) # Clinical White/Grey
    
    # Lighting setup for glossy obsidian
    py5.ambient_light(30, 30, 35)
    py5.directional_light(255, 255, 255, 0.5, 1, -1) # Strong main highlight
    py5.directional_light(200, 220, 255, -1, -0.5, 0.5) # Soft silver/blue fill
    py5.point_light(0, 50, 150, 0, -500, 200) # Subtle magnetic blue under-lighting
    
    # Material properties
    py5.specular(255, 255, 255)
    py5.shininess(50)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_x(py5.PI / 4 + np.sin(t * 0.3) * 0.1)
    py5.rotate_y(t * 0.5)
    
    py5.fill(10, 10, 12) # Obsidian Black
    
    res = 80
    base_radius = 250
    
    # We will draw a deformed sphere using triangle strips
    for i in range(res):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        lat1 = py5.PI * (-0.5 + float(i) / res)
        lat2 = py5.PI * (-0.5 + float(i + 1) / res)
        
        for j in range(res + 1):
            lon = py5.TWO_PI * float(j) / res
            
            # Point 1
            nx1 = np.cos(lon) * np.cos(lat1)
            ny1 = np.sin(lon) * np.cos(lat1)
            nz1 = np.sin(lat1)
            
            # Ferrofluid spike math: use noise to create sharp peaks
            noise_val1 = py5.os_noise(nx1 * 1.5, ny1 * 1.5, nz1 * 1.5 + t)
            # Power function creates sharp spikes from smooth noise
            spike1 = abs(noise_val1) ** 4 * 400
            
            r1 = base_radius + spike1
            x1 = r1 * nx1
            y1 = r1 * ny1
            z1 = r1 * nz1
            
            # Point 2
            nx2 = np.cos(lon) * np.cos(lat2)
            ny2 = np.sin(lon) * np.cos(lat2)
            nz2 = np.sin(lat2)
            
            noise_val2 = py5.os_noise(nx2 * 1.5, ny2 * 1.5, nz2 * 1.5 + t)
            spike2 = abs(noise_val2) ** 4 * 400
            
            r2 = base_radius + spike2
            x2 = r2 * nx2
            y2 = r2 * ny2
            z2 = r2 * nz2
            
            py5.normal(nx1, ny1, nz1)
            py5.vertex(x1, y1, z1)
            
            py5.normal(nx2, ny2, nz2)
            py5.vertex(x2, y2, z2)
            
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
