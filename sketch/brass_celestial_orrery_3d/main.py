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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def draw_gear(radius, teeth, depth):
    inner_r = radius * 0.8
    outer_r = radius * 1.05
    
    py5.begin_shape(py5.TRIANGLE_STRIP)
    for i in range(teeth * 2 + 1):
        angle = i * py5.PI / teeth
        
        # Alternate between inner and outer radius for teeth
        r = outer_r if i % 2 == 0 else inner_r
        
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        
        py5.vertex(x, y, -depth/2)
        py5.vertex(x, y, depth/2)
    py5.end_shape()

def draw_ring(radius, thickness, depth):
    py5.begin_shape(py5.QUAD_STRIP)
    res = 60
    for i in range(res + 1):
        angle = i * py5.TWO_PI / res
        x1 = radius * np.cos(angle)
        y1 = radius * np.sin(angle)
        x2 = (radius + thickness) * np.cos(angle)
        y2 = (radius + thickness) * np.sin(angle)
        
        py5.vertex(x1, y1, 0)
        py5.vertex(x2, y2, 0)
    py5.end_shape()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
def draw():
    py5.background(15, 5, 10) # Velvety Burgundy/Black
    
    py5.ambient_light(60, 50, 40)
    py5.directional_light(255, 230, 180, 1, 1, -1) # Warm brass light
    py5.directional_light(150, 100, 80, -1, -0.5, 0.5) # Copper fill light
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.01
    
    # Global rotation
    py5.rotate_x(py5.PI / 3 + np.sin(t * 0.5) * 0.1)
    py5.rotate_z(py5.frame_count * 0.005)
    
    # Central object (Lapis Lazuli)
    py5.push_matrix()
    py5.fill(30, 80, 180) # Lapis Blue
    py5.rotate_y(t * 2)
    py5.sphere(80)
    py5.pop_matrix()
    
    # Nested rings and gears
    num_rings = 5
    for i in range(num_rings):
        py5.push_matrix()
        
        radius = 150 + i * 80
        speed = 0.02 * (num_rings - i) * (-1 if i % 2 == 0 else 1)
        
        # Inclination
        py5.rotate_x(i * py5.PI / 8)
        py5.rotate_y(i * py5.PI / 6)
        
        py5.rotate_z(py5.frame_count * speed)
        
        # Material alternating Brass and Copper
        if i % 2 == 0:
            py5.fill(218, 165, 32) # Polished Brass
            draw_ring(radius, 15, 5)
            # Add a planetary sphere on the ring
            py5.push_matrix()
            py5.translate(radius + 7.5, 0, 0)
            py5.fill(184, 115, 51) # Bronze/Copper planet
            py5.sphere(25)
            py5.pop_matrix()
        else:
            py5.fill(184, 115, 51) # Tarnished Copper
            draw_gear(radius, 40 + i * 10, 10)
            
        py5.pop_matrix()
        
    # Outer cage
    py5.push_matrix()
    py5.rotate_x(t * 0.5)
    py5.rotate_y(t * 0.7)
    py5.no_fill()
    py5.stroke(218, 165, 32, 100) # Brass wireframe
    py5.stroke_weight(2)
    py5.sphere(600)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
