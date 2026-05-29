from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from collections import deque

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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid_size, grid_a, grid_b, next_a, next_b, history, history_len
    grid_size = 120
    
    # Initialize A to 1, B to 0
    grid_a = np.ones((grid_size, grid_size), dtype=np.float32)
    grid_b = np.zeros((grid_size, grid_size), dtype=np.float32)
    
    # Seed B in center
    cx, cy = grid_size // 2, grid_size // 2
    r = 10
    grid_b[cx-r:cx+r, cy-r:cy+r] = 1.0
    
    next_a = np.zeros((grid_size, grid_size), dtype=np.float32)
    next_b = np.zeros((grid_size, grid_size), dtype=np.float32)
    
    history_len = 60
    history = deque(maxlen=history_len)

def update_rd():
    global grid_a, grid_b, next_a, next_b
    
    # Gray-Scott parameters
    dA = 1.0
    dB = 0.5
    f = 0.055
    k = 0.062
    
    # Pre-calculate laplacians
    # 3x3 convolution
    # [0.05, 0.2, 0.05]
    # [0.2, -1.0, 0.2]
    # [0.05, 0.2, 0.05]
    
    # Shift arrays for fast neighbor access
    a_up = np.roll(grid_a, -1, axis=0)
    a_down = np.roll(grid_a, 1, axis=0)
    a_left = np.roll(grid_a, -1, axis=1)
    a_right = np.roll(grid_a, 1, axis=1)
    
    a_up_left = np.roll(a_up, -1, axis=1)
    a_up_right = np.roll(a_up, 1, axis=1)
    a_down_left = np.roll(a_down, -1, axis=1)
    a_down_right = np.roll(a_down, 1, axis=1)
    
    lap_a = (a_up + a_down + a_left + a_right) * 0.2 + \
            (a_up_left + a_up_right + a_down_left + a_down_right) * 0.05 - \
            grid_a * 1.0
            
    b_up = np.roll(grid_b, -1, axis=0)
    b_down = np.roll(grid_b, 1, axis=0)
    b_left = np.roll(grid_b, -1, axis=1)
    b_right = np.roll(grid_b, 1, axis=1)
    
    b_up_left = np.roll(b_up, -1, axis=1)
    b_up_right = np.roll(b_up, 1, axis=1)
    b_down_left = np.roll(b_down, -1, axis=1)
    b_down_right = np.roll(b_down, 1, axis=1)
    
    lap_b = (b_up + b_down + b_left + b_right) * 0.2 + \
            (b_up_left + b_up_right + b_down_left + b_down_right) * 0.05 - \
            grid_b * 1.0
            
    ab2 = grid_a * grid_b * grid_b
    
    # Slowly vary f and k over time
    t = py5.frame_count * 0.01
    dyn_f = f + np.sin(t) * 0.01
    dyn_k = k + np.cos(t * 0.8) * 0.005
    
    next_a = grid_a + (dA * lap_a - ab2 + dyn_f * (1.0 - grid_a))
    next_b = grid_b + (dB * lap_b + ab2 - (dyn_k + dyn_f) * grid_b)
    
    next_a = np.clip(next_a, 0.0, 1.0)
    next_b = np.clip(next_b, 0.0, 1.0)
    
    grid_a[:] = next_a
    grid_b[:] = next_b

def draw():
    # Run multiple steps per frame to speed up simulation
    for _ in range(8):
        update_rd()
        
    history.appendleft(grid_b.copy())
    
    py5.blend_mode(py5.BLEND)
    py5.background(10, 80, 5)
    py5.blend_mode(py5.ADD)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    t = py5.frame_count * 0.01
    
    # Rotate scene
    py5.rotate_x(1.2 + np.sin(t * 0.5) * 0.2)
    py5.rotate_z(t * 0.2)
    
    cell_size = 18
    
    py5.translate(-grid_size * cell_size / 2, -grid_size * cell_size / 2, 0)
    
    py5.no_stroke()
    
    # Draw history slices
    for z_idx, past_b in enumerate(history):
        z_offset = z_idx * 15
        
        alpha_scale = (history_len - z_idx) / history_len
        
        # We only draw points where B is high
        y_coords, x_coords = np.where(past_b > 0.2)
        
        if len(x_coords) == 0:
            continue
            
        py5.begin_shape(py5.POINTS)
        py5.stroke_weight(4)
        for i in range(len(x_coords)):
            x = x_coords[i]
            y = y_coords[i]
            val = past_b[y, x]
            
            hue = (280 + val * 100 + z_idx * 2 + t * 50) % 360
            alpha = py5.remap(val, 0.2, 1.0, 0, 80) * alpha_scale
            
            py5.stroke(hue, 90, 100, alpha)
            py5.vertex(x * cell_size, y * cell_size, z_offset)
            
        py5.end_shape()
        
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
