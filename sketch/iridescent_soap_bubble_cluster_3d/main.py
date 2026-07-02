from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global bubbles
    bubbles = []
    for _ in range(12):
        bubbles.append({
            'x': random.uniform(-400, 400),
            'y': random.uniform(-400, 400),
            'z': random.uniform(-400, 400),
            'base_radius': random.uniform(150, 450),
            'seed_offset': random.uniform(0, 1000),
            'hue_shift': random.uniform(0, 360),
            'rot_axis': (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
        })

def draw_wobbly_sphere(b, time_val):
    res = 40
    r_base = b['base_radius']
    seed = b['seed_offset']
    h_shift = b['hue_shift']
    
    for i in range(res):
        lat0 = py5.PI * (-0.5 + float(i) / res)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = py5.PI * (-0.5 + float(i + 1) / res)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(res + 1):
            lng = py5.TWO_PI * float(j) / res
            x0 = math.cos(lng) * zr0
            y0 = math.sin(lng) * zr0
            
            x1 = math.cos(lng) * zr1
            y1 = math.sin(lng) * zr1
            
            nx0 = x0 * 0.8
            ny0 = y0 * 0.8
            nz0 = z0 * 0.8
            noise_val0 = py5.os_noise(nx0, ny0, nz0 + seed, time_val)
            r0_final = r_base + noise_val0 * r_base * 0.35
            
            nx1 = x1 * 0.8
            ny1 = y1 * 0.8
            nz1 = z1 * 0.8
            noise_val1 = py5.os_noise(nx1, ny1, nz1 + seed, time_val)
            r1_final = r_base + noise_val1 * r_base * 0.35
            
            hue0 = (h_shift + (x0 + y0 + z0) * 60 + time_val * 60) % 360
            hue1 = (h_shift + (x1 + y1 + z1) * 60 + time_val * 60) % 360
            
            rim0 = abs(z0)
            rim1 = abs(z1)
            
            alpha0 = py5.remap(1.0 - rim0, 0, 1, 10, 80)
            alpha1 = py5.remap(1.0 - rim1, 0, 1, 10, 80)
            
            bright0 = py5.remap(1.0 - rim0, 0, 1, 40, 100)
            bright1 = py5.remap(1.0 - rim1, 0, 1, 40, 100)
            
            py5.fill(hue0, 90, bright0, alpha0)
            py5.vertex(x0 * r0_final, y0 * r0_final, z0 * r0_final)
            
            py5.fill(hue1, 90, bright1, alpha1)
            py5.vertex(x1 * r1_final, y1 * r1_final, z1 * r1_final)
        py5.end_shape()

def draw():
    py5.background(5, 5, 10)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_x(py5.frame_count * 0.001)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.02
    
    for b in bubbles:
        py5.push_matrix()
        dx = py5.os_noise(b['seed_offset'], time_val * 0.5) * 300 - 150
        dy = py5.os_noise(b['seed_offset'] + 100, time_val * 0.5) * 300 - 150
        dz = py5.os_noise(b['seed_offset'] + 200, time_val * 0.5) * 300 - 150
        
        py5.translate(b['x'] + dx, b['y'] + dy, b['z'] + dz)
        
        rx, ry, rz = b['rot_axis']
        py5.rotate(time_val, rx, ry, rz)
        
        draw_wobbly_sphere(b, time_val)
        py5.pop_matrix()
        
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

py5.run_sketch()
