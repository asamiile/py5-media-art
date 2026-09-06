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

# Spatial Grid for 12-fold Faraday Quasicrystal (16:9)
Nx, Ny = 640, 360
x_coords = np.linspace(-9.0, 9.0, Nx, dtype=np.float32)
y_coords = np.linspace(-9.0 * (Ny / Nx), 9.0 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# 12-fold Quasicrystal wavevectors
N_WAVES = 12
k1 = 2.4
k2 = 4.63  # 2 * k1 * cos(pi/12) for resonant triad coupling
angles = np.linspace(0, 2.0 * np.pi, N_WAVES, endpoint=False)
cos_ang1 = np.cos(angles).astype(np.float32)
sin_ang1 = np.sin(angles).astype(np.float32)
cos_ang2 = np.cos(angles + np.pi / 12.0).astype(np.float32)
sin_ang2 = np.sin(angles + np.pi / 12.0).astype(np.float32)

# Dual Studio Directional Lighting:
# Light 1 (Key): Upper-left, vivid Cyan
Lx1, Ly1, Lz1 = -0.6, -0.6, 0.52
L_mag1 = np.sqrt(Lx1**2 + Ly1**2 + Lz1**2)
Lx1, Ly1, Lz1 = Lx1 / L_mag1, Ly1 / L_mag1, Lz1 / L_mag1
Hx1, Hy1, Hz1 = Lx1, Ly1, Lz1 + 1.0
H_mag1 = np.sqrt(Hx1**2 + Hy1**2 + Hz1**2)
Hx1, Hy1, Hz1 = Hx1 / H_mag1, Hy1 / H_mag1, Hz1 / H_mag1

# Light 2 (Rim): Lower-right, Royal Amethyst / Magenta
Lx2, Ly2, Lz2 = 0.6, 0.6, 0.52
L_mag2 = np.sqrt(Lx2**2 + Ly2**2 + Lz2**2)
Lx2, Ly2, Lz2 = Lx2 / L_mag2, Ly2 / L_mag2, Lz2 / L_mag2
Hx2, Hy2, Hz2 = Lx2, Ly2, Lz2 + 1.0
H_mag2 = np.sqrt(Hx2**2 + Hy2**2 + Hz2**2)
Hx2, Hy2, Hz2 = Hx2 / H_mag2, Hy2 / H_mag2, Hz2 / H_mag2

# Bouncing Pilot-Wave Surface Micro-Droplets
MAX_DROPLETS = 420
droplets = []


class BouncingDroplet:
    def __init__(self, px, py):
        self.px = px
        self.py = py
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(-1.2, 1.2)
        self.prev_x = self.px
        self.prev_y = self.py
        self.life = random.uniform(50.0, 150.0)
        self.max_life = self.life
        self.size = random.uniform(2.2, 4.5)
        self.bounce_phase = random.uniform(0.0, 2.0 * np.pi)

    def update(self, grad_x, grad_y):
        self.prev_x = self.px
        self.prev_y = self.py
        self.bounce_phase += 0.22

        # Droplets surf downhill toward wave troughs
        self.vx = self.vx * 0.92 - grad_x * 0.45 + random.uniform(-0.15, 0.15)
        self.vy = self.vy * 0.92 - grad_y * 0.45 + random.uniform(-0.15, 0.15)

        self.px += self.vx
        self.py += self.vy
        self.life -= 1.0

    @property
    def is_dead(self):
        return (self.life <= 0 or self.px < -30 or self.px > py5.width + 30 or
                self.py < -30 or self.py > py5.height + 30)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_faraday_quasicrystal(frame_idx):
    # Normalized time cycle over TOTAL_FRAMES
    t = (frame_idx / TOTAL_FRAMES) * 6.0 * np.pi

    zeta1 = np.zeros((Ny, Nx), dtype=np.float32)
    zeta2 = np.zeros((Ny, Nx), dtype=np.float32)

    for i in range(N_WAVES):
        kx1, ky1 = k1 * cos_ang1[i], k1 * sin_ang1[i]
        phase1 = kx1 * X_grid + ky1 * Y_grid + 0.25 * np.sin(0.35 * t + i * 0.8)
        zeta1 += np.cos(phase1)

        kx2, ky2 = k2 * cos_ang2[i], k2 * sin_ang2[i]
        phase2 = kx2 * X_grid + ky2 * Y_grid - 0.2 * t + 0.5 * np.cos(0.2 * t + i)
        zeta2 += np.cos(phase2)

    # Subharmonic two-frequency parametric resonance
    omega1 = 2.0 * np.pi * 0.35
    omega2 = 2.0 * np.pi * 0.70
    zeta = (np.cos(omega1 * t) * (zeta1 / N_WAVES) + 0.55 * np.cos(omega2 * t + 0.7) * (zeta2 / N_WAVES))

    # Surface normal and curvature calculation
    dzeta_dx = np.gradient(zeta, axis=1) * (Nx / 18.0)
    dzeta_dy = np.gradient(zeta, axis=0) * (Ny / (18.0 * Ny / Nx))

    norm_mag = np.sqrt(dzeta_dx**2 + dzeta_dy**2 + 1.0)
    Nx_s = -dzeta_dx / norm_mag
    Ny_s = -dzeta_dy / norm_mag
    Nz_s = 1.0 / norm_mag

    # Dual-light Blinn-Phong specular and diffuse illumination
    NdotL1 = np.maximum(0.0, Nx_s * Lx1 + Ny_s * Ly1 + Nz_s * Lz1)
    NdotH1 = np.maximum(0.0, Nx_s * Hx1 + Ny_s * Hy1 + Nz_s * Hz1)
    specular1 = NdotH1**36.0

    NdotL2 = np.maximum(0.0, Nx_s * Lx2 + Ny_s * Ly2 + Nz_s * Lz2)
    NdotH2 = np.maximum(0.0, Nx_s * Hx2 + Ny_s * Hy2 + Nz_s * Hz2)
    specular2 = NdotH2**28.0

    curv = np.maximum(0.0, - (np.gradient(Nx_s, axis=1) + np.gradient(Ny_s, axis=0)))

    return zeta, dzeta_dx, dzeta_dy, NdotL1, specular1, NdotL2, specular2, curv


def render_faraday_surface(zeta, NdotL1, specular1, NdotL2, specular2, curv):
    # Palette Architecture:
    # 1. Deep Liquid Obsidian Mirror (60%): #02040c
    r = np.full_like(X_grid, 2.0)
    g = np.full_like(X_grid, 4.0)
    b = np.full_like(X_grid, 14.0)

    # Ambient liquid elevation (Indigo / Cobalt)
    elev_pos = np.maximum(0.0, zeta)
    r += elev_pos * 10.0
    g += elev_pos * 35.0
    b += elev_pos * 95.0

    # 2. 12-Fold Quasicrystal Interference Ribs (30%): Electric Cyan & Royal Amethyst
    r += NdotL1 * 12.0 + specular1 * 190.0
    g += NdotL1 * 175.0 + specular1 * 245.0
    b += NdotL1 * 230.0 + specular1 * 255.0

    r += NdotL2 * 155.0 + specular2 * 235.0
    g += NdotL2 * 20.0 + specular2 * 90.0
    b += NdotL2 * 205.0 + specular2 * 255.0

    # 3. Quasicrystal Crest Singularities (10% Accent): Incandescent Solar White & Amber
    crest_spikes = (curv / (np.max(curv) + 1e-4))**2.5
    r += crest_spikes * 255.0
    g += crest_spikes * 220.0
    b += crest_spikes * 110.0

    peak_spec = (specular1 * specular2)**0.5 + specular1**2.5
    r += peak_spec * 255.0
    g += peak_spec * 255.0
    b += peak_spec * 255.0

    # Assemble into py5 ARGB buffer (0=Alpha, 1=Red, 2=Green, 3=Blue)
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global droplets

    # 1. Physics update
    (zeta, dzeta_dx, dzeta_dy,
     NdotL1, specular1, NdotL2, specular2, curv) = compute_faraday_quasicrystal(py5.frame_count)

    # 2. Render surface into pixel buffer
    render_faraday_surface(zeta, NdotL1, specular1, NdotL2, specular2, curv)

    # 3. Blit surface field upscaled to 4K
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

    # 4. Spawn bouncing surface micro-droplets
    if len(droplets) < MAX_DROPLETS:
        spawn_n = min(20, MAX_DROPLETS - len(droplets))
        for _ in range(spawn_n):
            spx = random.uniform(50, py5.width - 50)
            spy = random.uniform(50, py5.height - 50)
            droplets.append(BouncingDroplet(spx, spy))

    # 5. Render Bouncing Pilot-Wave Droplets on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_droplets = []
    for d in droplets:
        # Sample wave surface gradient at droplet location
        gx_idx = int(np.clip((d.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy_idx = int(np.clip((d.py / py5.height) * (Ny - 1), 0, Ny - 1))
        grad_x = dzeta_dx[gy_idx, gx_idx]
        grad_y = dzeta_dy[gy_idx, gx_idx]

        d.update(grad_x, grad_y)
        if not d.is_dead:
            active_droplets.append(d)
            life_norm = d.life / d.max_life
            alpha = int(life_norm * 230)
            bounce = 0.5 + 0.5 * np.sin(d.bounce_phase)
            cur_size = d.size * (1.0 + 0.6 * bounce)

            # Luminous droplet color (Electric Cyan to Solar White)
            cr = int(140 + bounce * 115)
            cg = int(225 + bounce * 30)
            cb = int(255)

            # Glow aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.35))
            py5.circle(d.px, d.py, cur_size * 2.6)

            # Core droplet bead
            py5.fill(255, 255, 250, alpha)
            py5.circle(d.px, d.py, cur_size * 1.0)

            # Hydrodynamic wake streak
            py5.stroke(cr, cg, cb, int(alpha * 0.45))
            py5.stroke_weight(1.3)
            py5.line(d.px, d.py, d.prev_x, d.prev_y)

    droplets = active_droplets
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Droplets: {len(droplets)}")

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
