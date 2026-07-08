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

# Maintain a list of points (x, y, dx, dy, r, g, b)
points = []

def add_point(x, y):
    dx = random.uniform(-0.5, 0.5)
    dy = random.uniform(-0.5, 0.5)
    
    # Cyberpunk palette
    palette = [
        (138, 43, 226), # BlueViolet
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (20, 20, 40)    # Dark
    ]
    
    c = random.choice(palette)
    # Add some variation
    r = py5.constrain(c[0] + random.uniform(-20, 20), 0, 255)
    g = py5.constrain(c[1] + random.uniform(-20, 20), 0, 255)
    b = py5.constrain(c[2] + random.uniform(-20, 20), 0, 255)
    
    points.append({'pos': np.array([x, y]), 'vel': np.array([dx, dy]), 'color': (r, g, b)})

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    
    # Initialize points uniformly
    for _ in range(300):
        add_point(random.uniform(-SIZE[0], SIZE[0]), random.uniform(-SIZE[1], SIZE[1]))

def draw():
    py5.background(5, 5, 10)
    
    global points
    
    # Update points
    zoom = 1.008
    new_points = []
    
    for p in points:
        p['pos'] = p['pos'] * zoom + p['vel']
        
        # Keep if within bounds
        if np.linalg.norm(p['pos']) < SIZE[0] * 2:
            new_points.append(p)
            
    points = new_points
    
    # Inject new points near center to maintain density
    while len(points) < 400:
        angle = random.uniform(0, py5.TWO_PI)
        rad = random.uniform(0, 50)
        add_point(rad * np.cos(angle), rad * np.sin(angle))
        
    # Prepare for Voronoi
    pts_array = np.array([p['pos'] for p in points])
    
    # Add bounding points far away to close cells
    L = SIZE[0] * 4
    bounds = np.array([
        [-L, -L], [L, -L], [L, L], [-L, L],
        [0, -L], [0, L], [-L, 0], [L, 0]
    ])
    all_pts = np.vstack([pts_array, bounds])
    
    try:
        vor = Voronoi(all_pts)
    except Exception as e:
        print(f"Voronoi error: {e}")
        py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
        return
        
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    py5.stroke(200, 255, 255, 150)
    py5.stroke_weight(2)
    
    # Draw cells
    for i, region_index in enumerate(vor.point_region[:len(points)]):
        region = vor.regions[region_index]
        if not region or -1 in region:
            continue
            
        polygon = [vor.vertices[v] for v in region]
        
        c = points[i]['color']
        
        # Calculate cell area roughly or use distance to center to fade
        dist = np.linalg.norm(points[i]['pos'])
        alpha = py5.remap(dist, 0, SIZE[0], 255, 0)
        alpha = py5.constrain(alpha, 0, 255)
        
        py5.fill(c[0], c[1], c[2], alpha * 0.8)
        
        py5.begin_shape()
        for v in polygon:
            py5.vertex(v[0], v[1])
        py5.end_shape(py5.CLOSE)
        
        # Optional: draw a smaller inner polygon for a shattered look
        if alpha > 50:
            py5.fill(c[0] * 0.5, c[1] * 0.5, c[2] * 0.5, alpha * 0.5)
            py5.no_stroke()
            py5.begin_shape()
            center = points[i]['pos']
            for v in polygon:
                # shrink towards center
                sv = center + (v - center) * 0.7
                py5.vertex(sv[0], sv[1])
            py5.end_shape(py5.CLOSE)
            py5.stroke(200, 255, 255, 150)
            
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
