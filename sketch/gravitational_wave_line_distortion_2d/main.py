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
    py5.background(0)
    py5.no_fill()
    
    t = py5.frame_count / TOTAL_FRAMES
    
    num_lines = 150
    points_per_line = 300
    
    line_spacing = py5.height / num_lines
    point_spacing = py5.width / points_per_line
    
    # Gravity wells
    gw1_x = py5.width / 2 + py5.cos(t * py5.TWO_PI) * 400
    gw1_y = py5.height / 2 + py5.sin(t * py5.TWO_PI) * 200
    
    gw2_x = py5.width / 2 + py5.cos(t * py5.TWO_PI * 1.5 + py5.PI) * 300
    gw2_y = py5.height / 2 + py5.sin(t * py5.TWO_PI * 1.5) * 300
    
    py5.stroke_weight(2)
    
    for i in range(num_lines):
        base_y = i * line_spacing
        
        py5.begin_shape()
        for j in range(points_per_line + 1):
            base_x = j * point_spacing
            
            # Distance to gravity wells
            dx1 = base_x - gw1_x
            dy1 = base_y - gw1_y
            dist1 = py5.sqrt(dx1*dx1 + dy1*dy1)
            
            dx2 = base_x - gw2_x
            dy2 = base_y - gw2_y
            dist2 = py5.sqrt(dx2*dx2 + dy2*dy2)
            
            # Gravity pull (Gaussian-like)
            pull1 = py5.exp(-dist1 * dist1 / 100000) * 150
            pull2 = py5.exp(-dist2 * dist2 / 60000) * -100
            
            # Subtle noise for spacetime foam
            noise_val = py5.os_noise(base_x * 0.005, base_y * 0.005, t * 3) * 20
            
            total_displacement = pull1 + pull2 + noise_val
            
            # Color mapping based on distortion
            distortion_amt = abs(total_displacement)
            if distortion_amt < 10:
                py5.stroke(0, 0, 100, 90) # White
            else:
                hue = (200 + distortion_amt * 2 - t * 360) % 360
                py5.stroke(hue, 80, 100, 90)
                
            py5.vertex(base_x, base_y + total_displacement)
            
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
