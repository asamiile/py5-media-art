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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(length, depth, max_depth, t):
    if depth == 0:
        return
        
    # Draw the current branch segment
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 0.5, 12))
    
    # Color based on depth and time
    hue = (120 + depth * 25 + t * 50) % 360
    brightness = py5.remap(depth, 0, max_depth, 100, 50)
    py5.stroke(hue, 80, brightness, 80)
    
    py5.line(0, 0, 0, 0, -length, 0)
    
    # Move to the end of the branch
    py5.translate(0, -length, 0)
    
    # Wind sway factor using Perlin noise
    sway = py5.noise(depth * 0.1, t * 1.5) * py5.PI / 8 - py5.PI / 16
    
    # Spawn 3 child branches in 3D space
    num_branches = 3
    angle_spread = py5.PI / 3 + py5.sin(t + depth * 0.5) * 0.2
    
    for i in range(num_branches):
        py5.push_matrix()
        
        # Rotate around Y axis to spread branches outward in a circle
        py5.rotate_y(i * py5.TWO_PI / num_branches + t * 0.5 * (1 if depth % 2 == 0 else -1))
        
        # Tilt outwards and add wind sway
        py5.rotate_z(angle_spread + sway)
        
        # Add some curl
        py5.rotate_x(py5.sin(t * 2 + depth) * 0.1)
        
        # Recursive call with shorter length
        draw_branch(length * 0.65, depth - 1, max_depth, t)
        
        py5.pop_matrix()

def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height, 0)
    
    # Spin the entire tree slowly
    py5.rotate_y(t * 0.3)
    
    # Tilt the camera slightly down
    py5.rotate_x(-py5.PI / 8)
    
    # Move up slightly so the base isn't completely off-screen
    py5.translate(0, py5.height * 0.2, 0)
    
    # Start recursive branching
    max_depth = 9
    initial_length = 350.0
    draw_branch(initial_length, max_depth, max_depth, t)

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
