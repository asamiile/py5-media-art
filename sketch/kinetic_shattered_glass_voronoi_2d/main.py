from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.spatial import Voronoi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Variables for the animation
points_base = None
velocities = None
colors = None

def setup():
    global points_base, velocities, colors
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize 800 random points with slow drifting velocities
    num_points = 800
    points_base = np.random.rand(num_points, 2) * np.array([SIZE[0], SIZE[1]])
    
    # Expand slightly beyond screen for voronoi boundary logic
    borders = np.array([
        [-SIZE[0]*2, -SIZE[1]*2], [SIZE[0]*3, -SIZE[1]*2],
        [-SIZE[0]*2, SIZE[1]*3], [SIZE[0]*3, SIZE[1]*3]
    ])
    points_base = np.vstack([points_base, borders])
    
    velocities = (np.random.rand(num_points + 4, 2) - 0.5) * 2.0
    # Keep border points still
    velocities[num_points:] = 0
    
    colors = []
    for i in range(num_points):
        # Cold ice-blue, deep navy, stark white
        r = random.random()
        if r < 0.6:
            colors.append([16, 32, 64, 150]) # Deep navy
        elif r < 0.9:
            colors.append([160, 224, 255, 120]) # Ice blue
        else:
            colors.append([255, 255, 255, 200]) # White
    for i in range(4):
        colors.append([0, 0, 0, 0])

def draw():
    global points_base
    py5.background(5, 5, 8) # Very dark obsidian
    py5.blend_mode(py5.ADD)
    
    # Update points slowly
    points_base += velocities
    
    # Apply a subtle perlin noise drift to the velocities for a "stress" look
    for i in range(len(velocities)-4):
        n_x = py5.noise(points_base[i, 0] * 0.002, points_base[i, 1] * 0.002, py5.frame_count * 0.01) - 0.5
        n_y = py5.noise(points_base[i, 0] * 0.002 + 1000, points_base[i, 1] * 0.002 + 1000, py5.frame_count * 0.01) - 0.5
        velocities[i, 0] += n_x * 0.1
        velocities[i, 1] += n_y * 0.1
        
        # Dampen velocity
        velocities[i] *= 0.98

    # Compute Voronoi
    vor = Voronoi(points_base)
    
    py5.stroke(255, 255, 255, 40)
    py5.stroke_weight(2)
    
    # Draw cells
    for point_idx, region_idx in enumerate(vor.point_region):
        if point_idx >= len(colors):
            continue
        region = vor.regions[region_idx]
        if not -1 in region and len(region) > 0:
            polygon = [vor.vertices[i] for i in region]
            py5.fill(*colors[point_idx])
            
            # Add stress fracture separation over time
            # Scale polygon slightly relative to its center based on noise
            center = np.mean(polygon, axis=0)
            fracture = py5.noise(center[0] * 0.01, center[1] * 0.01, py5.frame_count * 0.05)
            scale = 0.98 - fracture * 0.1
            
            py5.begin_shape()
            for v in polygon:
                scaled_v = center + (v - center) * scale
                py5.vertex(scaled_v[0], scaled_v[1])
            py5.end_shape(py5.CLOSE)

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
