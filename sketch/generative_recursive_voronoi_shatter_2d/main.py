from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5
from scipy.spatial import Voronoi

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

# Seed points
points = None
velocities = None

def setup():
    global points, velocities
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(250, 250, 248)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize with a few points
    num_initial = 10
    points = np.random.rand(num_initial, 2) * np.array(SIZE)
    velocities = (np.random.rand(num_initial, 2) - 0.5) * 2.0
    
    # Add dummy boundary points far outside to close the voronoi cells on screen
    w, h = SIZE
    boundaries = np.array([
        [-w*2, -h*2], [w*3, -h*2], [-w*2, h*3], [w*3, h*3],
        [w/2, -h*2], [w/2, h*3], [-w*2, h/2], [w*3, h/2]
    ])
    points = np.vstack([points, boundaries])
    velocities = np.vstack([velocities, np.zeros_like(boundaries)])

def draw():
    global points, velocities
    
    # Motion
    t = py5.frame_count * 0.01
    
    # Update only inner points (not the last 8 boundary points)
    N = len(points) - 8
    
    # Add some noise-based acceleration
    for i in range(N):
        px, py = points[i]
        ax = py5.os_noise(px * 0.005, py * 0.005, t) * 2 - 1
        ay = py5.os_noise(px * 0.005 + 100, py * 0.005 + 100, t) * 2 - 1
        velocities[i, 0] += ax * 0.1
        velocities[i, 1] += ay * 0.1
        
        # Friction
        velocities[i] *= 0.95
        
        points[i] += velocities[i]
        
        # Bounce off walls slightly (soft boundary)
        if points[i, 0] < 0: velocities[i, 0] += 0.5
        if points[i, 0] > SIZE[0]: velocities[i, 0] -= 0.5
        if points[i, 1] < 0: velocities[i, 1] += 0.5
        if points[i, 1] > SIZE[1]: velocities[i, 1] -= 0.5

    # Shatter (add points)
    if py5.frame_count % 30 == 0 and N < 1000:
        # Pick a random existing point and split it into 3 close points
        target_idx = np.random.randint(0, N)
        p = points[target_idx]
        
        new_points = p + (np.random.rand(2, 2) - 0.5) * 50
        new_vels = (np.random.rand(2, 2) - 0.5) * 5.0
        
        points = np.insert(points, N, new_points, axis=0)
        velocities = np.insert(velocities, N, new_vels, axis=0)
    
    # Calculate Voronoi
    try:
        vor = Voronoi(points)
    except Exception as e:
        print("Voronoi error:", e)
        # Skip this frame if coplanar or numerical issue
        pass
    else:
        # We'll fade the background slowly
        py5.blend_mode(py5.BLEND)
        py5.no_stroke()
        py5.fill(250, 250, 248, 40)
        py5.rect(0, 0, SIZE[0], SIZE[1])
        
        py5.stroke(20, 25, 30, 150)
        py5.stroke_weight(2)
        
        # Draw the ridges
        for simplex in vor.ridge_vertices:
            simplex = np.asarray(simplex)
            if np.all(simplex >= 0):
                p0 = vor.vertices[simplex[0]]
                p1 = vor.vertices[simplex[1]]
                
                # Only draw if roughly inside screen
                if (-500 < p0[0] < SIZE[0]+500 and -500 < p0[1] < SIZE[1]+500) or \
                   (-500 < p1[0] < SIZE[0]+500 and -500 < p1[1] < SIZE[1]+500):
                    py5.line(p0[0], p0[1], p1[0], p1[1])

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
