from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.spatial import cKDTree
from collections import deque

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

# DLA Simulation parameters
# Because simulating DLA during rendering is too slow (random walks take forever),
# we will generate the cluster instantly using a fast spatial approximation
# or we just pre-calculate it before rendering starts.
# Actually, random walks are slow. Let's pre-generate using a fast heuristic:
# We just add points that are touching existing points, biased towards the center.
# A true DLA uses random walks, but a close visual approximation is the Eden Growth Model
# or DLA with a biased attachment probability.

NUM_PARTICLES = 30000
PARTICLE_RADIUS = py5.height * 0.003
CLUSTER_RADIUS = py5.height * 0.45

tree_pts = [] # List of (x, y)
tree_colors = []

def precalculate_dla():
    global tree_pts
    
    print("Pre-calculating DLA cluster...")
    
    # Start with a seed in the center
    cx, cy = py5.width / 2, py5.height / 2
    tree_pts.append(np.array([cx, cy]))
    
    # We will do true DLA but optimized.
    # We maintain a spawn radius and a kill radius.
    max_dist_sq = 0.0
    r_sq = PARTICLE_RADIUS * 2.0
    r_sq *= r_sq
    
    # Fast DLA using a grid to check collisions instead of KDTree for speed
    grid_size = PARTICLE_RADIUS * 2
    cols = int(py5.width / grid_size) + 1
    rows = int(py5.height / grid_size) + 1
    
    grid = [[[] for _ in range(rows)] for _ in range(cols)]
    
    def add_to_grid(idx, pt):
        c = int(pt[0] / grid_size)
        r = int(pt[1] / grid_size)
        if 0 <= c < cols and 0 <= r < rows:
            grid[c][r].append(idx)
            
    def check_collision(pt):
        c = int(pt[0] / grid_size)
        r = int(pt[1] / grid_size)
        
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                nc = c + dc
                nr = r + dr
                if 0 <= nc < cols and 0 <= nr < rows:
                    for idx in grid[nc][nr]:
                        other = tree_pts[idx]
                        dist_sq = (pt[0] - other[0])**2 + (pt[1] - other[1])**2
                        if dist_sq < r_sq:
                            return True
        return False
        
    add_to_grid(0, tree_pts[0])
    
    max_radius = PARTICLE_RADIUS * 4.0
    
    for i in range(1, NUM_PARTICLES):
        if i % 5000 == 0:
            print(f"Generated {i}/{NUM_PARTICLES} particles...")
            
        spawn_radius = max_radius + PARTICLE_RADIUS * 10
        
        if spawn_radius > CLUSTER_RADIUS:
            break
            
        # Spawn random walker
        theta = random.random() * 2 * np.pi
        px = cx + spawn_radius * np.cos(theta)
        py = cy + spawn_radius * np.sin(theta)
        
        while True:
            # Random walk step
            # Bias slightly towards center to speed up
            angle = random.random() * 2 * np.pi
            step_x = np.cos(angle) * PARTICLE_RADIUS
            step_y = np.sin(angle) * PARTICLE_RADIUS
            
            # Bias
            dir_cx = cx - px
            dir_cy = cy - py
            norm = np.sqrt(dir_cx**2 + dir_cy**2)
            if norm > 0:
                step_x += (dir_cx / norm) * (PARTICLE_RADIUS * 0.2)
                step_y += (dir_cy / norm) * (PARTICLE_RADIUS * 0.2)
                
            px += step_x
            py += step_y
            
            dist_to_center = np.sqrt((px - cx)**2 + (py - cy)**2)
            
            # If it wanders too far, kill and respawn
            if dist_to_center > spawn_radius + PARTICLE_RADIUS * 20:
                theta = random.random() * 2 * np.pi
                px = cx + spawn_radius * np.cos(theta)
                py = cy + spawn_radius * np.sin(theta)
                continue
                
            # Check collision
            pt = np.array([px, py])
            if check_collision(pt):
                tree_pts.append(pt)
                add_to_grid(len(tree_pts)-1, pt)
                if dist_to_center > max_radius:
                    max_radius = dist_to_center
                break
                
    print(f"DLA Generation complete. Total particles: {len(tree_pts)}")

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    
    precalculate_dla()
    
    # Calculate colors
    cx, cy = py5.width / 2, py5.height / 2
    for pt in tree_pts:
        dx = pt[0] - cx
        dy = pt[1] - cy
        dist = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        # Color based on angle and distance
        hue = (np.degrees(angle) + dist * 0.2) % 360
        sat = 80 + random.random() * 20
        br = 70 + random.random() * 30
        tree_colors.append((hue, sat, br))

def draw():
    py5.background(0, 0, 5, 20) # Slight trail effect
    
    # Animate blooming by revealing particles over time
    particles_per_frame = len(tree_pts) / TOTAL_FRAMES
    # Ease out the speed
    t = py5.frame_count / TOTAL_FRAMES
    # Ease out cubic: 1 - (1-t)^3
    eased_t = 1.0 - (1.0 - t)**3
    
    visible_count = int(eased_t * len(tree_pts))
    visible_count = min(visible_count, len(tree_pts))
    
    py5.no_stroke()
    
    # We redraw everything up to visible_count to ensure it's bright
    for i in range(visible_count):
        pt = tree_pts[i]
        c = tree_colors[i]
        
        # Draw particle
        py5.fill(c[0], c[1], c[2], 80)
        py5.circle(pt[0], pt[1], PARTICLE_RADIUS * 1.5)
        
        # Draw glowing core
        py5.fill(c[0], c[1] * 0.5, 100)
        py5.circle(pt[0], pt[1], PARTICLE_RADIUS * 0.5)

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
