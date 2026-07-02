from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
GRID_SIZE = 30
SPACING = 30
MAX_HEIGHT = 200

# Pre-calculate building heights and start times
heights = {}
start_times = {}

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize the city grid
    cx, cz = GRID_SIZE / 2, GRID_SIZE / 2
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            dist_to_center = py5.dist(x, z, cx, cz)
            # Higher buildings towards center, but with noise variation
            base_h = py5.remap(dist_to_center, 0, GRID_SIZE * 0.7, MAX_HEIGHT, 10)
            base_h = max(10, base_h)
            noise_val = py5.os_noise(x * 0.1, z * 0.1)
            final_h = base_h * noise_val * 2
            heights[(x, z)] = final_h
            
            # Start times propagate outwards with some randomness
            start_times[(x, z)] = int(dist_to_center * 15 + random.uniform(0, 30))

def draw():
    py5.background(15, 10, 15) # Dark space
    
    py5.ambient_light(200, 40, 30)
    py5.directional_light(200, 80, 100, -1, 1, -1)
    py5.directional_light(30, 60, 80, 1, 0, 0)
    
    # Set isometric view
    py5.ortho(-py5.width/2, py5.width/2, -py5.height/2, py5.height/2, -5000, 5000)
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(-py5.asin(1 / py5.sqrt(3)))
    py5.rotate_y(py5.PI / 4)
    
    # Slight rotation over time for dynamic feel
    py5.rotate_y(py5.frame_count * 0.002)
    
    offset = (GRID_SIZE * SPACING) / 2
    py5.translate(-offset, 0, -offset)
    
    py5.no_stroke()
    
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            start = start_times[(x, z)]
            target_h = heights[(x, z)]
            
            if py5.frame_count < start:
                continue
                
            # Elastic easing for height
            t = (py5.frame_count - start) / 120.0 # 2 seconds to build
            t = min(1.0, max(0.0, t))
            
            # easeOutElastic
            c4 = (2 * py5.PI) / 3
            if t == 0:
                h = 0
            elif t == 1:
                h = target_h
            else:
                h = target_h * ((2 ** (-10 * t)) * py5.sin((t * 10 - 0.75) * c4) + 1)
            
            py5.push_matrix()
            py5.translate(x * SPACING, -h/2, z * SPACING)
            
            # Coloring: active building phase glows orange, established is cool blue/cyan
            if t < 1.0:
                py5.fill(30, 80, 100) # Orange glow
                py5.emissive(30, 80, 50)
            else:
                h_ratio = target_h / MAX_HEIGHT
                hue = py5.lerp(200, 260, h_ratio)
                py5.fill(hue, 80, 80)
                py5.emissive(0, 0, 0)
                
            py5.box(SPACING * 0.8, h, SPACING * 0.8)
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
