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

cols, rows = 0, 0
scl = 80
w = 4000
h = 3000

def setup():
    global cols, rows
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cols = w // scl
    rows = h // scl

def draw():
    py5.blend_mode(py5.BLEND)
    # Deep purple background
    py5.background(270, 100, 10)
    
    py5.blend_mode(py5.ADD)
    time = py5.frame_count * 0.05
    
    # --- Draw Retro Sun ---
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 - 200, -800)
    py5.no_stroke()
    
    sun_radius = 600
    for i in range(100):
        y = py5.remap(i, 0, 100, -sun_radius, sun_radius)
        # Scanlines effect
        if i % 4 == 0 or i % 4 == 1:
            continue
            
        x_width = np.sqrt(sun_radius**2 - y**2)
        
        # Gradient from yellow to pink
        hue = py5.remap(y, -sun_radius, sun_radius, 40, 320)
        py5.fill(hue, 90, 100)
        py5.rect(-x_width, y, x_width*2, sun_radius/50.0)
    py5.pop_matrix()
    
    # --- Draw Neon Grid Terrain ---
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2 + 200, 100)
    py5.rotate_x(py5.PI / 2.2)
    py5.translate(-w/2, -h/2)
    
    py5.stroke(320, 100, 100) # Hot Pink
    py5.stroke_weight(3)
    py5.no_fill()
    
    # Create the rolling effect by offsetting the noise Y coordinate
    y_offset = -time * 2
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            for dy in (0, 1):
                cy = y + dy
                
                # Terrain height (flat in middle for road, mountains on sides)
                nx = py5.remap(x, 0, cols, -1, 1)
                dist_from_center = abs(nx)
                
                noise_val = py5.os_noise(x * 0.1, cy * 0.1 + y_offset)
                
                # Create a valley in the center
                mountain_factor = py5.remap(dist_from_center, 0, 1, -0.5, 1.5)
                mountain_factor = max(0.0, mountain_factor)
                
                z = noise_val * 600 * mountain_factor
                
                px = x * scl
                py_coord = cy * scl
                
                py5.vertex(px, py_coord, z)
        py5.end_shape()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
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
