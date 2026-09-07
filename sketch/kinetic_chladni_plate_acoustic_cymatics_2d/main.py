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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Grid for Circular Chladni Plate (16:9 aspect ratio)
Nx, Ny = 640, 360
x_coords = np.linspace(-1.0, 1.0, Nx, dtype=np.float32)
y_coords = np.linspace(- (Ny / Nx), (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

R_grid = np.sqrt(X_grid**2 + Y_grid**2) + 1e-5
Theta_grid = np.arctan2(Y_grid, X_grid)

# Circular Plate Domain: Radius R0 = 0.52 (fits well inside 16:9 frame)
R_PLATE = 0.52
plate_mask = np.where(R_grid <= R_PLATE, 1.0, 0.0).astype(np.float32)
brass_rim = np.exp(- ((R_grid - R_PLATE) / 0.008)**2).astype(np.float32)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Fluorescent Lycopodium Sand Particles
MAX_SAND = 950
sand_particles = []


class SandGrain:
    def __init__(self, px, py):
        self.px = px
        self.py = py
        self.vx = 0.0
        self.vy = 0.0
        self.prev_x = self.px
        self.prev_y = self.py
        self.life = random.uniform(60.0, 180.0)
        self.max_life = self.life
        self.size = random.uniform(1.8, 3.8)

    def update(self, grad_x, grad_y, local_vibration):
        self.prev_x = self.px
        self.prev_y = self.py

        # Acoustic radiation force drives sand away from antinodes towards nodes (W = 0)
        # Random acoustic micro-jostle proportional to local vibration amplitude
        jostle = local_vibration * 1.8
        jx = random.uniform(-jostle, jostle)
        jy = random.uniform(-jostle, jostle)

        # Gradient force: downhill towards nodal lines
        self.vx = self.vx * 0.88 - grad_x * 0.75 + jx
        self.vy = self.vy * 0.88 - grad_y * 0.75 + jy

        self.px += self.vx
        self.py += self.vy

        # Keep within plate boundary
        dx = self.px - py5.width / 2.0
        dy = self.py - py5.height / 2.0
        dist = np.sqrt(dx**2 + dy**2)
        max_dist_px = R_PLATE * (py5.width / 2.0)
        if dist > max_dist_px:
            self.life = 0

        self.life -= 1.0

    @property
    def is_dead(self):
        return self.life <= 0


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_chladni_modes(frame_idx):
    # Normalized time cycle over TOTAL_FRAMES
    t = (frame_idx / TOTAL_FRAMES) * 4.0 * np.pi

    # Smooth modal weight interpolation between integer azimuthal symmetries (m=2, 4, 6)
    # Guaranteed C^inf smooth across entire circle with zero branch cut artifacts
    w1 = np.cos(t * 0.5)**2
    w2 = np.sin(t * 0.5)**2 * np.cos(t * 0.8)**2
    w3 = np.sin(t * 0.5)**2 * np.sin(t * 0.8)**2

    r_norm = R_grid / R_PLATE
    # Mode 2 (2-fold symmetry)
    term2 = np.cos(2 * Theta_grid + 0.3 * np.sin(t * 0.7)) * np.cos(14.0 * r_norm) / np.sqrt(r_norm + 0.1)
    # Mode 4 (4-fold symmetry)
    term4 = np.cos(4 * Theta_grid - 0.4 * t) * np.cos(20.0 * r_norm - np.pi * 0.25) / np.sqrt(r_norm + 0.1)
    # Mode 6 (6-fold symmetry)
    term6 = np.cos(6 * Theta_grid + 0.2 * t) * np.cos(26.0 * r_norm - np.pi * 0.5) / np.sqrt(r_norm + 0.1)
    # Radial axisymmetric breathing mode
    term0 = np.cos(8.0 * r_norm) * np.cos(1.6 * t)

    # Vibration field W(x, y, t)
    W = (w1 * term2 + w2 * term4 + w3 * term6 + 0.35 * term0) * plate_mask

    # Kinetic energy antinodes: |W|^2
    kinetic_energy = W**2

    # Nodal line dust accumulation field (where W ~ 0)
    nodal_dust = np.exp(- (W / 0.038)**2) * plate_mask
    ambient_dust = np.exp(- (W / 0.14)**2) * plate_mask

    # Acoustic potential gradient for particle advection: grad(|W|^2)
    dW_dx = np.gradient(kinetic_energy, axis=1) * (Nx / 2.0)
    dW_dy = np.gradient(kinetic_energy, axis=0) * (Ny / (2.0 * Ny / Nx))

    return W, kinetic_energy, nodal_dust, ambient_dust, dW_dx, dW_dy


def render_chladni_plate(kinetic_energy, nodal_dust, ambient_dust):
    # Palette Architecture:
    # 1. Anodized Carbon-Composite Plate Base (60%): #020308
    r = np.full_like(X_grid, 2.0)
    g = np.full_like(X_grid, 3.0)
    b = np.full_like(X_grid, 8.0)

    # Antinode kinetic vibration energy (Royal Amethyst & Deep Indigo Glow)
    r += kinetic_energy * plate_mask * 90.0
    g += kinetic_energy * plate_mask * 15.0
    b += kinetic_energy * plate_mask * 185.0

    # Ambient acoustic dust dispersion (Deep Sapphire / Cyan Sheen)
    r += ambient_dust * 15.0
    g += ambient_dust * 95.0
    b += ambient_dust * 190.0

    # 2. Primary Nodal Line Sand Filaments (30%): Electric Cyan & Mint Emerald
    r += nodal_dust * 10.0
    g += nodal_dust * 245.0
    b += nodal_dust * 215.0

    # 3. High-Density Nodal Singularities (10% Accent): Incandescent Solar Gold & White
    peak_nodes = nodal_dust**2.2
    r += peak_nodes * 255.0
    g += peak_nodes * 240.0
    b += peak_nodes * 180.0

    # Circular Brass Rim
    r += brass_rim * 225.0
    g += brass_rim * 180.0
    b += brass_rim * 55.0

    # Assemble into py5 ARGB buffer (0=Alpha, 1=Red, 2=Green, 3=Blue)
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global sand_particles

    # 1. Physics update
    (W, kinetic_energy, nodal_dust,
     ambient_dust, dW_dx, dW_dy) = compute_chladni_modes(py5.frame_count)

    # 2. Render plate into pixel buffer
    render_chladni_plate(kinetic_energy, nodal_dust, ambient_dust)

    # 3. Blit plate field upscaled to 4K
    img = py5.create_image(Nx, Ny, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = pixel_buffer
        img.update_np_pixels()
    else:
        a = pixel_buffer[..., 0].astype(np.int32)
        r = pixel_buffer[..., 1].astype(np.int32)
        g = pixel_buffer[..., 2].astype(np.int32)
        b = pixel_buffer[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()

    py5.image(img, 0, 0, py5.width, py5.height)

    # 4. Spawn new sand grains within circular plate
    center_px = py5.width / 2.0
    center_py = py5.height / 2.0
    max_radius_px = R_PLATE * (py5.width / 2.0)

    if len(sand_particles) < MAX_SAND:
        spawn_n = min(25, MAX_SAND - len(sand_particles))
        for _ in range(spawn_n):
            angle = random.uniform(0.0, 2.0 * np.pi)
            rad = np.sqrt(random.uniform(0.0, 1.0)) * (max_radius_px * 0.96)
            spx = center_px + np.cos(angle) * rad
            spy = center_py + np.sin(angle) * rad
            sand_particles.append(SandGrain(spx, spy))

    # 5. Render Fluorescent Sand Grains on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_sand = []
    for s in sand_particles:
        gx_idx = int(np.clip((s.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy_idx = int(np.clip((s.py / py5.height) * (Ny - 1), 0, Ny - 1))

        grad_x = dW_dx[gy_idx, gx_idx]
        grad_y = dW_dy[gy_idx, gx_idx]
        local_vib = kinetic_energy[gy_idx, gx_idx]

        s.update(grad_x, grad_y, local_vib)
        if not s.is_dead:
            active_sand.append(s)
            life_norm = s.life / s.max_life
            alpha = int(life_norm * 240)

            # Crystalline sand grain luminescence (Mint Emerald to Pure White)
            cr = int(180 + life_norm * 75)
            cg = int(245 + life_norm * 10)
            cb = int(210 + life_norm * 45)

            # Glow aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.35))
            py5.circle(s.px, s.py, s.size * 2.6)

            # Core sand crystal
            py5.fill(255, 255, 245, alpha)
            py5.circle(s.px, s.py, s.size * 1.0)

            # Motion wake
            py5.stroke(cr, cg, cb, int(alpha * 0.45))
            py5.stroke_weight(1.2)
            py5.line(s.px, s.py, s.prev_x, s.prev_y)

    sand_particles = active_sand
    py5.blend_mode(py5.BLEND)

    # Fail-safe blank screen check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Sand: {len(sand_particles)}")

    # Finalize render
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        mp4_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
        output_mp4 = SKETCH_DIR / "output.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", str(mp4_path),
        ], check=True)
        shutil.copyfile(mp4_path, output_mp4)

        # Save preview snapshot from midpoint
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


def draw():
    try:
        draw_frame()
    except Exception:
        import traceback
        traceback.print_exc()
        import os
        os._exit(1)


py5.run_sketch()
