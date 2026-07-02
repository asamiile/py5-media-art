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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid of filings
cols = 120
rows = 80

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(15, 10, 10) # Dark base
    
    time = py5.frame_count * 0.02
    
    w = SIZE[0] / cols
    h = SIZE[1] / rows
    
    py5.blend_mode(py5.ADD)
    
    # Magnets
    m1_x = SIZE[0]/2 + py5.sin(time * 0.5) * 600
    m1_y = SIZE[1]/2 + py5.cos(time * 0.4) * 400
    m1_strength = 50000.0
    
    m2_x = SIZE[0]/2 + py5.sin(-time * 0.3) * 800
    m2_y = SIZE[1]/2 + py5.cos(-time * 0.6) * 500
    m2_strength = -40000.0 # Repulsor
    
    m3_x = SIZE[0]/2 + py5.cos(time * 0.2) * 500
    m3_y = SIZE[1]/2 + py5.sin(time * 0.3) * 600
    m3_strength = 60000.0
    
    for i in range(cols):
        for j in range(rows):
            x = i * w + w/2
            y = j * h + h/2
            
            # Calculate field vectors
            dx1 = x - m1_x; dy1 = y - m1_y
            d1_sq = dx1*dx1 + dy1*dy1 + 1000
            vx1 = (dx1 / d1_sq) * m1_strength
            vy1 = (dy1 / d1_sq) * m1_strength
            
            dx2 = x - m2_x; dy2 = y - m2_y
            d2_sq = dx2*dx2 + dy2*dy2 + 1000
            vx2 = (dx2 / d2_sq) * m2_strength
            vy2 = (dy2 / d2_sq) * m2_strength
            
            dx3 = x - m3_x; dy3 = y - m3_y
            d3_sq = dx3*dx3 + dy3*dy3 + 1000
            vx3 = (dx3 / d3_sq) * m3_strength
            vy3 = (dy3 / d3_sq) * m3_strength
            
            vx = vx1 + vx2 + vx3
            vy = vy1 + vy2 + vy3
            
            angle = py5.atan2(vy, vx)
            mag = py5.sqrt(vx*vx + vy*vy)
            
            # Add some perlin noise for organic look
            n = py5.os_noise(i * 0.1, j * 0.1, time * 0.2)
            angle += (n - 0.5) * 0.5
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(angle)
            
            length = py5.remap(mag, 0, 100, w*0.2, w*1.5)
            if length > w*2: length = w*2
            
            hue = (mag * 2 + time * 20) % 360
            
            # Iron filing
            py5.stroke(hue, 80, 100, 80)
            py5.stroke_weight(2)
            py5.line(-length/2, 0, length/2, 0)
            
            # Glowing tip
            py5.no_stroke()
            py5.fill(0, 0, 100, 90)
            py5.ellipse(length/2, 0, 4, 4)
            
            py5.pop_matrix()
            
    py5.blend_mode(py5.BLEND)

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
