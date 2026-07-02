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
    
    global grid_w, grid_h, cols, rows, scl
    scl = 15
    grid_w = 2000
    grid_h = 2000
    cols = grid_w // scl
    rows = grid_h // scl

def get_wave_height(x, y, t, sources):
    total_h = 0
    total_amp = 0
    for sx, sy, freq, amp, phase in sources:
        dist = np.sqrt((x - sx)**2 + (y - sy)**2)
        total_h += np.sin(dist * freq - t * 4 + phase) * amp
        total_amp += amp
    return total_h, total_amp

def draw():
    # Background
    py5.blend_mode(py5.BLEND)
    py5.background(240, 90, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # Define wave sources that move over time
    sources = [
        (grid_w/2 + np.sin(t*0.5)*500, grid_h/2 + np.cos(t*0.3)*500, 0.02, 120, 0),
        (grid_w/2 + np.cos(t*0.8)*400, grid_h/2 + np.sin(t*0.4)*400, 0.03, 80, 2),
        (grid_w/2 + np.sin(t*1.2)*300, grid_h/2 + np.cos(t*0.7)*600, 0.015, 150, 4)
    ]
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 + 200, -500)
    
    py5.rotate_x(py5.PI / 3 + np.sin(t*0.2) * 0.1)
    py5.rotate_z(t * 0.1)
    
    py5.translate(-grid_w / 2, -grid_h / 2, 0)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Current row
            px1 = x * scl
            py1 = y * scl
            h1, max_h = get_wave_height(px1, py1, t, sources)
            
            # Color based on height and position
            norm_h1 = (h1 + max_h) / (max_h * 2)
            hue1 = (180 + norm_h1 * 120 + t * 20) % 360
            py5.stroke(hue1, 90, 100, 80)
            py5.vertex(px1, py1, h1)
            
            # Next row
            px2 = x * scl
            py2 = (y + 1) * scl
            h2, _ = get_wave_height(px2, py2, t, sources)
            norm_h2 = (h2 + max_h) / (max_h * 2)
            hue2 = (180 + norm_h2 * 120 + t * 20) % 360
            py5.stroke(hue2, 90, 100, 80)
            py5.vertex(px2, py2, h2)
            
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
