from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import scipy.special as sp
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

# Bessel modes definitions: (n, m, amplitude, phase_offset, speed_mult)
# We choose a set of visually interesting modes (both symmetric and asymmetric)
MODES = [
    (0, 1, 1.0, 0.0, 1.0),       # Fundamental breathing mode (symmetric)
    (1, 2, 0.7, np.pi/3, 1.8),   # Asymmetric mode with 2 angular lobes
    (3, 1, 0.6, -np.pi/4, 2.4),  # Asymmetric mode with 6 angular lobes
    (2, 2, 0.5, np.pi/6, 3.1)    # Complex mode
]

# Mode eigenvalues (zeros of Bessel functions)
ZEROS = {}
for n in set(m[0] for m in MODES):
    # Get the maximum m needed for this n
    max_m = max(m[1] for m in MODES if m[0] == n)
    ZEROS[n] = sp.jn_zeros(n, max_m)

# Precomputed grid coordinates
W, H = SIZE
x = np.linspace(-1.2, 1.2, W, dtype=np.float32)
y = np.linspace(-1.2 * (H/W), 1.2 * (H/W), H, dtype=np.float32)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
THETA = np.arctan2(Y, X)

# Boundary mask: smooth edge at r = 1.0
BOUNDARY_MASK = np.clip((1.0 - R) / 0.02, 0.0, 1.0)
# Inside mask
INSIDE_MASK = (R <= 1.0).astype(np.float32)

# Normalise radial values for Bessel evaluation (radius of membrane is 1.0)
R_NORM = np.clip(R, 0.0, 1.0)

# Precompute Bessel functions for each mode: J_n(lambda_nm * r)
MODE_J = []
for n, m, amp, phase, speed in MODES:
    alpha = ZEROS[n][m - 1]  # m-th zero of J_n
    # Evaluate J_n(alpha * r)
    j_val = sp.jn(n, alpha * R_NORM)
    # Clamp boundary to exactly 0 to ensure stability
    j_val = j_val * INSIDE_MASK
    # Normalize mode values to avoid overflow
    max_val = np.max(np.abs(j_val))
    if max_val > 0:
        j_val /= max_val
    MODE_J.append((n, amp, phase, speed, j_val))


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 5, 15)  # Dark purple-black background


def draw():
    t = py5.frame_count / TOTAL_FRAMES
    theta_t = t * np.pi * 2.0

    # Calculate displacement field as a linear combination of active modes
    disp = np.zeros_like(R)
    for n, amp, phase, speed, j_val in MODE_J:
        # Time oscillation
        osc = np.cos(speed * theta_t * 3.0 + phase)
        # Spatial oscillation (radial + angular)
        if n == 0:
            disp += amp * j_val * osc
        else:
            disp += amp * j_val * np.cos(n * THETA + speed * theta_t) * osc

    # Normalize displacement to [-1, 1] range inside the membrane
    disp_norm = disp / 2.5

    # Coloring logic based on displacement and gradients
    # Palette colors:
    # Background/Void: Deep Amethyst Void (12, 8, 24)
    # Electric Cyan (60%): (0, 220, 220)
    # Neon Amethyst (30%): (180, 40, 200)
    # Solar Gold (10%): (240, 180, 20)

    # Base background
    r_arr = np.full_like(R, 12.0)
    g_arr = np.full_like(R, 8.0)
    b_arr = np.full_like(R, 24.0)

    # Positive displacement: Cyan
    pos_mask = (disp_norm > 0) * INSIDE_MASK
    # Negative displacement: Magenta/Amethyst
    neg_mask = (disp_norm < 0) * INSIDE_MASK
    abs_disp = np.abs(disp_norm)

    # Blend colors
    r_arr = np.where(pos_mask, r_arr * (1 - abs_disp) + 0.0 * abs_disp, r_arr)
    g_arr = np.where(pos_mask, g_arr * (1 - abs_disp) + 220.0 * abs_disp, g_arr)
    b_arr = np.where(pos_mask, b_arr * (1 - abs_disp) + 220.0 * abs_disp, b_arr)

    r_arr = np.where(neg_mask, r_arr * (1 - abs_disp) + 180.0 * abs_disp, r_arr)
    g_arr = np.where(neg_mask, g_arr * (1 - abs_disp) + 40.0 * abs_disp, g_arr)
    b_arr = np.where(neg_mask, b_arr * (1 - abs_disp) + 200.0 * abs_disp, b_arr)

    # Additive nodal lines (where displacement is close to zero, but inside membrane)
    nodal_thickness = 0.015
    nodal_mask = (abs_disp < nodal_thickness) * INSIDE_MASK
    nodal_factor = (1.0 - abs_disp / nodal_thickness) * nodal_mask

    # Glow on nodal lines: Solar Gold
    r_arr += nodal_factor * 240.0
    g_arr += nodal_factor * 180.0
    b_arr += nodal_factor * 20.0

    # Draw membrane border boundary glow: Solar Gold
    border_mask = np.exp(-((R - 1.0) ** 2) / 0.0001)
    r_arr += border_mask * 240.0
    g_arr += border_mask * 180.0
    b_arr += border_mask * 20.0

    # Apply clipping
    r_img = np.clip(r_arr, 0, 255).astype(np.uint8)
    g_img = np.clip(g_arr, 0, 255).astype(np.uint8)
    b_img = np.clip(b_arr, 0, 255).astype(np.uint8)

    # Blit directly to screen pixels
    py5.load_np_pixels()
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = r_img
    py5.np_pixels[..., 2] = g_img
    py5.np_pixels[..., 3] = b_img
    py5.update_np_pixels()

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
