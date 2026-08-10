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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Dynamic duration: 15-20 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation grid size (lower resolution for high performance)
SIM_W = 960
SIM_H = 540

# PDE Parameters
DT = 0.15
K = 0.08  # Edge threshold parameter
DECAY = 0.992  # Slowly fade out intensity to keep it dynamic

# Simulation state arrays
intensity = None
source_grid = None

# Orbiting attractors for depositing ink
class Attractor:
    def __init__(self, idx):
        self.idx = idx
        self.x = random.uniform(0, SIM_W)
        self.y = random.uniform(0, SIM_H)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.radius = random.uniform(10, 30)
        self.strength = random.uniform(0.4, 0.8)
        self.angle_speed = random.uniform(-0.05, 0.05)
        self.angle = random.uniform(0, py5.TWO_PI)

    def update(self):
        # Orbit / wander logic using sine/cosine and random forces
        self.angle += self.angle_speed
        self.vx += py5.cos(self.angle) * 0.15 + random.uniform(-0.1, 0.1)
        self.vy += py5.sin(self.angle) * 0.15 + random.uniform(-0.1, 0.1)
        
        # Limit velocity
        speed = py5.dist(0, 0, self.vx, self.vy)
        if speed > 4.0:
            self.vx = (self.vx / speed) * 4.0
            self.vy = (self.vy / speed) * 4.0

        self.x += self.vx
        self.y += self.vy

        # Toroidal wrapping
        if self.x < 0: self.x += SIM_W
        if self.x >= SIM_W: self.x -= SIM_W
        if self.y < 0: self.y += SIM_H
        if self.y >= SIM_H: self.y -= SIM_H

attractors = []

def setup():
    global intensity, source_grid, attractors
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize simulation grids
    intensity = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    source_grid = np.zeros((SIM_H, SIM_W), dtype=np.float32)

    # Initialize attractors
    for i in range(8):
        attractors.append(Attractor(i))


def solve_perona_malik(grid, k_val, dt_val):
    # Compute finite differences with wrapping boundaries for continuous flow
    d_N = np.roll(grid, -1, axis=0) - grid
    d_S = np.roll(grid, 1, axis=0) - grid
    d_E = np.roll(grid, 1, axis=1) - grid
    d_W = np.roll(grid, -1, axis=1) - grid

    # Perona-Malik diffusion coefficient function c(grad) = 1 / (1 + (grad/k)^2)
    c_N = 1.0 / (1.0 + (d_N / k_val)**2)
    c_S = 1.0 / (1.0 + (d_S / k_val)**2)
    c_E = 1.0 / (1.0 + (d_E / k_val)**2)
    c_W = 1.0 / (1.0 + (d_W / k_val)**2)

    # PDE update step
    grid_next = grid + dt_val * (c_N * d_N + c_S * d_S + c_E * d_E + c_W * d_W)
    return grid_next


def draw():
    global intensity, source_grid

    # Clear source grid
    source_grid.fill(0)

    # Update and draw attractors onto the source grid
    # Generate meshgrid coordinates for vectorized distance computation
    y_coords, x_coords = np.ogrid[:SIM_H, :SIM_W]

    for att in attractors:
        att.update()
        # Compute distances in a toroidal grid (wrapping)
        dx = np.minimum(np.abs(x_coords - att.x), SIM_W - np.abs(x_coords - att.x))
        dy = np.minimum(np.abs(y_coords - att.y), SIM_H - np.abs(y_coords - att.y))
        dist_sq = dx**2 + dy**2
        
        # Soft gaussian spot deposit
        r_sq = att.radius**2
        spot = att.strength * np.exp(-dist_sq / (2 * r_sq))
        source_grid += spot

    # Add dynamic noise field background injection
    t = py5.frame_count * 0.01
    # Vectorized noise evaluation at downscaled coordinates
    scale = 0.015
    # To keep it extremely fast, we can sample noise on a smaller grid or generate a noise pattern
    # Let's generate a noise-based source grid:
    # We sample a few waves of noise and sum them up
    noise_grid = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    for oct_idx in range(2):
        freq = scale * (2**oct_idx)
        amp = 0.05 / (2**oct_idx)
        # Shift coordinates based on time to create a scrolling wind effect
        shift_x = py5.cos(t * 0.5) * 50.0
        shift_y = py5.sin(t * 0.5) * 50.0
        
        # We can use numpy's sine waves to simulate a complex noise field efficiently,
        # which is 100x faster than calling single-pixel py5.noise in a loop.
        xs = np.linspace(0, SIM_W * freq, SIM_W) + shift_x
        ys = np.linspace(0, SIM_H * freq, SIM_H) + shift_y
        X, Y = np.meshgrid(xs, ys)
        noise_grid += amp * (np.sin(X + Y) * np.cos(X - Y) + np.sin(Y * 1.5) * np.cos(X * 0.7))

    # Add source to intensity, decay slightly, and solve PDE
    intensity = intensity * DECAY + source_grid * 0.12 + np.clip(noise_grid, 0, 1) * 0.04
    intensity = np.clip(intensity, 0.0, 1.0)

    # Solve Perona-Malik diffusion
    intensity = solve_perona_malik(intensity, K, DT)

    # Compute gradient magnitude for highlighting edges
    d_x = (np.roll(intensity, 1, axis=1) - np.roll(intensity, -1, axis=1)) * 0.5
    d_y = (np.roll(intensity, 1, axis=0) - np.roll(intensity, -1, axis=0)) * 0.5
    grad_mag = np.sqrt(d_x**2 + d_y**2)

    # Map intensity and gradients to the color palette:
    # Deep Prussian Blue: R=10, G=25, B=45
    # Amethyst Purple: R=130, G=45, B=150
    # Golden Glow: R=255, G=190, B=50
    
    # We will interpolate colors based on intensity
    # Let's define the color channels as float32
    r_field = np.zeros_like(intensity)
    g_field = np.zeros_like(intensity)
    b_field = np.zeros_like(intensity)

    # Base colors mapping:
    # 0.0 - 0.4: Fade from black to Prussian Blue
    mask1 = intensity < 0.4
    r_field[mask1] = (intensity[mask1] / 0.4) * 10
    g_field[mask1] = (intensity[mask1] / 0.4) * 25
    b_field[mask1] = (intensity[mask1] / 0.4) * 45

    # 0.4 - 0.8: Prussian Blue to Amethyst Purple
    mask2 = (intensity >= 0.4) & (intensity < 0.8)
    t2 = (intensity[mask2] - 0.4) / 0.4
    r_field[mask2] = 10 + t2 * 120
    g_field[mask2] = 25 + t2 * 20
    b_field[mask2] = 45 + t2 * 105

    # 0.8 - 1.0: Amethyst Purple to Golden White
    mask3 = intensity >= 0.8
    t3 = (intensity[mask3] - 0.8) / 0.2
    r_field[mask3] = 130 + t3 * 125
    g_field[mask3] = 45 + t3 * 145
    b_field[mask3] = 150 + t3 * (-100)  # gold has lower blue

    # Overlay edge highlights using the gradient magnitude
    # Normalize grad_mag for visualization
    edge_mask = grad_mag > 0.02
    edge_factor = np.clip((grad_mag[edge_mask] - 0.02) / 0.05, 0.0, 1.0)
    
    # Blend in Golden Glow (255, 190, 50) on edges
    r_field[edge_mask] = r_field[edge_mask] * (1.0 - edge_factor) + 255 * edge_factor
    g_field[edge_mask] = g_field[edge_mask] * (1.0 - edge_factor) + 190 * edge_factor
    b_field[edge_mask] = b_field[edge_mask] * (1.0 - edge_factor) + 50 * edge_factor

    # Convert to ARGB format for py5 blitting
    r_int = np.clip(r_field, 0, 255).astype(np.uint8)
    g_int = np.clip(g_field, 0, 255).astype(np.uint8)
    b_int = np.clip(b_field, 0, 255).astype(np.uint8)
    a_int = np.full_like(r_int, 255)

    # Load upscaled version using Py5Image
    img = py5.create_image(SIM_W, SIM_H, py5.ARGB)
    img.load_np_pixels()
    # Map channels: 0 is alpha, 1 is red, 2 is green, 3 is blue
    img.np_pixels[:, :, 0] = a_int
    img.np_pixels[:, :, 1] = r_int
    img.np_pixels[:, :, 2] = g_int
    img.np_pixels[:, :, 3] = b_int
    img.update_np_pixels()

    # Draw to screen with bilinear scaling
    py5.image(img, 0, 0, *SIZE)

    # Save the frame
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
