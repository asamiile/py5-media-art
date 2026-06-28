from pathlib import Path
import shutil
import subprocess
import sys
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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global num_particles, px, py, vx, vy
    num_particles = 150_000
    
    # Initialize particles randomly across the screen
    # Normalizing coordinates between 0 and 1
    px = np.random.uniform(0, 1, num_particles)
    py = np.random.uniform(0, 1, num_particles)
    
    vx = np.zeros(num_particles)
    vy = np.zeros(num_particles)

def draw():
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 5, 0, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global px, py, vx, vy
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Morphing parameters for Chladni patterns
    # N and M control the mode of vibration
    n = np.interp(np.sin(t * py5.TWO_PI), [-1, 1], [2, 6])
    m = np.interp(np.cos(t * py5.TWO_PI * 0.7), [-1, 1], [3, 8])
    
    # Chladni function and its gradient
    # Z = sin(n*pi*x)*sin(m*pi*y) + sin(m*pi*x)*sin(n*pi*y)
    
    # Precalculate terms
    snx = np.sin(n * np.pi * px)
    sny = np.sin(n * np.pi * py)
    smx = np.sin(m * np.pi * px)
    smy = np.sin(m * np.pi * py)
    
    cnx = np.cos(n * np.pi * px)
    cny = np.cos(n * np.pi * py)
    cmx = np.cos(m * np.pi * px)
    cmy = np.cos(m * np.pi * py)
    
    # The gradient of Z squared (points move to Z=0)
    # Z = snx*smy + smx*sny
    z = snx * smy + smx * sny
    
    # dz/dx
    dzdx = (n * np.pi * cnx * smy) + (m * np.pi * cmx * sny)
    # dz/dy
    dzdy = (m * np.pi * snx * cmy) + (n * np.pi * smx * cny)
    
    # Force is negative gradient of Z^2 -> -2 * Z * gradient
    fx = -2 * z * dzdx
    fy = -2 * z * dzdy
    
    # Add random jitter so they don't get perfectly stuck
    fx += np.random.normal(0, 0.5, num_particles)
    fy += np.random.normal(0, 0.5, num_particles)
    
    # Update velocity with friction
    vx = vx * 0.8 + fx * 0.0001
    vy = vy * 0.8 + fy * 0.0001
    
    # Update positions
    px += vx
    py += vy
    
    # Keep inside bounds [0, 1]
    px = np.clip(px, 0.001, 0.999)
    py = np.clip(py, 0.001, 0.999)
    
    # Map to screen
    screen_x = px * py5.width
    screen_y = py * py5.height
    
    verts = np.column_stack((screen_x, screen_y))
    
    # Draw
    py5.no_fill()
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    
    # Glowing golden sand
    py5.stroke(255, 200, 100, 100)
    py5.vertices(verts)
    
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
