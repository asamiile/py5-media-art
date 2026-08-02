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
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Sketch Identification
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# Size Setup
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# SOM Grid dimensions
ROWS, COLS = 35, 35
N_NEURONS = ROWS * COLS

# Training Parameters
MAX_ITER = 100_000
LR_0 = 0.6
SIGMA_0 = max(ROWS, COLS) / 2.2
LAMBDA = MAX_ITER / np.log(SIGMA_0 + 1e-5)
STEPS_PER_FRAME = 90

# State Variables
_weights = np.zeros((N_NEURONS, 3), dtype=np.float32)
_iter = 0

# Precomputed neuron grid coordinates (row, col)
_neuron_rc = np.array([[r, c] for r in range(ROWS) for c in range(COLS)], dtype=np.float32)


def sample_torus_knot(t: float) -> np.ndarray:
    """Sample coordinates along a 3D Torus Knot with gaussian thickness."""
    # Knot parameters (p, q)
    p, q = 3, 7
    # Angle theta
    theta = random.uniform(0, py5.TWO_PI)
    
    # Calculate torus knot coordinates in [0.1, 0.9]^3
    r = 0.22 * (2.0 + np.sin(q * theta))
    x = 0.5 + r * np.cos(p * theta)
    y = 0.5 + r * np.sin(p * theta)
    z = 0.5 + 0.22 * np.cos(q * theta)
    
    # Add thickness noise
    x += random.gauss(0, 0.015)
    y += random.gauss(0, 0.015)
    z += random.gauss(0, 0.015)
    
    return np.array([x, y, z], dtype=np.float32)


def reset_som() -> None:
    """Initialize SOM grid in a flat sheet in the center of the 3D space."""
    global _weights, _iter
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            # Start flat at z = 0.5, with small noise
            _weights[idx] = [
                0.2 + 0.6 * (c / (COLS - 1)),
                0.2 + 0.6 * (r / (ROWS - 1)),
                0.5 + random.uniform(-0.01, 0.01)
            ]
    _iter = 0


def train_step() -> None:
    """Execute one competitive learning step of the Kohonen Map."""
    global _iter, _weights
    if _iter >= MAX_ITER:
        return

    # Decay learning rate and neighborhood radius
    lr = LR_0 * np.exp(-_iter / MAX_ITER)
    sigma = SIGMA_0 * np.exp(-_iter / LAMBDA)

    # Sample input point from torus knot shape
    sample = sample_torus_knot(_iter / MAX_ITER)

    # Find Best Matching Unit (BMU)
    diff = _weights - sample
    dists_sq = (diff * diff).sum(axis=1)
    bmu = int(dists_sq.argmin())

    # BMU grid position
    bmu_r, bmu_c = bmu // COLS, bmu % COLS
    bmu_pos = np.array([bmu_r, bmu_c], dtype=np.float32)

    # Neighborhood influence (Gaussian)
    d2 = ((_neuron_rc - bmu_pos) ** 2).sum(axis=1)
    influence = np.exp(-d2 / (2.0 * sigma * sigma + 1e-9)).astype(np.float32)

    # Update weights toward sample
    _weights += lr * influence[:, np.newaxis] * (sample - _weights)
    _weights = np.clip(_weights, 0.0, 1.0)

    _iter += 1


def rotate_3d(x: float, y: float, z: float, ang_x: float, ang_y: float) -> tuple[float, float, float]:
    """Rotate 3D coordinates around X and Y axes centered at 0.5."""
    # Shift center to 0.0
    dx, dy, dz = x - 0.5, y - 0.5, z - 0.5
    
    # Rotate around Y axis
    cos_y, sin_y = np.cos(ang_y), np.sin(ang_y)
    rx1 = dx * cos_y - dz * sin_y
    rz1 = dx * sin_y + dz * cos_y
    
    # Rotate around X axis
    cos_x, sin_x = np.cos(ang_x), np.sin(ang_x)
    ry2 = dy * cos_x - rz1 * sin_x
    rz2 = dy * sin_x + rz1 * cos_x
    
    # Shift back
    return rx1 + 0.5, ry2 + 0.5, rz2 + 0.5


def project_to_screen(x: float, y: float, z: float, scale_f: float) -> tuple[float, float]:
    """Manually project rotated 3D coordinates to 2D centered on screen."""
    # Center and scale
    screen_x = py5.width / 2.0 + (x - 0.5) * scale_f
    screen_y = py5.height / 2.0 + (y - 0.5) * scale_f
    return screen_x, screen_y


def setup() -> None:
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    reset_som()
    py5.background(4, 5, 8)  # Deep obsidian void


def draw() -> None:
    # Train SOM in background
    if _iter < MAX_ITER:
        for _ in range(STEPS_PER_FRAME):
            train_step()

    # Trail decay overlay
    py5.no_stroke()
    py5.fill(4, 5, 8, 18)
    py5.rect(0, 0, py5.width, py5.height)

    # Compute dynamic rotation angles based on time
    t_norm = py5.frame_count / TOTAL_FRAMES
    ang_x = t_norm * py5.TWO_PI * 0.8
    ang_y = t_norm * py5.TWO_PI * 1.3
    
    scale_f = py5.height * 0.82

    # Rotate all node weights into projected screen space
    rotated_pts = []
    for i in range(N_NEURONS):
        w = _weights[i]
        rx, ry, rz = rotate_3d(w[0], w[1], w[2], ang_x, ang_y)
        sx, sy = project_to_screen(rx, ry, rz, scale_f)
        rotated_pts.append((sx, sy, rz))

    # Draw Grid Edges
    py5.stroke_weight(1.0)
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            sx, sy, rz = rotated_pts[idx]
            
            # Depth-based alpha/intensity (rz ranges from -0.5 to 0.5)
            depth_norm = rz + 0.5  # [0, 1]

            # Right connection
            if c < COLS - 1:
                idx_r = idx + 1
                sx_r, sy_r, rz_r = rotated_pts[idx_r]
                depth_avg = (depth_norm + (rz_r + 0.5)) * 0.5
                
                # Gradient color: low depth (cyan) -> high depth (pink)
                # Cyan (0, 229, 255) -> Violet (160, 80, 255)
                r_col = int(160 * depth_avg)
                g_col = int(229 * (1.0 - depth_avg) + 80 * depth_avg)
                b_col = 255
                alpha = int((30 + depth_avg * 130) * 0.85)

                py5.stroke(r_col, g_col, b_col, alpha)
                py5.stroke_weight(0.8 + depth_avg * 1.8)
                py5.line(sx, sy, sx_r, sy_r)

            # Down connection
            if r < ROWS - 1:
                idx_d = idx + COLS
                sx_d, sy_d, rz_d = rotated_pts[idx_d]
                depth_avg = (depth_norm + (rz_d + 0.5)) * 0.5
                
                r_col = int(160 * depth_avg)
                g_col = int(229 * (1.0 - depth_avg) + 80 * depth_avg)
                b_col = 255
                alpha = int((30 + depth_avg * 130) * 0.85)

                py5.stroke(r_col, g_col, b_col, alpha)
                py5.stroke_weight(0.8 + depth_avg * 1.8)
                py5.line(sx, sy, sx_d, sy_d)

    # Draw Nodes (with organic flicker and bloom)
    py5.no_stroke()
    for i in range(N_NEURONS):
        sx, sy, rz = rotated_pts[i]
        depth_norm = rz + 0.5
        
        # Soft star flicker pulse
        pulse = py5.noise(sx * 0.03, sy * 0.03, t_norm * 20.0)

        # Draw only nodes with high depth visibility
        if depth_norm > 0.35:
            # Color: Cyan/Violet -> Soft Gold highlight for BMU adaptivity
            # Magenta (#ff2a85 : 255, 42, 133) for active depths
            r_col = int(255 * depth_norm)
            g_col = int(42 * depth_norm + 160 * (1.0 - depth_norm))
            b_col = int(133 * depth_norm + 255 * (1.0 - depth_norm))
            
            alpha = int((100 + depth_norm * 140) * (0.8 + 0.2 * pulse))
            size = (4.0 + depth_norm * 8.0) * (0.85 + 0.3 * pulse)

            py5.fill(r_col, g_col, b_col, int(30 * (0.7 + 0.3 * pulse)))
            py5.circle(sx, sy, size * 2.2)

            py5.fill(r_col, g_col, b_col, alpha)
            py5.circle(sx, sy, size)

    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Output frame saving
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Exit and compile
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot from the middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
