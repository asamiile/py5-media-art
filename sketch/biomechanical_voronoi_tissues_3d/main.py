from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os
from scipy.spatial import Delaunay

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

NUM_POINTS = 150
points_base = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points_base
    # Distribute points roughly in a sphere
    phi = np.arccos(1 - 2 * np.random.rand(NUM_POINTS))
    theta = 2 * np.pi * np.random.rand(NUM_POINTS)
    r = np.cbrt(np.random.rand(NUM_POINTS)) * 300
    
    points_base = np.zeros((NUM_POINTS, 3))
    points_base[:, 0] = r * np.sin(phi) * np.cos(theta)
    points_base[:, 1] = r * np.sin(phi) * np.sin(theta)
    points_base[:, 2] = r * np.cos(phi)

def draw():
    global points_base
    
    py5.background(15, 5, 5) # Very dark reddish black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.ambient_light(80, 50, 50)
    py5.directional_light(360, 100, 100, 0, 1, -1)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count * 0.02
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    # Animate points using noise for organic drift
    # and sine wave for breathing
    breathe = 1.0 + np.sin(t * 0.5) * 0.1
    
    current_points = np.copy(points_base) * breathe
    
    for i in range(NUM_POINTS):
        nx = py5.os_noise(points_base[i,0]*0.01, points_base[i,1]*0.01, t) - 0.5
        ny = py5.os_noise(points_base[i,1]*0.01, points_base[i,2]*0.01, t) - 0.5
        nz = py5.os_noise(points_base[i,2]*0.01, points_base[i,0]*0.01, t) - 0.5
        current_points[i,0] += nx * 50
        current_points[i,1] += ny * 50
        current_points[i,2] += nz * 50
        
    # Delaunay triangulation to get the tissue connections
    try:
        tri = Delaunay(current_points)
        simplices = tri.simplices
    except:
        simplices = []
        
    py5.blend_mode(py5.ADD)
    
    py5.begin_shape(py5.TRIANGLES)
    for simplex in simplices:
        # Check if we should draw this triangle
        p0 = current_points[simplex[0]]
        p1 = current_points[simplex[1]]
        p2 = current_points[simplex[2]]
        
        # Calculate distance to center to fade edges
        d = (np.linalg.norm(p0) + np.linalg.norm(p1) + np.linalg.norm(p2)) / 3.0
        
        if d < 350:
            # Determine if this is an organic tissue part or synthetic nerve
            is_synthetic = (simplex[0] + simplex[1] + simplex[2]) % 7 == 0
            
            if is_synthetic:
                py5.stroke(120, 100, 100, 50) # Neon green
                py5.stroke_weight(2)
                py5.fill(120, 100, 100, 10)
            else:
                py5.stroke(0, 80, 80, 30) # Reddish
                py5.stroke_weight(1)
                py5.fill(350, 60, d/350 * 50 + 20, 20) # Bone/Flesh
                
            py5.vertex(p0[0], p0[1], p0[2])
            py5.vertex(p1[0], p1[1], p1[2])
            py5.vertex(p2[0], p2[1], p2[2])
            
    py5.end_shape()
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            
        os._exit(0)

py5.run_sketch()
