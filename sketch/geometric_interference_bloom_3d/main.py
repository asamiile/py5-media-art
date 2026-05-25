from pathlib import Path
import shutil
import subprocess
import sys
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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(240, 90, 5)  # Deep indigo background
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.02
    
    # Create concentric blooming rings
    num_rings = 40
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(num_rings):
        radius = i * 25 + 50
        
        py5.push_matrix()
        # Ripple effect
        z_offset = py5.sin(t * 3 - i * 0.3) * 150
        py5.translate(0, 0, z_offset)
        
        # Rotation
        angle = t * (0.5 + i * 0.02)
        py5.rotate_z(angle)
        py5.rotate_x(py5.sin(t + i * 0.1) * 0.2)
        py5.rotate_y(py5.cos(t + i * 0.1) * 0.2)
        
        # Color transition
        hue = (i * 5 + t * 50) % 360
        py5.stroke(hue, 80, 80, 60)
        
        # Draw a complex polygon
        sides = 6
        py5.begin_shape()
        for j in range(sides):
            theta = py5.TWO_PI * j / sides
            r = radius * (1 + 0.2 * py5.sin(t * 5 + j))
            py5.vertex(r * py5.cos(theta), r * py5.sin(theta), 0)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
