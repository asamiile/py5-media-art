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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Attractor Parameters
NUM_PARTICLES = 200_000

# State
pts = None
stars = None

def setup():
    global pts, stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Particles
    pts = np.random.uniform(-0.1, 0.1, (NUM_PARTICLES, 3)).astype(np.float32)
    
    # Stars
    num_stars = 12000
    star_pos = np.random.uniform(-1500, 1500, (num_stars, 3))
    star_mag = np.random.uniform(0.5, 2.5, num_stars)
    stars = (star_pos, star_mag)

def de_jong_3d(p, a, b, c, d):
    # Extended De Jong map for 3D
    # We'll use a variation that couples Z
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    new_x = np.sin(a * y) - np.cos(b * x)
    new_y = np.sin(c * x) - np.cos(d * y)
    new_z = np.sin(a * z) - np.cos(c * y)
    return np.stack([new_x, new_y, new_z], axis=1)

def draw():
    global pts
    py5.background(2, 5, 10)  # Deep Obsidian
    
    # Camera
    t = py5.frame_count / 60.0
    cam_r = 800 + 100 * np.cos(t * 0.2)
    py5.camera(cam_r * np.cos(t * 0.15), -100 + 50 * np.sin(t * 0.3), cam_r * np.sin(t * 0.15), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke_weight(1)
    for p, m in zip(stars[0], stars[1]):
        alpha = 150 + 100 * np.sin(t * 5 + m * 10)
        py5.stroke(200, 230, 255, alpha)
        py5.point(*p)

    # Attractor Update
    # Dynamic parameters
    a = 1.4 + 0.1 * np.sin(t * 0.2)
    b = -2.3 + 0.1 * np.cos(t * 0.3)
    c = 2.4 + 0.1 * np.sin(t * 0.4)
    d = -1.2 + 0.1 * np.cos(t * 0.5)
    
    # Evolve particles
    # To get a "trail" effect with points, we only update them slightly or redraw many
    # Here we'll do 1 iteration per frame
    pts = de_jong_3d(pts, a, b, c, d)
    
    # Rendering
    # Scale pts
    render_pts = pts * 180
    
    # Color based on position/velocity
    # We'll use position for HSB mapping
    dist = np.linalg.norm(pts, axis=1)
    norm_dist = np.clip(dist / 2.0, 0, 1)
    
    # Multi-pass rendering
    bands = 5
    for i in range(bands):
        mask = (norm_dist >= i / bands) & (norm_dist < (i + 1) / bands)
        if not np.any(mask): continue
        
        # Color: Amber -> Violet -> Blue
        if i < 2: 
            py5.stroke(255, 191, 0, 80)   # Molten Amber
            py5.stroke_weight(1.0)
        elif i < 4: 
            py5.stroke(148, 0, 211, 120)  # Neon Violet
            py5.stroke_weight(1.2)
        else: 
            py5.stroke(0, 255, 255, 200)  # Electric Blue
            py5.stroke_weight(1.5)
        
        py5.points(render_pts[mask])

    # Post-process frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # FFmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264", "-crf", "36", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
