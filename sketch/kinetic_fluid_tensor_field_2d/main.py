from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

particles = None

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    num_particles = 20000
    
    # [x, y, age, max_age, major_minor]
    particles = np.zeros((num_particles, 5), dtype=np.float32)
    particles[:, 0] = np.random.rand(num_particles) * SIZE[0]
    particles[:, 1] = np.random.rand(num_particles) * SIZE[1]
    particles[:, 2] = np.random.rand(num_particles) * 100
    particles[:, 3] = np.random.rand(num_particles) * 50 + 50
    particles[:, 4] = np.random.randint(0, 2, size=num_particles) # 0 = major eigenvector, 1 = minor eigenvector

def draw():
    global particles
    
    if py5.frame_count == 1:
        py5.background(28, 30, 32) # Charcoal grey
        
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(28, 30, 32, 10) # Fading trail
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    s = 0.002
    
    px = particles[:, 0]
    py = particles[:, 1]
    
    # Compute 2x2 symmetric tensor field components from noise
    # T = [ Txx  Txy ]
    #     [ Txy  Tyy ]
    
    Txx = np.zeros_like(px)
    Tyy = np.zeros_like(py)
    Txy = np.zeros_like(px)
    
    for i in range(len(px)):
        Txx[i] = py5.noise(px[i]*s, py[i]*s, t) * 2 - 1.0
        Tyy[i] = py5.noise(px[i]*s + 1000, py[i]*s + 1000, t) * 2 - 1.0
        Txy[i] = py5.noise(px[i]*s + 2000, py[i]*s + 2000, t) * 2 - 1.0
        
    # Compute eigenvalues and eigenvectors
    # trace and determinant
    tr = Txx + Tyy
    det = Txx*Tyy - Txy**2
    
    # Eigenvalues lambda1, lambda2 (symmetric real matrix always has real roots)
    # L = tr/2 +- sqrt((tr/2)^2 - det)
    gap = np.sqrt(np.maximum((tr/2.0)**2 - det, 0.0))
    L1 = tr/2.0 + gap
    L2 = tr/2.0 - gap
    
    # Eigenvectors
    # for L1: [Txx - L1, Txy] dot v1 = 0 -> v1 = [-Txy, Txx - L1] or [Tyy - L1, -Txy]
    # for numeric stability, we use the row with larger norm, but simpler:
    # eigenvector angle theta: tan(2theta) = 2*Txy / (Txx - Tyy)
    theta = 0.5 * np.arctan2(2.0 * Txy, Txx - Tyy)
    
    # The two orthogonal eigenvectors are at theta and theta + pi/2
    
    vx = np.zeros_like(px)
    vy = np.zeros_like(py)
    
    major_mask = particles[:, 4] == 0
    minor_mask = particles[:, 4] == 1
    
    # Major (theta)
    vx[major_mask] = np.cos(theta[major_mask]) * 3.0
    vy[major_mask] = np.sin(theta[major_mask]) * 3.0
    
    # Minor (theta + pi/2)
    vx[minor_mask] = np.cos(theta[minor_mask] + np.pi/2.0) * 3.0
    vy[minor_mask] = np.sin(theta[minor_mask] + np.pi/2.0) * 3.0
    
    # Randomly flip direction so particles flow both ways along the tensor field lines
    # We can use the hash of particle id or just rely on noise
    # Let's just add it
    particles[:, 0] += vx
    particles[:, 1] += vy
    particles[:, 2] += 1
    
    # Wrap horizontally, reset if too old or out of bounds vertically
    dead = (particles[:, 2] > particles[:, 3]) | (particles[:, 0] < 0) | (particles[:, 0] > SIZE[0]) | (particles[:, 1] < 0) | (particles[:, 1] > SIZE[1])
    num_dead = np.sum(dead)
    
    if num_dead > 0:
        particles[dead, 0] = np.random.rand(num_dead) * SIZE[0] 
        particles[dead, 1] = np.random.rand(num_dead) * SIZE[1]
        particles[dead, 2] = 0
        particles[dead, 3] = np.random.rand(num_dead) * 50 + 50
    
    # Draw
    py5.stroke_weight(2)
    
    py5.begin_shape(py5.POINTS)
    # Luminous silver for major
    py5.stroke(224, 224, 224, 60)
    for i in range(len(px)):
        if major_mask[i]:
            py5.vertex(px[i], py[i])
    py5.end_shape()
    
    py5.begin_shape(py5.POINTS)
    # Electric teal for minor
    py5.stroke(0, 192, 208, 60)
    for i in range(len(px)):
        if minor_mask[i]:
            py5.vertex(px[i], py[i])
    py5.end_shape()

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
