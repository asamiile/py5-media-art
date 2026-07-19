from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_RINGS = 30
rings = []
for i in range(NUM_RINGS):
    r_inner = (i + 1) * 35
    r_outer = r_inner + random.uniform(5, 20)
    speed = random.uniform(-0.02, 0.02)
    segments = random.randint(3, 24)
    # Give random gap size to this ring so it doesn't change every frame
    gap_ratio = random.uniform(0.1, 0.5)
    rings.append({'inner': r_inner, 'outer': r_outer, 'speed': speed, 'segments': segments, 'gap_ratio': gap_ratio})

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    t = py5.frame_count
    
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.no_stroke()
    py5.fill(220)
    
    for ring in rings:
        py5.push_matrix()
        py5.rotate(t * ring['speed'])
        
        angle_step = py5.TWO_PI / ring['segments']
        gap = angle_step * ring['gap_ratio']
        
        for i in range(ring['segments']):
            start_angle = i * angle_step
            end_angle = start_angle + angle_step - gap
            
            py5.begin_shape()
            for a in np.linspace(start_angle, end_angle, 10):
                py5.vertex(np.cos(a) * ring['outer'], np.sin(a) * ring['outer'])
            for a in np.linspace(end_angle, start_angle, 10):
                py5.vertex(np.cos(a) * ring['inner'], np.sin(a) * ring['inner'])
            py5.end_shape(py5.CLOSE)
            
            # Use deterministic seed for blinking red dots based on frame and segment
            random.seed(t // 5 + i * 100)
            if random.random() < 0.1:
                py5.fill(255, 50, 50)
                mid_angle = (start_angle + end_angle) / 2
                py5.ellipse(np.cos(mid_angle) * (ring['inner'] + 5), np.sin(mid_angle) * (ring['inner'] + 5), 5, 5)
                py5.fill(220)
                
        py5.pop_matrix()
        
    py5.pop_matrix()
    
    # Restore random state for glitch effects
    random.seed()
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    if random.random() < 0.15:
        if random.random() < 0.5:
            shift = random.randint(5, 50)
            pixels[:, :-shift, 0] = pixels[:, shift:, 0] 
            pixels[:, shift:, 2] = pixels[:, :-shift, 2] 
            
        num_bands = random.randint(1, 5)
        for _ in range(num_bands):
            y_start = random.randint(0, SIZE[1] - 100)
            band_height = random.randint(10, 100)
            y_end = min(y_start + band_height, SIZE[1])
            shift = random.randint(-150, 150)
            
            if shift > 0:
                pixels[y_start:y_end, shift:] = pixels[y_start:y_end, :-shift].copy()
            elif shift < 0:
                pixels[y_start:y_end, :shift] = pixels[y_start:y_end, -shift:].copy()
                
    py5.set_np_pixels(pixels)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
