from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10  # 10 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global vertices, num_lats, num_lons
    num_lats = 100
    num_lons = 100
    vertices = np.zeros((num_lats, num_lons, 3))
    
    global lats, lons
    lats = np.linspace(0, np.pi, num_lats)
    lons = np.linspace(0, 2 * np.pi, num_lons)


def draw():
    py5.background(0)
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.02
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.5)
    
    # Spherical harmonics displacement
    base_radius = py5.height * 0.25
    
    Lons, Lats = np.meshgrid(lons, lats)
    
    # Complex combination of sine waves for resonance effect
    m1, m2 = 3, 5
    n1, n2 = 4, 3
    
    r1 = np.sin(m1 * Lons) * np.cos(n1 * Lats)
    r2 = np.sin(m2 * Lons + t) * np.cos(n2 * Lats - t)
    
    r_total = base_radius + 50 * (r1 + r2) + 20 * np.sin(t * 2)
    
    X = r_total * np.sin(Lats) * np.cos(Lons)
    Y = r_total * np.sin(Lats) * np.sin(Lons)
    Z = r_total * np.cos(Lats)
    
    py5.stroke_weight(1.5)
    py5.no_fill()
    
    # Draw points or mesh
    for i in range(num_lats - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(num_lons):
            # Calculate hue based on radius displacement
            disp1 = r_total[i, j] - base_radius
            hue = (200 + disp1 * 2 + t * 50) % 360
            py5.stroke(hue, 80, 80, 50)
            py5.vertex(X[i, j], Y[i, j], Z[i, j])
            
            disp2 = r_total[i+1, j] - base_radius
            hue2 = (200 + disp2 * 2 + t * 50) % 360
            py5.stroke(hue2, 80, 80, 50)
            py5.vertex(X[i+1, j], Y[i+1, j], Z[i+1, j])
        py5.end_shape()

    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
