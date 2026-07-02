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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def draw_spiral(arms, turns, max_radius):
    py5.begin_shape(py5.LINES)
    # Use vectorized numpy for speed
    t = np.linspace(0, turns * 2 * np.pi, 500)
    
    # We want thick bands, so we draw multiple closely spaced lines or use thick stroke
    for a in range(arms):
        angle_offset = (2 * np.pi / arms) * a
        # Logarithmic spiral
        r = np.exp(0.15 * t) * (max_radius / np.exp(0.15 * turns * 2 * np.pi))
        x = r * np.cos(t + angle_offset)
        y = r * np.sin(t + angle_offset)
        
        for i in range(len(t) - 1):
            py5.vertex(x[i], y[i])
            py5.vertex(x[i+1], y[i+1])
    py5.end_shape()

def draw_concentric_circles(num_circles, max_radius, thickness):
    for i in range(num_circles):
        r = (i + 1) * max_radius / num_circles
        py5.stroke_weight(thickness)
        py5.ellipse(0, 0, r * 2, r * 2)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Force a solid background every frame to clean the buffer
    py5.background(255)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Base Layer: Concentric circles
    py5.no_fill()
    py5.stroke(0)
    
    # Slowly scale the base circles for a pulsing effect
    pulse = 1.0 + 0.1 * np.sin(py5.frame_count * 0.05)
    py5.push_matrix()
    py5.scale(pulse)
    draw_concentric_circles(50, py5.width, 15)
    py5.pop_matrix()
    
    # Second Layer: Logarithmic Spirals overlapping with DIFFERENCE blend mode
    # to create intense Op Art moire patterns
    py5.blend_mode(py5.DIFFERENCE)
    
    py5.push_matrix()
    # Counter-rotate
    py5.rotate(-py5.frame_count * 0.01)
    py5.stroke(255) # White stroke against DIFFERENCE turns black over white, white over black
    py5.stroke_weight(25)
    draw_spiral(16, 5, py5.width * 1.5)
    py5.pop_matrix()
    
    # Third Layer: Another set of spirals rotating differently
    py5.push_matrix()
    py5.rotate(py5.frame_count * 0.015)
    py5.stroke(255)
    py5.stroke_weight(15)
    draw_spiral(8, 6, py5.width * 1.5)
    py5.pop_matrix()
    
    # Accent flash
    py5.blend_mode(py5.BLEND)
    if (py5.frame_count % 120) > 110:
        py5.fill(255, 0, 50, 100) # Neon red flash
        py5.no_stroke()
        py5.ellipse(0, 0, py5.width * 3, py5.width * 3)

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
