"""
kinetic_gierer_meinhardt_turing_2d
A 4K kinetic visualization of the Gierer-Meinhardt reaction-diffusion model,
simulating biological pattern formation (morphogenesis) with spots and stripes
that dynamically split, fuse, and oscillate in a bioluminescent void.
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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# --- Simulation Parameters ---
GRID_W = 480
GRID_H = 270

DT = 0.15
STEPS_PER_FRAME = 12

# Gierer-Meinhardt Model parameters (Optimized for high-contrast Turing Patterns)
DA = 0.005          # Activator diffusion rate
DH = 0.40           # Inhibitor diffusion rate
MU_A = 0.04         # Activator decay rate
MU_H = 0.10         # Inhibitor decay rate
RHO_A = 0.01        # Activator background feed
KAPPA = 0.01        # Small saturation limit

# Arrays: Activator (Act) and Inhibitor (Inh)
# Initialize with random noise to seed Turing patterns
Act = np.random.uniform(0.5, 2.5, (GRID_H, GRID_W)).astype(np.float32)
Inh = np.random.uniform(1.0, 4.0, (GRID_H, GRID_W)).astype(np.float32)


def laplacian(f):
    # Fast 5-point stencil Laplacian using numpy roll with wrapping boundaries
    return (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
            np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 4.0 * f)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Introduce localized seeds (stimuli) to break symmetry early on
    cx, cy = GRID_W // 2, GRID_H // 2
    y_indices, x_indices = np.ogrid[:GRID_H, :GRID_W]
    
    # Create several circular high-activator regions
    for angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        r = GRID_H // 4
        sx = int(cx + r * np.cos(angle))
        sy = int(cy + r * np.sin(angle))
        mask = (x_indices - sx) ** 2 + (y_indices - sy) ** 2 <= (GRID_H // 12) ** 2
        Act[mask] += 3.0
        
    print("[Setup] Gierer-Meinhardt lattice initialized with high-contrast parameters.")


def step_simulation(t):
    global Act, Inh
    # Modulate production rate rho over time to drive dynamic pattern morphing
    rho = 0.08 + 0.04 * np.sin(2 * np.pi * t / DURATION_SEC)
    
    for _ in range(STEPS_PER_FRAME):
        lap_a = laplacian(Act)
        lap_h = laplacian(Inh)
        
        # Gierer-Meinhardt terms
        # Production: rho * a^2 / (h * (1 + kappa * a^2))
        production = (rho * Act**2) / (Inh * (1.0 + KAPPA * Act**2))
        
        da_dt = DA * lap_a + production - MU_A * Act + RHO_A
        dh_dt = DH * lap_h + rho * Act**2 - MU_H * Inh
        
        Act = np.clip(Act + DT * da_dt, 0.0, 15.0)
        Inh = np.clip(Inh + DT * dh_dt, 0.0, 15.0)


def colorize(a_grid, h_grid, t):
    # Vectorized color mapping for bioluminescent theme
    # Background: deep charcoal void (10, 12, 22)
    # Activator (Stripes/Spots): Glowing Cyan-Teal transitioning to Coral-Magenta
    # Inhibitor: Ethereal Amethyst/Purple halo
    
    bg_r, bg_g, bg_b = 10, 12, 22
    
    # Normalize activator and inhibitor based on actual simulation ranges (Act ~0.4 to 7.0)
    an = np.clip((a_grid - 0.4) / 5.5, 0.0, 1.0)
    hn = np.clip((h_grid - 1.0) / 7.0, 0.0, 1.0)
    
    # Phase shift color over time for kinetic feel
    hue_shift = 0.5 + 0.5 * np.sin(2 * np.pi * t / DURATION_SEC)
    
    # Activator color: blending vibrant Cyan (0, 255, 240) and Coral/Pink (255, 60, 140)
    act_r = 0 * (1 - hue_shift) + 255 * hue_shift
    act_g = 255 * (1 - hue_shift) + 60 * hue_shift
    act_b = 240 * (1 - hue_shift) + 140 * hue_shift
    
    # Inhibitor color: Electric Purple/Amethyst (160, 40, 255)
    inh_r, inh_g, inh_b = 160, 40, 255
    
    # Blend color grids
    r = bg_r + (an * act_r + hn * inh_r * 0.45)
    g = bg_g + (an * act_g + hn * inh_g * 0.45)
    b = bg_b + (an * act_b + hn * inh_b * 0.45)
    
    # Highlight peak activator areas to look hot/luminescent (white glow core)
    peak = np.clip((a_grid - 4.5) / 2.0, 0.0, 1.0)
    r += peak * 120
    g += peak * 120
    b += peak * 120
    
    return np.clip(r, 0, 255).astype(np.uint8), np.clip(g, 0, 255).astype(np.uint8), np.clip(b, 0, 255).astype(np.uint8)


def draw():
    W, H = SIZE
    frame = py5.frame_count
    t = frame / FPS
    
    step_simulation(t)
    
    r_grid, g_grid, b_grid = colorize(Act, Inh, t)
    
    # Upscale 480x270 directly to 3840x2160 (8x repeat factor)
    sx = W // GRID_W
    sy = H // GRID_H
    
    r_up = np.repeat(np.repeat(r_grid, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_grid, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_grid, sy, axis=0), sx, axis=1)[:H, :W]
    
    # Write to py5 pixels
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255      # Alpha
    py5.np_pixels[:, :, 1] = r_up     # R
    py5.np_pixels[:, :, 2] = g_up     # G
    py5.np_pixels[:, :, 3] = b_up     # B
    py5.update_np_pixels()

    # Vignette shadow
    for i in range(16):
        alpha = int(3 + i * 4)
        m = i * 22
        py5.fill(240, 40, 3, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)

    # HUD telemetry
    py5.fill(280, 20, 95, 140)
    py5.text_size(20)
    py5.text(f"t={t:.2f}s | activator_max: {Act.max():.2f} | inhibitor_max: {Inh.max():.2f} | grid: {GRID_W}x{GRID_H}", 50, H - 50)

    # Blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    if frame == TOTAL_FRAMES // 2:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)


py5.run_sketch()
