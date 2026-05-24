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

MAX_DEPTH = 8

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(length, depth, t):
    if depth == 0:
        return
        
    py5.stroke_weight(depth * 1.5)
    
    # Map color to depth (leaves are green/cyan, trunk is magenta/purple)
    hue = py5.remap(depth, 1, MAX_DEPTH, 160, 320)
    # Slowly shift colors over time
    hue = (hue + t * 20) % 360
    py5.stroke(hue, 80, 100, 90)
    
    py5.line(0, 0, 0, 0, -length, 0)
    py5.translate(0, -length, 0)
    
    # The branching angle breathes over time
    angle = py5.remap(py5.sin(t * 0.5 + depth * 0.2), -1, 1, py5.PI/8, py5.PI/3)
    
    # We create a 3D split: one branch rotates X, one rotates Z, etc.
    # To make it fully 3D, we branch 3 ways.
    num_branches = 3
    
    for i in range(num_branches):
        py5.push_matrix()
        # Distribute branches evenly around the Y axis
        py5.rotate_y((py5.TWO_PI / num_branches) * i + t * 0.2)
        # Bend the branch outward
        py5.rotate_z(angle)
        
        draw_branch(length * 0.7, depth - 1, t)
        py5.pop_matrix()
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height - 100, 0)
    
    # Orbit the entire tree
    py5.rotate_x(-py5.PI / 6) # Look slightly down
    py5.rotate_y(t * 0.5)
    
    # Start the recursive fractal tree
    # 250px trunk length
    draw_branch(300, MAX_DEPTH, t)

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
