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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_LINES = 300
MAX_RADIUS = 1500

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_radial_burst(inner, outer, num, hue, alpha):
    py5.stroke(hue, 80, 100, alpha)
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for i in range(num):
        angle = py5.TWO_PI * i / num
        py5.vertex(py5.cos(angle) * inner, py5.sin(angle) * inner)
        py5.vertex(py5.cos(angle) * outer, py5.sin(angle) * outer)
    py5.end_shape()

def draw_concentric_rings(num, spacing, hue, alpha):
    py5.stroke(hue, 80, 100, alpha)
    py5.stroke_weight(4)
    py5.no_fill()
    for i in range(1, num):
        py5.circle(0, 0, i * spacing * 2)

def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.005
    
    # Enable additive blending
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Layer 1: Base radial burst rotating clockwise
    py5.push_matrix()
    py5.rotate(t)
    draw_radial_burst(50, MAX_RADIUS, 200, (py5.frame_count * 0.5) % 360, 60)
    py5.pop_matrix()
    
    # Layer 2: Offset radial burst rotating counter-clockwise
    py5.push_matrix()
    # Move the center slightly to create asymmetrical moire
    py5.translate(py5.sin(t*2) * 50, py5.cos(t*2) * 50)
    py5.rotate(-t * 1.1)
    draw_radial_burst(50, MAX_RADIUS, 200, (py5.frame_count * 0.5 + 120) % 360, 60)
    py5.pop_matrix()
    
    # Layer 3: Expanding concentric rings
    py5.push_matrix()
    # Scale pulses
    scale_factor = 1.0 + py5.sin(t * 5) * 0.1
    py5.scale(scale_factor)
    draw_concentric_rings(80, 15, (py5.frame_count * 0.5 + 240) % 360, 80)
    py5.pop_matrix()
    
    # Layer 4: Contracting concentric rings
    py5.push_matrix()
    py5.translate(py5.sin(-t*3) * 30, py5.cos(-t*3) * 30)
    scale_factor_2 = 1.0 + py5.cos(t * 4) * 0.1
    py5.scale(scale_factor_2)
    draw_concentric_rings(80, 14, 0, 0) # Use white
    py5.stroke(0, 0, 100, 50)
    py5.stroke_weight(3)
    py5.no_fill()
    for i in range(1, 80):
        py5.circle(0, 0, i * 14 * 2)
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
