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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 15000
pos = np.random.rand(NUM_PARTICLES, 2).astype(np.float32)
pos[:, 0] *= SIZE[0]
pos[:, 1] *= SIZE[1]

# Give each particle a base color property
hues = np.random.uniform(280, 340, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(15, 10, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    py5.no_fill()

def draw():
    global pos
    
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(15, 10, 10, 8)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.003
    noise_scale = 0.0015
    eps = 1.0
    
    # Compute gradients using py5.noise
    # py5.noise is not vectorized, but we can use list comprehension or a loop.
    # For 15,000 particles, doing it in Python might take a few milliseconds, which is fine for rendering.
    
    # We will compute multiple steps per frame to get longer trails
    steps = 3
    dt = 2.0
    
    for _ in range(steps):
        # We need dx and dy of the noise field
        # We can't easily vectorize py5.os_noise. Let's do it with a loop or list comp
        
        # To make it fast, we can use a small trick: 
        # Calculate noise manually using a simple vectorized 2D noise, or just bear with the loop.
        # Actually, numpy can't do py5.noise directly. But we can write a simple vectorized hash or just use loop.
        # 15,000 calls to py5.noise * 4 = 60,000 calls. In Python, that might take ~20-50ms.
        
        # A fast way to approximate gradient without calling noise 4 times per particle:
        # We can precompute a noise grid for the screen and use map_coordinates or just integer indexing!
        pass
    
    # Precompute noise grid for fast gradient lookup
    grid_res = 10
    cols = py5.width // grid_res + 2
    rows = py5.height // grid_res + 2
    
    # We only need to generate the noise grid once per frame
    noise_grid = np.zeros((rows, cols), dtype=np.float32)
    for r in range(rows):
        for c in range(cols):
            noise_grid[r, c] = py5.noise(c * grid_res * noise_scale, r * grid_res * noise_scale, time_val)
            
    # Compute gradients of the grid
    dy, dx = np.gradient(noise_grid)
    
    for _ in range(steps):
        # Map particle positions to grid indices
        c_idx = (pos[:, 0] / grid_res).astype(np.int32)
        r_idx = (pos[:, 1] / grid_res).astype(np.int32)
        
        # Bound indices
        c_idx = np.clip(c_idx, 0, cols - 1)
        r_idx = np.clip(r_idx, 0, rows - 1)
        
        # Get gradient
        grad_x = dx[r_idx, c_idx]
        grad_y = dy[r_idx, c_idx]
        
        # Vector perpendicular to gradient traces the contour line: (-grad_y, grad_x)
        vx = -grad_y
        vy = grad_x
        
        # Normalize velocity
        v_mag = np.sqrt(vx**2 + vy**2) + 0.0001
        vx = (vx / v_mag) * dt
        vy = (vy / v_mag) * dt
        
        # Add a tiny bit of inward spiral to make them cluster on peaks/valleys optionally,
        # but pure contour is perfectly perpendicular.
        
        new_x = pos[:, 0] + vx
        new_y = pos[:, 1] + vy
        
        # Wrap around screen
        new_x = new_x % py5.width
        new_y = new_y % py5.height
        
        # Drawing
        # We can draw lines from pos to new_pos
        # To avoid drawing long lines across the screen when wrapping, we filter
        dist_sq = (new_x - pos[:, 0])**2 + (new_y - pos[:, 1])**2
        valid = dist_sq < 100.0
        
        # Since we can't easily draw 15,000 lines with varying colors efficiently using Py5Shape without 
        # rebuilding it, we can just use points, or py5.lines(pts) if available, or just a loop.
        # A loop of 15,000 is perfectly fine for an offline renderer.
        py5.stroke_weight(2)
        for i in range(NUM_PARTICLES):
            if valid[i]:
                # Color shifts based on local noise value to highlight contours
                local_noise = noise_grid[r_idx[i], c_idx[i]]
                # 280 (purple) to 340 (pink) + noise mapping
                hue = (hues[i] + local_noise * 100 + time_val * 20) % 360
                
                # Speed based brightness
                py5.stroke(hue, 80, 90, 40)
                py5.line(pos[i, 0], pos[i, 1], new_x[i], new_y[i])
                
        pos[:, 0] = new_x
        pos[:, 1] = new_y

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
