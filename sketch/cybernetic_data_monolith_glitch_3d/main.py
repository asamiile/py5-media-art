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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
def draw():
    py5.background(10, 12, 15) # Near black
    
    # Lighting
    py5.ambient_light(50, 50, 50)
    py5.directional_light(200, 200, 200, -1, 1, -1)
    py5.point_light(0, 255, 100, py5.width/2, 0, 200) # Green top light
    py5.point_light(255, 0, 255, py5.width/2, py5.height, 200) # Magenta bottom light
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    t = py5.frame_count * 0.02
    
    # Slow rotation
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.002)
    
    cols, rows = 30, 80
    box_w, box_h = 20, 20
    monolith_width = cols * box_w
    monolith_height = rows * box_h
    
    py5.translate(-monolith_width/2, -monolith_height/2, 0)
    
    # Glitch wave
    glitch_y = (py5.frame_count * 15) % monolith_height
    
    for x in range(cols):
        for y in range(rows):
            
            px = x * box_w
            py = y * box_h
            
            # Base displacement
            n = py5.os_noise(x * 0.1, y * 0.05, t)
            pz = n * 150
            
            # Glitch effect
            is_glitching = abs(py - glitch_y) < 50
            
            py5.push_matrix()
            
            if is_glitching:
                # Random horizontal displacement
                gx = (py5.random(-50, 50)) if py5.random(1) > 0.5 else 0
                py5.translate(px + gx, py, pz)
                
                if py5.random(1) > 0.5:
                    py5.fill(255, 0, 255, 200) # Magenta
                else:
                    py5.fill(0, 255, 100, 200) # Green
            else:
                py5.translate(px, py, pz)
                
                # Base color
                c = 40 + n * 100
                py5.fill(c, c, c+10) # Brutalist grey
                
            # Draw block
            if n > 0.6 and not is_glitching:
                # High data node
                py5.fill(0, 255, 100, 255) # Hacker green data streams
                py5.box(box_w * 0.8, box_h * 0.8, box_w + n * 50)
            else:
                # Normal block
                py5.box(box_w * 0.9, box_h * 0.9, box_w)
                
            py5.pop_matrix()
            
            # Add scattered glowing data points on surface
            if py5.random(1) < 0.02 and not is_glitching:
                py5.push_matrix()
                py5.translate(px, py, pz + box_w/2 + 5)
                py5.fill(0, 255, 150, 255)
                py5.box(4)
                py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

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
