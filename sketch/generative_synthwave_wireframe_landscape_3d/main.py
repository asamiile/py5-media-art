from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

COLS = 120
ROWS = 120
SCL = 60

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global y_offsets, x_offsets
    y_offsets = np.linspace(0.1, 10, ROWS)
    x_offsets = np.linspace(-5, 5, COLS)

def draw():
    py5.background(10, 0, 20)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Calculate the moving Z landscape using a vectorizable noise proxy
    Y, X = np.meshgrid(y_offsets - (t * 20.0), x_offsets, indexing='ij')
    
    # Complex proxy for Perlin noise using intersecting waves
    Z = np.sin(X*1.5 + Y*1.2) * 2.0 + np.cos(X*3.0 - Y*2.0) * 1.0 + np.sin(Y*0.5) * 3.0
    
    # Flatten the terrain in the middle to create a "highway"
    center_dist = np.abs(np.linspace(-1, 1, COLS))
    highway_mask = np.clip(center_dist * 4.0 - 0.5, 0, 1)
    Z = Z * highway_mask
    
    # Manual 3D projection
    cx, cy = py5.width / 2, py5.height / 2
    fov = py5.height * 0.8
    
    # Y is depth, Z is height (elevation)
    depth = y_offsets[:, None] - (t * 20.0 % (10.0 / ROWS))
    
    # To keep it scrolling infinitely, we use a modulo on depth, but we must recalculate Z
    actual_depth = np.linspace(0.1, 10.0, ROWS)[:, None]
    actual_y = actual_depth - (t * 2.0 % (10.0 / ROWS))
    
    # Recalculate Z based on actual scrolling Y
    Y2, X2 = np.meshgrid(actual_y.flatten() - (t * 20.0), x_offsets, indexing='ij')
    Z = np.sin(X2*1.5 + Y2*1.2) * 2.0 + np.cos(X2*3.0 - Y2*2.0) * 1.0 + np.sin(Y2*0.5) * 3.0
    Z = Z * highway_mask
    
    # Project
    # Depth is Y2. X is X2. Elevation is Z.
    # Camera is slightly above the ground
    cam_height = 2.0
    
    x_proj = cx + (X2 / actual_depth) * fov
    y_proj = cy + ((Z + cam_height) / actual_depth) * fov
    
    # Draw a massive glowing synthwave sun in the background
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    sun_y = py5.height * 0.3
    # Draw the sun in multiple transparent layers to make it glow
    for r in range(1500, 400, -100):
        py5.fill(255, py5.remap(r, 400, 1500, 150, 0), 0, 10)
        py5.circle(py5.width / 2, sun_y, r)
        
    # Draw the core of the sun
    py5.fill(255, 200, 0, 200)
    py5.circle(py5.width / 2, sun_y, 400)
    
    # Draw "scanlines" over the sun by drawing black rectangles
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 0, 20)
    for i in range(10):
        line_y = sun_y + 50 + (i * 30) - (t * 50 % 30)
        py5.rect(py5.width / 2 - 800, line_y, 1600, i * 4)

    py5.stroke_weight(3)
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    # Draw the terrain grid (horizontal lines)
    for y in range(ROWS - 1):
        # Color based on depth to create glowing grid effect, fade in distance
        c_intensity = py5.remap(actual_y[y, 0], 0.1, 10.0, 255, 0)
        if c_intensity < 0: c_intensity = 0
        py5.stroke(c_intensity, 0, 255, c_intensity)
        
        points = np.column_stack((x_proj[y], y_proj[y]))
        
        py5.begin_shape()
        py5.vertices(points)
        py5.end_shape()
        
    # Draw the terrain grid (vertical lines)
    for x in range(COLS):
        c_intensity = 150
        py5.stroke(c_intensity, 0, 255, c_intensity)
        
        points = np.column_stack((x_proj[:, x], y_proj[:, x]))
        py5.begin_shape()
        py5.vertices(points)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
