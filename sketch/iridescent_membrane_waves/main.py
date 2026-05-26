"""
iridescent_membrane_waves
=========================
A thin luminescent membrane suspended in darkness, rippling with standing wave
interference. The surface is colored using thin-film interference mapping,
creating shimmering iridescent patterns that shift as waves propagate.

Palette: Deep Obsidian (bg), Iridescent teal-violet (thin-film), Rose-gold peaks, Electric white crests
Format: 15s @ 60fps -> iridescent_membrane_waves.mp4
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

# ── Wave Simulation Settings ─────────────────────────────────────────────────
GW, GH = 400, 225           # Simulation grid
DAMPING = 0.997              # Wave energy damping per step
WAVE_SPEED = 0.42            # Wave propagation speed (c²)
SUBSTEPS = 3                 # Physics substeps per frame
N_SOURCES = 5                # Number of wave excitation sources

# ── 3D Rendering Settings ────────────────────────────────────────────────────
HEIGHT_SCALE = 120.0         # How tall the waves appear in 3D
PERSPECTIVE_TILT = 0.55      # Camera tilt angle (radians)
MESH_SCALE_X = 4.0           # Grid cell width on screen
MESH_SCALE_Y = 2.8           # Grid cell height on screen (foreshortened)

# ── State ────────────────────────────────────────────────────────────────────
u_curr = None   # Current displacement
u_prev = None   # Previous displacement

# Wave source schedule: (start_frame, cx, cy, frequency, amplitude, duration)
wave_sources = []


def _init_wave_sources():
    """Create a schedule of wave sources at various positions."""
    global wave_sources
    wave_sources = []
    for i in range(N_SOURCES):
        start = int(i * TOTAL_FRAMES / N_SOURCES) + np.random.randint(0, 30)
        cx = np.random.randint(GW // 6, GW * 5 // 6)
        cy = np.random.randint(GH // 6, GH * 5 // 6)
        freq = np.random.uniform(0.06, 0.14)   # Oscillation frequency
        amp = np.random.uniform(0.4, 0.9)
        duration = np.random.randint(120, 300)  # How many frames active
        wave_sources.append((start, cx, cy, freq, amp, duration))

    # Add two persistent gentle sources for continuous motion
    wave_sources.append((0, GW // 3, GH // 2, 0.04, 0.25, TOTAL_FRAMES))
    wave_sources.append((0, GW * 2 // 3, GH // 3, 0.055, 0.2, TOTAL_FRAMES))


def _thin_film_color(thickness):
    """
    Map a scalar 'thickness' to an RGB color simulating thin-film interference.
    Uses a simplified model where the reflected color cycles through spectral
    orders as thickness increases.
    """
    # Normalize thickness to [0, 1] range for color cycling
    t = np.clip(thickness, 0.0, 1.0)

    # Multi-cycle sine waves offset by 120° for RGB channels
    # This creates the characteristic thin-film iridescence
    r = 0.5 + 0.5 * np.sin(t * np.pi * 6.0 + 0.0)
    g = 0.5 + 0.5 * np.sin(t * np.pi * 6.0 + 2.094)   # +2π/3
    b = 0.5 + 0.5 * np.sin(t * np.pi * 6.0 + 4.189)   # +4π/3

    # Shift toward teal-violet palette by biasing channels
    r = r * 0.7 + 0.05
    g = g * 0.85 + 0.08
    b = b * 0.95 + 0.12

    return r, g, b


def setup():
    global u_curr, u_prev
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.frame_rate(FPS)

    u_curr = np.zeros((GH, GW), dtype=np.float64)
    u_prev = np.zeros((GH, GW), dtype=np.float64)

    _init_wave_sources()

    # Initial gentle perturbation
    yy, xx = np.mgrid[:GH, :GW]
    u_curr = 0.15 * np.sin(xx * 0.05) * np.sin(yy * 0.07)
    u_prev = u_curr.copy()

    print(f"[{WORK_NAME}] Iridescent membrane initialized: {GW}x{GH}. Canvas: {SIZE[0]}x{SIZE[1]}.")


def draw():
    global u_curr, u_prev

    fc = py5.frame_count
    W, H = SIZE

    # ── Apply Wave Sources ───────────────────────────────────────────────────
    for start, cx, cy, freq, amp, duration in wave_sources:
        if start <= fc < start + duration:
            phase = (fc - start) * freq
            # Gaussian-shaped oscillating source
            yy, xx = np.ogrid[:GH, :GW]
            dist2 = ((xx - cx)**2 + (yy - cy)**2).astype(np.float64)
            source_radius = 8.0
            envelope = np.exp(-dist2 / (2.0 * source_radius**2))
            u_curr += amp * np.sin(phase * 2.0 * np.pi) * envelope * 0.08

    # ── Wave Equation Simulation ─────────────────────────────────────────────
    for _ in range(SUBSTEPS):
        # 2D wave equation: u_next = 2*u_curr - u_prev + c²*(Laplacian)
        lap = (
            np.roll(u_curr, 1, axis=0) + np.roll(u_curr, -1, axis=0) +
            np.roll(u_curr, 1, axis=1) + np.roll(u_curr, -1, axis=1) -
            4.0 * u_curr
        )

        u_next = 2.0 * u_curr - u_prev + WAVE_SPEED * lap
        u_next *= DAMPING

        # Absorbing boundary conditions (damp edges)
        edge = 15
        fade = np.ones((GH, GW), dtype=np.float64)
        for i in range(edge):
            f = i / edge
            fade[i, :] *= f
            fade[GH - 1 - i, :] *= f
            fade[:, i] *= f
            fade[:, GW - 1 - i] *= f
        u_next *= fade

        u_prev = u_curr.copy()
        u_curr = u_next

    # ── Compute Surface Properties ───────────────────────────────────────────
    displacement = u_curr.astype(np.float32)

    # Surface gradient for lighting
    dy, dx = np.gradient(displacement)
    grad_mag = np.sqrt(dx**2 + dy**2)

    # Thin-film thickness = base + displacement-dependent term
    # Normalize displacement to [0, 1] for color mapping
    d_min, d_max = displacement.min(), displacement.max()
    d_range = max(d_max - d_min, 0.001)
    thickness = (displacement - d_min) / d_range

    # Get iridescent colors
    ir, ig, ib = _thin_film_color(thickness)

    # Add rose-gold highlights on wave peaks
    peak_weight = np.clip((displacement - d_min) / d_range - 0.6, 0.0, 0.4) * 2.5
    ir += peak_weight * 0.86
    ig += peak_weight * 0.65
    ib += peak_weight * 0.51

    # Add electric white at extreme crests
    crest_weight = np.clip((displacement - d_min) / d_range - 0.85, 0.0, 0.15) * 6.0
    ir += crest_weight * 0.94
    ig += crest_weight * 0.96
    ib += crest_weight * 1.0

    # Specular highlights from gradient
    spec = np.clip(grad_mag * 8.0, 0.0, 0.5)
    ir += spec * 0.3
    ig += spec * 0.35
    ib += spec * 0.4

    # Clamp
    ir = np.clip(ir, 0.0, 1.0)
    ig = np.clip(ig, 0.0, 1.0)
    ib = np.clip(ib, 0.0, 1.0)

    # ── 3D Rendering ─────────────────────────────────────────────────────────
    py5.background(8, 6, 14)

    py5.push_matrix()
    py5.translate(W / 2, H / 2, -200)
    py5.rotate_x(1.0) # perspective tilt

    # Lighting
    py5.ambient_light(80, 70, 90)
    # Lights pointing in negative Z and Y to hit the normals
    py5.directional_light(200, 190, 220, 0.3, 0.5, -0.8)
    py5.directional_light(80, 100, 140, -0.5, 0.4, -0.5)
    py5.directional_light(255, 200, 200, 0, -1, 0)

    # Draw mesh as quad strips
    py5.no_stroke()
    
    # We want to center the mesh at 0,0 locally
    for row in range(GH - 1):
        py5.begin_shape(py5.QUAD_STRIP)
        for col in range(GW):
            for r in [row, row + 1]:
                x = (col - GW / 2) * MESH_SCALE_X
                y_val = (r - GH / 2) * MESH_SCALE_Y
                # Z is height in our new rotated coordinate system
                z_val = displacement[r, col] * HEIGHT_SCALE

                cr = int(ir[r, col] * 255)
                cg = int(ig[r, col] * 255)
                cb = int(ib[r, col] * 255)

                py5.fill(cr, cg, cb, 230)
                py5.vertex(x, y_val, z_val)

        py5.end_shape()
    py5.pop_matrix()

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid_frame = TOTAL_FRAMES // 2
        shutil.copyfile(
            str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        )
        print(f"[Render Preview] Saved preview image as {PREVIEW_FILENAME}")

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
