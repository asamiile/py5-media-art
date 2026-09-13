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

# Spatial Simulation Grid (16:9 aspect ratio, coronal plane)
Nx, Ny = 640, 360
x_coords = np.linspace(-3.6, 3.6, Nx, dtype=np.float32)
# Row 0 is the coronal apex (top of screen), Row Ny-1 is the photosphere limb (bottom of screen)
y_coords = np.linspace(3.80, -0.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[0] - y_coords[1])  # positive step for Cartesian gradient

# Bipolar Magnetic Footpoint Locations at the Photospheric Limb (Y ~ 0)
footpoint_d = 1.85  # Left footpoint at (-1.85, 0), Right at (+1.85, 0)

# Analytical Bipolar Dipolar Magnetic Flux Function: psi(X, Y)
# In the upper coronal half-plane (Y > 0), psi drops from pi at the surface to 0 at infinity
Y_safe = np.maximum(0.01, Y_grid)
theta_left = np.arctan2(Y_safe, X_grid + footpoint_d)
theta_right = np.arctan2(Y_safe, X_grid - footpoint_d)
# Subtended angle between rays from both footpoints
psi_field = np.clip(theta_right - theta_left, 0.0, np.pi).astype(np.float32)

# Magnetic Field Vectors Tangential to Contours of psi:
# B = (-d(psi)/dY, d(psi)/dX) so that field points clockwise over the arch from left to right
dpsi_dy, dpsi_dx = np.gradient(psi_field, dy, dx)
Bx_field = -dpsi_dy
By_field = dpsi_dx
B_mag = np.sqrt(Bx_field**2 + By_field**2) + 1e-4
Bx_norm = Bx_field / B_mag
By_norm = By_field / B_mag

# Normalized Arc-Length coordinate along magnetic loops s in [0, 1]
# s ~ 0 at left footpoint, s = 0.5 at coronal apex (X=0), s ~ 1 at right footpoint
s_coord = np.clip((np.arctan2(X_grid, Y_safe) / (np.pi / 2.0)) * 0.5 + 0.5, 0.0, 1.0).astype(np.float32)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Particles: Confined Solar Plasma Ions & Relativistic Nanoflare Electrons
MAX_PARTICLES = 1600
particles = []


class CoronalPlasmaParticle:
    def __init__(self, px, py, is_electron=False, speed_mult=1.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.is_electron = is_electron
        self.speed_mult = speed_mult

        if is_electron:
            # Relativistic electron accelerated by reconnecting current sheets
            self.life = random.uniform(50.0, 130.0)
            self.radius = random.uniform(1.2, 2.2)
        else:
            # Thermal chromospheric plasma ion spiraling along the coronal loop
            self.life = random.uniform(100.0, 260.0)
            self.radius = random.uniform(1.6, 3.4)

        self.max_life = self.life
        self.gyro_phase = random.uniform(0.0, 2.0 * np.pi)
        self.gyro_radius = random.uniform(2.5, 5.5) if is_electron else random.uniform(1.0, 3.0)

    def update(self, bx_screen, by_screen, alfven_boost, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        # High-frequency gyro-motion around magnetic field vector
        self.gyro_phase += 0.48 * dt
        gx = -by_screen * np.sin(self.gyro_phase) * self.gyro_radius
        gy = bx_screen * np.sin(self.gyro_phase) * self.gyro_radius

        # Field-aligned drift velocity along the coronal loop
        base_speed = 3.8 * self.speed_mult + alfven_boost * 3.2
        drift_speed = base_speed * (1.55 if self.is_electron else 1.0)
        self.px += (bx_screen * drift_speed + gx * 0.35) * dt
        self.py += (by_screen * drift_speed + gy * 0.35) * dt

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 100
            or self.px < -100
            or self.py > py5.height + 100
            or self.py < -100
        )


def compute_coronal_mhd_fields(frame):
    """
    Computes 2D magnetohydrodynamic (MHD) fields of the coronal loop:
    - Multi-strand braided magnetic flux ropes (Parker model)
    - Counter-propagating torsional Elsässer Alfvén waves
    - Magnetic reconnection current sheets and incandescent nanoflares
    - Photospheric convective granulation and spicule eruptions
    """
    t = frame / 60.0  # seconds

    # 1. Counter-Propagating Elsässer Alfvén Waves: z^+ (left-to-right) and z^- (right-to-left)
    vA = 2.5  # Alfvén propagation speed
    wave_k1 = 2.0 * np.pi
    wave_k2 = 4.0 * np.pi
    wave_k3 = 6.0 * np.pi

    # z^+ traveling along arc-length s from 0 to 1
    z_plus = (
        0.55 * np.cos(wave_k1 * s_coord - vA * t)
        + 0.35 * np.cos(wave_k2 * s_coord - 1.7 * vA * t + 0.8)
        + 0.20 * np.sin(wave_k3 * s_coord - 2.4 * vA * t - 1.2)
    )

    # z^- traveling in opposite direction from 1 to 0
    z_minus = (
        0.55 * np.cos(wave_k1 * (1.0 - s_coord) - vA * t + 1.4)
        + 0.35 * np.cos(wave_k2 * (1.0 - s_coord) - 1.7 * vA * t - 0.5)
        + 0.20 * np.sin(wave_k3 * (1.0 - s_coord) - 2.4 * vA * t + 2.1)
    )

    # Non-linear Elsässer cross-interaction creating localized wave collision packets
    alfven_interaction = np.abs(z_plus * z_minus)
    alfven_total = (z_plus + z_minus) * 0.5

    # 2. Multi-Strand Braided Magnetic Flux Ropes
    strand_sum = np.zeros_like(psi_field)
    current_sheet_sum = np.zeros_like(psi_field)

    strand_centers = np.linspace(0.82, 2.28, 16)
    for idx, psi_c in enumerate(strand_centers):
        # Braiding twist: each strand undulates with unique frequency and phase
        strand_twist = 0.036 * np.sin(2.2 * t + idx * 0.82) * np.sin(s_coord * np.pi)
        psi_target = psi_c + strand_twist
        dist_psi = np.abs(psi_field - psi_target)

        # Luminous strand profile
        strand_profile = np.exp(- (dist_psi**2) / (2.0 * (0.032**2)))
        strand_sum += strand_profile

        # Current sheet at strand interfaces where magnetic shear peaks
        shear_edge = np.exp(- ((dist_psi - 0.026)**2) / (2.0 * (0.016**2)))
        current_sheet_sum += shear_edge * (1.0 + 0.7 * np.cos(4.0 * s_coord + 2.2 * t))

    # Fine filamentary texture along field lines
    fine_strands = 0.35 * np.cos(48.0 * psi_field + 1.8 * t) * np.sin(np.pi * s_coord)
    strand_sum = np.maximum(0.0, strand_sum + fine_strands)

    # Smooth Coronal Loop Spatial Envelope
    loop_envelope = np.exp(- ((Y_grid - 1.65)**2) / 3.2) * np.exp(- (X_grid**2) / 7.2)
    # Mask out region below photosphere limb
    loop_envelope *= np.where(Y_grid > 0.02, 1.0, np.exp(- ((Y_grid - 0.02)**2) / 0.025))

    # 3. Incandescent Parker Nanoflare Reconnections
    # Triggered at wave collision zones where current sheets exceed critical threshold
    nanoflare_trigger = (current_sheet_sum * 0.42 + alfven_interaction * 1.7) * loop_envelope
    nanoflares = np.maximum(0.0, nanoflare_trigger - 0.92)**2.2

    # 4. Photospheric Limb & Convective Granulation at the Base (Y <= 0.35)
    granule_freq1 = 8.5
    granule_freq2 = 18.0
    granules = (
        0.65 * np.cos(granule_freq1 * X_grid - 0.7 * t)
        + 0.35 * np.cos(granule_freq2 * X_grid + 1.3 * t)
    )
    photosphere_limb = np.exp(- ((Y_grid - 0.0)**2) / (2.0 * (0.15**2))) * (1.0 + 0.3 * granules)

    # Upward spicules: narrow chromospheric plasma jets erupting near footpoints
    spicule_dist_l = np.abs(X_grid + footpoint_d)
    spicule_dist_r = np.abs(X_grid - footpoint_d)
    spicules = (
        np.exp(- (spicule_dist_l**2) / 0.14) + np.exp(- (spicule_dist_r**2) / 0.14)
    ) * np.exp(- ((Y_grid - 0.15)**2) / 0.45) * (1.0 + 0.45 * np.sin(16.0 * Y_grid - 4.2 * t))

    # 5. Field-aligned Alfven velocity boost for particles
    v_alfven_boost = (alfven_interaction * 1.3 + nanoflares * 2.2) * loop_envelope

    return (
        strand_sum,
        alfven_total,
        alfven_interaction,
        nanoflares,
        photosphere_limb,
        spicules,
        loop_envelope,
        v_alfven_boost,
    )


def render_coronal_canvas(
    strand_sum,
    alfven_total,
    alfven_interaction,
    nanoflares,
    photosphere_limb,
    spicules,
    loop_envelope,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Solar Corona Obsidian Void & Deep Chromospheric Indigo (#020108, #0a0618, #140924)
    - 30% Braided Magnetic Flux Ropes Electric Amber, Solar Gold & Coronal Cyan (#f59e0b, #fbbf24, #06b6d4)
    - 10% Incandescent Nanoflare Reconnection Diamond-White & Extreme UV Violet (#ffffff, #fef08a, #e879f9)
    """
    # 1. Background 60%: Solar Corona Obsidian Void & Chromospheric Gradient
    r_bg = 2.0 + np.maximum(0.0, Y_grid) * 0.6
    g_bg = 1.0 + np.maximum(0.0, Y_grid) * 0.4
    b_bg = 7.0 + np.maximum(0.0, Y_grid) * 3.6

    # Photospheric limb base glow (bottom of screen)
    r_limb = photosphere_limb * 145.0 + spicules * 95.0
    g_limb = photosphere_limb * 68.0 + spicules * 48.0
    b_limb = photosphere_limb * 28.0 + spicules * 88.0

    # 2. Secondary 30%: Braided Magnetic Flux Ropes Solar Gold & Coronal Cyan
    strand_intensity = strand_sum * loop_envelope * (1.0 + 0.42 * alfven_total)

    # Dual-tone magnetic ropes: Solar Amber/Gold core (#f59e0b, #fbbf24) with Coronal Cyan sheath (#06b6d4)
    strand_gold = np.clip(strand_intensity * 0.82, 0.0, 3.5)
    strand_cyan = np.clip(strand_intensity * 0.32 + alfven_interaction * loop_envelope * 0.85, 0.0, 2.5)

    r_rope = strand_gold * 245.0 + strand_cyan * 6.0
    g_rope = strand_gold * 175.0 + strand_cyan * 182.0
    b_rope = strand_gold * 25.0 + strand_cyan * 212.0

    # 3. Accent 10%: Incandescent Nanoflare Reconnection Diamond-White & Extreme UV Violet
    nano_intensity = nanoflares * 3.8
    r_nano = nano_intensity * 255.0
    g_nano = nano_intensity * 245.0
    b_nano = nano_intensity * 255.0

    # EUV Violet fluorescence around reconnection zones
    euv_intensity = np.maximum(0.0, alfven_interaction - 0.42) * loop_envelope * 2.0
    r_euv = euv_intensity * 210.0
    g_euv = euv_intensity * 80.0
    b_euv = euv_intensity * 250.0

    # Final Additive Composite
    r_final = np.clip(r_bg + r_limb + r_rope + r_nano + r_euv, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_bg + g_limb + g_rope + g_nano + g_euv, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_bg + b_limb + b_rope + b_nano + b_euv, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute coronal MHD fields
    (
        strand_sum,
        alfven_total,
        alfven_interaction,
        nanoflares,
        photosphere_limb,
        spicules,
        loop_envelope,
        v_alfven_boost,
    ) = compute_coronal_mhd_fields(py5.frame_count)

    # 2. Render pixel buffer
    render_coronal_canvas(
        strand_sum,
        alfven_total,
        alfven_interaction,
        nanoflares,
        photosphere_limb,
        spicules,
        loop_envelope,
    )

    # 3. Blit upscaled pixel buffer to 4K canvas
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

    # 4. Lagrangian Coronal Particle Spawning
    # Map physical coordinates X in [-3.6, 3.6] and Y in [3.80, -0.25] to screen pixels
    x_min, x_max = x_coords[0], x_coords[-1]
    y_top, y_bottom = y_coords[0], y_coords[-1]

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(55, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            # Choose footpoint: left or right
            is_left = random.random() < 0.5
            x_root = -footpoint_d if is_left else footpoint_d
            x_spawn = x_root + random.gauss(0.0, 0.16)
            y_spawn = random.uniform(0.02, 0.28)

            # Map to screen pixels: top is Y = y_top, bottom is Y = y_bottom
            px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
            py_screen = ((y_top - y_spawn) / (y_top - y_bottom)) * py5.height

            # Direction along magnetic field: left footpoint travels forward (+1.0), right travels backward (-1.0)
            direction = 1.0 if is_left else -1.0
            is_electron = roll < 0.28
            particles.append(CoronalPlasmaParticle(px, py_screen, is_electron=is_electron, speed_mult=direction))

    # 5. Advect and Render Lagrangian Coronal Particles
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        # Screen position to simulation grid indices
        norm_x = p.px / py5.width
        norm_y = p.py / py5.height  # 0 at top, 1 at bottom

        gx = int(np.clip(norm_x * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip(norm_y * (Ny - 1), 0, Ny - 1))

        # Magnetic field vector: Bx_norm points in +X (right), By_norm points in +Y (Cartesian up)
        bx = float(Bx_norm[gy, gx])
        by = float(By_norm[gy, gx])

        # On screen: +X is right (bx), but +Y is DOWNwards on screen (-by)
        bx_screen = bx
        by_screen = -by

        alfven_boost = float(v_alfven_boost[gy, gx])
        p.update(bx_screen, by_screen, alfven_boost)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.is_electron:
                # Reconnection electron: Blinding white-gold & EUV violet (#ffffff, #fef08a, #e879f9)
                cr, cg, cb = 255, 245, 180
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.42))
                py5.circle(p.px, p.py, p.radius * 3.6)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(cr, cg, cb, int(alpha * 0.88))
                py5.stroke_weight(1.8)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            else:
                # Coronal plasma ion: Solar amber & radiant gold (#f59e0b, #fbbf24)
                cr, cg, cb = 245, 175, 45
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 3.0)
                py5.fill(255, 235, 190, alpha)
                py5.circle(p.px, p.py, p.radius * 0.85)
                py5.stroke(cr, cg, cb, int(alpha * 0.75))
                py5.stroke_weight(1.4)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

    particles = active_particles
    py5.blend_mode(py5.BLEND)

    # 6. Safety check: fail-safe blank screen detection
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # 7. Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Coronal Particles: {len(particles)}")

    # 8. Finalize render on completion
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
