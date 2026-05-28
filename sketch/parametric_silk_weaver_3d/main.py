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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Keep trails by adding a black transparent box in front of camera
    # P3D requires disabling depth test for 2D background overlay or just using hint
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    # Reset matrix for overlay
    py5.push_matrix()
    py5.camera()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    py5.hint(py5.ENABLE_DEPTH_TEST)

    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2, -200)
    py5.rotate_x(time * 0.3)
    py5.rotate_y(time * 0.5)
    py5.rotate_z(time * 0.2)
    
    num_strands = 100
    points_per_strand = 300
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(num_strands):
        # Base angle for this strand
        offset = i * (2 * np.pi / num_strands)
        
        py5.begin_shape(py5.LINE_STRIP)
        
        # Color based on strand index and time
        hue = (i * (360 / num_strands) + time * 50) % 360
        # constrain palette to Magenta (300) -> Red (0) -> Gold (50) -> Cyan (180)
        # Just use a mapped palette instead
        if i % 3 == 0:
            py5.stroke(300, 90, 100, 30) # Magenta
        elif i % 3 == 1:
            py5.stroke(50, 90, 100, 30) # Gold
        else:
            py5.stroke(180, 90, 100, 30) # Cyan
            
        for t in range(points_per_strand):
            pt = t * 0.05
            
            # Parametric Lissajous 3D
            r = 600 * np.sin(pt * 0.5 + time + offset)
            x = r * np.sin(pt * 3 + offset) * np.cos(pt * 2)
            y = r * np.sin(pt * 3 + offset) * np.sin(pt * 2)
            z = r * np.cos(pt * 3 + offset)
            
            py5.vertex(x, y, z)
            
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
