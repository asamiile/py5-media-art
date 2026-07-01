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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_MANDALAS = 500
NUM_EPICYCLES = 7

# Data structures
# We have NUM_MANDALAS mandalas, each defined by NUM_EPICYCLES complex coefficients (magnitude, frequency, phase)
magnitudes = np.zeros((NUM_MANDALAS, NUM_EPICYCLES))
frequencies = np.zeros((NUM_MANDALAS, NUM_EPICYCLES))
phases = np.zeros((NUM_MANDALAS, NUM_EPICYCLES))
centers_x = np.zeros(NUM_MANDALAS)
centers_y = np.zeros(NUM_MANDALAS)
colors = np.zeros((NUM_MANDALAS, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize data
    for i in range(NUM_MANDALAS):
        # Position them in a large circle or spiral
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(0, SIZE[0] / 2 * 0.9)
        centers_x[i] = SIZE[0] / 2 + radius * np.cos(angle)
        centers_y[i] = SIZE[1] / 2 + radius * np.sin(angle)
        
        # Colors (vibrant neon)
        hue = np.random.uniform(0, 1)
        # simplistic hsv to rgb mapping for neon colors (mostly cyan, magenta, yellow)
        if hue < 0.33:
            colors[i] = [0, 255, np.random.randint(150, 255)] # Cyan-ish
        elif hue < 0.66:
            colors[i] = [255, 0, np.random.randint(150, 255)] # Magenta-ish
        else:
            colors[i] = [255, np.random.randint(150, 255), 0] # Yellow/Orange-ish
            
        # Epicycles
        for j in range(NUM_EPICYCLES):
            magnitudes[i, j] = np.random.uniform(10, 100) / (j + 1)
            # Frequencies are integer multiples for closed loops
            frequencies[i, j] = np.random.choice([-3, -2, -1, 1, 2, 3, 4, 5]) * (j + 1)
            phases[i, j] = np.random.uniform(0, 2 * np.pi)

def draw():
    # Subtle motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 20, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # We want to draw the continuous path of the epicycles
    # To avoid dotted lines, we'll draw a short line segment from previous t to current t
    t_prev = t - 0.02
    
    # Calculate current positions
    # Vectorized evaluation: sum of C_n * exp(i * (freq * t + phase))
    # X = sum(mag * cos(freq * t + phase)), Y = sum(mag * sin(freq * t + phase))
    
    # Broadcast t into the arrays
    angles_curr = frequencies * t + phases
    angles_prev = frequencies * t_prev + phases
    
    x_curr = centers_x + np.sum(magnitudes * np.cos(angles_curr), axis=1)
    y_curr = centers_y + np.sum(magnitudes * np.sin(angles_curr), axis=1)
    
    x_prev = centers_x + np.sum(magnitudes * np.cos(angles_prev), axis=1)
    y_prev = centers_y + np.sum(magnitudes * np.sin(angles_prev), axis=1)
    
    # Add a slow global rotation and zoom for extra kinetic feel
    global_rot = t * 0.1
    cx, cy = SIZE[0]/2, SIZE[1]/2
    
    def transform(x, y, angle):
        # Rotate around center
        dx = x - cx
        dy = y - cy
        rx = dx * np.cos(angle) - dy * np.sin(angle)
        ry = dx * np.sin(angle) + dy * np.cos(angle)
        
        # Zoom gently
        zoom = 1.0 + 0.2 * np.sin(t * 0.5)
        return cx + rx * zoom, cy + ry * zoom
        
    x_curr_t, y_curr_t = transform(x_curr, y_curr, global_rot)
    x_prev_t, y_prev_t = transform(x_prev, y_prev, global_rot - 0.1 * 0.02)
    
    # Format into line segments for py5.vertices(LINES)
    # Shape needs to be (NUM_MANDALAS * 2, 2)
    verts = np.zeros((NUM_MANDALAS * 2, 2))
    verts[0::2, 0] = x_prev_t
    verts[0::2, 1] = y_prev_t
    verts[1::2, 0] = x_curr_t
    verts[1::2, 1] = y_curr_t
    
    # We can't set per-vertex colors easily with py5.vertices without vertex_colors
    # But we can loop over color buckets to draw them incredibly fast
    # Let's just group them into our 3 main buckets (Cyan, Magenta, Yellow)
    
    cyan_mask = colors[:, 0] == 0
    magenta_mask = colors[:, 1] == 0
    yellow_mask = colors[:, 2] == 0
    
    def draw_bucket(mask, r, g, b):
        if not np.any(mask): return
        
        bucket_verts = np.zeros((np.sum(mask) * 2, 2))
        bucket_verts[0::2, 0] = x_prev_t[mask]
        bucket_verts[0::2, 1] = y_prev_t[mask]
        bucket_verts[1::2, 0] = x_curr_t[mask]
        bucket_verts[1::2, 1] = y_curr_t[mask]
        
        py5.stroke(r, g, b, 200)
        py5.stroke_weight(3)
        py5.begin_shape(py5.LINES)
        py5.vertices(bucket_verts)
        py5.end_shape()

    draw_bucket(cyan_mask, 0, 255, 200)
    draw_bucket(magenta_mask, 255, 0, 200)
    draw_bucket(yellow_mask, 255, 200, 0)

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
