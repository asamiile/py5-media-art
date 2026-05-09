from pathlib import Path
import subprocess
import sys
import py5
import numpy as np
from scipy.ndimage import gaussian_filter

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

# Physarum Parameters
NUM_AGENTS = 200_000
GRID_RES = 128
DECAY = 0.90
DIFFUSION_SIGMA = 0.4
SENSOR_ANGLE = np.pi / 4
SENSOR_DIST = 10.0
STEP_SIZE = 1.0
TURN_ANGLE = 0.2

# State
agents_pos = None
agents_dir = None
field = None
stars = None

def setup():
    global agents_pos, agents_dir, field, stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Agents in a central sphere
    r = np.random.uniform(0, 50, NUM_AGENTS)
    theta = np.random.uniform(0, 2 * np.pi, NUM_AGENTS)
    phi = np.arccos(np.random.uniform(-1, 1, NUM_AGENTS))
    
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    agents_pos = np.stack([x, y, z], axis=1).astype(np.float32)
    
    # Random initial directions (unit vectors)
    d_theta = np.random.uniform(0, 2 * np.pi, NUM_AGENTS)
    d_phi = np.arccos(np.random.uniform(-1, 1, NUM_AGENTS))
    dx = np.sin(d_phi) * np.cos(d_theta)
    dy = np.sin(d_phi) * np.sin(d_theta)
    dz = np.cos(d_phi)
    agents_dir = np.stack([dx, dy, dz], axis=1).astype(np.float32)
    
    # Initialize Field
    field = np.zeros((GRID_RES, GRID_RES, GRID_RES), dtype=np.float32)
    
    # Stars
    num_stars = 12000
    star_pos = np.random.uniform(-1500, 1500, (num_stars, 3))
    star_mag = np.random.uniform(0.5, 2.5, num_stars)
    stars = (star_pos, star_mag)

def draw():
    global agents_pos, agents_dir, field
    
    py5.background(2, 5, 10)  # Deep Obsidian
    
    # Camera
    t = py5.frame_count / 120.0
    cam_r = 600 + 100 * np.sin(t * 0.5)
    py5.camera(cam_r * np.cos(t), -200 + 100 * np.sin(t * 0.7), cam_r * np.sin(t), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke_weight(1)
    for p, m in zip(stars[0], stars[1]):
        alpha = 150 + 100 * np.sin(t * 5 + m * 10)
        py5.stroke(200, 230, 255, alpha)
        py5.point(*p)

    def world_to_grid(pos):
        SCALE = 0.35
        gpos = (pos * SCALE + GRID_RES // 2).astype(np.int32)
        np.clip(gpos, 0, GRID_RES - 1, out=gpos)
        return gpos

    # Move agents
    agents_pos += agents_dir * STEP_SIZE
    
    # Boundary check
    mask = (np.abs(agents_pos) > 180)
    agents_dir[mask] *= -1

    # 1. Sensing
    def sense(pos, angle_h, angle_v, dist):
        # Direction vector based on angles relative to current agents_dir
        # Simplified: Use random rotations for 3D sensing
        offset = np.random.normal(0, 0.5, (NUM_AGENTS, 3))
        sample_pos = pos + (agents_dir + offset * angle_h) * dist
        gpos = world_to_grid(sample_pos)
        return field[gpos[:, 0], gpos[:, 1], gpos[:, 2]]

    # Sample 3 points
    s_fwd = sense(agents_pos, 0, 0, SENSOR_DIST)
    s_left = sense(agents_pos, 0.5, 0, SENSOR_DIST)
    s_right = sense(agents_pos, -0.5, 0, SENSOR_DIST)
    
    # Steering
    steer = np.zeros((NUM_AGENTS, 3), dtype=np.float32)
    # Turn towards the best direction
    mask_fwd = (s_fwd > s_left) & (s_fwd > s_right)
    mask_left = (s_left > s_fwd) & (s_left > s_right)
    mask_right = (s_right > s_fwd) & (s_right > s_left)
    
    # Update directions with bias
    jitter = np.random.normal(0, 0.15, (NUM_AGENTS, 3))
    agents_dir[mask_left] += (np.random.normal(0, 0.3, (np.sum(mask_left), 3)) + jitter[mask_left])
    agents_dir[mask_right] -= (np.random.normal(0, 0.3, (np.sum(mask_right), 3)) - jitter[mask_right])
    agents_dir += jitter * 0.5
    
    # Renormalize
    mags = np.linalg.norm(agents_dir, axis=1, keepdims=True)
    agents_dir /= mags
    
    # 2. Deposit
    grid_pos = world_to_grid(agents_pos)
    np.add.at(field, (grid_pos[:, 0], grid_pos[:, 1], grid_pos[:, 2]), 1.0)
    
    # 3. Field Update
    field *= DECAY
    if py5.frame_count % 2 == 0:
        field = gaussian_filter(field, sigma=DIFFUSION_SIGMA)

    # Rendering
    # Actual positions = agents_pos
    dens = field[grid_pos[:, 0], grid_pos[:, 1], grid_pos[:, 2]]
    norm_dens = np.clip(dens / 4.0, 0, 1)
    
    # Multi-pass rendering
    # Divide into 3 bands: Cyan, Amethyst, White
    bands = 3
    for i in range(bands):
        mask = (norm_dens >= i / bands) & (norm_dens < (i + 1) / bands)
        if not np.any(mask): continue
        
        if i == 0: 
            py5.stroke(0, 230, 255, 60)   # Cyan (low density / trails)
            py5.stroke_weight(1.0)
        elif i == 1: 
            py5.stroke(153, 0, 255, 120) # Amethyst (medium density / branches)
            py5.stroke_weight(1.5)
        else: 
            py5.stroke(255, 255, 255, 200) # White (high density / nodes)
            py5.stroke_weight(2.0)
        
        py5.points(agents_pos[mask])

    # Post-process frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # FFmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264", "-crf", "32", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
