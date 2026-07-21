from pathlib import Path
import shutil
import subprocess
import sys
import random
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

BRUSH_SIZE = 600
brush = None

NUM_PARTICLES = 80
particles = []

def setup():
    global brush
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create the soft brush
    brush = py5.create_graphics(BRUSH_SIZE, BRUSH_SIZE)
    brush.begin_draw()
    brush.no_stroke()
    for r in range(BRUSH_SIZE, 0, -4):
        # Cubic falloff for softer edges and strong center
        a = 255 * (1.0 - r / BRUSH_SIZE) ** 3
        brush.fill(255, 255, 255, a)
        brush.circle(BRUSH_SIZE/2, BRUSH_SIZE/2, r)
    brush.end_draw()
    
    # Initialize particles
    for i in range(NUM_PARTICLES):
        particles.append({
            'x': random.uniform(0, SIZE[0]),
            'y': random.uniform(0, SIZE[1]),
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(-3, 3),
            'hue': random.uniform(320, 400) % 360, # pinks, purples, reds, oranges
            'scale': random.uniform(0.3, 1.2),
            'noise_offset': random.uniform(0, 1000)
        })
        
    py5.background(10, 0, 10)

def draw():
    # Subtle clear to allow slight trailing
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 0, 10, 50)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    t = py5.frame_count * 0.01
    
    for p in particles:
        # Move
        # Add some curling noise to velocity
        curl_x = (py5.noise(p['x'] * 0.002, p['y'] * 0.002, t + p['noise_offset']) - 0.5) * 2
        curl_y = (py5.noise(p['x'] * 0.002 + 100, p['y'] * 0.002 + 100, t + p['noise_offset']) - 0.5) * 2
        
        p['vx'] = p['vx'] * 0.98 + curl_x * 0.5
        p['vy'] = p['vy'] * 0.98 + curl_y * 0.5
        
        # Pull slightly towards center
        dx = SIZE[0]/2 - p['x']
        dy = SIZE[1]/2 - p['y']
        dist = np.sqrt(dx*dx + dy*dy)
        if dist > 0:
            p['vx'] += (dx / dist) * 0.05
            p['vy'] += (dy / dist) * 0.05
        
        p['x'] += p['vx']
        p['y'] += p['vy']
        
        # Bouncing logic
        if p['x'] < 0 or p['x'] > SIZE[0]: p['vx'] *= -1
        if p['y'] < 0 or p['y'] > SIZE[1]: p['vy'] *= -1
        
        # Draw brush
        size = BRUSH_SIZE * p['scale'] * (0.8 + 0.2 * np.sin(t * 3 + p['noise_offset']))
        
        # Modulate hue slightly
        current_hue = (p['hue'] + py5.frame_count * 0.2) % 360
        
        py5.tint(current_hue, 90, 100, 200)
        py5.image(brush, p['x'] - size/2, p['y'] - size/2, size, size)
    
    # Restore color mode for next frame clear
    py5.color_mode(py5.RGB, 255)

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
