from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Subtle clear for glowing trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    # We will weave multiple strands to form a thick web
    NUM_STRANDS = 5
    NUM_POINTS = 5000
    
    fc = py5.frame_count
    base_t = np.linspace(0, np.pi * 80, NUM_POINTS)
    
    # 3D Rotation matrices
    rx = fc * 0.005
    ry = fc * 0.007
    rz = fc * 0.003
    
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    
    mat_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    mat_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    mat_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    
    rot_matrix = mat_z @ mat_y @ mat_x
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    # Draw multiple offset strands
    for i in range(NUM_STRANDS):
        t_offset = i * 0.05
        t = base_t + fc * 0.02 + t_offset
        
        # Complex 3D Lissajous knot parameters
        x_3d = np.sin(3 * t + fc * 0.01) * SIZE[0] * 0.35
        y_3d = np.sin(4 * t + fc * 0.015) * SIZE[1] * 0.35
        z_3d = np.sin(7 * t + fc * 0.005) * SIZE[0] * 0.35
        
        # Combine into a single matrix of points (3, N)
        points_3d = np.vstack((x_3d, y_3d, z_3d))
        
        # Apply rotations
        rotated_points = rot_matrix @ points_3d
        
        # Add perspective projection
        z_offset = 2000
        z_depth = rotated_points[2] + z_offset
        scale = z_offset / z_depth
        
        x_proj = rotated_points[0] * scale
        y_proj = rotated_points[1] * scale
        
        # Map colors based on z-depth for atmospheric glowing effect
        # Strands closer to camera (lower z_depth) are brighter crimson/gold
        py5.no_fill()
        
        py5.begin_shape()
        for j in range(NUM_POINTS):
            depth_ratio = max(0, min(1, 1 - (z_depth[j] - 1000) / 2000))
            r = int(150 + 105 * depth_ratio)
            g = int(50 + 150 * depth_ratio)
            b = int(100 * depth_ratio)
            alpha = int(20 + 200 * depth_ratio)
            
            py5.stroke(r, g, b, alpha)
            py5.vertex(x_proj[j], y_proj[j])
        py5.end_shape()

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
