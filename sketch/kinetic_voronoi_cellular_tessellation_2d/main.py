from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
from scipy.spatial import Voronoi
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

NUM_SEEDS = 400

seeds = None
noise_offsets = None

def setup():
    global seeds, noise_offsets
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 15, 25)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize base positions and noise offsets for organic movement
    seeds = np.random.rand(NUM_SEEDS, 2) * [SIZE[0], SIZE[1]]
    noise_offsets = np.random.rand(NUM_SEEDS, 2) * 1000.0

def draw():
    py5.background(10, 15, 25)
    
    t = py5.frame_count * 0.003
    W, H = SIZE[0], SIZE[1]
    
    current_seeds = np.zeros_like(seeds)
    for i in range(NUM_SEEDS):
        nx = noise_offsets[i, 0] + t
        ny = noise_offsets[i, 1] + t
        
        # Calculate large organic drift using Perlin noise
        dx = (py5.os_noise(nx, ny, t) - 0.5) * W * 0.4
        dy = (py5.os_noise(nx + 100, ny + 100, t) - 0.5) * H * 0.4
        
        # Clamp to bounds to prevent seeds from wandering entirely off-screen
        current_seeds[i, 0] = np.clip(seeds[i, 0] + dx, 0, W)
        current_seeds[i, 1] = np.clip(seeds[i, 1] + dy, 0, H)
        
    # Generate mirror points to ensure the Voronoi cells are perfectly bounded by the screen edges
    pts_l = current_seeds.copy()
    pts_l[:, 0] = -pts_l[:, 0]
    
    pts_r = current_seeds.copy()
    pts_r[:, 0] = 2 * W - pts_r[:, 0]
    
    pts_t = current_seeds.copy()
    pts_t[:, 1] = -pts_t[:, 1]
    
    pts_b = current_seeds.copy()
    pts_b[:, 1] = 2 * H - pts_b[:, 1]
    
    # Combine all points and compute Voronoi
    all_pts = np.vstack([current_seeds, pts_l, pts_r, pts_t, pts_b])
    
    try:
        vor = Voronoi(all_pts)
    except Exception as e:
        print(f"[Warning] Voronoi computation failed on frame {py5.frame_count}: {e}")
        # If Qhull fails due to collinearity or precision, just save the previous frame
        py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
        return

    py5.stroke_weight(2.5)
    
    # We only draw the cells corresponding to the original points (indices 0 to NUM_SEEDS-1)
    for i in range(NUM_SEEDS):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        
        if -1 in region or len(region) == 0:
            continue
            
        polygon = vor.vertices[region]
        
        # Iridescent / soap bubble palette based on position
        cx, cy = current_seeds[i]
        
        # Color mapping creates shimmering pastel gradients
        r = py5.remap(np.sin(cx * 0.002 + t * 5), -1, 1, 100, 255)
        g = py5.remap(np.sin(cy * 0.003 + t * 4), -1, 1, 150, 255)
        b = py5.remap(np.cos((cx + cy) * 0.002 + t * 3), -1, 1, 200, 255)
        
        # Fill with a very subtle translucent glow
        py5.fill(r, g, b, 120)
        
        # Borders are bright and sharp
        py5.stroke(r, g, b, 255)
        
        py5.begin_shape()
        for p in polygon:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
        
        # Draw the seed point (nucleus)
        py5.no_stroke()
        py5.fill(255, 255, 255, 200)
        py5.circle(cx, cy, 6)
        
        # Restore stroke for the next polygon
        py5.stroke_weight(2.5)

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
