from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
from dataclasses import dataclass
import numpy as np
import py5

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # (3840, 2160)

# Caustic simulation grid dimensions
GRID_SCALE = 6
cols = SIZE[0] // GRID_SCALE  # 640
rows = SIZE[1] // GRID_SCALE  # 360

N_RAYS = 1500  # High density of ray tracing across the surface
N_STEPS = 85   # Tracer vertical depth layers
RAY_STEP_SIZE = 3.5

# Palettes
c_bg_top = np.array([5.0, 12.0, 22.0], dtype=np.float32)       # Deep marine top
c_bg_bot = np.array([1.0, 2.0, 4.0], dtype=np.float32)         # Deep abyss bottom

# Particles setup
particles = []


@dataclass
class DustParticle:
    x: float
    y: float
    size: float
    speed: float
    seed: float


def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize 320 floating organic particles
    for _ in range(320):
        particles.append(
            DustParticle(
                x=random.uniform(0, SIZE[0]),
                y=random.uniform(SIZE[1] * 0.22, SIZE[1]),
                size=random.uniform(2.5, 6.0),
                speed=random.uniform(0.6, 1.4),
                seed=random.uniform(0, 10000),
            )
        )


def wave_height(x: np.ndarray, t: float) -> np.ndarray:
    """Sum of multiple harmonics to represent water surface height displacement."""
    return (
        np.sin(x * 0.016 + t * 0.022) * 15.0
        + np.sin(x * 0.038 - t * 0.035) * 5.5
        + np.sin(x * 0.083 + t * 0.055) * 2.0
    )


def wave_slope(x: np.ndarray, t: float) -> np.ndarray:
    """Analytical derivative of wave_height with respect to x."""
    return (
        np.cos(x * 0.016 + t * 0.022) * 0.016 * 15.0
        + np.cos(x * 0.038 - t * 0.035) * 0.038 * 5.5
        + np.cos(x * 0.083 + t * 0.055) * 0.083 * 2.0
    )


def compute_caustic_density(t: float) -> np.ndarray:
    """Vectorized Snell-refraction mapping tracing rays through the depth column."""
    density = np.zeros((rows, cols), dtype=np.float32)

    # Cast rays uniformly across the grid width
    cx_src = np.linspace(0, cols, N_RAYS, endpoint=False)
    h = wave_height(cx_src, t)
    slope = wave_slope(cx_src, t)

    # Refraction angle approximation based on wave slope
    bend = -slope * 1.32

    # Vectorized vertical tracing coordinate fields
    depth = np.arange(N_STEPS, dtype=np.float32)
    y_start = rows * 0.18 + h

    # Broadcasting coordinates: shape is (N_RAYS, N_STEPS)
    Y = y_start[:, None] + depth[None, :] * RAY_STEP_SIZE
    X = cx_src[:, None] + bend[:, None] * depth[None, :] * 1.55

    # Map to integer grid coordinates
    grid_x = X.astype(np.int32)
    grid_y = Y.astype(np.int32)

    # Boundary filtering mask
    mask = (grid_x >= 0) & (grid_x < cols) & (grid_y >= 0) & (grid_y < rows)

    # Contribution weight decreases with depth representing scattering absorption
    weights = 1.0 / (depth + 18.0)
    W = np.repeat(weights[None, :], N_RAYS, axis=0)

    # Vectorized accumulation using numpy add.at
    np.add.at(density, (grid_y[mask], grid_x[mask]), W[mask])

    # Soften caustic bands via rapid NumPy box blur passes
    for _ in range(3):
        padded = np.pad(density, 1, mode="edge")
        density = (
            padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
            + padded[1:-1, 1:-1] * 2.5
        ) / 6.5

    return density


def draw():
    global particles

    t = py5.frame_count * 0.65

    # 1. Compute caustic density field
    density = compute_caustic_density(t)

    # 2. Build background volumetric light scattering colors
    y_coords = np.arange(rows)[:, None]
    factor = y_coords / rows
    bg = c_bg_top[None, None, :] * (1.0 - factor[:, :, None]) + c_bg_bot[None, None, :] * factor[:, :, None]

    # Map density peaks to glowing turquoise/teal hues
    light_intensity = np.minimum(1.0, density * 0.55)
    ray_r = light_intensity * 12.0
    ray_g = light_intensity * 185.0 + (light_intensity**2) * 70.0
    ray_b = light_intensity * 255.0
    ray_rgb = np.stack([ray_r, ray_g, ray_b], axis=2)

    # Composite light field over gradient abyss
    rgb = bg + ray_rgb
    rgb_uint8 = np.clip(rgb, 0, 255).astype(np.uint8)

    # High-quality bilinear upscaling to 4K resolution
    try:
        import cv2
        rgb_upscaled = cv2.resize(rgb_uint8, SIZE, interpolation=cv2.INTER_LINEAR)
    except ImportError:
        from PIL import Image
        img = Image.fromarray(rgb_uint8, 'RGB')
        img_upscaled = img.resize(SIZE, Image.BILINEAR)
        rgb_upscaled = np.array(img_upscaled)

    # Blit upscaled light field to py5 buffer
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255  # Alpha
    py5.np_pixels[:, :, 1] = rgb_upscaled[:, :, 0]  # Red
    py5.np_pixels[:, :, 2] = rgb_upscaled[:, :, 1]  # Green
    py5.np_pixels[:, :, 3] = rgb_upscaled[:, :, 2]  # Blue
    py5.update_np_pixels()

    # 3. Draw Water Surface Wave Outline
    py5.no_fill()
    py5.stroke(140, 245, 255, 140)
    py5.stroke_weight(3)
    py5.begin_shape()
    # Draw water wave boundary across the 4K viewport
    for sx in range(0, SIZE[0] + 16, 16):
        sy = (rows * 0.18 + wave_height(sx / GRID_SCALE, t)) * GRID_SCALE
        py5.vertex(sx, sy)
    py5.end_shape()

    # 4. Update and Draw Drifting Particles (Plankton / Dust)
    py5.no_stroke()
    for p in particles:
        # Move particle based on slow Perlin noise flow currents
        vx = (py5.noise(p.x * 0.002, p.y * 0.002, t * 0.008) - 0.46) * 1.6 * p.speed
        vy = (py5.noise(p.x * 0.002 + 100, p.y * 0.002 + 100, t * 0.008) - 0.45) * 1.1 * p.speed
        p.x = (p.x + vx) % SIZE[0]
        p.y = (p.y + vy) % SIZE[1]

        # Prevent particles from floating above the water line
        surface_limit = (rows * 0.18 + wave_height(p.x / GRID_SCALE, t)) * GRID_SCALE
        if p.y < surface_limit:
            p.y = surface_limit + 10

        # Sample local light intensity from density grid
        gx = int(p.x / GRID_SCALE)
        gy = int(p.y / GRID_SCALE)
        gx = max(0, min(cols - 1, gx))
        gy = max(0, min(rows - 1, gy))
        local_light = density[gy, gx]

        # Calculate lighting activation glow factors
        glow_factor = min(2.8, local_light * 6.5)
        alpha = int(45 + glow_factor * 60)
        draw_size = p.size * (1.0 + glow_factor * 0.6)

        # Draw glowing halo ring
        py5.fill(0, 229, 255, int(alpha * 0.35))
        py5.circle(p.x, p.y, draw_size * 2.8)

        # Draw particle core (warm sunlight gold glow when in beams)
        core_r = int(180 + (255 - 180) * min(1.0, glow_factor))
        core_g = int(210 + (230 - 210) * min(1.0, glow_factor))
        core_b = int(150 + (80 - 150) * min(1.0, glow_factor))
        py5.fill(core_r, core_g, core_b, alpha)
        py5.circle(p.x, p.y, draw_size)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress logging
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Complete render
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

        # Save a preview snapshot at the midpoint
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
