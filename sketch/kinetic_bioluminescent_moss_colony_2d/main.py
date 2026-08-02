from pathlib import Path
import random
import shutil
import subprocess
import sys
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
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Grid parameters for offscreen simulation
COLS = 384
ROWS = 216

# CA Parameters
MOISTURE_SCALE = 0.035
SPREAD_BIAS = 0.22
BASE_DECAY = 0.003
SPORE_CHANCE = 0.0004
GROWTH_RATE = 0.08

# Palette colors (RGB)
COLOR_BG = np.array([8, 8, 12], dtype=np.float32)       # Dark charcoal void
COLOR_MOSS = np.array([0, 240, 90], dtype=np.float32)    # Bioluminescent neon emerald
COLOR_SPORE = np.array([255, 175, 0], dtype=np.float32)  # Glowing solar amber

# Global state
cells = np.zeros((ROWS, COLS), dtype=np.float32)
moisture = np.zeros((ROWS, COLS), dtype=np.float32)
img_buffer = None

def seed_colonies():
    global cells
    print("[Moss Sim] Seeding initial colonies...")
    # Seed 22 random circular colonies
    for _ in range(22):
        cx = random.randint(15, COLS - 16)
        cy = random.randint(15, ROWS - 16)
        radius = random.randint(4, 10)
        for y in range(max(0, cy - radius), min(ROWS, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(COLS, cx + radius + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                    cells[y, x] = random.uniform(0.5, 0.9)

def precompute_moisture():
    global moisture
    print("[Moss Sim] Generating moisture field...")
    # Pre-generate moisture field using 2D noise
    for y in range(ROWS):
        for x in range(COLS):
            moisture[y, x] = py5.noise(x * MOISTURE_SCALE, y * MOISTURE_SCALE)

def setup():
    global img_buffer
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize offscreen image buffer
    img_buffer = py5.create_image(COLS, ROWS, py5.ARGB)
    
    # Set static noise seed for moisture
    py5.noise_seed(random.randint(0, 999999))
    precompute_moisture()
    seed_colonies()

def draw():
    global cells
    fc = py5.frame_count
    
    # Base decay increases dramatically in the final phase to wither the moss for a perfect loop
    if fc > 760:
        decay_val = BASE_DECAY + py5.remap(fc, 760, 900, 0.0, 0.08)
    else:
        decay_val = BASE_DECAY

    # --- 100% Vectorized Stochastic Cellular Automaton Step ---
    # Compute sum of 8 neighbors using vectorized shifted slices (handling boundaries)
    neighborhood = np.zeros_like(cells)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            shifted = np.roll(cells, shift=(dy, dx), axis=(0, 1))
            if dy == -1:
                shifted[-1, :] = 0
            elif dy == 1:
                shifted[0, :] = 0
            if dx == -1:
                shifted[:, -1] = 0
            elif dx == 1:
                shifted[:, 0] = 0
            neighborhood += shifted

    average_neighbors = neighborhood / 8.0
    
    # Growth is driven by neighbor density and local moisture
    growth = average_neighbors * (moisture + SPREAD_BIAS) * GROWTH_RATE
    
    # Random spore seeding
    spore_mask = (np.random.random((ROWS, COLS)) < SPORE_CHANCE) & (moisture > 0.45)
    spores = np.where(spore_mask, 0.22, 0.0).astype(np.float32)
    
    # Apply CA rules
    next_cells = cells + growth + spores - decay_val
    cells = np.clip(next_cells, 0.0, 1.0)
    
    # Track the active growth and spore births for highlighting
    activity = np.clip(growth + spores, 0.0, 1.0)

    # --- Vectorized Color Rendering ---
    # Interpolate colors based on cell value (V) and activity (A)
    V = cells[:, :, np.newaxis]
    A = activity[:, :, np.newaxis]
    
    # Base color = lerp(BG, MOSS, V)
    color = COLOR_BG + V * (COLOR_MOSS - COLOR_BG)
    # Highlight color = lerp(color, SPORE, A * 4.0)
    color = color + np.clip(A * 4.0, 0.0, 1.0) * (COLOR_SPORE - color)
    color = np.clip(color, 0, 255).astype(np.int32)
    
    # Construct ARGB pixels array
    # Set alpha based on cell value (fully resolved cells are slightly brighter)
    alpha = (np.clip(cells * 255.0, 40, 255)).astype(np.int32)
    
    # If cell value is 0, make it completely transparent so the canvas background is clean
    alpha = np.where(cells < 0.01, 0, alpha)
    
    argb = (
        (alpha << 24)
        | (color[:, :, 0] << 16)
        | (color[:, :, 1] << 8)
        | color[:, :, 2]
    )
    
    # Load into offscreen buffer
    img_buffer.load_pixels()
    img_buffer.pixels[:] = argb.flatten()
    img_buffer.update_pixels()

    # --- Draw to Main Screen ---
    # Clear screen with background color
    py5.background(int(COLOR_BG[0]), int(COLOR_BG[1]), int(COLOR_BG[2]))
    py5.blend_mode(py5.ADD)
    
    # Render offscreen buffer with an organic breathing wind sway
    sway_x = py5.sin(fc * 0.032) * 12.0
    sway_y = py5.cos(fc * 0.024) * 8.0
    
    # Draw scaled-up image (Processing automatically uses bilinear texture interpolation)
    py5.image(img_buffer, sway_x, sway_y, py5.width, py5.height)

    # Render a high-resolution cybernetic overlay grid on top
    # This represents the textured micro-mesh substrate that the moss grows on
    py5.blend_mode(py5.BLEND)
    py5.stroke(255, 255, 255, 6)
    py5.stroke_weight(0.5)
    
    # Drawing grid lines (spaced every 80 pixels)
    for x in range(0, py5.width, 80):
        py5.line(x, 0, x, py5.height)
    for y in range(0, py5.height, 80):
        py5.line(0, y, py5.width, y)

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame is at frame 450)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
