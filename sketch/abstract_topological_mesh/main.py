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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

COLS = 100
ROWS = 100
SPACING = 15
OFFSET_X = (COLS * SPACING) / 2
OFFSET_Y = (ROWS * SPACING) / 2

# Pre-calculate normalized coordinates for mathematical functions
u_vals = np.linspace(-py5.PI, py5.PI, COLS)
v_vals = np.linspace(-py5.PI, py5.PI, ROWS)
U, V = np.meshgrid(u_vals, v_vals)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5)
    
    t = py5.frame_count * 0.02
    
    # Lighting setup for glossy topological look
    py5.ambient_light(50, 50, 50)
    py5.point_light(0, 0, 100, 0, -500, 200)
    py5.directional_light(220, 80, 80, 1, 1, -1)
    
    # Material properties
    py5.specular(255, 255, 255)
    py5.shininess(50)
    py5.ambient(150, 150, 150)
    
    py5.translate(py5.width / 2, py5.height / 2 + 100, -200)
    
    # Slow orbital rotation
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.2)
    
    py5.no_stroke()
    
    # Mathematical function: mix of hyperbolic paraboloid, ripples, and noise
    # Z = sin(U * a) * cos(V * b) * R + noise
    # The parameters slowly shift over time
    
    freq_u = 2.0 + py5.sin(t * 0.5)
    freq_v = 2.0 + py5.cos(t * 0.3)
    
    Z = np.sin(U * freq_u + t) * np.cos(V * freq_v + t) * 150.0
    
    # Add a global saddle bend
    saddle = (U**2 - V**2) * 20.0
    Z += saddle
    
    # Draw the mesh using TRIANGLE_STRIP for performance
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Vertex 1 (Top row of strip)
            px1 = x * SPACING - OFFSET_X
            py1 = y * SPACING - OFFSET_Y
            pz1 = Z[y, x]
            
            # Map color based on Z height
            hue1 = (py5.remap(pz1, -200, 200, 180, 320) + t * 20) % 360
            py5.fill(hue1, 90, 100)
            py5.vertex(px1, py1, pz1)
            
            # Vertex 2 (Bottom row of strip)
            px2 = x * SPACING - OFFSET_X
            py2 = (y + 1) * SPACING - OFFSET_Y
            pz2 = Z[y + 1, x]
            
            hue2 = (py5.remap(pz2, -200, 200, 180, 320) + t * 20) % 360
            py5.fill(hue2, 90, 100)
            py5.vertex(px2, py2, pz2)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
