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

# Particle system settings
N = 1500
R = 45.0        # Neighbor alignment radius
SPEED = 5.0     # Particle speed (pixels per frame)

# State arrays
pos_x = np.zeros(N, dtype=np.float32)
pos_y = np.zeros(N, dtype=np.float32)
thetas = np.zeros(N, dtype=np.float32)

# Initialize positions randomly on the screen and random angles
W, H = SIZE
rng = np.random.default_rng(2026)
pos_x = rng.uniform(0.0, W, N).astype(np.float32)
pos_y = rng.uniform(0.0, H, N).astype(np.float32)
thetas = rng.uniform(-np.pi, np.pi, N).astype(np.float32)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 8, 14)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    global pos_x, pos_y, thetas

    # Smoothly modulate noise to demonstrate the phase transition
    t = py5.frame_count / TOTAL_FRAMES
    # Cycle noise level from 0.08 (highly ordered) to 1.8 (disordered chaos) and back
    noise_amplitude = 0.08 + 1.72 * (0.5 + 0.5 * np.cos(t * np.pi * 2.0 * 1.5))

    # Toroidal distance calculation (N x N)
    dx = pos_x[:, None] - pos_x[None, :]
    dy = pos_y[:, None] - pos_y[None, :]

    # Wrap coordinates for periodic boundary conditions
    dx = (dx + W / 2.0) % W - W / 2.0
    dy = (dy + H / 2.0) % H - H / 2.0

    dist2 = dx**2 + dy**2
    in_range = dist2 < R**2

    # Calculate average direction of neighbors (including self)
    vx = np.cos(thetas)
    vy = np.sin(thetas)
    
    sum_vx = np.sum(vx * in_range, axis=1)
    sum_vy = np.sum(vy * in_range, axis=1)
    
    # Calculate local alignment order parameter (0 = chaotic, 1 = aligned)
    counts = np.sum(in_range, axis=1)
    local_order = np.sqrt(sum_vx**2 + sum_vy**2) / counts

    # Update headings with noise
    thetas_new = np.arctan2(sum_vy, sum_vx)
    # Add random angular noise
    angular_noise = rng.uniform(-np.pi, np.pi, N).astype(np.float32) * noise_amplitude
    thetas = thetas_new + angular_noise

    # Update positions (toroidal wrapping)
    pos_x = (pos_x + SPEED * np.cos(thetas)) % W
    pos_y = (pos_y + SPEED * np.sin(thetas)) % H

    # Draw trails by overlaying a semi-translucent background rect
    py5.no_stroke()
    py5.fill(10, 8, 14, 22)  # High translucency for long trails
    py5.rect(0, 0, W, H)

    # Draw particles colored by their local alignment and density
    # Background: Abyss Void (10, 8, 14)
    # Aligned: Mint (0, 245, 160)
    # Chaotic: Cobalt Indigo (40, 60, 200)
    # High-density cores: Solar Amber (250, 180, 20)
    
    for i in range(N):
        order = local_order[i]
        density = counts[i]
        
        # Color interpolation based on local order
        r_col = 40.0 * (1.0 - order) + 0.0 * order
        g_col = 60.0 * (1.0 - order) + 245.0 * order
        b_col = 200.0 * (1.0 - order) + 160.0 * order
        
        # Highlight high density nodes with Solar Amber
        if density > 18:
            density_factor = min(1.0, (density - 18) / 15.0)
            r_col = r_col * (1.0 - density_factor) + 250.0 * density_factor
            g_col = g_col * (1.0 - density_factor) + 180.0 * density_factor
            b_col = b_col * (1.0 - density_factor) + 20.0 * density_factor

        py5.fill(r_col, g_col, b_col, 200)
        
        # Particle size reflects coordination
        size = 3.0 + 3.0 * order
        py5.ellipse(pos_x[i], pos_y[i], size, size)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot (mid frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
