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
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(280, 80, 5) # Deep void space (very dark purple)
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, -200)
    
    # Global time phase for a perfect 10-second loop
    t_phase = (py5.frame_count / TOTAL_FRAMES) * py5.TWO_PI
    
    # Slowly rotate the entire mandala
    py5.rotate_x(t_phase)
    py5.rotate_y(t_phase * 0.5)
    
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    num_curves = 150
    resolution = 400
    
    for i in range(num_curves):
        # Color mapping: Gold (40) to Electric Cyan (180)
        hue = py5.remap(i, 0, num_curves, 40, 180)
        py5.stroke(hue, 90, 80, 70)
        
        py5.begin_shape()
        for j in range(resolution):
            # Parametric path from 0 to 8*PI (4 loops)
            angle = py5.remap(j, 0, resolution - 1, 0, py5.TWO_PI * 4)
            
            # Frequencies
            wx = 3
            wy = 5
            wz = 7
            
            # Modulate phase with curve index and global time to animate
            px = (i * 0.05) + t_phase
            py = (i * 0.08) - t_phase * 2
            pz = (i * 0.03) + t_phase * 1.5
            
            # 3D Lissajous curve with an outer envelope
            envelope = 450 + 150 * np.sin(2 * angle + t_phase)
            x = envelope * np.sin(wx * angle + px)
            y = envelope * np.sin(wy * angle + py)
            z = envelope * np.sin(wz * angle + pz)
            
            # Add some inner geometric spirograph complexity
            x += 100 * np.cos(11 * angle - t_phase)
            y += 100 * np.sin(11 * angle + t_phase)
            z += 100 * np.cos(13 * angle)
            
            py5.curve_vertex(x, y, z)
        py5.end_shape()

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
