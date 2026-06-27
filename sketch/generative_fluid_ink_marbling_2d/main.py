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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_rings = 40
pts_per_ring = 800
total_pts = num_rings * pts_per_ring

positions = None
colors = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions, colors
    
    positions = np.zeros((total_pts, 2), dtype=np.float32)
    colors = np.zeros((total_pts, 3), dtype=np.float32)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    idx = 0
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(num_rings):
        r = 50 + i * 25
        hue = (i * 15) % 360
        
        for j in range(pts_per_ring):
            angle = j * py5.TWO_PI / pts_per_ring
            positions[idx, 0] = cx + r * np.cos(angle)
            positions[idx, 1] = cy + r * np.sin(angle)
            colors[idx, 0] = hue
            colors[idx, 1] = 80 - (i % 2) * 40
            colors[idx, 2] = 90
            idx += 1
            
    py5.background(10, 5, 95) 

def draw():
    global positions, colors
    
    py5.background(10, 5, 95)
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    t = py5.frame_count * 0.005
    noise_scale = 0.003
    
    eps = 1.0
    
    for i in range(total_pts):
        x = positions[i, 0]
        y = positions[i, 1]
        
        n1 = py5.os_noise(x * noise_scale, (y + eps) * noise_scale, t)
        n2 = py5.os_noise(x * noise_scale, (y - eps) * noise_scale, t)
        n3 = py5.os_noise((x + eps) * noise_scale, y * noise_scale, t)
        n4 = py5.os_noise((x - eps) * noise_scale, y * noise_scale, t)
        
        cx = (n1 - n2) / (2 * eps)
        cy = -(n3 - n4) / (2 * eps)
        
        positions[i, 0] += cx * 30.0
        positions[i, 1] += cy * 30.0
        
    idx = 0
    for i in range(num_rings):
        py5.stroke(colors[idx, 0], colors[idx, 1], colors[idx, 2], 80)
        py5.begin_shape()
        for j in range(pts_per_ring):
            py5.vertex(positions[idx, 0], positions[idx, 1])
            idx += 1
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
