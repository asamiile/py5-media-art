from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
N_PARTICLES = 180_000
N_HUBS = 6
STAR_COUNT = 10_000

# State
hubs_pos = np.random.uniform(-400, 400, (N_HUBS, 2))
hubs_mass = np.random.uniform(200, 500, N_HUBS)

stars_pos = np.zeros((STAR_COUNT, 2), dtype=np.float32)
stars_mag = np.zeros(STAR_COUNT, dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Init stars
    stars_pos[:, 0] = np.random.uniform(0, SIZE[0], STAR_COUNT)
    stars_pos[:, 1] = np.random.uniform(0, SIZE[1], STAR_COUNT)
    stars_mag[:] = np.random.uniform(50, 255, STAR_COUNT)


def draw():
    py5.background(0)
    
    # 1. Background Starfield
    py5.stroke_weight(1)
    for i in range(STAR_COUNT):
        twinkle = np.sin(py5.frame_count * 0.1 + i) * 50
        py5.stroke(stars_mag[i] + twinkle, 150)
        py5.point(stars_pos[i, 0], stars_pos[i, 1])

    # 2. Lensing Caustics
    t = py5.frame_count / TOTAL_FRAMES
    
    # Animate source position
    src_x = 200 * np.sin(t * 2 * np.pi)
    src_y = 150 * np.cos(t * 2 * np.pi * 1.5)
    
    # We'll sample particles in the "source plane" and map them to the "image plane"
    # Or vice versa. Let's use the lens equation: xi = eta + alpha(xi)
    # Actually, for caustics, we want to visualize regions of high magnification.
    # Magnification mu = 1 / det(Jacobian).
    
    # To keep it efficient, we'll sample a grid of points and distort them.
    grid_size = int(np.sqrt(N_PARTICLES))
    x = np.linspace(-SIZE[0]/2, SIZE[0]/2, grid_size)
    y = np.linspace(-SIZE[1]/2, SIZE[1]/2, grid_size)
    xx, yy = np.meshgrid(x, y)
    xi = np.stack([xx.flatten(), yy.flatten()], axis=1)
    
    # Calculate deflection alpha
    alpha = np.zeros_like(xi)
    for i in range(N_HUBS):
        dx = xi[:, 0] - hubs_pos[i, 0]
        dy = xi[:, 1] - hubs_pos[i, 1]
        r_sq = dx**2 + dy**2 + 1000 # softened
        alpha[:, 0] += hubs_mass[i] * dx / r_sq
        alpha[:, 1] += hubs_mass[i] * dy / r_sq
        
    # Source plane coordinates
    eta = xi - alpha
    
    # Source intensity (a simple Gaussian or nebula shape)
    dist_src = np.sqrt((eta[:, 0] - src_x)**2 + (eta[:, 1] - src_y)**2)
    intensity = np.exp(-dist_src**2 / (2 * 80**2))
    
    # We can also add a secondary source or noise
    intensity += 0.3 * np.exp(-((eta[:, 0] + src_x)**2 + (eta[:, 1] + src_y)**2) / (2 * 120**2))
    
    # Filter by intensity
    mask = intensity > 0.05
    points = xi[mask]
    ints = intensity[mask]
    
    # Rendering
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Glacial Aurora Palette: 200 (Cobalt) to 180 (Cyan) to 220 (Blue)
    # Map intensity to brightness and hue
    hues = np.interp(ints, [0.05, 1.0], [240, 180])
    sats = np.interp(ints, [0.05, 1.0], [80, 20])
    bris = np.interp(ints, [0.05, 1.0], [20, 100])
    alphas = np.interp(ints, [0.05, 1.0], [10, 80])
    
    # Batch draw points
    # P2D points() is quite fast
    # but we need different colors.
    
    # Sub-batch by hue/alpha to reduce stroke calls?
    # Actually, for 100k points, we should try to be fast.
    
    # Draw points with sub-sampling if needed
    for i in range(0, len(points), 2):
        py5.stroke(hues[i], sats[i], bris[i], alphas[i])
        py5.point(points[i, 0], points[i, 1])
        
    py5.pop_matrix()
    
    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "24",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
