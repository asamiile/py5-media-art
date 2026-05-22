"""
lenia_morphogenesis
==================
A 2D Lenia continuous cellular automaton simulation using FFT-based convolutions.
Cellular bodies are advected by active gradients, leaving trails of bioluminescent
particles that highlight biological self-organization.

Palette: Obsidian (bg), Electric Amethyst (body), Bio-Luminescent Cyan (halo), Core Solar Gold (core)
Format: 15s @ 60fps -> lenia_morphogenesis.mp4
"""

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

# ── Configuration ────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# ── Lenia Settings ───────────────────────────────────────────────────────────
GW, GH = 640, 360  # Simulation grid size (16:9)
R = 15.0           # Kernel radius
DT = 0.07          # Time step
MU = 0.20          # Growth center
SIGMA = 0.030      # Growth width

# ── Particles ─────────────────────────────────────────────────────────────────
N_TRACERS = 100_000

# ── State Variables ──────────────────────────────────────────────────────────
field = None
kernel_fft = None
tx = None
ty = None


def setup():
    global field, kernel_fft, tx, ty
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.frame_rate(FPS)

    # Initialize Lenia fields
    field = np.zeros((GH, GW), dtype=np.float32)

    # Define coordinate grid with periodic boundaries for FFT convolution
    x = np.minimum(np.arange(GW), GW - np.arange(GW))
    y = np.minimum(np.arange(GH), GH - np.arange(GH))
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)

    # Bell-shaped ring kernel profile
    r_norm = dist / R
    kernel = np.exp(-0.5 * ((r_norm - 0.5) / 0.15)**2)
    kernel[r_norm > 1.0] = 0.0
    kernel /= kernel.sum()

    kernel_fft = np.fft.fft2(kernel)

    # Seed multiple organic starting blobs
    for _ in range(6):
        cx = np.random.randint(GW // 3, GW * 2 // 3)
        cy = np.random.randint(GH // 3, GH * 2 // 3)
        r = np.random.uniform(14, 28)
        y_idx, x_idx = np.ogrid[:GH, :GW]
        d2 = (x_idx - cx)**2 + (y_idx - cy)**2
        mask = d2 < r**2
        field[mask] = np.random.uniform(0.2, 0.9, mask.sum())

    # Pre-convolve to smooth the seed blobs
    for _ in range(3):
        field = np.real(np.fft.ifft2(np.fft.fft2(field) * kernel_fft))
    field = np.clip(field * 3.5, 0.0, 1.0)

    # Setup particles
    tx = np.random.uniform(0, GW, N_TRACERS).astype(np.float32)
    ty = np.random.uniform(0, GH, N_TRACERS).astype(np.float32)

    print(f"[{WORK_NAME}] Lenia grid initialized: {GW}x{GH}. Canvas size: {SIZE[0]}x{SIZE[1]}.")


def draw():
    global field, tx, ty

    fc = py5.frame_count
    W, H = SIZE

    # ── Lenia Simulation Step ────────────────────────────────────────────────
    # Compute neighborhood density using FFT convolution
    field_fft = np.fft.fft2(field)
    U = np.real(np.fft.ifft2(field_fft * kernel_fft))

    # Growth function G(U) mapping density to state change
    G = 2.0 * np.exp(-0.5 * ((U - MU) / SIGMA)**2) - 1.0

    # Update field
    field = np.clip(field + DT * G, 0.0, 1.0)

    # ── Render Base Map (Grid Space) ─────────────────────────────────────────
    # Background: Obsidian (12, 10, 18)
    r_grid = np.full((GH, GW), 12.0, dtype=np.float32)
    g_grid = np.full((GH, GW), 10.0, dtype=np.float32)
    b_grid = np.full((GH, GW), 18.0, dtype=np.float32)

    # Blend Bio-Luminescent Cyan halo (0, 220, 200) based on neighborhood U
    w_halo = np.clip(U * 1.6, 0.0, 1.0)
    r_grid = r_grid * (1.0 - w_halo) + 0.0 * w_halo
    g_grid = g_grid * (1.0 - w_halo) + 220.0 * w_halo
    b_grid = b_grid * (1.0 - w_halo) + 200.0 * w_halo

    # Blend Electric Amethyst body (155, 60, 230) based on field state A
    w_body = np.clip(field * 2.2, 0.0, 1.0)
    r_grid = r_grid * (1.0 - w_body) + 155.0 * w_body
    g_grid = g_grid * (1.0 - w_body) + 60.0 * w_body
    b_grid = b_grid * (1.0 - w_body) + 230.0 * w_body

    # Blend Core Solar Gold centers (255, 190, 40) where core activity is high
    w_core = np.clip((field * U) ** 1.4 * 3.5, 0.0, 1.0)
    r_grid = r_grid * (1.0 - w_core) + 255.0 * w_core
    g_grid = g_grid * (1.0 - w_core) + 190.0 * w_core
    b_grid = b_grid * (1.0 - w_core) + 40.0 * w_core

    # Convert grid values to uint8 colors
    r_grid = np.clip(r_grid, 0, 255).astype(np.uint8)
    g_grid = np.clip(g_grid, 0, 255).astype(np.uint8)
    b_grid = np.clip(b_grid, 0, 255).astype(np.uint8)

    # ── Upscale Grid to Canvas ───────────────────────────────────────────────
    # Since GW, GH = 640, 360 and SIZE = 1920, 1080, scale factor is exactly 3.
    scale_x = W // GW
    scale_y = H // GH
    scale_block = np.ones((scale_y, scale_x), dtype=np.uint8)

    r_up = np.kron(r_grid, scale_block)[:H, :W]
    g_up = np.kron(g_grid, scale_block)[:H, :W]
    b_up = np.kron(b_grid, scale_block)[:H, :W]

    # ── Particles Advection ──────────────────────────────────────────────────
    # Calculate gradients of the Lenia field
    dy, dx = np.gradient(field)

    ix = np.clip(tx.astype(np.int32), 1, GW - 2)
    iy = np.clip(ty.astype(np.int32), 1, GH - 2)

    # Advect particles along gradients + small thermal noise
    grad_x = dx[iy, ix]
    grad_y = dy[iy, ix]

    tx += grad_x * 5.0 + np.random.normal(0, 0.12, N_TRACERS).astype(np.float32)
    ty += grad_y * 5.0 + np.random.normal(0, 0.12, N_TRACERS).astype(np.float32)

    # Wrap or re-spawn out of bounds particles
    oob = (tx < 0) | (tx >= GW) | (ty < 0) | (ty >= GH)
    n_oob = int(oob.sum())
    if n_oob > 0:
        tx[oob] = np.random.uniform(0, GW, n_oob).astype(np.float32)
        ty[oob] = np.random.uniform(0, GH, n_oob).astype(np.float32)

    # Map particles to canvas coordinates
    pix_x = np.clip((tx * (W / GW)).astype(np.int32), 0, W - 1)
    pix_y = np.clip((ty * (H / GH)).astype(np.int32), 0, H - 1)

    # Plot particles as additive gold dust (32, 24, 5)
    r_up_i = r_up.astype(np.int16)
    g_up_i = g_up.astype(np.int16)
    b_up_i = b_up.astype(np.int16)

    np.add.at(r_up_i, (pix_y, pix_x), 32)
    np.add.at(g_up_i, (pix_y, pix_x), 24)
    np.add.at(b_up_i, (pix_y, pix_x), 5)

    r_up = np.clip(r_up_i, 0, 255).astype(np.uint8)
    g_up = np.clip(g_up_i, 0, 255).astype(np.uint8)
    b_up = np.clip(b_up_i, 0, 255).astype(np.uint8)

    # ── Write to Py5 Pixels Buffer ───────────────────────────────────────────
    py5.load_np_pixels()
    ah, aw = py5.np_pixels.shape[:2]
    py5.np_pixels[:ah, :aw, 0] = 255  # Alpha channel
    py5.np_pixels[:ah, :aw, 1] = r_up[:ah, :aw]
    py5.np_pixels[:ah, :aw, 2] = g_up[:ah, :aw]
    py5.np_pixels[:ah, :aw, 3] = b_up[:ah, :aw]
    py5.update_np_pixels()

    # Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Render complete
    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        # Compile frames into MP4 using FFmpeg
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save mid-frame as preview snapshot
        mid_frame = TOTAL_FRAMES // 2
        shutil.copyfile(
            str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        )
        print(f"[Render Preview] Saved preview image as {PREVIEW_FILENAME}")

        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")


if __name__ == "__main__":
    py5.run_sketch()
