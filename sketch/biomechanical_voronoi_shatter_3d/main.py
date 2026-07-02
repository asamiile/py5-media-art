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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Voronoi points simulation
NUM_POINTS = 3000
points = None
normals = None
colors = None

def setup():
    global points, normals, colors
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    np.random.seed(42)
    # Generate points on a sphere
    phi = np.random.uniform(0, 2 * np.pi, NUM_POINTS)
    costheta = np.random.uniform(-1, 1, NUM_POINTS)
    theta = np.arccos(costheta)
    
    r = 600
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    points = np.column_stack((x, y, z))
    normals = points / r
    colors = np.random.uniform(120, 200, NUM_POINTS) # Teal / Cyan

def draw():
    global points, normals, colors
    py5.background(10, 15, 20)
    
    py5.translate(py5.width / 2, py5.height / 2, -400)
    
    cam_angle = py5.frame_count * 0.005
    py5.rotate_y(cam_angle)
    py5.rotate_x(cam_angle * 0.5)
    
    t = py5.frame_count * 0.02
    
    py5.directional_light(180, 50, 100, 1, 1, -1)
    py5.ambient_light(20, 20, 20)
    
    # Calculate expansion
    py5.no_stroke()
    
    for i in range(NUM_POINTS):
        # Noise based expansion per point
        nx = normals[i][0] * 5 + t
        ny = normals[i][1] * 5 + t
        nz = normals[i][2] * 5 + t
        
        noise_val = py5.os_noise(nx, ny, nz)
        expansion = max(0, noise_val - 0.3) * 2000
        
        px = points[i][0] + normals[i][0] * expansion
        py = points[i][1] + normals[i][1] * expansion
        pz = points[i][2] + normals[i][2] * expansion
        
        py5.push_matrix()
        py5.translate(px, py, pz)
        
        # Orient cell along normal
        # Simplified by just drawing boxes that rotate
        py5.rotate_x(expansion * 0.01)
        py5.rotate_y(expansion * 0.01)
        
        # Color mix
        hue = (colors[i] + expansion * 0.1) % 360
        bright = min(100, 50 + expansion * 0.2)
        
        py5.fill(hue, 90, bright, 90)
        
        # Draw a cell (box as placeholder for voronoi cell)
        # We shrink them slightly as they expand
        size = max(5, 40 - expansion * 0.02)
        py5.box(size, size, size * 2)
        
        # Inner glowing core
        py5.fill(180, 20, 100, 100)
        py5.box(size * 0.5)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
