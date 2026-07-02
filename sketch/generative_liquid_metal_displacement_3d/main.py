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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Variables for the sphere mesh
RESOLUTION = 60
vertices = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.sphere_detail(RESOLUTION)
    
    # Precompute basic sphere coordinates (theta and phi)
    for i in range(RESOLUTION + 1):
        lat = py5.remap(i, 0, RESOLUTION, 0, py5.PI)
        row = []
        for j in range(RESOLUTION + 1):
            lon = py5.remap(j, 0, RESOLUTION, 0, py5.TWO_PI)
            
            x = py5.sin(lat) * py5.cos(lon)
            y = py5.sin(lat) * py5.sin(lon)
            z = py5.cos(lat)
            
            row.append((x, y, z))
        vertices.append(row)

def draw():
    py5.background(0, 0, 10)
    
    # Setup camera and lighting
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_y(py5.frame_count * 0.007)
    
    # Dynamic lighting for "metal"
    lx = py5.cos(py5.frame_count * 0.02) * SIZE[1]
    lz = py5.sin(py5.frame_count * 0.02) * SIZE[1]
    
    py5.ambient_light(200, 20, 20)
    py5.point_light(200, 80, 100, lx, -SIZE[1]/2, lz)
    py5.point_light(0, 0, 100, -lx, SIZE[1]/2, -lz)
    
    py5.light_specular(0, 0, 100)
    py5.emissive(0, 0, 10)
    py5.specular(0, 0, 100)
    py5.shininess(15.0)
    
    # Material properties
    py5.fill(220, 20, 60)
    py5.no_stroke()
    
    time_offset = py5.frame_count * 0.015
    base_radius = SIZE[1] * 0.35
    
    for i in range(RESOLUTION):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(RESOLUTION + 1):
            # Vertex 1 (current row)
            v1x, v1y, v1z = vertices[i][j]
            n1 = py5.os_noise(v1x + time_offset, v1y + time_offset, v1z + time_offset)
            r1 = base_radius + py5.remap(n1, -1, 1, -SIZE[1]*0.1, SIZE[1]*0.15)
            
            py5.normal(v1x, v1y, v1z)
            py5.vertex(v1x * r1, v1y * r1, v1z * r1)
            
            # Vertex 2 (next row)
            v2x, v2y, v2z = vertices[i+1][j]
            n2 = py5.os_noise(v2x + time_offset, v2y + time_offset, v2z + time_offset)
            r2 = base_radius + py5.remap(n2, -1, 1, -SIZE[1]*0.1, SIZE[1]*0.15)
            
            py5.normal(v2x, v2y, v2z)
            py5.vertex(v2x * r2, v2y * r2, v2z * r2)
            
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
