from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 1200
pos = None

anchor_points = None

C1, C2, C3, C4, C5 = None, None, None, None, None

def setup():
    global pos, anchor_points, C1, C2, C3, C4, C5
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize points inside the bounds
    x = np.random.uniform(0, py5.width, NUM_POINTS)
    y = np.random.uniform(0, py5.height, NUM_POINTS)
    pos = np.column_stack((x, y))
    
    # Anchor points to bound the Voronoi regions
    margin = 2000
    w = py5.width
    h = py5.height
    
    anchors = []
    # Create a ring of anchor points far outside the screen
    for i in range(-10, 11):
        anchors.append([-margin, h/2 + i*500])
        anchors.append([w + margin, h/2 + i*500])
        anchors.append([w/2 + i*500, -margin])
        anchors.append([w/2 + i*500, h + margin])
    
    anchor_points = np.array(anchors)
    
    # Colors
    # Ruby Red (#9B1D20), Sapphire Blue (#0D3B66), Emerald Green (#2D728F), Amethyst Purple (#4B3F72), Amber Gold (#F4D35E)
    C1 = py5.color(155, 29, 32)
    C2 = py5.color(13, 59, 102)
    C3 = py5.color(45, 114, 143)
    C4 = py5.color(75, 63, 114)
    C5 = py5.color(244, 211, 94)

def get_cell_color(x, y, t):
    scale = 0.0015
    n_val = py5.os_noise(x * scale, y * scale, t * 1.5)
    
    if n_val < 0.25:
        f = n_val / 0.25
        return py5.lerp_color(C1, C2, f)
    elif n_val < 0.5:
        f = (n_val - 0.25) / 0.25
        return py5.lerp_color(C2, C3, f)
    elif n_val < 0.75:
        f = (n_val - 0.5) / 0.25
        return py5.lerp_color(C3, C4, f)
    else:
        f = (n_val - 0.75) / 0.25
        return py5.lerp_color(C4, C5, f)

def draw():
    global pos
    
    py5.background(26, 26, 26) # Dark Lead outline/background
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Update positions using a noise flow field
    noise_scale = 0.002
    angles = np.zeros(NUM_POINTS)
    # os_noise doesn't accept arrays easily in this wrapper, loop is okay for 1200 points
    # Wait, we can use a vectorized approach if possible, but python loop for 1200 is < 5ms
    speed = 3.0
    
    # Optimization: batch noise calls or just loop
    for i in range(NUM_POINTS):
        n = py5.os_noise(pos[i, 0] * noise_scale, pos[i, 1] * noise_scale, t * 2.0)
        angle = n * np.pi * 4.0
        pos[i, 0] += np.cos(angle) * speed
        pos[i, 1] += np.sin(angle) * speed
        
        # Soft wrap/bounce
        if pos[i, 0] < -100: pos[i, 0] += py5.width + 200
        if pos[i, 0] > py5.width + 100: pos[i, 0] -= py5.width + 200
        if pos[i, 1] < -100: pos[i, 1] += py5.height + 200
        if pos[i, 1] > py5.height + 100: pos[i, 1] -= py5.height + 200
        
    all_points = np.vstack((pos, anchor_points))
    vor = Voronoi(all_points)
    
    py5.stroke(26, 26, 26) # Dark lead
    py5.stroke_weight(5.0)
    
    for i in range(NUM_POINTS):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        
        if -1 in region or len(region) == 0:
            continue
            
        polygon = vor.vertices[region]
        
        cx, cy = pos[i]
        c = get_cell_color(cx, cy, t)
        py5.fill(c)
        
        py5.begin_shape()
        for v in polygon:
            py5.vertex(v[0], v[1])
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
