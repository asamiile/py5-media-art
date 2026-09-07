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

# Spatial Grid for Ferrofluid Surface (16:9)
Nx, Ny = 640, 360
x_coords = np.linspace(-6.0, 6.0, Nx, dtype=np.float32)
y_coords = np.linspace(-6.0 * (Ny / Nx), 6.0 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Hexagonal Rosensweig spike equilibrium positions
a0 = 1.35
spike_centers = []
for row in range(-5, 6):
    for col in range(-6, 7):
        sx = col * a0 + (0.5 * a0 if row % 2 != 0 else 0.0)
        sy = row * a0 * (np.sqrt(3.0) / 2.0)
        if -5.2 <= sx <= 5.2 and -3.0 <= sy <= 3.0:
            spike_centers.append((sx, sy))

spike_centers = np.array(spike_centers, dtype=np.float32)
N_SPIKES = len(spike_centers)
r_centers = np.sqrt(spike_centers[:, 0]**2 + spike_centers[:, 1]**2)

# Studio Lights:
# Key Light 1: Upper-left, Electric Cyan & Pure Silver
Lx1, Ly1, Lz1 = -0.55, -0.65, 0.52
L_mag1 = np.sqrt(Lx1**2 + Ly1**2 + Lz1**2)
Lx1, Ly1, Lz1 = Lx1 / L_mag1, Ly1 / L_mag1, Lz1 / L_mag1
Hx1, Hy1, Hz1 = Lx1, Ly1, Lz1 + 1.0
H_mag1 = np.sqrt(Hx1**2 + Hy1**2 + Hz1**2)
Hx1, Hy1, Hz1 = Hx1 / H_mag1, Hy1 / H_mag1, Hz1 / H_mag1

# Rim Light 2: Lower-right, Molten Bronze & Amber
Lx2, Ly2, Lz2 = 0.65, 0.55, 0.52
L_mag2 = np.sqrt(Lx2**2 + Ly2**2 + Lz2**2)
Lx2, Ly2, Lz2 = Lx2 / L_mag2, Ly2 / L_mag2, Lz2 / L_mag2
Hx2, Hy2, Hz2 = Lx2, Ly2, Lz2 + 1.0
H_mag2 = np.sqrt(Hx2**2 + Hy2**2 + Hz2**2)
Hx2, Hy2, Hz2 = Hx2 / H_mag2, Hy2 / H_mag2, Hz2 / H_mag2

# Trapped Superparamagnetic Tracer Sparks (leaping between peak apexes)
MAX_SPARKS = 380
sparks = []


class MagneticSpark:
    def __init__(self, src_idx, dst_idx, screen_peaks):
        self.src_idx = src_idx
        self.dst_idx = dst_idx
        self.progress = 0.0
        self.speed = random.uniform(0.015, 0.035)
        self.arch_height = random.uniform(25.0, 75.0)
        self.size = random.uniform(2.0, 4.2)
        self.px = screen_peaks[src_idx][0]
        self.py = screen_peaks[src_idx][1]
        self.prev_x = self.px
        self.prev_y = self.py

    def update(self, screen_peaks):
        self.prev_x = self.px
        self.prev_y = self.py
        self.progress += self.speed

        p0 = screen_peaks[self.src_idx]
        p1 = screen_peaks[self.dst_idx]

        # Parabolic arc trajectory along magnetic flux line
        t = self.progress
        self.px = (1.0 - t) * p0[0] + t * p1[0]
        linear_y = (1.0 - t) * p0[1] + t * p1[1]
        arc_offset = 4.0 * t * (1.0 - t) * self.arch_height
        self.py = linear_y - arc_offset

    @property
    def is_dead(self):
        return self.progress >= 1.0


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_ferrofluid_surface(frame_idx):
    # Normalized time cycle over TOTAL_FRAMES
    t = (frame_idx / TOTAL_FRAMES) * 6.0 * np.pi
    omega = 2.0
    tilt_amp = 0.22

    # Magnetic field vector precession
    bx_arr = tilt_amp * np.cos(omega * t - 0.75 * r_centers)
    by_arr = tilt_amp * np.sin(omega * t - 0.75 * r_centers)

    tip_x = spike_centers[:, 0] + bx_arr * 0.45
    tip_y = spike_centers[:, 1] + by_arr * 0.45

    # 3D Tensor broadcast over spatial grid for fast computation
    dx_all = X_grid[:, :, None] - tip_x[None, None, :]
    dy_all = Y_grid[:, :, None] - tip_y[None, None, :]
    r_all = np.sqrt(dx_all**2 + dy_all**2) + 1e-4

    # Conical peak profile with precession tilt asymmetry
    core_rad = 0.45
    cone_profile = np.exp(- (r_all / core_rad)**1.2) * (
        1.0 + 0.35 * (dx_all * bx_arr[None, None, :] + dy_all * by_arr[None, None, :])
    )
    zeta = np.sum(cone_profile, axis=2)

    # Spike tip intensity
    tip_points = np.sum(np.exp(- (r_all / 0.10)**2), axis=2)

    # Subtle magnetic ripples across background
    ripple = 0.05 * (np.cos(3.2 * X_grid) + np.cos(1.6 * X_grid + 2.77 * Y_grid) + np.cos(1.6 * X_grid - 2.77 * Y_grid))
    zeta += np.maximum(0.0, ripple)

    # Surface gradients for liquid mirror normal
    dzeta_dx = np.gradient(zeta, axis=1) * (Nx / 12.0)
    dzeta_dy = np.gradient(zeta, axis=0) * (Ny / (12.0 * Ny / Nx))

    norm_mag = np.sqrt(dzeta_dx**2 + dzeta_dy**2 + 1.0)
    Nx_s = -dzeta_dx / norm_mag
    Ny_s = -dzeta_dy / norm_mag
    Nz_s = 1.0 / norm_mag

    # Dual Blinn-Phong specular reflections
    NdotH1 = np.maximum(0.0, Nx_s * Hx1 + Ny_s * Hy1 + Nz_s * Hz1)
    specular1 = NdotH1**32.0

    NdotH2 = np.maximum(0.0, Nx_s * Hx2 + Ny_s * Hy2 + Nz_s * Hz2)
    specular2 = NdotH2**24.0

    fresnel = (1.0 - Nz_s)**1.5

    return zeta, tip_x, tip_y, tip_points, specular1, specular2, fresnel


def render_ferrofluid_mirror(specular1, specular2, fresnel, tip_points):
    # Palette Architecture:
    # 1. Deep Liquid Obsidian / Ferrofluid Mirror (60%): #010206
    r = np.full_like(X_grid, 2.0)
    g = np.full_like(X_grid, 3.0)
    b = np.full_like(X_grid, 10.0)

    # Fresnel slope reflectance (Cobalt / Chrome sheen)
    r += fresnel * 20.0
    g += fresnel * 40.0
    b += fresnel * 95.0

    # 2. 30% Metallic Silver & Electric Cyan / Cobalt Specular
    r += specular1 * 220.0
    g += specular1 * 245.0
    b += specular1 * 255.0

    # Warm Rim Specular (Molten Bronze & Amber)
    r += specular2 * 255.0
    g += specular2 * 140.0
    b += specular2 * 35.0

    # 3. 10% Needle Spike Tips (Incandescent Solar White & Gold)
    r += tip_points * 255.0
    g += tip_points * 255.0
    b += tip_points * 220.0

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
    global sparks

    # 1. Physics update
    (zeta, tip_x, tip_y, tip_points,
     specular1, specular2, fresnel) = compute_ferrofluid_surface(py5.frame_count)

    # 2. Render surface into pixel buffer
    render_ferrofluid_mirror(specular1, specular2, fresnel, tip_points)

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

    # Convert spike tip coordinates to 4K screen coordinates
    y_span = 12.0 * (Ny / Nx)
    screen_peaks = []
    for i in range(N_SPIKES):
        sc_x = ((tip_x[i] - (-6.0)) / 12.0) * py5.width
        sc_y = ((tip_y[i] - (-6.0 * (Ny / Nx))) / y_span) * py5.height
        screen_peaks.append((sc_x, sc_y))

    # 4. Spawn jumping magnetic spark particles between neighboring peaks
    if len(sparks) < MAX_SPARKS:
        spawn_n = min(18, MAX_SPARKS - len(sparks))
        for _ in range(spawn_n):
            src = random.randint(0, N_SPIKES - 1)
            # Find nearest neighbor peak
            p_src = spike_centers[src]
            dists = np.sum((spike_centers - p_src)**2, axis=1)
            dists[src] = 999.0
            dst = int(np.argmin(dists))
            sparks.append(MagneticSpark(src, dst, screen_peaks))

    # 5. Render Magnetic Sparks on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_sparks = []
    for s in sparks:
        s.update(screen_peaks)
        if not s.is_dead:
            active_sparks.append(s)
            fade = np.sin(s.progress * np.pi)
            alpha = int(fade * 240)

            # Spark color (Molten Gold to Electric Cyan)
            cr = int(255 - s.progress * 110)
            cg = int(200 + s.progress * 45)
            cb = int(60 + s.progress * 195)

            # Glow aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.35))
            py5.circle(s.px, s.py, s.size * 2.8)

            # Nucleus bead
            py5.fill(255, 255, 240, alpha)
            py5.circle(s.px, s.py, s.size * 1.0)

            # Trajectory streak
            py5.stroke(cr, cg, cb, int(alpha * 0.5))
            py5.stroke_weight(1.4)
            py5.line(s.px, s.py, s.prev_x, s.prev_y)

    sparks = active_sparks
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Sparks: {len(sparks)}")

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
