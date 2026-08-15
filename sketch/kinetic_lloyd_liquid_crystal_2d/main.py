from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import cv2
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Simulation Grid (downscaled for speed, upscaled for rendering)
GRID_W = 160
GRID_H = 90

# Seed points for Voronoi cells
N = 100
pos = np.zeros((N, 2), dtype=np.float32)
# Initialize random positions within simulation space
pos[:, 0] = np.random.rand(N) * GRID_W
pos[:, 1] = np.random.rand(N) * GRID_H

# Cell colors: HSB
colors = np.zeros((N, 3), dtype=np.float32)
for i in range(N):
    # Gradient of Hues (Teal to Violet to Accent Amber)
    colors[i] = [170.0 + np.random.rand() * 100.0, 85.0, 90.0]

# Telemetry: Entropy history
entropy_history = []
img_rgb_mid = None


def get_fluid_velocity(p, t):
    """
    Computes a vector field with two rotating vortex centers.
    """
    x = p[:, 0]
    y = p[:, 1]
    
    # Vortex 1: rotating clockwise
    v1_x = GRID_W * (0.3 + 0.1 * np.sin(t * 0.5))
    v1_y = GRID_H * (0.5 + 0.15 * np.cos(t * 0.5))
    
    # Vortex 2: rotating counter-clockwise
    v2_x = GRID_W * (0.7 - 0.1 * np.cos(t * 0.5))
    v2_y = GRID_H * (0.5 - 0.15 * np.sin(t * 0.5))
    
    # Vectors to vortex centers
    dx1, dy1 = x - v1_x, y - v1_y
    r1_sq = dx1**2 + dy1**2 + 10.0
    
    dx2, dy2 = x - v2_x, y - v2_y
    r2_sq = dx2**2 + dy2**2 + 10.0
    
    # Vortex velocities (tangential)
    vx = -dy1 / r1_sq * 18.0 + dy2 / r2_sq * 18.0
    vy =  dx1 / r1_sq * 18.0 - dx2 / r2_sq * 18.0
    
    # Thermal wind drift
    vx += 0.15 * np.sin(y * 0.1 + t)
    
    return np.stack([vx, vy], axis=-1)


def compute_voronoi_and_lloyd():
    """
    Calculates cell assignments on the grid and returns the centroid coordinates
    for Lloyd's relaxation.
    """
    global pos
    
    # Grid coordinate maps
    y_indices, x_indices = np.indices((GRID_H, GRID_W), dtype=np.float32)
    # Shape: (GRID_H, GRID_W, 2)
    grid_coords = np.stack([x_indices, y_indices], axis=-1)
    
    # Compute distance squared from every grid point to all N seeds
    # Shape: (GRID_H, GRID_W, N)
    diff = grid_coords[:, :, None, :] - pos[None, None, :, :]
    dist_sq = np.sum(diff ** 2, axis=-1)
    
    # Closest seed index for each pixel
    # Shape: (GRID_H, GRID_W)
    assignments = np.argmin(dist_sq, axis=-1)
    
    # Calculate centroids of assigned cells for Lloyd's relaxation
    centroids = np.copy(pos)
    counts = np.zeros(N)
    
    # Vectorized centroid accumulation
    for i in range(N):
        mask = (assignments == i)
        counts[i] = np.sum(mask)
        if counts[i] > 0:
            centroids[i, 0] = np.mean(grid_coords[mask, 0])
            centroids[i, 1] = np.mean(grid_coords[mask, 1])
            
    # Calculate cell size entropy (regularity indicator)
    non_zero_counts = counts[counts > 0]
    probs = non_zero_counts / np.sum(non_zero_counts)
    entropy = -np.sum(probs * np.log(probs))
    
    return assignments, centroids, entropy


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(3, 3, 8)


def draw():
    global pos, img_rgb_mid
    
    t = py5.frame_count / 60.0
    
    # --- 1. Physics: Fluid Advection + Lloyd's centroid relaxation ---
    assignments, centroids, entropy = compute_voronoi_and_lloyd()
    entropy_history.append(entropy)
    if len(entropy_history) > 300:
        entropy_history.pop(0)
        
    # Seed dynamics: Move toward centroids (Lloyd's step) + advected by fluid velocity
    v_fluid = get_fluid_velocity(pos, t)
    
    # Lloyd's relaxation parameter (0.0 = pure advection, 1.0 = pure relaxation)
    lloyd_rate = 0.08
    pos = pos + (centroids - pos) * lloyd_rate + v_fluid * 0.7
    
    # Contain seeds inside grid boundary
    pos[:, 0] = np.clip(pos[:, 0], 1.0, GRID_W - 2.0)
    pos[:, 1] = np.clip(pos[:, 1], 1.0, GRID_H - 2.0)
    
    # --- 2. Rendering the Voronoi Grid ---
    # We construct a low-res image representation of assignments, then upscale
    img_cells = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
    
    # Convert cell HSB colors to BGR for assignment image
    bgr_colors = []
    for i in range(N):
        h, s, b = colors[i]
        # Slowly modulate hue over time
        h_mod = (h + t * 4.0) % 360.0
        # HSB to RGB color conversion via OpenCV
        hsb_pixel = np.array([[[h_mod / 2.0, s * 2.55, b * 2.55]]], dtype=np.uint8)
        rgb_pixel = cv2.cvtColor(hsb_pixel, cv2.COLOR_HSV2RGB)
        bgr_colors.append(rgb_pixel[0, 0])
        
    # Paint pixels based on cell assignment
    for i in range(N):
        img_cells[assignments == i] = bgr_colors[i]
        
    # Extract cell boundaries using Sobel/Laplacian gradient filter
    gray_cells = cv2.cvtColor(img_cells, cv2.COLOR_RGB2GRAY)
    edges = cv2.Laplacian(gray_cells, cv2.CV_8U, ksize=3)
    
    # Apply glowing overlay onto cell image
    img_cells[edges > 20] = [255, 255, 255]  # White cell walls
    
    # Upscale the low-res assignment image to 4K resolution using bilinear filtering
    img_cells_4k = cv2.resize(img_cells, SIZE, interpolation=cv2.INTER_LINEAR)
    
    # Paint output to py5 canvas
    py5.load_np_pixels()
    py5.np_pixels[:, :, :3] = img_cells_4k
    py5.update_np_pixels()
    
    # --- 3. Telemetry HUD ---
    # Dynamic HUD overlay (4K text)
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("LIQUID CRYSTAL COALESCENCE // WARPED LLOYD'S RELAXATION", 50, 50)
    py5.text(f"VORONOI CELLS: {N} | RESOLUTION: 3840 x 2160 (4K)", 50, 85)
    py5.text(f"RELAXATION RATE: {lloyd_rate:.2f} | ENTROPY COEFFICIENT: {entropy:.4f}", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"SYSTEM THERMAL MIXING: {np.mean(np.linalg.norm(v_fluid, axis=1)):.3f} m/s", SIZE[0] - 50, 85)
    
    # Entropy Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("VORONOI CELL SIZE ENTROPY", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(0, 238, 221, 180)
    py5.begin_shape()
    for idx, val in enumerate(entropy_history):
        xx = gx + idx * (graph_w / 300)
        # Scale entropy to fit graph (entropy is around log(N) ~ 4.6)
        yy = gy + graph_h - (val / 5.0) * (graph_h - 10) - 5
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Blank screen check
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
        
        # Save preview mid-frame (grab from screen buffer)
        py5.load_np_pixels()
        img_rgb_mid = py5.np_pixels[:, :, :3].copy()
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
