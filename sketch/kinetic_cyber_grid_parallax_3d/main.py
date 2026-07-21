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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    global objects
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    objects = []
    for _ in range(250):
        objects.append({
            'x': random.uniform(-4000, 4000),
            'y': random.uniform(-2000, -200),
            'z': random.uniform(10, 6000),
            'size': random.uniform(50, 300),
            'type': random.choice(['rect', 'circle', 'triangle'])
        })

def project(x, y, z):
    # Simple perspective projection
    fov = 800.0
    if z < 1.0: z = 1.0
    scale = fov / z
    px = x * scale + SIZE[0] / 2
    py = y * scale + SIZE[1] / 2 + 500 # offset camera height
    return px, py, scale

def draw():
    py5.background(10, 0, 20) # Deep dark purple
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    speed = 800
    grid_size = 400
    z_offset = (t * speed) % grid_size
    
    # Infinite Floor Grid
    py5.stroke(0, 255, 255) # Neon cyan
    py5.stroke_weight(2)
    
    extent = 10000
    
    # Draw horizontal lines moving forward
    for z in range(10, 6000, grid_size):
        curr_z = z - z_offset
        if curr_z < 10: continue
        
        alpha = py5.remap(curr_z, 10, 6000, 255, 0)
        py5.stroke(0, 255, 255, alpha)
        
        x1, y1, _ = project(-extent, 0, curr_z)
        x2, y2, _ = project(extent, 0, curr_z)
        py5.line(x1, y1, x2, y2)
        
    # Draw vertical lines receding into distance
    for x in range(-extent, extent, grid_size):
        x1, y1, _ = project(x, 0, 10)
        x2, y2, _ = project(x, 0, 6000)
        
        # Simple line, fading requires multiple segments
        for seg_z in range(10, 6000, 500):
            sz1 = seg_z
            sz2 = seg_z + 500
            
            px1, py1, _ = project(x, 0, sz1)
            px2, py2, _ = project(x, 0, sz2)
            
            alpha = py5.remap(sz1, 10, 6000, 255, 0)
            py5.stroke(0, 255, 255, alpha)
            py5.line(px1, py1, px2, py2)
            
    # Draw floating data structures
    py5.no_fill()
    py5.stroke_weight(4)
    
    for obj in objects:
        curr_z = obj['z'] - t * speed * 1.5 # structures move towards camera
        
        # wrap around
        while curr_z < 10: curr_z += 6000
        while curr_z > 6000: curr_z -= 6000
        
        alpha = py5.remap(curr_z, 10, 6000, 255, 0)
        
        px, py, scale = project(obj['x'], obj['y'], curr_z)
        s = obj['size'] * scale
        
        if obj['type'] == 'rect':
            py5.stroke(255, 0, 255, alpha) # Magenta
            py5.rect_mode(py5.CENTER)
            py5.rect(px, py, s, s)
            py5.rect(px, py, s*0.8, s*0.8)
        elif obj['type'] == 'circle':
            py5.stroke(255, 255, 0, alpha) # Yellow
            py5.ellipse(px, py, s, s)
        elif obj['type'] == 'triangle':
            py5.stroke(0, 255, 100, alpha) # Green
            py5.triangle(px, py - s/2, px - s/2, py + s/2, px + s/2, py + s/2)

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
        import os
        os._exit(0)

py5.run_sketch()
