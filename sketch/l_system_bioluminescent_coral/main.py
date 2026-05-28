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

# L-System definitions
axiom = "X"
rules = {
    "X": "F+[[X]-X]-F[-FX]+X",
    "F": "FF"
}

def generate_lsystem(iters):
    current = axiom
    for _ in range(iters):
        next_seq = ""
        for char in current:
            next_seq += rules.get(char, char)
        current = next_seq
    return current

lsys = ""
MAX_DEPTH = 6

def setup():
    global lsys
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    lsys = generate_lsystem(MAX_DEPTH)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)
    py5.no_stroke()
    
    # Draw background
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.push_matrix()
    py5.camera()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    py5.hint(py5.ENABLE_DEPTH_TEST)
    
    py5.blend_mode(py5.ADD)

    time = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height)
    py5.rotate_x(py5.PI / 8) # slightly tilt back
    
    # Draw L-system
    length = 15.0
    angle = py5.radians(25) + np.sin(time * 0.5) * 0.05
    
    py5.stroke_weight(2)
    
    depth = 0
    hue_base = 180 + np.sin(time * 0.2) * 20
    
    for char in lsys:
        if char == "F":
            h = (hue_base + depth * 5) % 360
            py5.stroke(h, 90, 100, 50)
            py5.line(0, 0, 0, 0, -length, 0)
            py5.translate(0, -length, 0)
        elif char == "+":
            # swaying rotation
            sway = np.sin(time + depth * 0.1) * 0.1
            py5.rotate_z(angle + sway)
            py5.rotate_y(sway * 0.5)
        elif char == "-":
            sway = np.cos(time + depth * 0.1) * 0.1
            py5.rotate_z(-angle + sway)
            py5.rotate_y(sway * 0.5)
        elif char == "[":
            py5.push_matrix()
            depth += 1
        elif char == "]":
            py5.pop_matrix()
            depth -= 1

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
