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
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    py5.no_fill()

def draw():
    py5.background(0, 0, 0, 15)
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count / FPS
    # Slow rotation around Y and X axis
    rot_y = t * 0.5
    rot_x = t * 0.3
    
    # We will simulate Spherical Harmonics by generating a dense grid of points on a sphere
    # and warping their radius based on spherical harmonic functions.
    # To keep performance high, we draw lines/points.
    
    # Parameters for the spherical harmonic
    # We'll smoothly transition m and n over time using sine waves
    m0, m1 = 3, 5
    m2, m3 = 4, 6
    m4, m5 = 1, 2
    
    # Use nested loops for polar coordinates
    lat_steps = 60
    lon_steps = 60
    
    py5.stroke_weight(2)
    
    for i in range(lat_steps + 1):
        lat = py5.remap(i, 0, lat_steps, 0, py5.PI)
        
        py5.begin_shape(py5.LINE_STRIP)
        for j in range(lon_steps + 1):
            lon = py5.remap(j, 0, lon_steps, 0, py5.TWO_PI)
            
            # Spherical harmonic calculation
            # A simplified combination of sinusoids for visual effect
            r1 = math.sin(m0 * lat) ** m1
            r2 = math.cos(m2 * lon) ** m3
            r3 = math.sin(m4 * lat) ** m5
            r4 = math.cos(m5 * lon) ** m4
            
            # Blend based on time to animate the harmonic states
            blend_val = (math.sin(t) + 1) * 0.5
            radius = py5.remap(blend_val, 0, 1, abs(r1 + r2), abs(r3 + r4)) * py5.width * 0.3 + 100
            
            # Convert to Cartesian
            x = radius * math.sin(lat) * math.cos(lon)
            y = radius * math.sin(lat) * math.sin(lon)
            z = radius * math.cos(lat)
            
            # Apply 3D rotation manually for 2D projection
            # Rot Y
            x_rot_y = x * math.cos(rot_y) - z * math.sin(rot_y)
            z_rot_y = x * math.sin(rot_y) + z * math.cos(rot_y)
            
            # Rot X
            y_rot_x = y * math.cos(rot_x) - z_rot_y * math.sin(rot_x)
            z_rot_x = y * math.sin(rot_x) + z_rot_y * math.cos(rot_x)
            
            # Color
            hue = (200 + y_rot_x * 0.2 + t * 50) % 360
            py5.stroke(hue, 80, 80, 40)
            
            # Project
            py5.vertex(x_rot_y, y_rot_x)
        
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
