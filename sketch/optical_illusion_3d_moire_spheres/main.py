from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion Blur
    py5.push_style()
    py5.fill(0, 0, 0, 80)
    py5.no_stroke()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.rect(0, 0, py5.width, py5.height)
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.pop_style()

    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    num_lat = 40
    num_lon = 80
    radius = min(py5.width, py5.height) * 0.4
    
    # Inner Sphere (Cyan/Indigo)
    py5.push_matrix()
    py5.rotate_x(t * 0.5)
    py5.rotate_y(t * 0.3)
    py5.stroke(0, 150, 255, 180)
    draw_wireframe_sphere(radius * 0.98, num_lat, num_lon)
    py5.pop_matrix()
    
    # Outer Sphere (White/Cyan)
    py5.push_matrix()
    py5.rotate_x(-t * 0.2)
    py5.rotate_y(t * 0.6)
    py5.stroke(200, 255, 255, 180)
    draw_wireframe_sphere(radius, num_lat, num_lon)
    py5.pop_matrix()
    
    py5.blend_mode(py5.BLEND)

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

def draw_wireframe_sphere(r, lat_count, lon_count):
    # Latitudes
    for i in range(1, lat_count):
        lat = py5.PI * i / lat_count
        y = r * py5.cos(lat)
        ring_r = r * py5.sin(lat)
        py5.begin_shape()
        for j in range(lon_count + 1):
            lon = py5.TWO_PI * j / lon_count
            x = ring_r * py5.cos(lon)
            z = ring_r * py5.sin(lon)
            py5.vertex(x, y, z)
        py5.end_shape()
        
    # Longitudes
    for j in range(lon_count):
        lon = py5.TWO_PI * j / lon_count
        py5.begin_shape()
        for i in range(lat_count + 1):
            lat = py5.PI * i / lat_count
            y = r * py5.cos(lat)
            ring_r = r * py5.sin(lat)
            x = ring_r * py5.cos(lon)
            z = ring_r * py5.sin(lon)
            py5.vertex(x, y, z)
        py5.end_shape()

py5.run_sketch()
