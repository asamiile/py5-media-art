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
DURATION_SEC = 10
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

def superformula(angle, a, b, m, n1, n2, n3):
    t1 = abs((1/a) * py5.cos(m * angle / 4)) ** n2
    t2 = abs((1/b) * py5.sin(m * angle / 4)) ** n3
    r = (t1 + t2) ** (-1/n1)
    return r

def draw():
    py5.background(5)
    py5.ambient_light(0, 0, 20)
    py5.directional_light(200, 100, 100, 1, 1, -1)
    py5.directional_light(320, 80, 80, -1, -1, 1)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_y(py5.frame_count * 0.007)
    py5.rotate_z(py5.frame_count * 0.003)
    
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    
    res_lon = 80
    res_lat = 80
    
    # Animate parameters
    t = py5.frame_count / TOTAL_FRAMES * py5.TWO_PI
    m1 = 5 + py5.sin(t) * 2
    n1_1 = 0.5 + py5.cos(t) * 0.2
    n2_1 = 1.7
    n3_1 = 1.7
    
    m2 = 4 + py5.cos(t * 1.5) * 2
    n1_2 = 0.2 + py5.sin(t * 0.5) * 0.1
    n2_2 = 1.7
    n3_2 = 1.7
    
    a = 1
    b = 1
    base_radius = min(py5.width, py5.height) * 0.3
    
    for i in range(res_lat):
        lat0 = py5.remap(i, 0, res_lat, -py5.PI/2, py5.PI/2)
        lat1 = py5.remap(i + 1, 0, res_lat, -py5.PI/2, py5.PI/2)
        
        r2_0 = superformula(lat0, a, b, m2, n1_2, n2_2, n3_2)
        r2_1 = superformula(lat1, a, b, m2, n1_2, n2_2, n3_2)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(res_lon + 1):
            lon = py5.remap(j, 0, res_lon, -py5.PI, py5.PI)
            r1 = superformula(lon, a, b, m1, n1_1, n2_1, n3_1)
            
            x0 = base_radius * r1 * py5.cos(lon) * r2_0 * py5.cos(lat0)
            y0 = base_radius * r1 * py5.sin(lon) * r2_0 * py5.cos(lat0)
            z0 = base_radius * r2_0 * py5.sin(lat0)
            
            x1 = base_radius * r1 * py5.cos(lon) * r2_1 * py5.cos(lat1)
            y1 = base_radius * r1 * py5.sin(lon) * r2_1 * py5.cos(lat1)
            z1 = base_radius * r2_1 * py5.sin(lat1)
            
            dist_0 = py5.sqrt(x0*x0 + y0*y0 + z0*z0)
            hue0 = (dist_0 * 0.5 + py5.frame_count) % 360
            py5.fill(hue0, 80, 80, 50)
            py5.vertex(x0, y0, z0)
            
            dist_1 = py5.sqrt(x1*x1 + y1*y1 + z1*z1)
            hue1 = (dist_1 * 0.5 + py5.frame_count) % 360
            py5.fill(hue1, 80, 80, 50)
            py5.vertex(x1, y1, z1)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
