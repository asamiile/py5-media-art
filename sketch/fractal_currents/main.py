from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
PARTICLE_COUNT = 40000  # More particles since it's faster now
C = complex(-0.8, 0.156)  # Julia set constant

particles = None
stars = None

def setup():
    global particles, stars
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles (x, y)
    particles = np.random.uniform(0, 1, (PARTICLE_COUNT, 2))
    particles[:, 0] *= py5.width
    particles[:, 1] *= py5.height
    
    # Starfield
    stars = np.random.uniform(0, 1, (1200, 3))
    stars[:, 0] *= py5.width
    stars[:, 1] *= py5.height
    stars[:, 2] = np.random.uniform(0.5, 1.5)

def draw_starfield():
    py5.stroke(255, 100)
    for i in range(len(stars)):
        py5.stroke_weight(stars[i, 2])
        py5.point(stars[i, 0], stars[i, 1])

def draw():
    global particles
    # Subtle trail effect
    py5.fill(5, 5, 16, 25)
    py5.rect(0, 0, py5.width, py5.height)
    
    draw_starfield()
    
    # Vectorized Julia Flow
    zx = (particles[:, 0] / py5.width - 0.5) * 3.0
    zy = (particles[:, 1] / py5.height - 0.5) * 3.0
    z = zx + 1j * zy
    
    # One iteration of Julia set
    z_next = z * z + C
    
    # Velocity is the difference vector
    vx = z_next.real - z.real
    vy = z_next.imag - z.imag
    
    # Normalize
    mag = np.sqrt(vx**2 + vy**2)
    mag[mag == 0] = 1.0
    vx /= mag
    vy /= mag
    
    # Add some time-varying drift
    vx += np.sin(py5.frame_count * 0.05 + particles[:, 0] * 0.01) * 0.2
    vy += np.cos(py5.frame_count * 0.05 + particles[:, 1] * 0.01) * 0.2
    
    # Update particles
    particles[:, 0] += vx * 2.5
    particles[:, 1] += vy * 2.5
    
    # Phase for coloring
    phase = np.angle(z_next)
    
    # Draw Particles (use a fast method if possible, but point loop is okay with NumPy data)
    py5.color_mode(py5.HSB, 255)
    
    # Group particles by hue for faster drawing if needed, 
    # but let's try a simple loop first as point() is fast.
    # Actually, for 40k particles, a loop is slow. Let's use np_pixels if possible, 
    # or just a subsampled loop.
    
    # Subsample for drawing to keep it fast while maintaining density
    draw_step = 1
    for i in range(0, PARTICLE_COUNT, draw_step):
        p = particles[i]
        hue = (phase[i] * 40 + 160) % 255
        py5.stroke(hue, 180, 200, 150)
        py5.point(p[0], p[1])
        
    # Wrap around
    out_of_bounds = (particles[:, 0] < 0) | (particles[:, 0] > py5.width) | \
                    (particles[:, 1] < 0) | (particles[:, 1] > py5.height)
    particles[out_of_bounds] = np.random.uniform(0, 1, (np.sum(out_of_bounds), 2))
    particles[out_of_bounds, 0] *= py5.width
    particles[out_of_bounds, 1] *= py5.height

    py5.color_mode(py5.RGB, 255)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
