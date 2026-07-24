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

# Simulation parameters
NUM_ANTS = 50000
STEPS_PER_FRAME = 50

# Using a slightly scaled down grid for chunky pixel aesthetic
SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

# Langton's Ant Rule: R L L R
# 0 -> Right (+1)
# 1 -> Left (-1)
# 2 -> Left (-1)
# 3 -> Right (+1)
RULE_TURN = np.array([1, -1, -1, 1], dtype=np.int32)
DX = np.array([0, 1, 0, -1], dtype=np.int32) # N, E, S, W
DY = np.array([-1, 0, 1, 0], dtype=np.int32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid, ants_x, ants_y, ants_d
    
    grid = np.zeros((H, W), dtype=np.uint8)
    
    # Initialize ants in a dense cluster in the center
    # This creates a perfectly symmetrical growing crystal-like structure
    # Wait, if all ants are in exactly the exact same spot, they will do the exact same thing (unless they have different directions).
    # We scatter them in a small circle to get a complex, chaotic fungal growth.
    
    theta = np.random.uniform(0, py5.TWO_PI, NUM_ANTS)
    r = np.random.uniform(0, 20, NUM_ANTS)
    
    ants_x = np.clip(W//2 + r * np.cos(theta), 0, W-1).astype(np.int32)
    ants_y = np.clip(H//2 + r * np.sin(theta), 0, H-1).astype(np.int32)
    ants_d = np.random.randint(0, 4, NUM_ANTS, dtype=np.int32)
    
    # Precompute ARGB colors for the 4 states
    global colors
    c0 = np.array([255, 10, 15, 25], dtype=np.uint8)    # Dark void
    c1 = np.array([255, 0, 255, 255], dtype=np.uint8)   # Cyan
    c2 = np.array([255, 255, 0, 255], dtype=np.uint8)   # Magenta
    c3 = np.array([255, 255, 255, 255], dtype=np.uint8) # White
    colors = np.stack([c0, c1, c2, c3])

def draw():
    global grid, ants_x, ants_y, ants_d
    
    for _ in range(STEPS_PER_FRAME):
        # 1. Read current state of the grid under each ant
        # If multiple ants are on the same cell, numpy advanced indexing resolves sequentially or unpredictably.
        # This adds a beautiful chaotic noise to the deterministic rules.
        states = grid[ants_y, ants_x]
        
        # 2. Turn ant
        turn = RULE_TURN[states]
        ants_d = (ants_d + turn) % 4
        
        # 3. Update grid state
        # In case of multiple ants on the same cell, we just use the simple vectorized assignment.
        # It's not perfectly strictly ordered, but that's fine for art.
        grid[ants_y, ants_x] = (states + 1) % 4
        
        # 4. Move ant
        ants_x += DX[ants_d]
        ants_y += DY[ants_d]
        
        # 5. Handle boundaries (wrap around / toroidal)
        ants_x = ants_x % W
        ants_y = ants_y % H
        
    # Render
    py5.load_np_pixels()
    
    # Map grid states to colors
    img_data = colors[grid]
    
    # Optional: draw the ants themselves as bright yellow dots
    img_data[ants_y, ants_x] = np.array([255, 255, 255, 0], dtype=np.uint8) # Yellow
    
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
