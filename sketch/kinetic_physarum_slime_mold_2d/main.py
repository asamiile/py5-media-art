from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Slime Mold Parameters
NUM_AGENTS = 600000
SO = 9.0  # Sensor Offset distance
STEP = 1.5 # Movement step size
DECAY = 0.90 # Fast decay for sharp trails

SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

STEPS_PER_FRAME = 2

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid, px, py, angle, colormap
    
    grid = np.zeros((H, W), dtype=np.float32)
    
    # Initialize agents in a dense circle facing outwards
    r = np.random.uniform(0, min(W, H)*0.3, NUM_AGENTS)
    theta = np.random.uniform(0, py5.TWO_PI, NUM_AGENTS)
    
    px = W/2 + r * np.cos(theta)
    py = H/2 + r * np.sin(theta)
    
    # Facing outwards, but with some noise
    angle = theta + np.random.uniform(-0.5, 0.5, NUM_AGENTS)
    
    # Pre-generate a fiery colormap (Black -> Purple -> Magenta -> Orange -> Yellow -> White)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.2:
            p = v / 0.2
            colormap[i, 1:] = [int(p * 75), 0, int(p * 130)] # Deep Purple
        elif v < 0.45:
            p = (v - 0.2) / 0.25
            colormap[i, 1:] = [75 + int(p * 180), 0, 130 - int(p * 130)] # Magenta to Red
        elif v < 0.75:
            p = (v - 0.45) / 0.3
            colormap[i, 1:] = [255, int(p * 180), 0] # Red to Orange/Yellow
        else:
            p = (v - 0.75) / 0.25
            colormap[i, 1:] = [255, 180 + int(p * 75), int(p * 255)] # Yellow to White

def step_physarum(SA, RA):
    global grid, px, py, angle
    
    # 1. Sense
    # Compute sensor angles
    a_f = angle
    a_l = angle + SA
    a_r = angle - SA
    
    # Compute sensor positions
    sx_f = np.clip((px + np.cos(a_f) * SO).astype(np.int32), 0, W-1)
    sy_f = np.clip((py + np.sin(a_f) * SO).astype(np.int32), 0, H-1)
    
    sx_l = np.clip((px + np.cos(a_l) * SO).astype(np.int32), 0, W-1)
    sy_l = np.clip((py + np.sin(a_l) * SO).astype(np.int32), 0, H-1)
    
    sx_r = np.clip((px + np.cos(a_r) * SO).astype(np.int32), 0, W-1)
    sy_r = np.clip((py + np.sin(a_r) * SO).astype(np.int32), 0, H-1)
    
    # Read grid
    v_f = grid[sy_f, sx_f]
    v_l = grid[sy_l, sx_l]
    v_r = grid[sy_r, sx_r]
    
    # 2. Rotate
    rand = np.random.uniform(0, 1, NUM_AGENTS)
    
    # Conditions
    turn_left = (v_l > v_r) & (v_l > v_f)
    turn_right = (v_r > v_l) & (v_r > v_f)
    random_turn = (v_l == v_r) & (v_f < v_l) & (rand < 0.5)
    random_turn_r = (v_l == v_r) & (v_f < v_l) & (rand >= 0.5)
    
    angle[turn_left | random_turn] += RA
    angle[turn_right | random_turn_r] -= RA
    
    # 3. Move
    px += np.cos(angle) * STEP
    py += np.sin(angle) * STEP
    
    # Bounce off walls
    hit_x = (px < 0) | (px >= W)
    hit_y = (py < 0) | (py >= H)
    
    px = np.clip(px, 0, W-1.001)
    py = np.clip(py, 0, H-1.001)
    
    # Reverse angle and add some noise when hitting walls
    angle[hit_x] = np.pi - angle[hit_x] + np.random.uniform(-0.1, 0.1, np.sum(hit_x))
    angle[hit_y] = -angle[hit_y] + np.random.uniform(-0.1, 0.1, np.sum(hit_y))
    
    # 4. Deposit
    p_ix = px.astype(np.int32)
    p_iy = py.astype(np.int32)
    
    # Additive deposition (using np.add.at for safety with multiple agents on same pixel)
    np.add.at(grid, (p_iy, p_ix), 1.0)
    
    # 5. Diffuse and Decay
    # Custom fast blur using rolls (sum of 9 cells / 9)
    blur = (
        grid + 
        np.roll(grid, 1, 0) + np.roll(grid, -1, 0) + 
        np.roll(grid, 1, 1) + np.roll(grid, -1, 1) + 
        np.roll(np.roll(grid, 1, 0), 1, 1) + np.roll(np.roll(grid, -1, 0), -1, 1) + 
        np.roll(np.roll(grid, 1, 0), -1, 1) + np.roll(np.roll(grid, -1, 0), 1, 1)
    ) / 9.0
    
    grid = blur * DECAY

def draw():
    global grid
    
    t = py5.frame_count * 0.03
    
    # Modulate Sensor Angle (SA) and Rotation Angle (RA) over time to change patterns organically
    # Base SA ~ 22.5 deg (0.39 rad), RA ~ 45 deg (0.78 rad)
    SA = 0.39 + 0.15 * np.sin(t)
    RA = 0.78 + 0.3 * np.cos(t * 0.7)
    
    for _ in range(STEPS_PER_FRAME):
        step_physarum(SA, RA)
        
    py5.load_np_pixels()
    
    # Normalize grid to [0, 255] safely
    # The max value usually reaches around 20-40 depending on DECAY and density
    # We clip it to create a saturated glow effect
    intensity = np.clip(grid * 6.0, 0, 255).astype(np.uint8)
    
    img_data = colormap[intensity]
    
    # Scale up if necessary
    if SCALE > 1:
        img_data = np.repeat(np.repeat(img_data, SCALE, axis=0), SCALE, axis=1)
        
    py5.np_pixels[:] = img_data
    py5.update_np_pixels()

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
        import os
        os._exit(0)

py5.run_sketch()
