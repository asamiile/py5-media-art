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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def fbm(x, y, z, octaves=4):
    val = 0
    amp = 1.0
    freq = 1.0
    max_val = 0
    
    for _ in range(octaves):
        val += py5.os_noise(x * freq, y * freq, z * freq) * amp
        max_val += amp
        amp *= 0.5
        freq *= 2.0
        
    return val / max_val

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_x(time * 0.2)
    py5.rotate_y(time * 0.3)
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    r_base = 500
    
    lon_steps = 100
    lat_steps = 100
    
    for i in range(lon_steps):
        lon = py5.remap(i, 0, lon_steps, -py5.PI, py5.PI)
        py5.begin_shape(py5.POINTS)
        for j in range(lat_steps):
            lat = py5.remap(j, 0, lat_steps, -py5.HALF_PI, py5.HALF_PI)
            
            # Base sphere coordinates
            nx = np.cos(lat) * np.cos(lon)
            ny = np.cos(lat) * np.sin(lon)
            nz = np.sin(lat)
            
            # fBm displacement
            noise_val = fbm(nx * 1.5, ny * 1.5, nz * 1.5 + time)
            
            r_displaced = r_base + noise_val * 300
            
            x = nx * r_displaced
            y = ny * r_displaced
            z = nz * r_displaced
            
            # Color mapping (crimson to yellow/white)
            # noise_val goes from roughly 0.2 to 0.8
            hue = py5.remap(noise_val, 0.2, 0.8, -10, 60) % 360
            brightness = py5.remap(noise_val, 0.2, 0.8, 40, 100)
            
            py5.stroke(hue, 90, brightness, 80)
            py5.vertex(x, y, z)
        py5.end_shape()
        
    # Add a glowing core
    py5.blend_mode(py5.BLEND)
    py5.fill(15, 80, 100, 30)
    py5.no_stroke()
    py5.sphere(r_base - 50)

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
