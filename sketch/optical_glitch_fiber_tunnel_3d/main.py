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
    py5.color_mode(py5.HSB, 360, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(240, 100, 5)  # Very dark blue void
    py5.no_fill()
    
    t = py5.frame_count / TOTAL_FRAMES
    tunnel_length = 2000
    segments = 100
    
    py5.translate(py5.width / 2, py5.height / 2, 400)
    
    # We fly forward
    z_offset = (t * (tunnel_length / segments)) * segments
    
    for i in range(25):  # 25 fiber optic strands
        py5.begin_shape()
        
        # Fiber base hue
        hue = (200 + i * 5 + t * 60) % 360
        
        for j in range(segments):
            z = -j * (tunnel_length / segments) + (z_offset % (tunnel_length / segments))
            
            # Parametric path
            noise_x = py5.os_noise(i * 0.1, j * 0.05 - t * 2) * 400
            noise_y = py5.os_noise(i * 0.1 + 100, j * 0.05 - t * 2) * 400
            
            # Radius of the tunnel
            r = 300 + py5.sin(j * 0.1 + t * py5.TWO_PI) * 100
            angle = (i / 25) * py5.TWO_PI + (j * 0.02)
            
            x = py5.cos(angle) * r + noise_x
            y = py5.sin(angle) * r + noise_y
            
            # Pulse logic
            pulse = py5.sin(j * 0.5 - t * py5.TWO_PI * 5 + i)
            brightness = 100 if pulse > 0.9 else 30
            stroke_weight = 4 if pulse > 0.9 else 1
            
            py5.stroke(hue, 80, brightness)
            py5.stroke_weight(stroke_weight)
            
            py5.curve_vertex(x, y, z)
            
        py5.end_shape()

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
        import os
        os._exit(0)

py5.run_sketch()
