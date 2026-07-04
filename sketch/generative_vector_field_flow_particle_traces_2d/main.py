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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 100000

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0, 0, 5) # Initial solid dark background
    
    global particles
    # Particles array: [x, y, hue]
    particles = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    particles[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    
    # We will use py5's OpenSimplex noise internally through py5.noise, but for 100k particles it's slow.
    # Instead we'll vectorize it.
    # Actually, py5.os_noise() can be called efficiently.
    # But for ultimate performance in py5, we should use numpy for the noise if possible,
    # or just use a mathematical pseudo-noise formula.
    # Let's generate a complex deterministic trigonometric field to avoid slow Python loops.

def vector_field(x, y, t):
    # A continuous, morphing vector field using trigonometric functions instead of perlin noise
    # This is much faster to compute for 100,000 points using numpy arrays.
    
    # Normalize coordinates to a reasonable scale
    nx = x / py5.width * 5.0
    ny = y / py5.height * 5.0
    
    # Complex trigonometric interference pattern
    angle = np.sin(nx + t) * np.cos(ny - t*1.5) * 2.0 * np.pi
    angle += np.sin(ny * 2.0 - t) * np.pi
    angle += np.cos(nx * 1.5 + ny * 1.5 + t*2.0) * np.pi
    
    return angle

def draw():
    # Draw semi-transparent rectangle to fade previous frames (trail effect)
    py5.fill(0, 0, 5, 8)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    global particles
    
    t = py5.frame_count / TOTAL_FRAMES * np.pi * 2 # Complete 1 full cycle
    
    # Compute angles for all particles simultaneously
    angles = vector_field(particles[:, 0], particles[:, 1], t)
    
    # Determine velocity
    speed = 4.0
    
    # Update positions
    particles[:, 0] += np.cos(angles) * speed
    particles[:, 1] += np.sin(angles) * speed
    
    # Map angles to hues (normalize angle to 0-360)
    particles[:, 2] = (angles / (2 * np.pi) * 360 + 180) % 360
    
    # Wrap around screen edges
    particles[:, 0] = particles[:, 0] % py5.width
    particles[:, 1] = particles[:, 1] % py5.height
    
    # Draw particles
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    # py5 has py5.points() which accepts a 2D numpy array of coordinates!
    # But it doesn't support an array of colors directly unless we use begin_shape.
    # Since we have 100,000 points, iterating in python is slow.
    # A great trick is to use py5.points(particles[:, :2]) with a single color,
    # OR we can bin them by hue if we want varied colors.
    
    # Let's bin the particles into 36 color buckets for fast drawing
    # Bucket size: 10 degrees of hue
    hue_bins = np.floor(particles[:, 2] / 10).astype(int)
    
    for b in range(36):
        mask = (hue_bins == b)
        if np.any(mask):
            py5.stroke(b * 10, 80, 100, 30)
            py5.points(particles[mask, :2])
            
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
