import numpy as np
import scipy.ndimage as nd
from pathlib import Path
import subprocess
import sys
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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Resolution (scaled down for performance)
SCALE = 2
SIM_W = SIZE[0] // SCALE
SIM_H = SIZE[1] // SCALE

# Physarum Parameters
NUM_AGENTS = 50000
SENSOR_ANGLE = np.pi / 4.0
SENSOR_DIST = 9.0
ROTATION_ANGLE = np.pi / 4.0
STEP_SIZE = 1.0
DECAY_RATE = 0.95

# Initialize Agents
agents_pos = np.zeros((NUM_AGENTS, 2), dtype=np.float32)
agents_angle = np.random.uniform(0, 2 * np.pi, NUM_AGENTS)

# Start agents in a circle
radius = min(SIM_W, SIM_H) * 0.2
theta = np.random.uniform(0, 2 * np.pi, NUM_AGENTS)
r = np.random.uniform(0, radius, NUM_AGENTS)
agents_pos[:, 0] = SIM_W / 2 + r * np.cos(theta)
agents_pos[:, 1] = SIM_H / 2 + r * np.sin(theta)

# Pheromone Grid
grid = np.zeros((SIM_H, SIM_W), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    py5.background(0)

def draw():
    global agents_pos, agents_angle, grid
    
    # 1. Agents sense the grid
    # Calculate sensor positions (left, forward, right)
    sensor_angles = np.array([-SENSOR_ANGLE, 0, SENSOR_ANGLE])
    angles_expanded = agents_angle[:, None] + sensor_angles[None, :]
    
    dx = np.cos(angles_expanded) * SENSOR_DIST
    dy = np.sin(angles_expanded) * SENSOR_DIST
    
    sx = np.clip((agents_pos[:, 0:1] + dx).astype(np.int32), 0, SIM_W - 1)
    sy = np.clip((agents_pos[:, 1:2] + dy).astype(np.int32), 0, SIM_H - 1)
    
    # Sample grid values at sensors
    sensor_vals = grid[sy, sx]
    
    # 2. Agents rotate based on sensory input
    left_vals = sensor_vals[:, 0]
    fwd_vals = sensor_vals[:, 1]
    right_vals = sensor_vals[:, 2]
    
    turn_left = (left_vals > fwd_vals) & (left_vals > right_vals)
    turn_right = (right_vals > fwd_vals) & (right_vals > left_vals)
    random_turn = (left_vals == right_vals) & (left_vals > fwd_vals)
    
    agents_angle[turn_left] -= ROTATION_ANGLE
    agents_angle[turn_right] += ROTATION_ANGLE
    
    # Randomly pick left or right if equal
    rand_mask = random_turn & (np.random.rand(NUM_AGENTS) < 0.5)
    agents_angle[rand_mask] -= ROTATION_ANGLE
    agents_angle[random_turn & ~rand_mask] += ROTATION_ANGLE
    
    # 3. Move agents
    agents_pos[:, 0] += np.cos(agents_angle) * STEP_SIZE
    agents_pos[:, 1] += np.sin(agents_angle) * STEP_SIZE
    
    # 4. Handle boundary collisions (wrap around)
    agents_pos[:, 0] = agents_pos[:, 0] % SIM_W
    agents_pos[:, 1] = agents_pos[:, 1] % SIM_H
    
    # 5. Deposit pheromones
    px = np.clip(agents_pos[:, 0].astype(np.int32), 0, SIM_W - 1)
    py_coords = np.clip(agents_pos[:, 1].astype(np.int32), 0, SIM_H - 1)
    np.add.at(grid, (py_coords, px), 1.0)
    
    # 6. Diffuse and decay grid
    grid = nd.gaussian_filter(grid, sigma=1.0)
    grid *= DECAY_RATE
    
    # Rendering
    # Map the grid intensity to colors
    # Cyber Fungi Palette: Neon Orange / Hot Pink / Electric Violet
    intensity = np.clip(grid * 5.0, 0, 255)
    
    # Color mapping using a custom colormap
    t_val = intensity / 255.0
    r = np.clip(255 * t_val * 1.5, 0, 255)
    g = np.clip(255 * (t_val ** 2), 0, 255)
    b = np.clip(255 * t_val * 0.5, 0, 255)
    
    # Special highlight for high intensity (Hot Pink / Violet)
    high_mask = t_val > 0.6
    r[high_mask] = 255
    g[high_mask] = 50 + 200 * (1 - t_val[high_mask])
    b[high_mask] = 200 + 55 * t_val[high_mask]
    
    pixels = np.zeros((SIM_H, SIM_W, 4), dtype=np.uint8)
    pixels[..., 0] = r.astype(np.uint8)
    pixels[..., 1] = g.astype(np.uint8)
    pixels[..., 2] = b.astype(np.uint8)
    pixels[..., 3] = 255
    
    # Scale up to output size
    py5.load_np_pixels()
    actual_h, actual_w = py5.np_pixels.shape[:2]
    scale_y = actual_h // SIM_H
    scale_x = actual_w // SIM_W
    
    scaled_pixels = np.repeat(np.repeat(pixels, scale_y, axis=0), scale_x, axis=1)
    
    if scaled_pixels.shape[0] != actual_h or scaled_pixels.shape[1] != actual_w:
        sh, sw = scaled_pixels.shape[:2]
        ch, cw = min(sh, actual_h), min(sw, actual_w)
        py5.np_pixels[:ch, :cw] = scaled_pixels[:ch, :cw]
    else:
        py5.np_pixels[:] = scaled_pixels
        
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "20M", "-maxrate", "25M", "-bufsize", "30M",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()
