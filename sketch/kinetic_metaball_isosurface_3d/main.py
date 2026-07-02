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
DURATION_SEC = 10
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
    
    global grid_x, grid_y, grid_z, coords
    res = 40
    xs = np.linspace(-400, 400, res)
    ys = np.linspace(-400, 400, res)
    zs = np.linspace(-400, 400, res)
    grid_x, grid_y, grid_z = np.meshgrid(xs, ys, zs, indexing='ij')
    coords = np.stack([grid_x, grid_y, grid_z], axis=-1).reshape(-1, 3)

def draw():
    py5.background(0)
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.03
    py5.rotate_x(t * 0.4)
    py5.rotate_y(t * 0.6)
    
    # 4 Orbiting metaballs
    mb1 = np.array([200 * np.sin(t), 200 * np.cos(t * 1.5), 150 * np.sin(t * 0.5)])
    mb2 = np.array([-250 * np.cos(t * 1.2), 150 * np.sin(t * 0.8), -200 * np.cos(t * 1.1)])
    mb3 = np.array([100 * np.sin(t * 1.7), -250 * np.cos(t * 0.9), 250 * np.sin(t * 1.3)])
    mb4 = np.array([py5.os_noise(t, 0, 0) * 400 - 200, py5.os_noise(0, t, 0) * 400 - 200, py5.os_noise(0, 0, t) * 400 - 200])
    
    radii = np.array([80000, 90000, 75000, 85000])
    mbs = np.stack([mb1, mb2, mb3, mb4])
    
    # Calculate scalar field: sum( r_i / |p - c_i|^2 )
    diff = coords[:, None, :] - mbs[None, :, :]
    dist_sq = np.sum(diff**2, axis=2) + 1e-5
    field = np.sum(radii / dist_sq, axis=1)
    
    # Isosurface threshold
    mask = (field > 0.9) & (field < 1.3)
    active_points = coords[mask]
    
    py5.stroke_weight(5)
    py5.begin_shape(py5.POINTS)
    for p in active_points:
        dist = np.linalg.norm(p)
        hue = (150 + dist * 0.3 + t * 20) % 360
        py5.stroke(hue, 80, 100, 60)
        py5.vertex(p[0], p[1], p[2])
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
            
        import os
        os._exit(0)

py5.run_sketch()
