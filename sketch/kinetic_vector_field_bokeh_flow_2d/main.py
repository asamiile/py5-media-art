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

# Parameters
NUM_PARTICLES = 300
BRUSH_SIZE = 300

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles
    
    # Initialize particles
    particles = []
    for i in range(NUM_PARTICLES):
        particles.append({
            'x': np.random.uniform(0, py5.width),
            'y': np.random.uniform(0, py5.height),
            'vx': 0.0,
            'vy': 0.0,
            'scale': np.random.uniform(0.1, 1.5),
            'hue': np.random.uniform(180, 300), # Cool hues (cyan to magenta)
            'noise_offset': np.random.uniform(0, 100)
        })

def draw():
    # Subtle fade for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Use the snippet requested by user
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    for p in particles:
        # Vector field movement using noise
        nx = p['x'] * 0.002
        ny = p['y'] * 0.002
        nz = t * 2.0
        
        angle = py5.os_noise(nx, ny, nz) * py5.TWO_PI * 4
        
        # Calculate forces
        force_x = np.cos(angle)
        force_y = np.sin(angle)
        
        p['vx'] += force_x * 0.2
        p['vy'] += force_y * 0.2
        
        # Apply friction
        p['vx'] *= 0.92
        p['vy'] *= 0.92
        
        # Move
        p['x'] += p['vx']
        p['y'] += p['vy']
        
        # Wrap around edges
        if p['x'] < 0: p['x'] += py5.width
        if p['x'] > py5.width: p['x'] -= py5.width
        if p['y'] < 0: p['y'] += py5.height
        if p['y'] > py5.height: p['y'] -= py5.height
        
        # User snippet adapted for stability
        size = BRUSH_SIZE * p['scale'] * (0.8 + 0.2 * np.sin(t * py5.TWO_PI * 3 + p['noise_offset']))
        current_hue = (p['hue'] + py5.frame_count * 0.2) % 360
        
        py5.fill(current_hue, 90, 100, 15)
        py5.circle(p['x'], p['y'], size)
        py5.fill(current_hue, 90, 100, 200)
        py5.circle(p['x'], p['y'], size * 0.1)

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
        import os
        os._exit(0)

py5.run_sketch()
