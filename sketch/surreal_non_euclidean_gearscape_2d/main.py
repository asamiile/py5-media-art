from pathlib import Path
import shutil
import subprocess
import sys
import random
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

gears = []

class Gear:
    def __init__(self, x, y, r, teeth, speed, start_angle, color):
        self.x = x
        self.y = y
        self.r = r
        self.teeth = teeth
        self.speed = speed
        self.start_angle = start_angle
        self.color = color

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate some interlocking gears in a grid-like or loose structure
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Center gear
    gears.append(Gear(SIZE[0]/2, SIZE[1]/2, 300, 24, 0.01, 0, (300, 80, 100, 80)))
    
    # Create satellite gears
    for i in range(8):
        angle = i * (py5.TWO_PI / 8)
        dist = 500
        gx = SIZE[0]/2 + py5.cos(angle) * dist
        gy = SIZE[1]/2 + py5.sin(angle) * dist
        gears.append(Gear(gx, gy, 200, 16, -0.015, angle, (240, 80, 100, 80)))
        
        # Second layer
        gx2 = gx + py5.cos(angle) * 350
        gy2 = gy + py5.sin(angle) * 350
        gears.append(Gear(gx2, gy2, 150, 12, 0.02, angle*2, (330, 80, 100, 80)))

def warp_point(x, y, tx, ty):
    # Non-euclidean domain warping based on time
    dx = x - SIZE[0]/2
    dy = y - SIZE[1]/2
    dist = py5.sqrt(dx*dx + dy*dy)
    
    # Warping power based on noise and time
    noise_val = py5.os_noise(x * 0.002, y * 0.002, ty)
    warp_amount = py5.sin(dist * 0.005 - tx) * 150 * noise_val
    
    angle = py5.atan2(dy, dx)
    wx = x + py5.cos(angle) * warp_amount
    wy = y + py5.sin(angle) * warp_amount
    return wx, wy

def draw():
    py5.background(20, 100, 10) # Deep dark indigo
    py5.blend_mode(py5.ADD)
    
    tx = py5.frame_count * 0.05
    ty = py5.frame_count * 0.01
    
    py5.stroke_weight(4)
    
    for g in gears:
        py5.fill(*g.color)
        py5.stroke(g.color[0], 50, 100, 100)
        
        rotation = g.start_angle + py5.frame_count * g.speed
        
        py5.begin_shape()
        num_points = g.teeth * 4
        for i in range(num_points):
            theta = i * (py5.TWO_PI / num_points)
            # Alternate radius for teeth
            inner_r = g.r * 0.8
            outer_r = g.r
            
            # Simple square wave for teeth
            mod = i % 4
            if mod == 0 or mod == 1:
                cr = outer_r
            else:
                cr = inner_r
                
            # Point on the unwarped gear
            px = g.x + py5.cos(theta + rotation) * cr
            py = g.y + py5.sin(theta + rotation) * cr
            
            wx, wy = warp_point(px, py, tx, ty)
            py5.vertex(wx, wy)
            
        py5.end_shape(py5.CLOSE)
        
        # Inner hole
        py5.fill(20, 100, 10, 100)
        py5.begin_shape()
        for i in range(32):
            theta = i * (py5.TWO_PI / 32)
            cr = g.r * 0.3
            px = g.x + py5.cos(theta + rotation) * cr
            py = g.y + py5.sin(theta + rotation) * cr
            wx, wy = warp_point(px, py, tx, ty)
            py5.vertex(wx, wy)
        py5.end_shape(py5.CLOSE)
        

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
