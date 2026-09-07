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

# Simulation Grid (16:9 aspect ratio)
Nx, Ny = 640, 360
Lx, Ly = 60.0, 34.0
dx = Lx / Nx
dy = Ly / Ny

# Coordinate meshes
x = np.linspace(-Lx / 2, Lx / 2, Nx, endpoint=False, dtype=np.float32)
y = np.linspace(-Ly / 2, Ly / 2, Ny, endpoint=False, dtype=np.float32)
X, Y = np.meshgrid(x, y)

# Fourier wavenumbers for 2D NLS
kx = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx).astype(np.float32)
ky = 2.0 * np.pi * np.fft.fftfreq(Ny, d=dy).astype(np.float32)
KX, KY = np.meshgrid(kx, ky)
K2 = (KX**2 + KY**2).astype(np.float32)

# NLS Simulation parameters (Benjamin-Feir modulational instability)
dt = 0.016
gamma = 1.45  # Focusing cubic nonlinearity

disp_half = np.exp(-1j * 0.25 * dt * K2).astype(np.complex64)
k2_max = float(np.max(K2))
filter_mask = np.exp(- (K2 / (k2_max * 0.38))**8).astype(np.float32)

# Initial Peregrine / Benjamin-Feir wave packet envelope
seed_cx = random.uniform(-4.0, 4.0)
seed_cy = random.uniform(-2.0, 2.0)
gauss_env = np.exp(- ((X - seed_cx)**2 / 160.0 + (Y - seed_cy)**2 / 90.0)).astype(np.float32)
psi = (gauss_env * 1.6 + 0.65).astype(np.complex64)

# Add modulation sidebands to seed self-focusing
psi += (0.22 * np.exp(1j * (0.32 * X + 0.16 * Y + random.uniform(0, 2 * np.pi)))).astype(np.complex64)
psi += (0.22 * np.exp(1j * (-0.26 * X + 0.24 * Y + random.uniform(0, 2 * np.pi)))).astype(np.complex64)

# Underlying deep oceanic wave spectrum (Stokes / Gerstner components)
wave_components = [
    {"k": np.array([0.42, 0.16], dtype=np.float32), "w": 1.05, "amp": 1.15, "steep": 0.55},
    {"k": np.array([0.36, -0.22], dtype=np.float32), "w": 0.96, "amp": 0.90, "steep": 0.50},
    {"k": np.array([0.62, 0.10], dtype=np.float32), "w": 1.28, "amp": 0.55, "steep": 0.40},
    {"k": np.array([0.18, 0.34], dtype=np.float32), "w": 0.74, "amp": 0.75, "steep": 0.45},
]

# Pixel buffer for wave surface
surf_pixels = np.zeros((Ny, Nx, 4), dtype=np.uint8)
surf_pixels[..., 3] = 255

# Dynamic foam and spray particles
MAX_PARTICLES = 450
particles = []


class FoamParticle:
    def __init__(self, x, y, vx, vy, life, max_life, size, r, g, b):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = max_life
        self.size = size
        self.r = r
        self.g = g
        self.b = b

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08
        self.vx *= 0.97
        self.vy *= 0.97
        self.life -= 1.0

    @property
    def is_dead(self):
        return self.life <= 0


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def update_physics():
    global psi

    # 1. Strang-splitting step for 2D NLS envelope
    psi_k = np.fft.fft2(psi) * disp_half
    psi = np.fft.ifft2(psi_k)

    mag2 = np.abs(psi)**2
    sat_mag2 = np.minimum(mag2, 9.0)
    psi = psi * np.exp(1j * dt * gamma * sat_mag2)

    psi_k = np.fft.fft2(psi) * (disp_half * filter_mask)
    psi = np.fft.ifft2(psi_k)


def render_sea_surface(frame_num):
    global psi, surf_pixels

    t = frame_num * 0.045
    envelope = np.abs(psi).astype(np.float32)

    # 2. Synthesize deep ocean swells with Stokes crest sharpening
    sea = np.zeros_like(X)
    for w in wave_components:
        phase = w["k"][0] * X + w["k"][1] * Y - w["w"] * t
        stokes = np.cos(phase) + 0.5 * w["steep"] * np.cos(2.0 * phase)
        sea += w["amp"] * stokes

    # Spatially modulate swells by NLS envelope (forming monumental rogue surges)
    elevation = sea * (0.55 + 0.55 * (envelope**1.35))

    # 3. 3D Surface Normals & Specular Illumination
    gx = (np.roll(elevation, -1, axis=1) - np.roll(elevation, 1, axis=1)) / (2.0 * dx)
    gy = (np.roll(elevation, -1, axis=0) - np.roll(elevation, 1, axis=0)) / (2.0 * dy)

    scale_bump = 0.85
    nx = -gx * scale_bump
    ny = -gy * scale_bump
    nz = np.ones_like(nx)
    norm = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-6
    nx /= norm
    ny /= norm
    nz /= norm

    # Key directional light (cool moonlight / distant starburst)
    lx, ly, lz = 0.52, -0.62, 0.58
    diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)

    # Blinn-Phong specular glints
    hx, hy, hz = lx / 1.6, ly / 1.6, (lz + 1.0) / 1.6
    hn = np.sqrt(hx**2 + hy**2 + hz**2)
    hx /= hn
    hy /= hn
    hz /= hn
    spec = np.clip(nx * hx + ny * hy + nz * hz, 0.0, 1.0) ** 24

    # Glancing-angle Fresnel rim reflection
    fresnel = np.clip((1.0 - nz)**3, 0.0, 1.0)

    # 4. Color Hierarchy: Abyss -> Sapphire -> Electric Cyan -> Sunlit Gold Spires
    # Abyssal midnight navy base
    r = np.full_like(elevation, 2.0)
    g = np.full_like(elevation, 5.0)
    b = np.full_like(elevation, 16.0)

    # Swells: Rich Indigo to Cobalt Sapphire (#124484)
    swell = np.clip((elevation + 1.4) / 3.2, 0.0, 1.0)**1.5
    r += swell * (10.0 + 22.0 * diffuse)
    g += swell * (38.0 + 46.0 * diffuse)
    b += swell * (112.0 + 64.0 * diffuse)

    # Wave Crests: Luminous Electric Cyan (#24d8e8)
    crest = np.clip((elevation - 1.2) / 1.8, 0.0, 1.0)**1.9
    r += crest * (28.0 + 65.0 * spec)
    g += crest * (195.0 + 60.0 * spec)
    b += crest * (232.0 + 23.0 * spec)

    # Spontaneous Rogue Wave Spires: Incandescent Gold (#ffe699) & Pure White Peak
    rogue_factor = np.clip((envelope - 1.6) / 1.3, 0.0, 1.0) * np.clip((elevation - 1.8) / 1.6, 0.0, 1.0)
    r += rogue_factor * (255.0 + 15.0 * spec)
    g += rogue_factor * (228.0 + 25.0 * spec)
    b += rogue_factor * (135.0 + 120.0 * spec)

    # Extreme summits reach pure blinding radiance
    peak = np.clip((elevation - 3.4) / 1.2, 0.0, 1.0)
    r += peak * 255.0
    g += peak * 255.0
    b += peak * 255.0

    # Liquid Fresnel sheen and specular caustic reflections
    r += fresnel * 22.0 + spec * 95.0 * crest
    g += fresnel * 80.0 + spec * 125.0 * crest
    b += fresnel * 138.0 + spec * 135.0 * crest

    surf_pixels[..., 0] = np.clip(r, 0, 255).astype(np.uint8)
    surf_pixels[..., 1] = np.clip(g, 0, 255).astype(np.uint8)
    surf_pixels[..., 2] = np.clip(b, 0, 255).astype(np.uint8)

    # 5. Foam and Spray Particle Spawning along Critical Surging Crests
    high_peaks = np.argwhere((elevation > 2.2) & (envelope > 1.4))
    if len(high_peaks) > 0 and len(particles) < MAX_PARTICLES:
        num_spawn = min(15, MAX_PARTICLES - len(particles))
        idx_choices = np.random.choice(len(high_peaks), size=num_spawn, replace=True)
        for idx in idx_choices:
            py_idx, px_idx = high_peaks[idx]
            cx = (px_idx / Nx) * py5.width + random.uniform(-5.0, 5.0)
            cy = (py_idx / Ny) * py5.height + random.uniform(-5.0, 5.0)

            # Velocity oriented along wave front normal + upward spray
            vx = gx[py_idx, px_idx] * -6.0 + random.uniform(0.5, 2.5)
            vy = gy[py_idx, px_idx] * -6.0 + random.uniform(-2.8, -0.5)
            life = random.uniform(16.0, 36.0)
            size = random.uniform(2.5, 5.0)

            # Sunlit gold sparks on rogue crests, crystalline cyan elsewhere
            if random.random() < 0.65:
                pr, pg, pb = 255, 238, 195
            else:
                pr, pg, pb = 175, 245, 255
            particles.append(FoamParticle(cx, cy, vx, vy, life, life, size, pr, pg, pb))


def draw():
    global particles

    # Advance physics
    update_physics()

    # Render surface
    render_sea_surface(py5.frame_count)

    # Draw sea image
    img = py5.create_image(Nx, Ny, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = surf_pixels
        img.update_np_pixels()
    else:
        r = surf_pixels[..., 0].astype(np.int32)
        g = surf_pixels[..., 1].astype(np.int32)
        b = surf_pixels[..., 2].astype(np.int32)
        a = surf_pixels[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()

    py5.image(img, 0, 0, py5.width, py5.height)

    # Render 4K Sea Foam and Spray Particles with Additive Glow
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in particles:
        p.update()
        if not p.is_dead:
            active_particles.append(p)
            alpha_ratio = p.life / p.max_life

            py5.no_stroke()
            # Outer soft atmospheric glow
            py5.fill(p.r, p.g, p.b, int(alpha_ratio * 65))
            py5.circle(p.x, p.y, p.size * 2.5 * alpha_ratio)
            # Bright sparkling droplet core
            py5.fill(p.r, p.g, p.b, int(alpha_ratio * 220))
            py5.circle(p.x, p.y, p.size * alpha_ratio)

    particles = active_particles
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Foam: {len(particles)}")

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


py5.run_sketch()
