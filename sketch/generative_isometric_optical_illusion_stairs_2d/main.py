from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_SIZE = 25
W = 80 # width of a block
H = 40 # height of a block in isometric (W/2)
D = 300 # max depth of a block

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 10, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)

def draw_block(x, y, z, light_dir):
    # Base 2D coordinates for an isometric grid
    px = (x - y) * W / 2.0
    py_c = (x + y) * H / 2.0
    
    # Vertices of the top face
    t0 = (px, py_c - z)
    t1 = (px + W/2, py_c + H/2 - z)
    t2 = (px, py_c + H - z)
    t3 = (px - W/2, py_c + H/2 - z)
    
    # Vertices of the bottom face
    b0 = (px, py_c)
    b1 = (px + W/2, py_c + H/2)
    b2 = (px, py_c + H)
    b3 = (px - W/2, py_c + H/2)

    # Normals (pseudo, simplified for shading)
    n_top = np.array([0, 0, 1])
    n_right = np.array([1, 0, 0])
    n_left = np.array([0, -1, 0])
    
    def calc_shade(n):
        # dot product with light dir
        val = np.dot(n, light_dir)
        # map from [-1, 1] to [0.3, 1.0]
        return py5.remap(val, -1, 1, 0.2, 1.0)
    
    py5.stroke(20)
    py5.stroke_weight(1.5)
    
    # Draw left face (t3, t2, b2, b3)
    s_left = calc_shade(n_left)
    py5.fill(220 * s_left)
    py5.quad(t3[0], t3[1], t2[0], t2[1], b2[0], b2[1], b3[0], b3[1])
    
    # Draw right face (t1, t2, b2, b1)
    s_right = calc_shade(n_right)
    py5.fill(220 * s_right)
    py5.quad(t1[0], t1[1], t2[0], t2[1], b2[0], b2[1], b1[0], b1[1])
    
    # Draw top face (t0, t1, t2, t3)
    s_top = calc_shade(n_top)
    py5.fill(220 * s_top)
    py5.quad(t0[0], t0[1], t1[0], t1[1], t2[0], t2[1], t3[0], t3[1])

def draw():
    py5.background(10, 10, 10)
    
    t = py5.frame_count * 0.02
    
    # Rotating light direction
    lx = np.cos(t * 0.5)
    ly = np.sin(t * 0.5)
    lz = 1.0 # Light comes from slightly above
    light_dir = np.array([lx, ly, lz])
    light_dir = light_dir / np.linalg.norm(light_dir)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2 - 200)
    
    # Build list of blocks so we can sort them by draw order
    # x + y is depth in isometric
    blocks = []
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            # Complex wave logic
            wave = np.sin((x + y) * 0.3 - t * 2.0) * np.cos((x - y) * 0.2)
            noise = py5.os_noise(x * 0.1, y * 0.1, t * 0.5) - 0.5
            
            # The height Z
            z = (wave * 0.5 + noise * 0.5) * D + D
            
            # Distance from center for radial falloff
            cx = x - GRID_SIZE/2
            cy = y - GRID_SIZE/2
            dist = np.sqrt(cx*cx + cy*cy)
            
            if dist < GRID_SIZE / 2:
                # scale z down at edges
                falloff = 1.0 - (dist / (GRID_SIZE/2))
                z *= falloff
                
                # Add to list
                blocks.append({'x': x - GRID_SIZE/2, 'y': y - GRID_SIZE/2, 'z': z, 'order': x + y})
                
    # Sort blocks: draw back-to-front
    blocks.sort(key=lambda b: b['order'])
    
    for b in blocks:
        draw_block(b['x'], b['y'], b['z'], light_dir)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
