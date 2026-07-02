from pathlib import Path
import shutil
import subprocess
import sys
import math
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2 + 300, -500)
    
    time = py5.frame_count * 0.01
    progress = py5.frame_count / TOTAL_FRAMES
    
    py5.rotate_y(progress * py5.TWO_PI)
    py5.rotate_x(math.sin(progress * py5.TWO_PI) * 0.1 - 0.2)
    
    py5.ambient_light(50, 50, 30)
    py5.directional_light(45, 100, 100, 1, 1, -1) # Gold
    py5.directional_light(180, 80, 100, -1, 0, 0) # Cyan
    py5.directional_light(20, 80, 60, 0, -1, 1) # Bronze
    
    # Construct an ancient temple structure
    grid_size = 15
    spacing = 150
    
    # Sacred geometry overlay
    py5.push_matrix()
    py5.translate(0, -600, 0)
    py5.rotate_y(-progress * py5.TWO_PI * 2)
    py5.rotate_x(py5.PI / 2)
    py5.no_fill()
    py5.stroke(180, 80, 100, 150)
    py5.stroke_weight(5)
    for r in range(1, 6):
        py5.ellipse(0, 0, r * 300, r * 300)
    py5.pop_matrix()

    py5.no_stroke()
    
    for x in range(-grid_size // 2, grid_size // 2 + 1):
        for z in range(-grid_size // 2, grid_size // 2 + 1):
            px = x * spacing
            pz = z * spacing
            
            dist_sq = px*px + pz*pz
            if dist_sq > 250000:
                continue
                
            # Height based on distance and noise
            dist = math.sqrt(dist_sq)
            n = py5.noise(x * 0.1, z * 0.1, time * 0.2)
            
            # Dissolve effect
            dissolve = py5.noise(x * 0.05, z * 0.05, time) * 800
            
            h = py5.remap(math.cos(dist * 0.01 + time * 2), -1, 1, 100, 800)
            h *= n
            
            if h < dissolve:
                # Draw floating glowing dust instead
                py5.push_matrix()
                py5.translate(px, -dissolve, pz)
                py5.fill(180, 80, 100, 200) # Cyan dust
                py5.box(10)
                py5.pop_matrix()
                continue
                
            py5.push_matrix()
            py5.translate(px, -h / 2, pz)
            
            # Bronze/Gold depending on height
            if h > 500:
                py5.fill(45, 80, 90) # Gold
            else:
                py5.fill(30, 70, 50) # Bronze
                
            py5.box(spacing * 0.8, h, spacing * 0.8)
            py5.pop_matrix()
            
            # Top cap
            py5.push_matrix()
            py5.translate(px, -h, pz)
            py5.fill(45, 100, 100) # Bright gold
            py5.sphere(spacing * 0.4)
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
