from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

SLICES = 12
SLICE_ANGLE = py5.TWO_PI / SLICES

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_base_segment(t):
    # Draw complex, abstract, asymmetrical geometry inside the base slice
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(15):
        # Parametric curves driven by time and index
        # We constrain the base shape roughly within the SLICE_ANGLE pie slice
        r = py5.remap(i, 0, 15, 50, 450)
        
        # Noise-driven control points
        c1x = r * py5.cos(py5.noise(i, t * 0.5) * SLICE_ANGLE)
        c1y = r * py5.sin(py5.noise(i, t * 0.5) * SLICE_ANGLE)
        
        c2x = (r + 100) * py5.cos(py5.noise(i + 10, t * 0.4) * SLICE_ANGLE)
        c2y = (r + 100) * py5.sin(py5.noise(i + 10, t * 0.4) * SLICE_ANGLE)
        
        c3x = (r + 200) * py5.cos(py5.noise(i + 20, t * 0.3) * SLICE_ANGLE)
        c3y = (r + 200) * py5.sin(py5.noise(i + 20, t * 0.3) * SLICE_ANGLE)
        
        c4x = (r + 300) * py5.cos(py5.noise(i + 30, t * 0.2) * SLICE_ANGLE)
        c4y = (r + 300) * py5.sin(py5.noise(i + 30, t * 0.2) * SLICE_ANGLE)
        
        # Dynamic color
        hue = (i * 20 + t * 50) % 360
        py5.stroke(hue, 90, 100, 80)
        
        # Draw elegant bezier curves
        py5.bezier(c1x, c1y, 0, c2x, c2y, py5.sin(t+i)*50, c3x, c3y, py5.cos(t+i)*50, c4x, c4y, 0)
        
        # Add some glowing nodes
        if py5.noise(i, t) > 0.6:
            py5.push_matrix()
            py5.translate(c4x, c4y, 0)
            py5.no_stroke()
            py5.fill((hue + 180) % 360, 80, 100, 90)
            py5.circle(0, 0, 10)
            py5.pop_matrix()

def draw():
    # Motion blur background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 8, 25)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Global rotation
    py5.rotate_z(-t * 0.1)
    
    # Kaleidoscope reflection logic
    for i in range(SLICES):
        py5.push_matrix()
        # Rotate to the current slice
        py5.rotate_z(i * SLICE_ANGLE)
        
        # Every odd slice is flipped (mirrored) to create perfect symmetry
        if i % 2 == 1:
            py5.scale(1, -1)
            
        draw_base_segment(t)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
