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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

N_PARTICLES = 150000

px = None
py = None
vx = None
vy = None

def setup():
    global px, py, vx, vy
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(20, 10, 5)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    px = np.random.uniform(0, SIZE[0], N_PARTICLES).astype(np.float32)
    py = np.random.uniform(0, SIZE[1], N_PARTICLES).astype(np.float32)
    vx = np.zeros(N_PARTICLES, dtype=np.float32)
    vy = np.zeros(N_PARTICLES, dtype=np.float32)

def chladni_val_and_grad(x, y, n, m, a=1.0, b=1.0):
    # Map coordinates to [-pi, pi] based on screen size
    scale = np.pi / min(SIZE) * 2.0
    sx = (x - SIZE[0]/2) * scale
    sy = (y - SIZE[1]/2) * scale
    
    snx = np.sin(n * sx)
    sny = np.sin(n * sy)
    smx = np.sin(m * sx)
    smy = np.sin(m * sy)
    
    cnx = np.cos(n * sx)
    cny = np.cos(n * sy)
    cmx = np.cos(m * sx)
    cmy = np.cos(m * sy)
    
    L = a * snx * smy + b * smx * sny
    
    dL_dx = (a * n * cnx * smy + b * m * cmx * sny) * scale
    dL_dy = (a * m * snx * cmy + b * n * smx * cny) * scale
    
    fx = -2.0 * L * dL_dx
    fy = -2.0 * L * dL_dy
    
    return fx, fy

def draw():
    global px, py, vx, vy
    
    # Very slight fade for motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(20, 10, 5, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Smoothly transition parameters
    t = py5.frame_count * 0.005
    n = 2.0 + np.sin(t * 1.3) * 1.5
    m = 3.0 + np.cos(t * 0.9) * 2.0
    
    fx, fy = chladni_val_and_grad(px, py, n, m)
    
    # Add some noise to prevent them from getting completely stuck
    noise_str = 2.0
    nx = py5.os_noise(px * 0.01, py * 0.01, t) * 2 - 1
    ny = py5.os_noise(px * 0.01 + 100, py * 0.01 + 100, t) * 2 - 1
    
    # Accelerate
    force_mult = 50.0
    vx += fx * force_mult + nx * noise_str
    vy += fy * force_mult + ny * noise_str
    
    # Drag
    vx *= 0.90
    vy *= 0.90
    
    px += vx
    py += vy
    
    # Keep on screen by wrapping
    px = np.mod(px, SIZE[0])
    py = np.mod(py, SIZE[1])
    
    # Draw points
    py5.blend_mode(py5.ADD)
    py5.stroke(255, 240, 200, 100)
    py5.stroke_weight(1.5)
    
    py5.begin_shape(py5.POINTS)
    for i in range(N_PARTICLES):
        py5.vertex(px[i], py[i])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
