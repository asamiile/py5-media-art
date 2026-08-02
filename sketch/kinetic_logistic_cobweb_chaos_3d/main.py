from pathlib import Path
import sys
import random
import math
import subprocess
import shutil
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes
from lib.animation import frames_dir

# Directories and parameters
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

FPS = 60
TOTAL_FRAMES = 900  # 15 seconds
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Numerical parameters
N_TRAJ = 250
MAX_HISTORY = 120  # 60 cobweb steps (120 lines)
SUBSTEPS = 2

# Generative seed (ensures no fixed seeds)
SEED = random.randint(0, 1000000)
rng = np.random.RandomState(SEED)

# Initial states: x values in [0.2, 0.8]
x_state = rng.uniform(0.2, 0.8, N_TRAJ).astype(np.float32)

# Trajectory histories: list of lists storing (x, y) coordinates
histories = [[(x_state[j], x_state[j])] for j in range(N_TRAJ)]

# Twinkling background stars
stars_x = np.zeros(600, dtype=np.float32)
stars_y = np.zeros(600, dtype=np.float32)
stars_phase = np.zeros(600, dtype=np.float32)

# Color configurations (5 groups of 50 trajectories)
GROUP_HUES = [180, 220, 270, 320, 40]
GROUP_SATS = [85, 80, 75, 85, 95]
GROUP_SIZE = N_TRAJ // len(GROUP_HUES)

def setup():
    global stars_x, stars_y, stars_phase
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 40, 6)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate background stars
    stars_x = rng.uniform(0, py5.width, 600)
    stars_y = rng.uniform(0, py5.height, 600)
    stars_phase = rng.uniform(0, np.pi * 2, 600)

def update_physics():
    global x_state, histories
    
    # Modulate r over 900 frame loop (starts at 2.9, rises to 3.99, falls back to 2.9)
    progress = (py5.frame_count - 1) / TOTAL_FRAMES
    theta_mod = 2.0 * np.pi * progress
    r_val = 2.9 + 1.09 * (0.5 * (1.0 - np.cos(theta_mod)))
    
    for j in range(N_TRAJ):
        x = x_state[j]
        hist = histories[j]
        
        for _ in range(SUBSTEPS):
            # Logistic Map step
            y = r_val * x * (1.0 - x)
            # Add vertical staircase segment: (x, x) -> (x, y)
            hist.append((x, x))
            # Add horizontal staircase segment: (x, y) -> (y, y)
            hist.append((x, y))
            x = y
            
        x_state[j] = x
        
        # Keep history length bounded
        if len(hist) > MAX_HISTORY:
            histories[j] = hist[-MAX_HISTORY:]

def draw():
    # Clear screen with translucent fill for motion blur trails
    py5.fill(240, 40, 6, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw background stars
    for i in range(600):
        brightness = 35 + 25 * np.sin(py5.frame_count * 0.05 + stars_phase[i])
        py5.stroke(220, 15, brightness, 140)
        py5.stroke_weight(rng.uniform(0.8, 2.0))
        py5.point(stars_x[i], stars_y[i])
        
    # Update physics
    update_physics()
    
    # Camera / Projection parameters
    center_x, center_y = py5.width / 2.0, py5.height / 2.0
    cam_dist = 1100.0
    fov = 1200.0
    
    # 3D Rotations
    rot_y = py5.frame_count * 0.007
    rot_z = py5.frame_count * 0.004
    cy, sy = math.cos(rot_y), math.sin(rot_y)
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    
    # Collect all segments from all trajectories to sort by depth
    # A segment is represented as: [x1_2d, y1_2d, x2_2d, y2_2d, depth, group_idx, segment_age]
    segments = []
    
    for j in range(N_TRAJ):
        hist = histories[j]
        group_idx = j // GROUP_SIZE
        n_pts = len(hist)
        if n_pts < 2:
            continue
            
        # Cylindrical wrap helper
        def wrap_point(cx, cy_val):
            # Radius depends on x coordinate
            R = 330.0 + cx * 160.0
            # Angle wraps with y coordinate
            phi = cy_val * 2.5 * math.pi - 0.75 * math.pi
            # Height depends on x coordinate
            Z = (cx - 0.5) * 800.0
            
            x3 = R * math.cos(phi)
            y3 = R * math.sin(phi)
            z3 = Z
            
            # Y rotation
            x3_r = x3 * cy - z3 * sy
            z3_r = x3 * sy + z3 * cy
            
            # Z rotation
            x3_rf = x3_r * cz - y3 * sz
            y3_rf = x3_r * sz + y3 * cz
            
            # Perspective projection
            depth = y3_rf + cam_dist
            sx = center_x + (x3_rf * fov) / depth
            sy_proj = center_y + (z3_r * fov) / depth
            return sx, sy_proj, depth

        # Precompute projected points
        proj_pts = []
        for px, py_val in hist:
            proj_pts.append(wrap_point(px, py_val))
            
        # Generate segments
        for i in range(1, n_pts):
            sx0, sy0, d0 = proj_pts[i - 1]
            sx1, sy1, d1 = proj_pts[i]
            
            avg_depth = (d0 + d1) / 2.0
            segments.append([sx0, sy0, sx1, sy1, avg_depth, group_idx, i / n_pts])
            
    # Sort segments by depth (painters algorithm: back to front)
    # Average depth is at index 4
    segments.sort(key=lambda s: s[4], reverse=True)
    
    # Render segments in 10 depth bins per group to optimize performance
    # For each group, we split its segments into 10 depth chunks and draw them
    N_BINS = 10
    
    for g in range(len(GROUP_HUES)):
        hue = GROUP_HUES[g]
        sat = GROUP_SATS[g]
        
        # Filter segments belonging to this color group
        group_segs = [s for s in segments if s[5] == g]
        if not group_segs:
            continue
            
        # Split into depth bins
        bin_size = max(1, len(group_segs) // N_BINS)
        for b in range(N_BINS):
            bin_chunk = group_segs[b * bin_size : (b + 1) * bin_size]
            if not bin_chunk:
                continue
                
            # Average depth of the bin (for glow calculations)
            avg_bin_depth = sum(s[4] for s in bin_chunk) / len(bin_chunk)
            
            # Depth cueing: further away = dimmer and thinner
            depth_factor = max(0.2, min(1.2, (cam_dist + 400.0 - avg_bin_depth) / 800.0))
            
            # Multi-pass Glow Rendering
            # 1. Glow pass 1 (thick, low-alpha)
            py5.stroke(hue, sat, 90, 8 * depth_factor)
            py5.stroke_weight(7.0 * depth_factor)
            py5.begin_shape(py5.LINES)
            for sx0, sy0, sx1, sy1, _, _, age_factor in bin_chunk:
                py5.vertex(sx0, sy0)
                py5.vertex(sx1, sy1)
            py5.end_shape()
            
            # 2. Glow pass 2 (medium)
            py5.stroke(hue, sat, 95, 24 * depth_factor)
            py5.stroke_weight(3.0 * depth_factor)
            py5.begin_shape(py5.LINES)
            for sx0, sy0, sx1, sy1, _, _, age_factor in bin_chunk:
                py5.vertex(sx0, sy0)
                py5.vertex(sx1, sy1)
            py5.end_shape()
            
            # 3. Core pass (sharp, bright, slightly desaturated core)
            py5.stroke(hue, max(0, sat - 20), 100, 80 * depth_factor)
            py5.stroke_weight(1.0 * depth_factor)
            py5.begin_shape(py5.LINES)
            for sx0, sy0, sx1, sy1, _, _, age_factor in bin_chunk:
                py5.vertex(sx0, sy0)
                py5.vertex(sx1, sy1)
            py5.end_shape()

    # Fail-safe: check standard deviation to prevent blank frames
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress indicator
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    # Compile video on last frame
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot at mid-point
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Cleanup temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
