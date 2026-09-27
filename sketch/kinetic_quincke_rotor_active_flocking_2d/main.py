"""
kinetic_quincke_rotor_active_flocking_2d
2D electrohydrodynamic and active matter simulation of Quincke Rotation and Polar Flocking:
Maxwell-Wagner interface charge relaxation, supercritical symmetry-breaking bifurcation (E > E_c),
hydrodynamic lubrication self-propulsion (Quincke rollers), Vicsek-Toner-Tu polar flocking bands,
macroscopic active vortex mills, and Blinn-Phong specular dielectric liquid chrome optics.

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

# Dual Specular Light Vectors for Dielectric Liquid Chrome Shading
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

# Active Matter Parameters
NUM_ROLLERS = 2000
E_CRIT_TIME = 3.5            # Seconds when E exceeds E_c
FLOCK_TIME = 7.5             # Seconds when polar alignment dominates
VORTEX_TIME = 11.5           # Seconds when macroscopic vortex mill condenses


class QuinckeRoller:
    """Active dielectric colloid undergoing Quincke rotation and collective flocking."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.theta = random.uniform(-np.pi, np.pi)
        self.speed = 0.0
        self.omega = 0.0
        self.radius = random.uniform(2.2, 3.6)
        self.history = []

    def update(self, t, align_fx, align_fy, vortex_active):
        self.history.append((self.x, self.y))
        if len(self.history) > 6:
            self.history.pop(0)

        # 1. Spontaneous Symmetry Breaking Bifurcation (E > E_c)
        if t < E_CRIT_TIME:
            # Sub-critical Brownian jitter
            self.speed = 0.0015 * random.uniform(0.2, 0.8)
            self.theta += random.gauss(0.0, 0.25)
        elif t < FLOCK_TIME:
            # Supercritical Quincke rotation: particles accelerate to steady rolling speed
            tau_acc = (t - E_CRIT_TIME) / (FLOCK_TIME - E_CRIT_TIME)
            target_speed = 0.014 * min(1.0, tau_acc * 1.5)
            self.speed = 0.92 * self.speed + 0.08 * target_speed
            self.theta += random.gauss(0.0, 0.08)
        elif t < VORTEX_TIME:
            # Hydrodynamic polar alignment: steering toward neighbor flux
            self.speed = 0.016
            target_angle = np.arctan2(align_fy, align_fx)
            angle_diff = np.arctan2(np.sin(target_angle - self.theta), np.cos(target_angle - self.theta))
            self.theta += 0.12 * angle_diff + random.gauss(0.0, 0.035)
        else:
            # Active Vortex Mill: Azimuthal circulation around center
            self.speed = 0.018
            r_c = np.sqrt(self.x**2 + self.y**2)
            phi = np.arctan2(self.y, self.x)
            vortex_angle = phi + np.pi * 0.5 + 0.12 * (1.2 - r_c)
            angle_diff = np.arctan2(np.sin(vortex_angle - self.theta), np.cos(vortex_angle - self.theta))
            self.theta += 0.18 * angle_diff + random.gauss(0.0, 0.025)

        # Position step
        self.x += self.speed * np.cos(self.theta)
        self.y += self.speed * np.sin(self.theta)

        # Soft boundary confinement
        margin_x, margin_y = 2.9, 1.6
        if self.x > margin_x:
            self.x = margin_x
            self.theta = np.pi - self.theta
        elif self.x < -margin_x:
            self.x = -margin_x
            self.theta = np.pi - self.theta
        if self.y > margin_y:
            self.y = margin_y
            self.theta = -self.theta
        elif self.y < -margin_y:
            self.y = -margin_y
            self.theta = -self.theta


rollers = []
for _ in range(NUM_ROLLERS):
    rollers.append(QuinckeRoller(random.uniform(-2.6, 2.6), random.uniform(-1.4, 1.4)))


def compute_hydrodynamic_fields(t, frame):
    """
    Vectorized computation of continuous electrohydrodynamic fields:
    1. Dielectric liquid substrate micro-vorticity
    2. Travelling polar solitary wave streamfunctions
    3. Macroscopic vortex mill circulation
    4. Electrode rail geometry & dielectric potential relief
    5. Specular normal map & Blinn-Phong chrome shading
    """
    # 1. Electric Field Ramping & Charge Relaxation Relief
    e_field_strength = min(1.0, t / 4.0)
    electrode_rails = (
        np.exp(-((Y_grid - 1.55)**2) / 0.02) +
        np.exp(-((Y_grid + 1.55)**2) / 0.02) +
        np.exp(-((X_grid - 2.85)**2) / 0.02) +
        np.exp(-((X_grid + 2.85)**2) / 0.02)
    )

    # 2. Polar Wavefield & Hydrodynamic Vortex Lattice
    k_flock = 5.5
    omega_flock = 4.2
    flock_phase = k_flock * (X_grid * 0.8 + Y_grid * 0.6) - omega_flock * t

    if t < E_CRIT_TIME:
        hydro_vorticity = 0.15 * np.sin(8.0 * X_grid) * np.sin(8.0 * Y_grid) * e_field_strength
        polar_wave = np.zeros_like(X_grid)
    elif t < VORTEX_TIME:
        tau = min(1.0, (t - E_CRIT_TIME) / (FLOCK_TIME - E_CRIT_TIME))
        polar_wave = np.exp(-((np.mod(flock_phase, 2.0 * np.pi) - np.pi)**2) / 0.6) * tau
        hydro_vorticity = (
            np.sin(6.0 * X_grid - 2.5 * t) * np.cos(6.0 * Y_grid + 1.8 * t) * 0.8 +
            polar_wave * 1.2
        )
    else:
        # Macroscopic Vortex Mill
        r_c = np.sqrt(X_grid**2 + Y_grid**2)
        theta_c = np.arctan2(Y_grid, X_grid)
        tau_vort = min(1.0, (t - VORTEX_TIME) / 2.0)
        vortex_core = np.exp(-((r_c - 1.1)**2) / 0.35) * (1.0 + 0.4 * np.sin(6.0 * theta_c - t * 6.0))
        hydro_vorticity = vortex_core * tau_vort * 1.8
        polar_wave = vortex_core * tau_vort

    # 3. Total Optical Relief Map
    relief_field = (
        electrode_rails * 1.5 +
        np.abs(hydro_vorticity) * 1.2 +
        polar_wave * 1.8
    )

    # 4. Surface Normal Gradient
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 5. Dual Specular Glints
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**38.0
    specular2 = ndoth2**52.0

    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        electrode_rails,
        hydro_vorticity,
        polar_wave,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )


def render_field_to_buffer(
    electrode_rails,
    hydro_vorticity,
    polar_wave,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes fields into ARGB pixel buffer using the 4-color palette:
    1. Active Quincke Rollers & Polar Flocking Bands: Incandescent Amber (#ffb703) & Solar Orange (#ff7b00)
    2. Hydrodynamic Fluid Micro-Vortices: Electric Cyan (#00f0ff) & Deep Sapphire (#0077b6)
    3. Specular Electrode Rails & Discharge Glints: Diamond White (#ffffff) & Solar Platinum (#fff3b0)
    4. Dielectric Oil Bath Abyss: Deep Midnight Obsidian (#030611, #090e22)
    """
    # Background: Dielectric liquid pool
    r_norm = np.clip(np.sqrt(X_grid**2 + Y_grid**2) / 3.2, 0.0, 1.0)
    r_field = 3.0 + 9.0 * r_norm
    g_field = 6.0 + 12.0 * r_norm
    b_field = 17.0 + 28.0 * r_norm

    # 1. Hydrodynamic Fluid Vortices & Dielectric Liquid Wake (Cyan & Sapphire)
    vort_norm = np.clip(np.abs(hydro_vorticity) * 1.1, 0.0, 2.0)
    diff_total = diffuse1 * 0.65 + diffuse2 * 0.45
    r_field += vort_norm * (0.0 + diff_total * 30.0)
    g_field += vort_norm * (160.0 + diff_total * 75.0)
    b_field += vort_norm * (245.0 + diff_total * 95.0)

    # 2. Polar Solitary Wave Fronts (Incandescent Amber & Gold)
    polar_norm = np.clip(polar_wave * 1.3, 0.0, 2.5)
    r_field += polar_norm * 255.0
    g_field += polar_norm * 170.0
    b_field += polar_norm * 15.0

    # 3. Electrode Micro-Rails (Gold & Platinum Chrome)
    rail_norm = np.clip(electrode_rails * 1.4, 0.0, 2.0)
    r_field += rail_norm * 220.0
    g_field += rail_norm * 210.0
    b_field += rail_norm * 180.0

    # 4. Dual Blinn-Phong Specular Liquid Chrome Highlights
    spec_total = specular1 * 1.25 + specular2 * 1.05
    r_field += spec_total * 255.0
    g_field += spec_total * 248.0
    b_field += spec_total * 235.0

    # Final Buffer Transfer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def update_and_draw_rollers(t):
    """Simulate and render active Quincke rollers with Vicsek alignment and comet tails."""
    scale_x = float(py5.width) / 6.4
    scale_y = float(py5.height) / 3.6
    cx = float(py5.width) * 0.5
    cy = float(py5.height) * 0.5

    # Collective polar orientation vector field
    global_align_fx = 0.8 * np.cos(t * 0.3) + 0.2
    global_align_fy = 0.6 * np.sin(t * 0.4)
    vortex_active = (t >= VORTEX_TIME)

    py5.blend_mode(py5.ADD)
    py5.no_stroke()

    for r in rollers:
        r.update(t, global_align_fx, global_align_fy, vortex_active)

        sx = cx + r.x * scale_x
        sy = cy - r.y * scale_y

        # Draw comet wake
        if len(r.history) >= 2:
            py5.stroke(255, 140, 20, 110)
            py5.stroke_weight(r.radius * 0.7)
            for i in range(len(r.history) - 1):
                x1, y1 = r.history[i]
                x2, y2 = r.history[i + 1]
                py5.line(cx + x1 * scale_x, cy - y1 * scale_y, cx + x2 * scale_x, cy - y2 * scale_y)
            py5.no_stroke()

        # Draw rotating Quincke roller bead
        py5.fill(255, 190, 40, 230)
        py5.circle(sx, sy, r.radius * 2.0)

        # Spinning dipole orientation pointer
        px = sx + r.radius * 1.5 * np.cos(r.theta)
        py = sy - r.radius * 1.5 * np.sin(r.theta)
        py5.stroke(255, 255, 255, 220)
        py5.stroke_weight(1.5)
        py5.line(sx, sy, px, py)
        py5.no_stroke()

        # Soft outer charge aura
        py5.fill(255, 120, 0, 50)
        py5.circle(sx, sy, r.radius * 4.2)

    py5.blend_mode(py5.BLEND)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Hydrodynamic State
    (
        electrode_rails,
        hydro_vorticity,
        polar_wave,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    ) = compute_hydrodynamic_fields(t, frame)

    # 2. Render Continuum Fields to ARGB Pixel Buffer
    render_field_to_buffer(
        electrode_rails,
        hydro_vorticity,
        polar_wave,
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

    # 4. Render Active Quincke Rollers
    update_and_draw_rollers(t)

    # 5. Save Current Frame to Disk Cache
    frame_path = FRAMES_DIR / f"frame-{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at peak polar band formation (frame 560, t ~ 9.33s)
    if frame == 560:
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        py5.save_frame(str(preview_path))
        print(f"[Preview Saved] Polar band preview captured: {preview_path}")

    # Safety check on first frame
    if frame == 1:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            os._exit(1)

    # Progress feedback
    if frame % 60 == 0:
        progress_pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Rollers: {len(rollers)}")

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

        # Fallback preview if frame 560 didn't trigger
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
