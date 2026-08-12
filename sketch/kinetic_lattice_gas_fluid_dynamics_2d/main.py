from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Grid size (half resolution for performance and fluid dynamics look)
GRID_W = SIZE[0] // 2
GRID_H = SIZE[1] // 2

# HPP Lattice Gas state: 4 channels for East, North, West, South
# Shape (GRID_H, GRID_W, 4) boolean array
state = np.random.rand(GRID_H, GRID_W, 4) < 0.15

# Circular obstacle in the center
obstacle = np.zeros((GRID_H, GRID_W), dtype=bool)
cy, cx = GRID_H // 2, GRID_W // 2
r = 25
Y, X = np.meshgrid(np.arange(GRID_H), np.arange(GRID_W), indexing='ij')
obstacle[(X - cx)**2 + (Y - cy)**2 < r**2] = True

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def update_lattice_gas():
    global state
    
    # 1. Streaming phase
    streamed = np.zeros_like(state)
    streamed[:, :, 0] = np.roll(state[:, :, 0], 1, axis=1)  # East
    streamed[:, :, 1] = np.roll(state[:, :, 1], 1, axis=0)  # North
    streamed[:, :, 2] = np.roll(state[:, :, 2], -1, axis=1) # West
    streamed[:, :, 3] = np.roll(state[:, :, 3], -1, axis=0) # South
    
    # 2. Obstacle reflection (bounce-back boundary)
    # If a particle hits the obstacle, it reverses its direction
    # We exchange East <-> West, North <-> South inside the obstacle boundary
    hit_mask = obstacle
    
    # Reversal swap
    rev_state = np.zeros_like(streamed)
    rev_state[:, :, 0] = np.where(hit_mask, streamed[:, :, 2], streamed[:, :, 0]) # East becomes West
    rev_state[:, :, 2] = np.where(hit_mask, streamed[:, :, 0], streamed[:, :, 2]) # West becomes East
    rev_state[:, :, 1] = np.where(hit_mask, streamed[:, :, 3], streamed[:, :, 1]) # North becomes South
    rev_state[:, :, 3] = np.where(hit_mask, streamed[:, :, 1], streamed[:, :, 3]) # South becomes North
    
    # 3. Collision phase (HPP rules)
    # Head-on collision: East/West meet and North/South are empty -> scatter to North/South
    c0 = rev_state[:, :, 0]
    c1 = rev_state[:, :, 1]
    c2 = rev_state[:, :, 2]
    c3 = rev_state[:, :, 3]
    
    ew_collision = c0 & c2 & ~c1 & ~c3
    ns_collision = c1 & c3 & ~c0 & ~c2
    
    state = rev_state.copy()
    
    # East/West scattering to North/South
    state[:, :, 0] = np.where(ew_collision, False, state[:, :, 0])
    state[:, :, 2] = np.where(ew_collision, False, state[:, :, 2])
    state[:, :, 1] = np.where(ew_collision, True, state[:, :, 1])
    state[:, :, 3] = np.where(ew_collision, True, state[:, :, 3])
    
    # North/South scattering to East/West
    state[:, :, 1] = np.where(ns_collision, False, state[:, :, 1])
    state[:, :, 3] = np.where(ns_collision, False, state[:, :, 3])
    state[:, :, 0] = np.where(ns_collision, True, state[:, :, 0])
    state[:, :, 2] = np.where(ns_collision, True, state[:, :, 2])
    
    # 4. Inflow boundary: continuously inject particles from the left
    # Injecting East-moving particles
    state[:, :4, 0] = np.random.rand(GRID_H, 4) < 0.65
    
    # Ensure obstacle cells remain empty of fluid particles
    state[obstacle] = False

def draw():
    update_lattice_gas()
    
    # Calculate density (number of particles per cell)
    density = np.sum(state, axis=2).astype(np.float32)
    # Smooth density using a quick box blur to make it look like a continuous fluid
    smoothed_density = (
        density +
        np.roll(density, 1, axis=1) + np.roll(density, -1, axis=1) +
        np.roll(density, 1, axis=0) + np.roll(density, -1, axis=0)
    ) / 5.0
    
    # Normalize for visualization
    v_max = 3.0
    density_norm = np.clip(smoothed_density / v_max, 0.0, 1.0)
    
    # Color mapping:
    # Background: Obsidian Abyss
    # Dominant: Electric Blue (`#1e90ff`)
    # Secondary: Bright Mint (`#3eb489`)
    # Accent: Solar Gold (`#ffd700`) inside obstacle & boundaries
    
    # Map smoothed density to color channels
    r = (density_norm * 0.1 + (1.0 - density_norm) * 0.02) * 255
    g = (density_norm * 0.6 + (1.0 - density_norm) * 0.05) * 255
    b = (density_norm * 1.0 + (1.0 - density_norm) * 0.1) * 255
    
    # Dilate obstacle outline for a glowing edge effect
    dilated_obstacle = (
        np.roll(obstacle, 1, axis=1) | np.roll(obstacle, -1, axis=1) |
        np.roll(obstacle, 1, axis=0) | np.roll(obstacle, -1, axis=0)
    )
    outline = dilated_obstacle & ~obstacle
    
    r = np.where(outline, 255.0, r)
    g = np.where(outline, 215.0, g)
    b = np.where(outline, 0.0, b)
    
    # Dark shadow for the obstacle itself
    r = np.where(obstacle, 10.0, r)
    g = np.where(obstacle, 10.0, g)
    b = np.where(obstacle, 15.0, b)
    
    img_data = np.zeros((GRID_H, GRID_W, 4), dtype=np.uint8)
    img_data[:, :, 0] = 255  # Alpha
    img_data[:, :, 1] = np.clip(r, 0, 255).astype(np.uint8)
    img_data[:, :, 2] = np.clip(g, 0, 255).astype(np.uint8)
    img_data[:, :, 3] = np.clip(b, 0, 255).astype(np.uint8)
    
    img = py5.create_image(GRID_W, GRID_H, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:] = img_data
    img.update_pixels()
    
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
