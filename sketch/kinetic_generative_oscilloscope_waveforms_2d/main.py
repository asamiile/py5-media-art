from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    py5.no_fill()

def draw():
    py5.background(120, 100, 5, 20)  # Very dark green background
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count / FPS
    
    num_lines = 10
    points_per_line = 3000
    
    for i in range(num_lines):
        py5.begin_shape(py5.LINE_STRIP)
        
        hue = 120 + i * 5  # Terminal phosphor green variations
        py5.stroke(hue, 90, 90, 50)
        py5.stroke_weight(2)
        
        freq_x = 3 + py5.os_noise(i * 0.1, t * 0.2) * 5
        freq_y = 4 + py5.os_noise(i * 0.1 + 10, t * 0.2) * 5
        phase_x = t * (1 + i * 0.1)
        phase_y = t * (1.2 + i * 0.1)
        
        for p in range(points_per_line):
            pt = p / points_per_line * py5.TWO_PI
            
            # AM and FM modulation
            mod_x = math.sin(pt * 15 + t * 5) * 0.1
            mod_y = math.sin(pt * 12 + t * 4) * 0.1
            
            x = math.sin((pt + mod_x) * freq_x + phase_x) * (py5.width * 0.4)
            y = math.sin((pt + mod_y) * freq_y + phase_y) * (py5.height * 0.4)
            
            # Apply distortion
            distortion = py5.os_noise(x * 0.005, y * 0.005, t) * 50
            
            py5.vertex(x + distortion, y + distortion)
            
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
