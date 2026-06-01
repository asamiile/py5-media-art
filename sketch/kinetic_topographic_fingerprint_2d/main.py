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
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(180, 80, 10) # Very dark teal
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    num_rings = 180
    points_per_ring = 360
    
    # We will draw distorted concentric rings
    for r in range(1, num_rings):
        base_radius = r * 15
        
        # Color gradient across the rings
        hue = (160 + r * 0.2 + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 90, 80, 60)
        py5.stroke_weight(2.5)
        
        py5.begin_shape()
        for angle_deg in range(0, points_per_ring + 1):
            angle = py5.radians(angle_deg % 360)
            
            x_base = base_radius * np.cos(angle)
            y_base = base_radius * np.sin(angle)
            
            # Domain warping the vertices
            noise_scale = 0.0015
            dx = py5.os_noise(x_base * noise_scale, y_base * noise_scale, t) * 600
            dy = py5.os_noise((x_base + 500) * noise_scale, (y_base + 500) * noise_scale, t) * 600
            
            py5.vertex(x_base + dx, y_base + dy)
        py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
