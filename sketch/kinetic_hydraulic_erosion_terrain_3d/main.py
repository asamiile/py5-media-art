from pathlib import Path
import random
import shutil
import subprocess
import sys
import math
import numpy as np
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
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Simulation grid parameters (Must be power of 2 for Diamond-Square)
GRID = 128

# Hydraulic erosion parameters
N_DROPS = 500  # Droplets simulated per frame
MAX_STEPS = 40
INERTIA = 0.08
CAPACITY = 3.5
DEPOSITION = 0.12
EROSION = 0.25
EVAPORATION = 0.025
MIN_SLOPE = 0.002

# Projection settings
SPACING = 15.5
MAX_HEIGHT = 450.0

# Global state arrays
h = np.zeros((GRID, GRID), dtype=np.float32)
deposit = np.zeros((GRID, GRID), dtype=np.float32)

def generate_diamond_square(roughness=0.55):
    """Generate heightmap via the Diamond-Square algorithm."""
    global h
    n = GRID
    size = n + 1
    temp_h = np.zeros((size, size), dtype=np.float32)
    temp_h[0, 0] = temp_h[0, -1] = temp_h[-1, 0] = temp_h[-1, -1] = random.uniform(0.3, 0.7)

    step = n
    scale = roughness
    while step > 1:
        half = step // 2

        # Diamond step
        for r in range(0, n, step):
            for c in range(0, n, step):
                avg = (temp_h[r, c] + temp_h[r + step, c] + temp_h[r, c + step] + temp_h[r + step, c + step]) / 4.0
                temp_h[r + half, c + half] = avg + random.uniform(-1, 1) * scale

        # Square step
        for r in range(0, n + 1, half):
            for c in range((r + half) % step, n + 1, step):
                neighbors = []
                if r - half >= 0:
                    neighbors.append(temp_h[r - half, c])
                if r + half < size:
                    neighbors.append(temp_h[r + half, c])
                if c - half >= 0:
                    neighbors.append(temp_h[r, c - half])
                if c + half < size:
                    neighbors.append(temp_h[r, c + half])
                temp_h[r, c] = np.mean(neighbors) + random.uniform(-1, 1) * scale

        step = half
        scale *= roughness

    # Normalize to [0, 1] and copy to h
    temp_h = (temp_h - temp_h.min()) / (temp_h.max() - temp_h.min() + 1e-9)
    h[:] = temp_h[:n, :n]

def get_gradient_and_height(r, c):
    """Compute gradient and height at grid position (r, c) using bilinear interpolation."""
    ri, ci = int(r), int(c)
    ri = max(0, min(ri, GRID - 2))
    ci = max(0, min(ci, GRID - 2))
    fr, fc = r - ri, c - ci

    h00 = h[ri, ci]
    h10 = h[ri + 1, ci]
    h01 = h[ri, ci + 1]
    h11 = h[ri + 1, ci + 1]

    # Bilinear height
    height = h00 * (1 - fr) * (1 - fc) + h10 * fr * (1 - fc) + h01 * (1 - fr) * fc + h11 * fr * fc

    # Gradient vectors
    gr = (h10 - h00) * (1 - fc) + (h11 - h01) * fc
    gc = (h01 - h00) * (1 - fr) + (h11 - h10) * fr
    return gr, gc, height

def simulate_erosion():
    """Simulate particle-based hydraulic erosion for N_DROPS."""
    global h, deposit
    
    # Decelerate/decay deposit map to ensure water trails glow dynamically
    deposit *= 0.91
    
    for _ in range(N_DROPS):
        # Spawn droplet at random grid coordinates
        pos_r = random.uniform(1, GRID - 2)
        pos_c = random.uniform(1, GRID - 2)
        vel_r, vel_c = 0.0, 0.0
        water = 1.0
        sediment = 0.0

        for _ in range(MAX_STEPS):
            if water < 0.01:
                break
            ri, ci = int(pos_r), int(pos_c)
            if not (0 < ri < GRID - 1 and 0 < ci < GRID - 1):
                break

            gr, gc, old_h = get_gradient_and_height(pos_r, pos_c)

            # Update velocity vector
            vel_r = vel_r * INERTIA - gr * (1.0 - INERTIA)
            vel_c = vel_c * INERTIA - gc * (1.0 - INERTIA)
            speed = math.hypot(vel_r, vel_c) + 1e-9
            vel_r /= speed
            vel_c /= speed

            new_r = pos_r + vel_r
            new_c = pos_c + vel_c
            if not (0 < new_r < GRID - 1 and 0 < new_c < GRID - 1):
                break

            _, _, new_h = get_gradient_and_height(new_r, new_c)
            dh = new_h - old_h

            # Droplet sediment capacity
            capacity = max(-dh, MIN_SLOPE) * speed * water * CAPACITY

            if sediment > capacity:
                # Over-saturated: deposit excess sediment
                dep_val = (sediment - capacity) * DEPOSITION
                sediment -= dep_val
                h[ri, ci] += dep_val
                deposit[ri, ci] += dep_val * 6.0
            else:
                # Under-saturated: erode sediment from 3x3 neighborhood
                erode_val = min((capacity - sediment) * EROSION, -dh + 0.01)
                erode_val = max(erode_val, 0.0)
                
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        er, ec = ri + dr, ci + dc
                        if 0 <= er < GRID and 0 <= ec < GRID:
                            weight = max(0.0, 1.0 - abs(dr) - abs(dc) * 0.5)
                            h[er, ec] -= erode_val * weight * 0.25
                            deposit[er, ec] += erode_val * weight * 2.5
                sediment += erode_val

            pos_r, pos_c = new_r, new_c
            water *= (1.0 - EVAPORATION)

        # Deposit remaining sediment at death point
        ri, ci = int(pos_r), int(pos_c)
        if 0 <= ri < GRID and 0 <= ci < GRID:
            h[ri, ci] += sediment
            deposit[ri, ci] += sediment * 4.0

    # Ensure boundaries stay clamped
    h = np.clip(h, 0.0, 1.0)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed heightmap
    random.seed(random.randint(0, 999999))
    generate_diamond_square(roughness=0.52)

def draw():
    fc = py5.frame_count
    
    # Base background (obsidian void)
    py5.background(10, 10, 14)
    py5.blend_mode(py5.BLEND)
    
    # 1. Run erosion step
    simulate_erosion()
    
    # 2. Compute 3D Isometric Projection coordinates
    cx_scr = py5.width / 2.0
    cy_scr = py5.height / 2.0 + 80.0
    
    # Slow orbital rotation over time
    angle = fc * 0.0018 - 0.28
    
    # Compute points
    rot_cos = math.cos(angle)
    rot_sin = math.sin(angle)
    
    # Matrices of grid coordinates
    C, R = np.meshgrid(np.arange(GRID), np.arange(GRID))
    X = (C - GRID / 2.0) * SPACING
    Z = (R - GRID / 2.0) * SPACING
    Y = -h * MAX_HEIGHT
    
    # 3D Y-Axis Rotation
    RotX = X * rot_cos - Z * rot_sin
    RotZ = X * rot_sin + Z * rot_cos
    
    # Projection coords
    proj_x = cx_scr + RotX
    proj_y = cy_scr + RotZ * 0.45 + Y
    
    # Compute quad center depth values for Painter's hidden-surface removal
    # (using average depth of the 4 corners of each quad)
    quads = []
    for r in range(GRID - 1):
        for c in range(GRID - 1):
            # Calculate depth (RotZ) for the 4 corners
            z00 = RotZ[r, c]
            z10 = RotZ[r + 1, c]
            z01 = RotZ[r, c + 1]
            z11 = RotZ[r + 1, c + 1]
            avg_z = (z00 + z10 + z01 + z11) / 4.0
            quads.append((avg_z, r, c))
            
    # Sort quads from back to front (descending depth)
    quads.sort(key=lambda q: q[0], reverse=True)
    
    min_z = RotZ.min()
    max_z = RotZ.max()
    z_range = max_z - min_z + 1e-9
    
    # 3. Draw sorted quads (Hidden-line wireframe rendering)
    for avg_z, r, c in quads:
        # Determine coordinate indices
        # Vertices: 0=(r,c), 1=(r+1,c), 2=(r+1,c+1), 3=(r,c+1)
        x0, y0 = proj_x[r, c], proj_y[r, c]
        x1, y1 = proj_x[r + 1, c], proj_y[r + 1, c]
        x2, y2 = proj_x[r + 1, c + 1], proj_y[r + 1, c + 1]
        x3, y3 = proj_x[r, c + 1], proj_y[r, c + 1]
        
        # Occlusion fill: solid background color to mask out lines behind it
        py5.fill(10, 10, 14)
        
        # Wireframe color: Hologram Teal with distance-based fog
        depth_t = (avg_z - min_z) / z_range  # 0 (back) to 1 (front)
        
        # Base neon teal fog scaling
        c_r = int(py5.remap(depth_t, 0, 1, 0, 0))
        c_g = int(py5.remap(depth_t, 0, 1, 40, 240))
        c_b = int(py5.remap(depth_t, 0, 1, 48, 180))
        
        # Highlight water trails: check active deposit value
        active_dep = (deposit[r, c] + deposit[r+1, c] + deposit[r+1, c+1] + deposit[r, c+1]) / 4.0
        if active_dep > 0.008:
            # Shift color to glowing orange/gold based on activity
            gold_t = min(1.0, active_dep * 5.0)
            c_r = int(py5.lerp(c_r, 255, gold_t))
            c_g = int(py5.lerp(c_g, 135, gold_t))
            c_b = int(py5.lerp(c_b, 0, gold_t))
            py5.stroke_weight(py5.remap(depth_t, 0, 1, 0.8, 2.2))
        else:
            py5.stroke_weight(py5.remap(depth_t, 0, 1, 0.4, 1.2))
            
        py5.stroke(c_r, c_g, c_b, int(py5.remap(depth_t, 0, 1, 55, 235)))
        
        # Draw closed occluding quad
        py5.begin_shape(py5.QUADS)
        py5.vertex(x0, y0)
        py5.vertex(x1, y1)
        py5.vertex(x2, y2)
        py5.vertex(x3, y3)
        py5.end_shape(py5.CLOSE)

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame is at frame 450)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
