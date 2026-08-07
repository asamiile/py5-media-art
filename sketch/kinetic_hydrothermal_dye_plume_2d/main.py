"""
kinetic_hydrothermal_dye_plume_2d
A 4K kinetic visualization of hydrothermal vents emitting glowing dye plumes
that diffuse into a deep abyssal void, simulated via Perlin noise advection 
and grid-based density diffusion.
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# --- Simulation Parameters ---
GRID_W = 320
GRID_H = 180

# We will initialize density grid
density = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Particles array structure:
# N x 9 float32 array: [x, y, vx, vy, age, lifespan, hue, sat, bri]
MAX_PARTICLES = 4000
particles = np.zeros((0, 9), dtype=np.float32)

# Palettes
PALETTES = [
    # Abyssal Bioluminescent: [Hue, Sat, Bri]
    np.array([[330, 85, 95], [195, 90, 90], [45, 95, 95]], dtype=np.float32),
    # Volcanic Magma:
    np.array([[12, 95, 90], [32, 90, 95], [55, 95, 100]], dtype=np.float32),
    # Radioactive Toxic:
    np.array([[135, 90, 85], [170, 85, 90], [280, 80, 95]], dtype=np.float32),
]
active_palette = PALETTES[0]

phase = 0.0

# Pre-generate random wave parameters for fast vectorized flow field
rng = np.random.default_rng(208)
N_WAVES = 16
WAVE_KX = rng.uniform(-1.5, 1.5, N_WAVES).astype(np.float32)
WAVE_KY = rng.uniform(-1.5, 1.5, N_WAVES).astype(np.float32)
WAVE_KT = rng.uniform(-0.5, 0.5, N_WAVES).astype(np.float32)
WAVE_PH = rng.uniform(0, 2*np.pi, N_WAVES).astype(np.float32)


def get_flow(px, py, t):
    """
    Vectorized wave-based flow field (substitute for curl noise).
    Returns (flow_x, flow_y) arrays of the same shape as px, py.
    """
    flow_x = np.zeros_like(px)
    flow_y = np.zeros_like(py)
    
    # Scale coordinates
    sx = px * 0.005
    sy = py * 0.005
    
    for i in range(N_WAVES):
        angle = WAVE_KX[i] * sx + WAVE_KY[i] * sy + WAVE_KT[i] * t + WAVE_PH[i]
        # X flow uses sine, Y flow uses cosine to make it swirl/curl-like
        flow_x += np.sin(angle)
        flow_y += np.cos(angle)
        
    # Normalize
    flow_x /= N_WAVES
    flow_y /= N_WAVES
    return flow_x, flow_y


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    print("[Setup] Initializing simulation state...")


def emit_plume(x, y, amount):
    global particles
    if len(particles) >= MAX_PARTICLES:
        # Prune oldest particles
        particles = particles[amount:]
        
    new_parts = np.zeros((amount, 9), dtype=np.float32)
    angles = np.random.uniform(-np.pi * 0.85, -np.pi * 0.15, amount).astype(np.float32)
    speeds = np.random.normal(2.5, 0.6, amount).astype(np.float32)
    
    new_parts[:, 0] = x + np.random.normal(0, 18, amount)  # x
    new_parts[:, 1] = y + np.random.normal(0, 10, amount)  # y
    new_parts[:, 2] = np.cos(angles) * speeds * 0.4 + np.random.normal(0, 0.2, amount)  # vx
    new_parts[:, 3] = np.sin(angles) * speeds + np.random.normal(0, 0.3, amount)  # vy
    new_parts[:, 4] = 0  # age
    new_parts[:, 5] = np.random.randint(180, 480, amount)  # lifespan
    
    # Choose color from palette
    c_indices = np.random.randint(0, 3, amount)
    colors = active_palette[c_indices]
    new_parts[:, 6] = colors[:, 0] + np.random.normal(0, 5, amount)  # hue
    new_parts[:, 7] = colors[:, 1]  # sat
    new_parts[:, 8] = colors[:, 2]  # bri
    
    particles = np.vstack([particles, new_parts])


def draw():
    global phase, particles, density
    W, H = SIZE
    frame = py5.frame_count
    phase += 0.015
    
    # Emitters at the bottom
    if frame % 2 == 0:
        # Three vents at the bottom
        emit_plume(W * 0.25, H * 0.88, 6)
        emit_plume(W * 0.50, H * 0.88, 8)
        emit_plume(W * 0.75, H * 0.88, 6)
        
    if py5.is_mouse_pressed:
        emit_plume(py5.mouse_x, py5.mouse_y, 15)
        
    # --- Update Density (Diffusion Step) ---
    density *= 0.955
    # Fast vectorized box blur via numpy roll
    density = (density * 3.0 + 
               np.roll(density, 1, axis=0) + 
               np.roll(density, -1, axis=0) + 
               np.roll(density, 1, axis=1) + 
               np.roll(density, -1, axis=1)) / 7.0

    # --- Update Particles ---
    if len(particles) > 0:
        # Calculate wave-based flow field for each particle
        flow_x, flow_y = get_flow(particles[:, 0], particles[:, 1], phase)
        
        # Buoyancy (upwards force)
        buoy_y = -0.05
        
        particles[:, 2] = particles[:, 2] * 0.975 + flow_x * 0.22
        particles[:, 3] = particles[:, 3] * 0.975 + flow_y * 0.22 + buoy_y
        
        particles[:, 0] += particles[:, 2]
        particles[:, 1] += particles[:, 3]
        particles[:, 4] += 1.0  # age
        
        # Inject particle life into density grid
        life_pct = 1.0 - (particles[:, 4] / particles[:, 5])
        life_pct = np.clip(life_pct, 0.0, 1.0)
        
        grid_x = (particles[:, 0] / W * GRID_W).astype(np.int32)
        grid_y = (particles[:, 1] / H * GRID_H).astype(np.int32)
        
        valid = (grid_x >= 0) & (grid_x < GRID_W) & (grid_y >= 0) & (grid_y < GRID_H)
        
        # Add to density
        np.add.at(density, (grid_y[valid], grid_x[valid]), life_pct[valid] * 0.045)
        density = np.clip(density, 0.0, 1.0)
        
        # Filter dead particles
        dead = (particles[:, 4] >= particles[:, 5]) | (particles[:, 1] < -50) | (particles[:, 0] < -50) | (particles[:, 0] > W + 50)
        particles = particles[~dead]

    # --- Rendering ---
    py5.background(220, 28, 6)  # Deep indigo-black void
    
    # Render density grid (Upscaled via custom billingual/blend box drawing)
    # Using low-alpha large rects to create a volumetric fog look
    scale_w = W / GRID_W
    scale_h = H / GRID_H
    
    py5.no_stroke()
    # Draw blurred density cells
    rows, cols = np.where(density > 0.005)
    for r, c in zip(rows, cols):
        val = density[r, c]
        hue = 200 + val * 45
        py5.fill(hue, 85, 20 + val * 70, val * 38)
        py5.rect(c * scale_w, r * scale_h, scale_w * 1.5, scale_h * 1.5)

    # Render particles with dual-pass glow halos
    for p in particles:
        px, py = p[0], p[1]
        age, lifespan = p[4], p[5]
        life = 1.0 - age / lifespan
        size = 3.0 + (1.0 - life) * 14.0
        hue, sat, bri = p[6], p[7], p[8]
        
        # Glow outer pass
        py5.fill(hue, sat * 0.8, bri * 0.8, life * 15.0)
        py5.circle(px, py, size * 2.8)
        
        # Core inner pass
        py5.fill(hue, sat, bri, life * 35.0)
        py5.circle(px, py, size * 1.2)

    # Vignette shadow framing
    for i in range(16):
        alpha = int(4 + i * 5)
        m = i * 22
        py5.fill(220, 30, 4, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)

    # HUD Readout
    py5.fill(200, 40, 85, 140)
    py5.text_size(20)
    py5.text(f"t={frame/FPS:.2f}s  particles: {len(particles)}  grid: {GRID_W}x{GRID_H}", 50, H - 50)

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
            print("[Render Cleanup] frames removed.")
        import os
        os._exit(0)


py5.run_sketch()
