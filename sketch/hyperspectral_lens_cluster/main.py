from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

# Add project root to path for lib imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Configuration
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_GALAXIES = 50
NUM_STARS_PER_GALAXY = 1200
TOTAL_PARTICLES = NUM_GALAXIES * NUM_STARS_PER_GALAXY

# Foreground Lens Cluster (Dark Matter / Galaxies)
NUM_LENSES = 6
lens_pos = np.random.uniform(-300, 300, (NUM_LENSES, 2)).astype(np.float32)
lens_mass = np.random.uniform(40000, 80000, NUM_LENSES).astype(np.float32)

# Background Galaxies
bg_galaxy_pos = np.zeros((TOTAL_PARTICLES, 2), dtype=np.float32)
bg_galaxy_col = np.zeros((TOTAL_PARTICLES, 3), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P2D) # 2D is enough for the projection-based lens effect
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize background galaxies
    for i in range(NUM_GALAXIES):
        center = np.random.uniform(-py5.width, py5.width, 2)
        base_col = np.array([
            np.random.uniform(150, 255),
            np.random.uniform(150, 255),
            np.random.uniform(150, 255)
        ])
        for j in range(NUM_STARS_PER_GALAXY):
            idx = i * NUM_STARS_PER_GALAXY + j
            offset = np.random.normal(0, 100, 2)
            bg_galaxy_pos[idx] = center + offset
            bg_galaxy_col[idx] = base_col * np.random.uniform(0.7, 1.3)

def draw():
    f = py5.frame_count
    t = f / TOTAL_FRAMES
    
    py5.background(2, 2, 8)
    py5.blend_mode(py5.ADD)
    
    # Subtle movement of background and lenses
    curr_bg_pos = bg_galaxy_pos + np.array([f * 0.5, f * 0.3])
    # Wrap background
    curr_bg_pos[:, 0] = ((curr_bg_pos[:, 0] + py5.width) % (py5.width * 2)) - py5.width
    curr_bg_pos[:, 1] = ((curr_bg_pos[:, 1] + py5.height) % (py5.height * 2)) - py5.height
    
    # Lenses move slowly
    curr_lens_pos = lens_pos + np.array([
        50 * np.sin(f * 0.01),
        50 * np.cos(f * 0.01)
    ])
    
    # Shift to center
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Vectorized Lensing Calculation
    # curr_bg_pos: (N, 2), curr_lens_pos: (L, 2), lens_mass: (L,)
    
    # diffs: (N, L, 2)
    diffs = curr_bg_pos[:, np.newaxis, :] - curr_lens_pos[np.newaxis, :, :]
    # dists: (N, L)
    dists = np.sqrt(np.sum(diffs**2, axis=2))
    dists = np.clip(dists, 5, None)
    
    # deflection_mags: (N, L) = Mass / dist
    deflection_mags = lens_mass[np.newaxis, :] / dists
    # deflections_per_lens: (N, L, 2) = (diff / dist) * mag
    deflections_per_lens = (diffs / dists[:, :, np.newaxis]) * deflection_mags[:, :, np.newaxis]
    # total_deflection: (N, 2)
    total_deflection = -np.sum(deflections_per_lens, axis=1)
    
    # Chromatic aberration
    # We'll render in three batches: R, G, B
    
    # Red
    py5.stroke_weight(1.8)
    p_r = curr_bg_pos + total_deflection * 1.08
    py5.begin_shape(py5.POINTS)
    for i in range(0, TOTAL_PARTICLES, 2):
        py5.stroke(bg_galaxy_col[i, 0], 0, 0, 150)
        py5.vertex(p_r[i, 0], p_r[i, 1])
    py5.end_shape()
    
    # Green
    p_g = curr_bg_pos + total_deflection * 1.0
    py5.begin_shape(py5.POINTS)
    for i in range(0, TOTAL_PARTICLES, 2):
        py5.stroke(0, bg_galaxy_col[i, 1], 0, 150)
        py5.vertex(p_g[i, 0], p_g[i, 1])
    py5.end_shape()
    
    # Blue
    p_b = curr_bg_pos + total_deflection * 0.92
    py5.begin_shape(py5.POINTS)
    for i in range(0, TOTAL_PARTICLES, 2):
        py5.stroke(0, 0, bg_galaxy_col[i, 2], 150)
        py5.vertex(p_b[i, 0], p_b[i, 1])
    py5.end_shape()
    
    # Foreground Lenses (Visible as very faint glows)
    py5.no_stroke()
    for l_idx in range(NUM_LENSES):
        l_p = curr_lens_pos[l_idx]
        py5.fill(255, 255, 255, 10)
        py5.circle(l_p[0], l_p[1], 20)

    # Video & Preview Save
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if f >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error during video encoding: {e}")

if __name__ == "__main__":
    py5.run_sketch()
