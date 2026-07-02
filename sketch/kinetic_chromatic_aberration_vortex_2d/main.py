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
DURATION_SEC = 15  # 15 seconds for reasonable render time
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 15000
particles = None

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # particles array: [angle, radius, base_size, speed_offset]
    particles = np.zeros((NUM_PARTICLES, 4))
    particles[:, 0] = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    # Distribute them mostly far away
    particles[:, 1] = np.random.uniform(50, SIZE[0] * 1.5, NUM_PARTICLES)
    particles[:, 2] = np.random.uniform(5, 50, NUM_PARTICLES)
    particles[:, 3] = np.random.uniform(0.5, 3.0, NUM_PARTICLES)

def draw_layer(cx, cy, angles, radii, sizes, r_offset, a_offset, color):
    r = radii + r_offset
    a = angles + a_offset
    x = cx + r * np.cos(a)
    y = cy + r * np.sin(a)
    
    half = sizes / 2.0
    
    # We want to rotate these corners by angle a + continuous rotation over time
    rot = a * 2.0 # local rotation
    cos_a = np.cos(rot)
    sin_a = np.sin(rot)
    
    tl_x = -half * cos_a - (-half) * sin_a
    tl_y = -half * sin_a + (-half) * cos_a
    
    tr_x = half * cos_a - (-half) * sin_a
    tr_y = half * sin_a + (-half) * cos_a
    
    br_x = half * cos_a - half * sin_a
    br_y = half * sin_a + half * cos_a
    
    bl_x = -half * cos_a - half * sin_a
    bl_y = -half * sin_a + half * cos_a
    
    quads = np.zeros((NUM_PARTICLES * 4, 2))
    quads[0::4, 0] = x + tl_x
    quads[0::4, 1] = y + tl_y
    quads[1::4, 0] = x + tr_x
    quads[1::4, 1] = y + tr_y
    quads[2::4, 0] = x + br_x
    quads[2::4, 1] = y + br_y
    quads[3::4, 0] = x + bl_x
    quads[3::4, 1] = y + bl_y
    
    py5.fill(*color)
    py5.begin_shape(py5.QUADS)
    py5.vertices(quads)
    py5.end_shape()

def draw():
    global particles
    
    # Motion blur effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 60)
    py5.rect(0, 0, SIZE[0]*2, SIZE[1]*2)
    
    py5.blend_mode(py5.ADD)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    # Update logic
    particles[:, 0] += 0.005 * particles[:, 3] # Orbit speed
    particles[:, 1] -= 3.0 * particles[:, 3]   # Inward pull
    
    # Reset particles that fall into the center hole
    reset_mask = particles[:, 1] < 20
    num_reset = np.sum(reset_mask)
    if num_reset > 0:
        particles[reset_mask, 1] = np.random.uniform(SIZE[0]*1.2, SIZE[0]*1.5, num_reset)
        particles[reset_mask, 0] = np.random.uniform(0, np.pi * 2, num_reset)
    
    angles = particles[:, 0]
    radii = particles[:, 1]
    
    # Perspective scaling: smaller as they get closer, but also warped by gravity
    sizes = particles[:, 2] * np.clip(radii / 1000.0, 0.1, 2.0)
    
    # Aberration is stronger near the center
    aberration = 1500.0 / (radii + 50.0)
    
    draw_layer(cx, cy, angles, radii, sizes,  aberration,  aberration*0.001, (255, 30, 30, 180)) # Red
    draw_layer(cx, cy, angles, radii, sizes,  0,           0,                (30, 255, 30, 180)) # Green
    draw_layer(cx, cy, angles, radii, sizes, -aberration, -aberration*0.001, (30, 30, 255, 180)) # Blue

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
