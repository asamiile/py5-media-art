from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math

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
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(15)
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_x(py5.PI / 4 + py5.sin(t * 0.5) * 0.2)
    py5.rotate_y(t * 0.3)
    
    # Lighting for shiny black material
    py5.ambient_light(0, 0, 10)
    py5.point_light(200, 20, 100, 500, -500, 500)
    py5.point_light(280, 40, 80, -500, 500, 500)
    py5.specular(0, 0, 80)
    py5.shininess(10)
    
    py5.fill(0, 0, 5) # Very dark grey
    py5.no_stroke()
    
    # Draw deformed sphere
    detail = 60
    r_base = 300
    
    for i in range(detail):
        lon1 = py5.remap(i, 0, detail, 0, py5.PI * 2)
        lon2 = py5.remap(i + 1, 0, detail, 0, py5.PI * 2)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(detail + 1):
            lat = py5.remap(j, 0, detail, -py5.PI / 2, py5.PI / 2)
            
            # Point 1
            x1 = math.cos(lat) * math.cos(lon1)
            y1 = math.cos(lat) * math.sin(lon1)
            z1 = math.sin(lat)
            
            noise_val1 = py5.os_noise(x1 * 2 + t, y1 * 2, z1 * 2)
            # Threshold noise to create spikes
            spike1 = max(0, noise_val1 - 0.4) * 500
            
            r1 = r_base + spike1
            py5.normal(x1, y1, z1) # Not perfect normals but works for shiny effect
            py5.vertex(x1 * r1, y1 * r1, z1 * r1)
            
            # Point 2
            x2 = math.cos(lat) * math.cos(lon2)
            y2 = math.cos(lat) * math.sin(lon2)
            z2 = math.sin(lat)
            
            noise_val2 = py5.os_noise(x2 * 2 + t, y2 * 2, z2 * 2)
            spike2 = max(0, noise_val2 - 0.4) * 500
            
            r2 = r_base + spike2
            py5.normal(x2, y2, z2)
            py5.vertex(x2 * r2, y2 * r2, z2 * r2)
            
        py5.end_shape()

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
