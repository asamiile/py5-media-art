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

# Spatial Grid (16:9 aspect ratio)
Nx, Ny = 640, 360
x_coords = np.linspace(-4.5, 4.5, Nx, dtype=np.float32)
y_coords = np.linspace(-4.5 * (Ny / Nx), 4.5 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# RGBA pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Trapped Fluorescent Colloidal Nanoparticles
MAX_COLLOIDS = 380
colloids = []


class TrappedColloid:
    def __init__(self, px, py, target_skyrmion_idx):
        self.px = px
        self.py = py
        self.vx = 0.0
        self.vy = 0.0
        self.skyrmion_idx = target_skyrmion_idx
        self.orbit_angle = random.uniform(0.0, 2.0 * np.pi)
        self.orbit_radius = random.uniform(0.48, 0.78)
        self.orbit_speed = random.uniform(0.035, 0.075) * random.choice([-1.0, 1.0])
        self.life = random.uniform(50.0, 140.0)
        self.max_life = self.life
        self.size = random.uniform(2.0, 4.2)

    def update(self, s_center):
        cx, cy = s_center
        # Convert skyrmion center to 4K screen coordinates
        sc_px = ((cx - (-4.5)) / 9.0) * py5.width
        sc_py = ((cy - (-4.5 * (Ny / Nx))) / (9.0 * (Ny / Nx))) * py5.height

        self.orbit_angle += self.orbit_speed
        rad_px = self.orbit_radius * (py5.width / 9.0)
        target_x = sc_px + np.cos(self.orbit_angle) * rad_px
        target_y = sc_py + np.sin(self.orbit_angle) * rad_px

        # Elastic pulling towards defect ring
        self.vx = self.vx * 0.82 + (target_x - self.px) * 0.18
        self.vy = self.vy * 0.82 + (target_y - self.py) * 0.18

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


def compute_chiral_skyrmions(frame_idx):
    # Normalized time cycle across 18s (2 full choreography loops)
    t = (frame_idx / TOTAL_FRAMES) * 4.0 * np.pi

    # 8 Chiral Liquid Crystal Skyrmions with topological Skyrmion Hall drift
    # Positions driven by simulated in-plane AC electric field
    centers = [
        (-2.3 + 0.55 * np.cos(t * 1.15), -1.0 + 0.42 * np.sin(t * 1.15), 1, 1.0, 0.68),
        (-0.75 + 0.45 * np.cos(-t * 0.95 + 1.2), -1.25 + 0.52 * np.sin(-t * 0.95 + 1.2), -1, -1.0, 0.72),
        (0.85 + 0.62 * np.cos(t * 1.05 + 2.3), -0.95 + 0.42 * np.sin(t * 1.05 + 2.3), 1, 1.0, 0.66),
        (2.35 + 0.52 * np.cos(-t * 1.25 + 3.4), -1.15 + 0.50 * np.sin(-t * 1.25 + 3.4), -1, -1.0, 0.70),
        (-2.15 + 0.50 * np.cos(-t * 1.05 + 4.2), 1.12 + 0.42 * np.sin(-t * 1.05 + 4.2), -1, -1.0, 0.70),
        (-0.65 + 0.62 * np.cos(t * 1.22 + 0.6), 1.22 + 0.52 * np.sin(t * 1.22 + 0.6), 1, 1.0, 0.68),
        (0.92 + 0.45 * np.cos(-t * 1.12 + 1.9), 1.05 + 0.42 * np.sin(-t * 1.12 + 1.9), -1, -1.0, 0.72),
        (2.45 + 0.52 * np.cos(t * 0.95 + 3.0), 1.22 + 0.52 * np.sin(t * 0.95 + 3.0), 1, 1.0, 0.66)
    ]

    nx = np.zeros((Ny, Nx), dtype=np.float32)
    ny = np.zeros((Ny, Nx), dtype=np.float32)
    nz = np.ones((Ny, Nx), dtype=np.float32)

    center_coords = []
    for cx, cy, charge, chir, R0 in centers:
        center_coords.append((cx, cy))
        dx = X_grid - cx
        dy = Y_grid - cy
        r2 = dx**2 + dy**2
        r = np.sqrt(r2) + 1e-4
        alpha = np.arctan2(dy, dx)

        # 2pi hedgehog / chiral vortex director twist
        theta_prof = np.pi / (1.0 + (r / R0)**2.5)
        phi_prof = charge * alpha + chir * (np.pi * 0.45)
        weight = np.exp(- (r / (2.3 * R0))**4)

        nx += np.sin(theta_prof) * np.cos(phi_prof) * weight
        ny += np.sin(theta_prof) * np.sin(phi_prof) * weight
        nz += (np.cos(theta_prof) - 1.0) * weight

    # Normalize director field |n| = 1
    norm = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-4
    nx /= norm
    ny /= norm
    nz /= norm

    # 1. Crossed Polarizers POM transmission: Maltese Cross isogyres (zeros of nx * ny)
    isogyre_extinction = 1.0 - np.exp(- (nx * ny * 4.5)**2)

    # 2. Retardation delta = (1 - nz^2) * 2.85 (Multi-order Michel-Levy interference colors)
    retardation = (1.0 - nz**2) * 2.85
    I_r = np.sin(retardation * np.pi * 0.82)**2 * (1.0 - nz**2)
    I_g = np.sin(retardation * np.pi * 1.02)**2 * (1.0 - nz**2)
    I_b = np.sin(retardation * np.pi * 1.28)**2 * (1.0 - nz**2)

    # 3. Topological charge density Q = (1/4pi) n . (dn/dx x dn/dy)
    dnx_dx = (np.roll(nx, -1, axis=1) - np.roll(nx, 1, axis=1)) * 0.5
    dnx_dy = (np.roll(nx, -1, axis=0) - np.roll(nx, 1, axis=0)) * 0.5
    dny_dx = (np.roll(ny, -1, axis=1) - np.roll(ny, 1, axis=1)) * 0.5
    dny_dy = (np.roll(ny, -1, axis=0) - np.roll(ny, 1, axis=0)) * 0.5
    dnz_dx = (np.roll(nz, -1, axis=1) - np.roll(nz, 1, axis=1)) * 0.5
    dnz_dy = (np.roll(nz, -1, axis=0) - np.roll(nz, 1, axis=0)) * 0.5

    cross_x = dny_dx * dnz_dy - dnz_dx * dny_dy
    cross_y = dnz_dx * dnx_dy - dnx_dx * dnz_dy
    cross_z = dnx_dx * dny_dy - dny_dx * dnx_dy
    Q_dens = np.abs(nx * cross_x + ny * cross_y + nz * cross_z) * 12.0

    return nx, ny, nz, isogyre_extinction, I_r, I_g, I_b, Q_dens, center_coords


def render_pom_field(nx, ny, nz, isogyre_extinction, I_r, I_g, I_b, Q_dens, center_coords):
    global pixel_buffer

    # 1. Base Homeotropic Extinction (60% background/matrix): #020309
    r = np.full_like(X_grid, 2.0)
    g = np.full_like(X_grid, 3.0)
    b = np.full_like(X_grid, 9.0)

    # 2. Birefringent Michel-Levy Interference Colors (30% secondary): Emerald, Peacock Cyan, Amethyst
    r += (I_r * 235.0 + 15.0) * isogyre_extinction
    g += (I_g * 200.0 + 35.0) * isogyre_extinction
    b += (I_b * 248.0 + 55.0) * isogyre_extinction

    # 3. Topological Skyrmion Core Halos (10% accent): Incandescent Solar Amber & White
    halo = np.clip(Q_dens * 1.8, 0.0, 1.0)**1.4
    r += halo * 255.0
    g += halo * 215.0
    b += halo * 45.0

    # Luminous core boundary ring around homeotropic point
    for cx, cy in center_coords:
        d = np.sqrt((X_grid - cx)**2 + (Y_grid - cy)**2)
        core_ring = np.exp(- (d - 0.05)**2 / 0.007)
        r += core_ring * 255.0
        g += core_ring * 240.0
        b += core_ring * 180.0

    # Assemble into py5 ARGB buffer (0=Alpha, 1=Red, 2=Green, 3=Blue)
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global colloids

    # 1. Physics update
    nx, ny, nz, isogyre_extinction, I_r, I_g, I_b, Q_dens, center_coords = compute_chiral_skyrmions(py5.frame_count)

    # 2. Render POM field into pixel buffer
    render_pom_field(nx, ny, nz, isogyre_extinction, I_r, I_g, I_b, Q_dens, center_coords)

    # 3. Blit POM image upscaled to 4K
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

    # 4. Spawn replacement colloidal nanoparticles around skyrmions
    if len(colloids) < MAX_COLLOIDS:
        spawn_count = min(20, MAX_COLLOIDS - len(colloids))
        for _ in range(spawn_count):
            s_idx = random.randint(0, len(center_coords) - 1)
            cx, cy = center_coords[s_idx]
            angle = random.uniform(0.0, 2.0 * np.pi)
            rad = random.uniform(0.45, 0.80)
            cpx = ((cx + np.cos(angle) * rad - (-4.5)) / 9.0) * py5.width
            cpy = ((cy + np.sin(angle) * rad - (-4.5 * (Ny / Nx))) / (9.0 * (Ny / Nx))) * py5.height
            colloids.append(TrappedColloid(cpx, cpy, s_idx))

    # 5. Render Fluorescent Colloids on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_colloids = []
    for c in colloids:
        s_target = center_coords[c.skyrmion_idx % len(center_coords)]
        c.update(s_target)
        if not c.is_dead:
            active_colloids.append(c)
            life_norm = c.life / c.max_life
            alpha = int(life_norm * 240)

            # Fluorescent amber to diamond white
            cr = 255
            cg = int(195 + life_norm * 55)
            cb = int(60 + life_norm * 180)

            # Outer glow aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.35))
            py5.circle(c.px, c.py, c.size * 2.8)

            # Radiant bead nucleus
            py5.fill(cr, cg, cb, alpha)
            py5.circle(c.px, c.py, c.size * 1.1)

            # Trajectory streak
            py5.stroke(cr, cg, cb, int(alpha * 0.45))
            py5.stroke_weight(1.2)
            py5.line(c.px, c.py, c.px - c.vx * 2.0, c.py - c.vy * 2.0)

    colloids = active_colloids
    py5.blend_mode(py5.BLEND)

    # Fail-safe check
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Colloids: {len(colloids)}")

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
