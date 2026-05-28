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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    # Use P3D to use the depth buffer trick for Voronoi
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global num_cells, cells
    num_cells = 80
    cells = []
    
    for i in range(num_cells):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        vx = py5.random(-2, 2)
        vy = py5.random(-2, 2)
        base_hue = py5.random(120, 280)
        cells.append({'x': x, 'y': y, 'vx': vx, 'vy': vy, 'hue': base_hue})

def draw():
    py5.background(10, 80, 10)
    
    # Orthographic projection for 2D look
    py5.ortho()
    
    # We draw a large cone for each cell. The depth buffer will automatically
    # draw the Voronoi boundaries where the cones intersect!
    py5.push_matrix()
    py5.translate(0, 0, -500)
    
    t = py5.frame_count * 0.02
    
    # Update and draw cells
    cone_radius = 1200
    cone_height = 800
    
    for i, cell in enumerate(cells):
        # Move cells
        cell['x'] += cell['vx'] * (1.0 + np.sin(t + i)*0.5)
        cell['y'] += cell['vy'] * (1.0 + np.cos(t + i)*0.5)
        
        # Wrap around
        if cell['x'] < -200: cell['x'] = py5.width + 200
        if cell['x'] > py5.width + 200: cell['x'] = -200
        if cell['y'] < -200: cell['y'] = py5.height + 200
        if cell['y'] > py5.height + 200: cell['y'] = -200
        
        # Pulsing color
        hue = (cell['hue'] + py5.frame_count * 0.5 + np.sin(t * 2 + i) * 20) % 360
        py5.fill(hue, 80, 80)
        
        py5.push_matrix()
        py5.translate(cell['x'], cell['y'], 0)
        
        # Draw a cone using triangle fan
        py5.begin_shape(py5.TRIANGLE_FAN)
        # Tip of the cone (closest to camera)
        py5.vertex(0, 0, cone_height)
        
        # Base of the cone
        num_segments = 32
        for s in range(num_segments + 1):
            theta = (s / num_segments) * py5.TWO_PI
            cx = py5.cos(theta) * cone_radius
            cy = py5.sin(theta) * cone_radius
            py5.vertex(cx, cy, 0)
            
        py5.end_shape()
        py5.pop_matrix()
        
    py5.pop_matrix()
    
    # Draw "nuclei" as spheres
    py5.push_matrix()
    py5.translate(0, 0, 350)
    for i, cell in enumerate(cells):
        py5.push_matrix()
        py5.translate(cell['x'], cell['y'], 0)
        py5.fill((cell['hue'] + 180) % 360, 90, 100)
        
        n_size = 15 + np.sin(t * 3 + i) * 5
        py5.sphere(n_size)
        py5.pop_matrix()
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
