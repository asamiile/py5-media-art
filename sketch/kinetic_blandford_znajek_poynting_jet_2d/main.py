"""
kinetic_blandford_znajek_poynting_jet_2d
2D general relativistic electrodynamics simulation of the Blandford-Znajek Process:
spinning Kerr black hole magnetosphere (a/M = 0.95), Lense-Thirring ergosphere frame-dragging,
parabolic magnetic flux surfaces, horizon rotational energy extraction, collimated
relativistic Poynting jets, equatorial reconnection current sheet, and plasma chrome optics.

1920x1080 @ 60fps, 900 frames (15 seconds).
"""

from pathlib import Path
import os
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = PREVIEW_SIZE

# Spatial Simulation Domain (16:9 aspect ratio, 960x540 grid)
Nx, Ny = 960, 540
x_coords = np.linspace(-3.2, 3.2, Nx, dtype=np.float32)
y_coords = np.linspace(-1.8, 1.8, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Kerr Metric Parameters (Geometrized units G=c=1)
M = 0.50                     # Black hole mass scale
A_SPIN = 0.95 * M            # Extreme Kerr spin parameter
R_HORIZON = M + np.sqrt(M**2 - A_SPIN**2)  # Event horizon r+ ~ 0.656
OMEGA_H = A_SPIN / (2.0 * M * R_HORIZON)   # Horizon angular frequency
OMEGA_F = 0.5 * OMEGA_H                    # Blandford-Znajek optimal field line frequency

# Polar coordinates (Z-axis along vertical Y)
R_sph = np.sqrt(X_grid**2 + Y_grid**2)
Theta_sph = np.arctan2(np.abs(X_grid), np.abs(Y_grid))  # Angle from polar jet axis

# Ergosphere outer boundary (static limit): r_ergo(theta) = M + sqrt(M^2 - a^2 cos^2(theta))
R_ergo = M + np.sqrt(np.maximum(0.0, M**2 - (A_SPIN * np.cos(Theta_sph))**2))

# Dual Specular Light Vectors for Plasma Chrome Shading
light1 = np.array([0.55, -0.65, 0.52], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.58, 0.64], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5 (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255


class Lepton:
    """Lagrangian synchrotron lepton or relativistic jet spark."""
    def __init__(self, x, y, ptype="jet", vx=0.0, vy=0.0, life=90.0, radius=2.5, color_rgba=None):
        self.x = float(x)
        self.y = float(y)
        self.ptype = ptype
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.radius = float(radius)
        self.color_rgba = color_rgba or (0, 240, 255, 210)
        self.is_dead = False
        self.history = []

    def update(self):
        self.life -= 1.0
        if self.life <= 0.0:
            self.is_dead = True
            return

        self.history.append((self.x, self.y))
        if len(self.history) > 6:
            self.history.pop(0)

        r = np.sqrt(self.x**2 + self.y**2)
        if self.ptype == "jet":
            # Accelerated along vertical polar funnel
            self.vy *= 1.025
            self.vx *= 0.94
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "ergo":
            # Swirling in the frame-dragging ergosphere
            omega_drag = 0.08 / (r**2 + 0.1)
            new_x = self.x * np.cos(omega_drag) - self.y * np.sin(omega_drag)
            new_y = self.x * np.sin(omega_drag) + self.y * np.cos(omega_drag)
            self.x = 0.97 * new_x
            self.y = 0.97 * new_y
        elif self.ptype == "plasmoid":
            # Magnetic reconnection plasmoid ejected along equator
            self.vx *= 1.015
            self.vy *= 0.92
            self.x += self.vx
            self.y += self.vy


particles = []


def compute_blandford_znajek_state(t, frame):
    """
    Vectorized computation of general relativistic electrodynamic fields:
    1. Black hole event horizon & photon sphere shadow
    2. Ergosphere frame-dragging flow field
    3. Parabolic Blandford-Znajek magnetic flux surfaces Psi(r, theta)
    4. Relativistic Poynting jet funnels (S^r energy extraction)
    5. Equatorial magnetic reconnection current sheet
    6. Dual-light Blinn-Phong specular plasma chrome normal shading
    """
    # 1. Event Horizon & Ergosphere Masks
    horizon_mask = (R_sph <= R_HORIZON)
    ergo_mask = (R_sph > R_HORIZON) & (R_sph <= R_ergo)

    # Lense-Thirring Frame Dragging Streamfunction
    drag_angle = np.arctan2(Y_grid, X_grid) + (2.0 * M * A_SPIN / (R_sph**3 + 0.2)) * t * 4.0
    ergo_flow = np.exp(-((R_sph - 0.5 * (R_HORIZON + R_ergo))**2) / 0.08) * (1.0 + 0.4 * np.sin(4.0 * drag_angle))

    # 2. Blandford-Znajek Parabolic Magnetic Streamfunction Psi(r, theta) = r^p (1 - cos theta)
    psi_mag = (R_sph**0.65) * (1.0 - np.cos(Theta_sph))
    twisted_flux = np.cos(22.0 * psi_mag - OMEGA_F * t * 8.0)

    # 3. Relativistic Poynting Jet Funnels (S^r along +/- Y axis)
    jet_width = 0.12 + 0.22 * np.sqrt(np.maximum(0.0, np.abs(Y_grid) - R_HORIZON))
    jet_profile = np.exp(-(X_grid**2) / (2.0 * jet_width**2)) * (np.abs(Y_grid) > (R_HORIZON * 0.8))

    # Jet propagation wave packets
    poynting_waves = 1.0 + 0.45 * np.sin(18.0 * np.abs(Y_grid) - 22.0 * t)
    s_poynting = jet_profile * poynting_waves * min(1.0, t / 2.0)

    # 4. Equatorial Magnetic Reconnection Current Sheet (Y ~ 0)
    current_sheet = (
        np.exp(-(Y_grid**2) / 0.018) *
        (R_sph > (R_ergo * 0.9)) *
        (1.0 + 0.4 * np.cos(14.0 * np.abs(X_grid) - 6.0 * t))
    )

    # 5. Photon Sphere Luminous Ring (r ~ 1.5 M)
    r_photon = 1.45 * M
    photon_ring = np.exp(-((R_sph - r_photon)**2) / 0.008) * 1.5

    # 6. Composite Optical Relief Map
    relief_field = (
        s_poynting * 2.2 +
        ergo_flow * 1.4 +
        np.abs(twisted_flux) * 0.85 +
        current_sheet * 1.3 +
        photon_ring * 2.0
    )
    relief_field[horizon_mask] = 0.0

    # 7. Surface Normal Calculation
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 8. Specular Highlights (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**38.0
    specular2 = ndoth2**54.0

    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        horizon_mask,
        ergo_mask,
        ergo_flow,
        s_poynting,
        current_sheet,
        photon_ring,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )


def render_field_to_buffer(
    horizon_mask,
    ergo_mask,
    ergo_flow,
    s_poynting,
    current_sheet,
    photon_ring,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes relativistic electromagnetic fields into the ARGB buffer using the 4-color palette:
    1. Poynting Jet Core & Photon Ring: Electric Glacial Cyan (#00f0ff) & Diamond White (#ffffff)
    2. Ergosphere Frame Dragging & Twisted Helices: Incandescent Solar Amber (#ffb703) & Molten Gold (#ff7b00)
    3. Equatorial Current Sheet & Plasmoids: Actinic Amethyst (#9d4edd) & Laser Magenta (#ff007f)
    4. Kerr Spacetime Abyss: Deep Midnight Obsidian (#02040a, #080d1e)
    """
    # Background: Curved spacetime vacuum
    r_norm = np.clip(R_sph / 3.4, 0.0, 1.0)
    r_field = 2.0 + 8.0 * r_norm
    g_field = 4.0 + 10.0 * r_norm
    b_field = 12.0 + 26.0 * r_norm

    # 1. Ergosphere Frame-Dragging Swirl (Incandescent Amber & Gold)
    ergo_norm = np.clip(ergo_flow * 1.25, 0.0, 2.2)
    diff_total = diffuse1 * 0.65 + diffuse2 * 0.45
    r_field += ergo_norm * (220.0 + diff_total * 35.0)
    g_field += ergo_norm * (140.0 + diff_total * 45.0)
    b_field += ergo_norm * (10.0 + diff_total * 20.0)

    # 2. Equatorial Reconnection Current Sheet (Actinic Amethyst & Laser Magenta)
    sheet_norm = np.clip(current_sheet * 1.4, 0.0, 2.5)
    r_field += sheet_norm * 240.0
    g_field += sheet_norm * 20.0
    b_field += sheet_norm * 180.0

    # 3. Collimated Relativistic Poynting Jet Funnels (Luminous Electric Cyan & Glacial White)
    jet_norm = np.clip(s_poynting * 1.35, 0.0, 3.0)
    r_field += jet_norm * 30.0
    g_field += jet_norm * 230.0
    b_field += jet_norm * 255.0

    # 4. Photon Sphere Ring (Diamond White Flare)
    ring_norm = np.clip(photon_ring * 1.5, 0.0, 2.5)
    r_field += ring_norm * 255.0
    g_field += ring_norm * 255.0
    b_field += ring_norm * 240.0

    # 5. Dual Blinn-Phong Specular Plasma Chrome Glints
    spec_total = specular1 * 1.35 + specular2 * 1.05
    r_field += spec_total * 255.0
    g_field += spec_total * 250.0
    b_field += spec_total * 240.0

    # 6. Event Horizon Blackout (Absolute Gravitational Black Hole Void)
    r_field[horizon_mask] = 0.0
    g_field[horizon_mask] = 0.0
    b_field[horizon_mask] = 0.0

    # Final Buffer Transfer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def update_and_draw_particles(t):
    """Simulate and render Lagrangian synchrotron leptons and reconnection sparks."""
    global particles

    # Spawn relativistic polar jet particles
    if len(particles) < 2400:
        for _ in range(8):
            sign_y = 1.0 if random.random() > 0.5 else -1.0
            particles.append(
                Lepton(
                    random.uniform(-0.12, 0.12),
                    sign_y * (R_HORIZON * 1.05 + random.uniform(0.0, 0.1)),
                    ptype="jet",
                    vx=random.uniform(-0.003, 0.003),
                    vy=sign_y * random.uniform(0.045, 0.075),
                    life=random.uniform(50, 90),
                    radius=random.uniform(1.8, 3.4),
                    color_rgba=(0, 240, 255, 220)
                )
            )

    # Spawn ergosphere frame-dragging tracers
    if len(particles) < 2400:
        for _ in range(6):
            angle = random.uniform(-np.pi, np.pi)
            r = random.uniform(R_HORIZON * 1.05, 1.25)
            particles.append(
                Lepton(
                    r * np.cos(angle),
                    r * np.sin(angle),
                    ptype="ergo",
                    life=random.uniform(60, 110),
                    radius=random.uniform(2.0, 3.8),
                    color_rgba=(255, 185, 30, 200)
                )
            )

    # Spawn equatorial reconnection plasmoids
    if t > 5.0 and len(particles) < 2400:
        for _ in range(4):
            sign_x = 1.0 if random.random() > 0.5 else -1.0
            particles.append(
                Lepton(
                    sign_x * random.uniform(1.1, 1.6),
                    random.uniform(-0.06, 0.06),
                    ptype="plasmoid",
                    vx=sign_x * random.uniform(0.02, 0.04),
                    vy=random.uniform(-0.005, 0.005),
                    life=random.uniform(35, 70),
                    radius=random.uniform(2.2, 4.5),
                    color_rgba=(255, 20, 160, 230)
                )
            )

    scale_x = float(py5.width) / 6.4
    scale_y = float(py5.height) / 3.6
    cx = float(py5.width) * 0.5
    cy = float(py5.height) * 0.5

    py5.blend_mode(py5.ADD)
    py5.no_stroke()

    alive_particles = []
    for p in particles:
        p.update()
        if p.is_dead:
            continue
        alive_particles.append(p)

        sx = cx + p.x * scale_x
        sy = cy - p.y * scale_y

        if not (-50 <= sx <= py5.width + 50 and -50 <= sy <= py5.height + 50):
            continue

        life_ratio = p.life / p.max_life
        r, g, b, base_alpha = p.color_rgba
        alpha = base_alpha * life_ratio

        # Particle streak
        if len(p.history) >= 2:
            py5.stroke(r, g, b, alpha * 0.6)
            py5.stroke_weight(p.radius * 0.6)
            for i in range(len(p.history) - 1):
                x1, y1 = p.history[i]
                x2, y2 = p.history[i + 1]
                py5.line(cx + x1 * scale_x, cy - y1 * scale_y, cx + x2 * scale_x, cy - y2 * scale_y)
            py5.no_stroke()

        py5.fill(r, g, b, alpha)
        py5.circle(sx, sy, p.radius)

        py5.fill(r, g, b, alpha * 0.25)
        py5.circle(sx, sy, p.radius * 2.8)

    particles = alive_particles
    py5.blend_mode(py5.BLEND)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute General Relativistic State
    (
        horizon_mask,
        ergo_mask,
        ergo_flow,
        s_poynting,
        current_sheet,
        photon_ring,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    ) = compute_blandford_znajek_state(t, frame)

    # 2. Render Continuum Fields to ARGB Buffer
    render_field_to_buffer(
        horizon_mask,
        ergo_mask,
        ergo_flow,
        s_poynting,
        current_sheet,
        photon_ring,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )

    # 3. Blit Buffer to Canvas
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
        packed = (a << 24) | (r << 16) | (g << 8) | b
        img.pixels[:] = packed.flatten()
        img.update_pixels()

    py5.image(img, 0, 0, py5.width, py5.height)

    # 4. Render Lagrangian Relativistic Leptons
    update_and_draw_particles(t)

    # 5. Save Current Frame to Disk Cache
    frame_path = FRAMES_DIR / f"frame-{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at peak collimated jet flash (frame 570, t ~ 9.5s)
    if frame == 570:
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        py5.save_frame(str(preview_path))
        print(f"[Preview Saved] Blandford-Znajek jet preview captured: {preview_path}")

    # Safety check on first frame
    if frame == 1:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            os._exit(1)

    # Progress feedback
    if frame % 60 == 0:
        progress_pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Leptons: {len(particles)}")

    # 6. Video Compilation & Cleanup
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()

        print("\n[Render Complete] Compiling H.264 video with FFmpeg...")
        output_mp4 = SKETCH_DIR / "output.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            str(output_mp4)
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"[Video Compiled] Master MP4 saved: {output_mp4}")
        except subprocess.CalledProcessError as e:
            print(f"[FFmpeg Error] Failed to encode video: {e}")
            sys.exit(1)

        # Fallback preview if frame 570 didn't trigger
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        if not preview_path.exists():
            midpoint_frame = FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png"
            if midpoint_frame.exists():
                shutil.copyfile(midpoint_frame, preview_path)
                print(f"[Preview Saved] Fallback preview saved: {preview_path}")

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.\n")

        os._exit(0)


def settings():
    py5.size(SIZE[0], SIZE[1], py5.P2D)


def setup():
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[Setup Complete] Rendering {WORK_NAME} ({SIZE[0]}x{SIZE[1]} @ {FPS}fps, {TOTAL_FRAMES} frames)...")


def draw():
    try:
        draw_frame()
    except Exception:
        import traceback
        traceback.print_exc()
        os._exit(1)


if __name__ == "__main__":
    py5.run_sketch()
