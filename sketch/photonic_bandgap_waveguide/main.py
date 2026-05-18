from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Paths & Settings
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- FDTD Simulation Configuration ---
W_sim, H_sim = 320, 180  # Grid dimensions
Ez = np.zeros((H_sim, W_sim), dtype=np.float32)
Hx = np.zeros((H_sim + 1, W_sim), dtype=np.float32)
Hy = np.zeros((H_sim, W_sim + 1), dtype=np.float32)

# Stability Coefficients
Cx = 0.5
Cy = 0.5
dt_sim = 1.0

# Photonic Crystal Defect Grid (epsilon_r)
epsilon_r = np.ones((H_sim, W_sim), dtype=np.float32)
a = 16  # Lattice Constant
r = 4.5  # Pillar Radius
epsilon_pillar = 12.0

# Define Defect Channel Path (L-shaped)
# Horizontal center: y = 90, x <= 160
# Vertical center: x = 160, y <= 90
def in_waveguide(x, y):
    dist_h = np.abs(y - 90)
    dist_v = np.abs(x - 160)
    is_in_h = (x <= 160) and (dist_h < 12)
    is_in_v = (y <= 90) and (dist_v < 12)
    return is_in_h or is_in_v

# Populate pillars (omitting defect path)
for y_grid in range(a // 2, H_sim, a):
    for x_grid in range(a // 2, W_sim, a):
        if in_waveguide(x_grid, y_grid):
            continue
        yy, xx = np.ogrid[:H_sim, :W_sim]
        mask = (xx - x_grid)**2 + (yy - y_grid)**2 <= r**2
        epsilon_r[mask] = epsilon_pillar

# Sponge absorbing boundary layers (Damping grid)
damping = np.ones((H_sim, W_sim), dtype=np.float32)
border = 15
for d in range(border):
    factor = 0.92 + 0.08 * (d / border) ** 2
    damping[:, d] = np.minimum(damping[:, d], factor)          # Left
    damping[:, -d-1] = np.minimum(damping[:, -d-1], factor)    # Right
    damping[d, :] = np.minimum(damping[d, :], factor)          # Top
    damping[-d-1, :] = np.minimum(damping[-d-1, :], factor)    # Bottom

# Wave Physics Constants
FREQUENCY = 0.024  # Normalized bandgap frequency
STEPS_PER_FRAME = 3

# Colors for Rendering (RGB)
COLOR_BG = np.array([5, 5, 12])
COLOR_CREST = np.array([0, 230, 255])  # Electric Teal
COLOR_TROUGH = np.array([255, 80, 120])  # Glowing Coral

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)  # CAP at 1x to prevent Retina doubling performance drop
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global Ez, Hx, Hy
    
    # 1. Physics Engine: Run FDTD updates
    for _ in range(STEPS_PER_FRAME):
        # H-field updates
        Hx[1:-1, :] -= Cy * (Ez[1:, :] - Ez[:-1, :])
        Hy[:, 1:-1] += Cx * (Ez[:, 1:] - Ez[:, :-1])
        
        # E-field update modulated by spatial epsilon
        Ez += (1.0 / epsilon_r) * (Cx * (Hy[:, 1:] - Hy[:, :-1]) - Cy * (Hx[1:, :] - Hx[:-1, :]))
        
        # Sponge Boundary absorption
        Ez *= damping
        
        # Soft sinusoidal wave source injection
        t = (py5.frame_count * STEPS_PER_FRAME) * dt_sim
        envelope = np.clip(py5.frame_count / 90.0, 0.0, 1.0)
        wave_val = np.sin(2.0 * np.pi * FREQUENCY * t) * envelope
        Ez[78:103, 10] = Ez[78:103, 10] * 0.5 + wave_val * 0.5

    # 2. Render Field directly to pixel array
    vis_field = np.clip(Ez * 0.7, -1.0, 1.0)
    pixels = np.zeros((H_sim, W_sim, 3), dtype=np.uint8)
    
    pos_mask = vis_field > 0
    neg_mask = vis_field <= 0
    
    # Positive crests (Teal)
    t_pos = vis_field[pos_mask][:, None]
    pixels[pos_mask] = ((1.0 - t_pos) * COLOR_BG + t_pos * COLOR_CREST).astype(np.uint8)
    
    # Negative troughs (Coral)
    t_neg = (-vis_field[neg_mask])[:, None]
    pixels[neg_mask] = ((1.0 - t_neg) * COLOR_BG + t_neg * COLOR_TROUGH).astype(np.uint8)
    
    # 3. Upscale & Display
    img = Image.fromarray(pixels, mode='RGB')
    img_resized = img.resize(SIZE, Image.BILINEAR)
    py5.set_np_pixels(np.array(img_resized), bands='RGB')
    
    # 4. Render overlay: Glowing pillars
    scale_x = SIZE[0] / W_sim
    scale_y = SIZE[1] / H_sim
    pr = r * scale_x
    
    py5.push_style()
    py5.blend_mode(py5.ADD)
    for y_grid in range(a // 2, H_sim, a):
        for x_grid in range(a // 2, W_sim, a):
            if in_waveguide(x_grid, y_grid):
                continue
            
            px = x_grid * scale_x
            py = y_grid * scale_y
            
            # Query wave intensity from localized cell
            val = np.clip(Ez[y_grid, x_grid] ** 2 * 3.0, 0.0, 1.0)
            
            # Evanescent soft gold halo glow
            glow_r = pr * (1.8 + val * 0.8)
            py5.no_stroke()
            py5.fill(210, 160, 45, 12 + val * 48)
            py5.circle(px, py, glow_r)
            
            # Solid Core Gold Pillar
            py5.fill(218 + val * 37, 165 + val * 55, 32 + val * 68)
            py5.stroke(255, 235, 150, 40 + val * 100)
            py5.stroke_weight(1.0 + val * 1.5)
            py5.circle(px, py, pr)
    py5.pop_style()

    # 5. Save Frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Real-time stdout progress logs to prevent timeouts
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # 6. Finalization & FFmpeg encoding
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Encoding {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Mirror outputs
        subprocess.run(["cp", str(SKETCH_DIR / f"{WORK_NAME}.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        # Save exact preview image from middle of the clip
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

if __name__ == "__main__":
    py5.run_sketch()
