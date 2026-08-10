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

# --- Simulation Grid Setup ---
GRID_W = 240
GRID_H = 135

# State field: integer grain IDs
# Initialize with random states 1 to 32
Q = 32
h = np.random.randint(1, Q + 1, size=(GRID_H, GRID_W), dtype=np.int32)
max_grain_id = Q

# Temperature for Metropolis updates (higher = more grain boundaries wiggle chaotically)
T = 0.15

# Color Palette (Bioluminescent / Metallic themes)
# Curated HSL colors converted to RGB
palette = np.array([
    [10, 20, 40],     # Deep Ocean Abyss
    [24, 38, 70],     # Dark Navy
    [40, 80, 120],    # Deep Teal
    [160, 40, 100],   # Electric Purple
    [230, 80, 40],    # Bioluminescent Orange
    [240, 160, 30],   # Solar Gold
    [30, 200, 160],   # Bright Mint
    [0, 150, 220],    # Cyan
    [90, 40, 140],    # Amethyst
    [200, 50, 80],    # Coral
    [120, 220, 80],   # Emerald Green
    [50, 50, 80],     # Slate Grey
    [80, 100, 120],   # Steel Blue
    [220, 220, 240],  # Metallic Platinum
    [100, 20, 80],    # Dark Magenta
    [20, 100, 100]    # Pine
], dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def step_simulation(frame):
    global h, max_grain_id, T
    
    # Slowly lower temperature over time (annealing)
    T = max(0.02, 0.25 * (1.0 - frame / TOTAL_FRAMES))
    
    # Periodic Recrystallization: Inject a new nucleating grain
    if frame > 0 and frame % 90 == 0:
        max_grain_id += 1
        cx = np.random.randint(10, GRID_W - 10)
        cy = np.random.randint(10, GRID_H - 10)
        r = np.random.randint(4, 8)
        
        # Draw a circular nucleus of the new grain phase
        Y_idx, X_idx = np.indices((GRID_H, GRID_W))
        dist = np.sqrt((X_idx - cx)**2 + (Y_idx - cy)**2)
        h[dist <= r] = max_grain_id

    # 4 sweeps of Potts Monte Carlo updates per frame
    for _ in range(4):
        # Roll neighbors to evaluate energy
        n0 = np.roll(h, 1, axis=0)
        n1 = np.roll(h, -1, axis=0)
        n2 = np.roll(h, 1, axis=1)
        n3 = np.roll(h, -1, axis=1)
        n4 = np.roll(np.roll(h, 1, axis=0), 1, axis=1)
        n5 = np.roll(np.roll(h, 1, axis=0), -1, axis=1)
        n6 = np.roll(np.roll(h, -1, axis=0), 1, axis=1)
        n7 = np.roll(np.roll(h, -1, axis=0), -1, axis=1)
        
        # Subgrid updates (9 independent subsets so they can update in parallel without race conditions)
        for dy in range(3):
            for dx in range(3):
                sub_h = h[dy::3, dx::3]
                
                # Neighbor slices
                n0_s = n0[dy::3, dx::3]
                n1_s = n1[dy::3, dx::3]
                n2_s = n2[dy::3, dx::3]
                n3_s = n3[dy::3, dx::3]
                n4_s = n4[dy::3, dx::3]
                n5_s = n5[dy::3, dx::3]
                n6_s = n6[dy::3, dx::3]
                n7_s = n7[dy::3, dx::3]
                
                # Randomly pick a candidate state from one of the neighbors
                choices = np.random.randint(0, 8, size=sub_h.shape)
                candidates = np.choose(choices, [n0_s, n1_s, n2_s, n3_s, n4_s, n5_s, n6_s, n7_s])
                
                # Energy calculation (number of different neighbors)
                E_old = ((n0_s != sub_h).astype(int) + (n1_s != sub_h).astype(int) +
                         (n2_s != sub_h).astype(int) + (n3_s != sub_h).astype(int) +
                         (n4_s != sub_h).astype(int) + (n5_s != sub_h).astype(int) +
                         (n6_s != sub_h).astype(int) + (n7_s != sub_h).astype(int))

                E_new = ((n0_s != candidates).astype(int) + (n1_s != candidates).astype(int) +
                         (n2_s != candidates).astype(int) + (n3_s != candidates).astype(int) +
                         (n4_s != candidates).astype(int) + (n5_s != candidates).astype(int) +
                         (n6_s != candidates).astype(int) + (n7_s != candidates).astype(int))
                
                dE = E_new - E_old
                
                # Metropolis criteria
                accept = (dE <= 0) | (np.random.rand(*sub_h.shape) < np.exp(-dE / T))
                sub_h[accept] = candidates[accept]

def draw():
    global h, T
    
    W, H = SIZE
    frame = py5.frame_count
    
    # Step physics
    step_simulation(frame)
    
    # Detect boundaries (cells that don't match their neighbors)
    n0 = np.roll(h, 1, axis=0)
    n1 = np.roll(h, -1, axis=0)
    n2 = np.roll(h, 1, axis=1)
    n3 = np.roll(h, -1, axis=1)
    boundaries = (h != n0) | (h != n1) | (h != n2) | (h != n3)
    
    # Map grains to colors
    grain_colors = palette[h % len(palette)]
    
    # Add glowing boundary overlay
    b_mask = boundaries.astype(np.float32)
    # Box blur of boundaries for neon glow width
    glow = (
        np.roll(b_mask, 1, axis=0) + np.roll(b_mask, -1, axis=0) +
        np.roll(b_mask, 1, axis=1) + np.roll(b_mask, -1, axis=1) + b_mask
    ) / 5.0
    
    # Blend neon gold/amber boundaries (255, 170, 20)
    glow_color = np.array([255.0, 160.0, 30.0])
    
    # Combine: grain color + glow * glow_color
    pixels_rgb = grain_colors * (1.0 - glow[:, :, None] * 0.7) + glow[:, :, None] * glow_color * 0.9
    pixels_rgb = np.clip(pixels_rgb, 0.0, 255.0).astype(np.uint8)
    
    # Upscale
    sx = W // GRID_W
    sy = H // GRID_H
    
    r_up = np.repeat(np.repeat(pixels_rgb[:, :, 0], sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(pixels_rgb[:, :, 1], sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(pixels_rgb[:, :, 2], sy, axis=0), sx, axis=1)[:H, :W]
    
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255  # Alpha
    py5.np_pixels[:, :, 1] = r_up
    py5.np_pixels[:, :, 2] = g_up
    py5.np_pixels[:, :, 3] = b_up
    py5.update_np_pixels()
    
    # Draw faint grid pattern overlay
    py5.stroke(255, 255, 255, 8)
    py5.stroke_weight(1)
    step_grid = 60
    for x in range(0, W, step_grid):
        py5.line(x, 0, x, H)
    for y in range(0, H, step_grid):
        py5.line(0, y, W, y)
        
    # Vignette
    py5.no_stroke()
    for i in range(12):
        alpha = int(4 + i * 3)
        m = i * 20
        py5.fill(5, 5, 15, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)
        
    # Technical HUD Telemetry
    py5.fill(255, 160, 30, 210)
    py5.text_font(py5.create_font("Courier", 16))
    py5.text("SYSTEM: POLYCRYSTALLINE GRAIN BOUNDARY MIGRATION", 50, 60)
    py5.text("ALGORITHM: VECTORIZED METROPOLIS POTTS SOLVER", 50, 85)
    py5.text(f"ANNEALING TEMPERATURE: {T:.4f} | ORIENTATIONS: {Q}", 50, 110)
    py5.text(f"MAX PHASE ID: {max_grain_id} | RESOLUTION: 3840x2160 (4K)", 50, 135)
    py5.text(f"FRAME: {frame}/{TOTAL_FRAMES} | DURATION: {DURATION_SEC}s", 50, 160)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (mid-frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
