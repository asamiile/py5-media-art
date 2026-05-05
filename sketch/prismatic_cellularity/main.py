from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Feature points parameters
NUM_POINTS = 32
points = None
point_vels = None

def setup():
    global points, point_vels
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize feature points
    points = np.random.rand(NUM_POINTS, 2) * np.array([py5.width, py5.height])
    point_vels = (np.random.rand(NUM_POINTS, 2) - 0.5) * 2.0

def draw():
    global points, point_vels
    
    # Update points (drift)
    points += point_vels
    # Bounce
    mask_x = (points[:, 0] < 0) | (points[:, 0] > py5.width)
    mask_y = (points[:, 1] < 0) | (points[:, 1] > py5.height)
    point_vels[mask_x, 0] *= -1
    point_vels[mask_y, 1] *= -1
    
    # Time-based modulation
    t = py5.frame_count / TOTAL_FRAMES
    breath = 0.5 + 0.5 * np.sin(t * np.pi * 2)
    
    # Render using NumPy at half resolution for speed
    SCALE_FACTOR = 2
    w, h = py5.pixel_width // SCALE_FACTOR, py5.pixel_height // SCALE_FACTOR
    # Create coordinate grid
    x_coords = np.linspace(0, py5.width, w)
    y_coords = np.linspace(0, py5.height, h)
    xv, yv = np.meshgrid(x_coords, y_coords)
    
    # Reshape points for broadcasting: (N, 1, 1, 2)
    pts_reshaped = points.reshape(NUM_POINTS, 1, 1, 2)
    # Reshape pixel coords for broadcasting: (1, H, W, 2)
    pix_coords = np.stack([xv, yv], axis=-1).reshape(1, h, w, 2)
    
    # Compute distances: (N, H, W)
    # L1 distance (Manhattan)
    dists_l1 = np.sum(np.abs(pix_coords - pts_reshaped), axis=-1)
    # L2 distance (Euclidean)
    dists_l2 = np.sqrt(np.sum((pix_coords - pts_reshaped)**2, axis=-1))
    
    # Hybrid distance
    blend = 0.3 + 0.4 * breath
    dists = blend * dists_l1 + (1.0 - blend) * dists_l2
    
    # Find F1 and F2 efficiently using partition
    # (N, H, W) -> partition along axis 0
    part = np.partition(dists, 1, axis=0)
    f1 = part[0]
    f2 = part[1]
    
    # Edge detection: F2 - F1
    edges = f2 - f1
    edge_norm = np.clip(edges / (20.0 + 10.0 * breath), 0, 1)
    
    # Spectral mapping - softer and more atmospheric
    h_field = (f1 * 0.02 + t * 0.05) % 1.0
    s_field = 0.6 + 0.3 * np.sin(f1 * 0.1)
    # Brightness masked by edge density to reveal background
    b_field = (1.0 - edge_norm) * 0.8 + 0.2 * breath
    
    # Background: Deep Indigo
    bg_color = np.array([5, 5, 20]) / 255.0
    
    def hsb_to_rgb(h, s, b):
        i = (h * 6).astype(int)
        f = h * 6 - i
        p = b * (1 - s)
        q = b * (1 - f * s)
        t = b * (1 - (1 - f) * s)
        i = i % 6
        rgb = np.zeros((h.shape[0], h.shape[1], 3))
        mask0 = (i == 0); rgb[mask0] = np.stack([b[mask0], t[mask0], p[mask0]], axis=-1)
        mask1 = (i == 1); rgb[mask1] = np.stack([q[mask1], b[mask1], p[mask1]], axis=-1)
        mask2 = (i == 2); rgb[mask2] = np.stack([p[mask2], b[mask2], t[mask2]], axis=-1)
        mask3 = (i == 3); rgb[mask3] = np.stack([p[mask3], q[mask3], b[mask3]], axis=-1)
        mask4 = (i == 4); rgb[mask4] = np.stack([t[mask4], p[mask4], b[mask4]], axis=-1)
        mask5 = (i == 5); rgb[mask5] = np.stack([b[mask5], p[mask5], q[mask5]], axis=-1)
        return rgb

    rgb_field = hsb_to_rgb(h_field, s_field, b_field)
    
    # Mask by edge detection to create gaps
    mask = (edges > 15).astype(float).reshape(h, w, 1)
    rgb_field *= (1.0 - mask * 0.8)
    
    # Upscale the field back to full resolution using np.repeat
    final_rgb = np.repeat(np.repeat(rgb_field, SCALE_FACTOR, axis=0), SCALE_FACTOR, axis=1)
    # Match size
    final_rgb = final_rgb[:py5.pixel_height, :py5.pixel_width]
    
    # Blending with Indigo baseline
    final_rgb = np.clip(final_rgb + bg_color.reshape(1, 1, 3), 0, 1)
    
    # Set pixels with Subtle Chromatic Aberration
    shift = 3
    ca_rgb = final_rgb.copy()
    ca_rgb[:, shift:, 0] = final_rgb[:, :-shift, 0] # R shifts right
    ca_rgb[:, :-shift, 2] = final_rgb[:, shift:, 2] # B shifts left
    
    py5.set_np_pixels((ca_rgb * 255).astype(np.uint8), bands="RGB")
    
    # Draw stars and haze
    np.random.seed(42)
    stars = np.random.rand(150, 3)
    np.random.seed()
    py5.no_stroke()
    for sx, sy, ss in stars:
        py5.fill(1, 0, 1, 0.4 * ss)
        py5.circle(sx * py5.width, sy * py5.height, ss * 3)
    
    for i in range(10):
        alpha = (10 - i) * 0.02
        py5.fill(240/360, 0.8, 0.5, alpha)
        py5.rect(0, py5.height - i * 20, py5.width, 20)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Save first frame as preview immediately for early review
    if py5.frame_count == 1:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))

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

py5.run_sketch()
