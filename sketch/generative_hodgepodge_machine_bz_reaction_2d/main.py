from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Internal resolution for the Hodgepodge Machine (to keep it real-time)
W_INT = SIZE[0] // 4
H_INT = SIZE[1] // 4

Q = 100       # Max state
k1 = 2        # Infection rate
k2 = 3        # Infection rate
g = 34        # Illness progression rate

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid, pixel_array
    
    # Initialize randomly
    grid = np.random.randint(0, Q + 1, size=(H_INT, W_INT), dtype=np.int32)
    
    # Pre-allocate image array (RGBA)
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255

def draw():
    global grid, pixel_array
    
    STEPS_PER_FRAME = 2
    
    for _ in range(STEPS_PER_FRAME):
        # We need to count the number of infected (0 < state < Q) and ill (state == Q)
        # and sum the states of infected neighbors.
        # We can use scipy convolve2d or just numpy rolling for a Moore neighborhood
        
        N = np.roll(grid, -1, axis=0)
        S = np.roll(grid, 1, axis=0)
        E = np.roll(grid, -1, axis=1)
        W = np.roll(grid, 1, axis=1)
        NE = np.roll(N, -1, axis=1)
        NW = np.roll(N, 1, axis=1)
        SE = np.roll(S, -1, axis=1)
        SW = np.roll(S, 1, axis=1)
        
        # Count cells
        neighbors_ill = (N == Q).astype(np.int32) + (S == Q).astype(np.int32) + \
                        (E == Q).astype(np.int32) + (W == Q).astype(np.int32) + \
                        (NE == Q).astype(np.int32) + (NW == Q).astype(np.int32) + \
                        (SE == Q).astype(np.int32) + (SW == Q).astype(np.int32)
                        
        neighbors_infected = ((N > 0) & (N < Q)).astype(np.int32) + ((S > 0) & (S < Q)).astype(np.int32) + \
                             ((E > 0) & (E < Q)).astype(np.int32) + ((W > 0) & (W < Q)).astype(np.int32) + \
                             ((NE > 0) & (NE < Q)).astype(np.int32) + ((NW > 0) & (NW < Q)).astype(np.int32) + \
                             ((SE > 0) & (SE < Q)).astype(np.int32) + ((SW > 0) & (SW < Q)).astype(np.int32)
                             
        sum_infected = np.where((N > 0) & (N < Q), N, 0) + np.where((S > 0) & (S < Q), S, 0) + \
                       np.where((E > 0) & (E < Q), E, 0) + np.where((W > 0) & (W < Q), W, 0) + \
                       np.where((NE > 0) & (NE < Q), NE, 0) + np.where((NW > 0) & (NW < Q), NW, 0) + \
                       np.where((SE > 0) & (SE < Q), SE, 0) + np.where((SW > 0) & (SW < Q), SW, 0)
        
        # Apply rules
        next_grid = np.copy(grid)
        
        # Rule 1: Healthy (state == 0)
        mask_healthy = (grid == 0)
        next_grid[mask_healthy] = np.floor(neighbors_infected[mask_healthy] / k1) + np.floor(neighbors_ill[mask_healthy] / k2)
        
        # Rule 2: Infected (0 < state < Q)
        mask_infected = (grid > 0) & (grid < Q)
        total_cells = neighbors_infected[mask_infected] + neighbors_ill[mask_infected] + 1
        total_cells = np.maximum(total_cells, 1) # Avoid division by zero
        next_grid[mask_infected] = np.floor((sum_infected[mask_infected] + grid[mask_infected]) / total_cells) + g
        
        # Rule 3: Ill (state == Q)
        mask_ill = (grid == Q)
        next_grid[mask_ill] = 0
        
        # Cap at Q
        grid = np.clip(next_grid, 0, Q)

    # Color mapping: map 0 to Q to an RGB gradient
    # We can use a sine-based color palette for beautiful continuous color bands
    norm_grid = grid.astype(np.float32) / Q
    
    # Cosine palette: a + b * cos(2 * pi * (c * t + d))
    # E.g. fire/magma palette
    r = (0.5 + 0.5 * np.cos(2 * np.pi * (1.0 * norm_grid + 0.0))) * 255
    g_c = (0.5 + 0.5 * np.cos(2 * np.pi * (1.0 * norm_grid + 0.33))) * 255
    b = (0.5 + 0.5 * np.cos(2 * np.pi * (1.0 * norm_grid + 0.67))) * 255
    
    pixel_array[:, :, 0] = r.astype(np.uint8)
    pixel_array[:, :, 1] = g_c.astype(np.uint8)
    pixel_array[:, :, 2] = b.astype(np.uint8)
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Draw scaled up to full size
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
