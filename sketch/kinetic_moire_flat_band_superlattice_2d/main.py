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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Simulation Grid (16:9 aspect ratio, 800x450 grid)
Nx, Ny = 800, 450
x_coords = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_coords = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Hexagonal Basis Unit Vectors for Moiré Brillouin Zone
SQRT3_2 = float(np.sqrt(3.0) / 2.0)
u1 = np.array([0.0, 1.0], dtype=np.float32)
u2 = np.array([SQRT3_2, -0.5], dtype=np.float32)
u3 = np.array([-SQRT3_2, -0.5], dtype=np.float32)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Vectors for Specular Copper and Sapphire Shading
light1 = np.array([0.55, -0.60, 0.58], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.67], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Moiré Excitons, Domain-Wall Solitons & Tunneling Bursts
MAX_PARTICLES = 1600
particles = []


class MoireParticle:
    def __init__(self, px, py, ptype="exciton", vx=0.0, vy=0.0, life=120.0, radius=2.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "exciton", "soliton", "burst"
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.radius = radius

    def update(self, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "exciton":
            # Trapped inside AA quantum dot with quantum orbital precession
            self.px += (self.vx + random.uniform(-0.3, 0.3)) * dt
            self.py += (self.vy + random.uniform(-0.3, 0.3)) * dt
            self.vx *= 0.94
            self.vy *= 0.94
        elif self.ptype == "soliton":
            # Chiral drift along domain-wall boundaries
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.99
            self.vy *= 0.99
        elif self.ptype == "burst":
            # Fast interlayer tunneling radiation
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.95
            self.vy *= 0.95

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 120
            or self.px < -120
            or self.py > py5.height + 120
            or self.py < -120
        )


def compute_moire_fields(frame):
    """
    Computes 2D continuum model fields for twisted bilayer graphene:
    - Breathing Moiré wavevector k_M(t) and scale transformation
    - AA-stacking Local Density of States (LDOS) localization
    - Chiral AB/BA topological domain-wall network
    - 3D Blinn-Phong specular copper and sapphire normal shading
    """
    t = frame * 0.035
    t_norm = frame / TOTAL_FRAMES

    # 1. Dynamic Twist Angle & Moiré Wavevector Modulation
    # Smooth breathing modulation of the Moiré period
    theta_rad = 0.024 + 0.009 * np.sin(t * 1.6) + 0.004 * np.cos(t * 3.2)
    k_M = 2.0 * np.sin(theta_rad * 0.5) * 110.0  # Normalized Moiré wavevector magnitude

    # Slow macroscopic rotation of the Moiré lattice
    rot_angle = t * 0.12
    cos_r = np.cos(rot_angle)
    sin_r = np.sin(rot_angle)
    X_rot = X_grid * cos_r - Y_grid * sin_r
    Y_rot = X_grid * sin_r + Y_grid * cos_r

    # Wavevector projections: b_j . r
    b1_dot_r = k_M * (u1[0] * X_rot + u1[1] * Y_rot)
    b2_dot_r = k_M * (u2[0] * X_rot + u2[1] * Y_rot)
    b3_dot_r = k_M * (u3[0] * X_rot + u3[1] * Y_rot)

    # 2. Interlayer Tunneling Potential & AA-Stacking Constructive Interference
    cos1 = np.cos(b1_dot_r)
    cos2 = np.cos(b2_dot_r)
    cos3 = np.cos(b3_dot_r)
    tunneling_sum = cos1 + cos2 + cos3  # Values in [-1.5, 3.0]

    # AA-Stacking Local Density of States (LDOS) Peaks:
    # Sharp localization when all 3 wavevectors interfere constructively (tunneling_sum -> 3.0)
    aa_raw = np.maximum(0.0, (tunneling_sum - 0.4) / 2.6)**2.8
    ldos_aa = aa_raw * (1.0 + 0.35 * np.cos(t * 2.5 + X_rot * 1.5))

    # 3. Chiral AB / BA Topological Domain-Wall Network
    # Soliton boundaries occur where the phase differences cross zero
    dw_hex = (
        np.sin(b1_dot_r * 0.5)**2 * np.sin(b2_dot_r * 0.5)**2
        + np.sin(b2_dot_r * 0.5)**2 * np.sin(b3_dot_r * 0.5)**2
        + np.sin(b3_dot_r * 0.5)**2 * np.sin(b1_dot_r * 0.5)**2
    )
    # Smooth continuous domain wall lines connecting AA nodes
    domain_walls = (
        np.exp(- (dw_hex - 0.28)**2 / 0.035)
        * np.exp(- (X_grid**2 + Y_grid**2) / 12.0)
        * 1.2
    )

    # Secondary Moiré interference ripples
    moire_fringes = (
        np.cos(tunneling_sum * np.pi)**2
        * np.exp(- (X_grid**2 + Y_grid**2) / 9.0)
        * 0.45
    )

    # 4. Total Quantum Moiré Energy Density
    I_moire = (
        ldos_aa * 2.2
        + domain_walls * 1.3
        + moire_fringes * 0.55
    )

    # 5. 3D Blinn-Phong Specular Normal Shading
    H_surf = np.sqrt(np.clip(I_moire, 0.0, 4.0)) * 0.55
    grad_H_y, grad_H_x = np.gradient(H_surf, dy, dx)
    norm_denom = np.sqrt(grad_H_x**2 + grad_H_y**2 + 1.0)
    Nx_s = -grad_H_x / norm_denom
    Ny_s = -grad_H_y / norm_denom
    Nz_s = 1.0 / norm_denom

    # Light 1: Molten copper specular reflection
    spec1 = np.maximum(0.0, Nx_s * h1[0] + Ny_s * h1[1] + Nz_s * h1[2])**22
    # Light 2: Electric sapphire specular reflection
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Ny_s * h2[1] + Nz_s * h2[2])**16

    return (
        I_moire,
        ldos_aa,
        domain_walls,
        moire_fringes,
        spec1,
        spec2,
        k_M,
        rot_angle,
        t,
    )


def render_moire_canvas(
    I_moire,
    ldos_aa,
    domain_walls,
    moire_fringes,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer following 60-30-10 palette rules:
    - 60% Substrate Obsidian Void & Deep Carbon Indigo (#03050c, #080c1d)
    - 30% AA Flat-Band Molten Copper & Warm Rose Gold (#f97316, #fb923c, #ea580c)
    - 30% Domain-Wall Sapphire & Electric Iris Violet (#6366f1, #818cf8, #4338ca)
    - 10% Incandescent AA Quantum Dot Core Diamond-White & Solar Platinum (#ffffff, #fef08a)
    """
    # 1. Background 60%: Carbon substrate obsidian void with subtle radial depth
    r_bg = 2.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 4.0
    g_bg = 3.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 6.0
    b_bg = 10.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 20.0

    # 2. Dominant 60% (of foreground): Molten Copper & Warm Rose Gold (#f97316, #fb923c)
    copper_stream = np.clip(ldos_aa * 1.35, 0.0, 2.5)
    r_copper = copper_stream * 249.0
    g_copper = copper_stream * 115.0
    b_copper = copper_stream * 22.0

    # Secondary 30%: Domain-Wall Sapphire & Electric Iris Violet (#6366f1, #818cf8)
    sapphire_stream = np.clip(domain_walls * 1.45 + moire_fringes * 0.8, 0.0, 2.5)
    r_sapphire = sapphire_stream * 99.0
    g_sapphire = sapphire_stream * 102.0
    b_sapphire = sapphire_stream * 241.0

    # Specular liquid reflections (Light 1: copper gold, Light 2: sapphire)
    spec_r = spec1 * 255.0 + spec2 * 140.0
    spec_g = spec1 * 180.0 + spec2 * 160.0
    spec_b = spec1 * 60.0 + spec2 * 255.0

    # Combined Moiré foreground
    r_wave = r_copper * 0.65 + r_sapphire * 0.35 + spec_r * 0.40
    g_wave = g_copper * 0.60 + g_sapphire * 0.40 + spec_g * 0.40
    b_wave = b_copper * 0.30 + b_sapphire * 0.70 + spec_b * 0.40

    blend_factor = np.clip(I_moire * 0.85, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_factor) + r_wave * blend_factor
    g_mid = g_bg * (1.0 - blend_factor) + g_wave * blend_factor
    b_mid = b_bg * (1.0 - blend_factor) + b_wave * blend_factor

    # 3. Accent 10%: Incandescent AA Quantum Dot Core Diamond-White & Solar Platinum (#ffffff, #fef08a)
    dot_accent = np.clip((ldos_aa * ldos_aa) * 2.2 + spec1 * 0.50, 0.0, 2.5)
    r_accent = dot_accent * 255.0
    g_accent = dot_accent * 248.0
    b_accent = dot_accent * 210.0

    # Final pixel buffer compilation clamped to uint8
    r_final = np.clip(r_mid + r_accent, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_mid + g_accent, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_mid + b_accent, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute Moiré flat-band fields
    (
        I_moire,
        ldos_aa,
        domain_walls,
        moire_fringes,
        spec1,
        spec2,
        k_M,
        rot_angle,
        t,
    ) = compute_moire_fields(py5.frame_count)

    # 2. Render pixel buffer canvas
    render_moire_canvas(
        I_moire,
        ldos_aa,
        domain_walls,
        moire_fringes,
        spec1,
        spec2,
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

    # 4. Spawn Lagrangian Quantum Particles
    if len(particles) < MAX_PARTICLES:
        spawn_n = min(45, MAX_PARTICLES - len(particles))
        # Find high-intensity AA sites by probabilistic sampling
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.55:
                # Moiré Excitons: Swirling around AA quantum dots
                rand_x = random.uniform(x_coords[0], x_coords[-1])
                rand_y = random.uniform(y_coords[0], y_coords[-1])
                screen_px = (rand_x - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
                screen_py = (rand_y - y_coords[0]) / (y_coords[-1] - y_coords[0]) * py5.height

                ang = random.uniform(0.0, 2.0 * np.pi)
                spd = random.uniform(1.2, 3.2)
                particles.append(MoireParticle(
                    screen_px,
                    screen_py,
                    ptype="exciton",
                    vx=np.cos(ang) * spd,
                    vy=np.sin(ang) * spd,
                    life=random.uniform(50.0, 110.0),
                    radius=random.uniform(1.4, 2.8)
                ))

            elif roll < 0.85:
                # Domain-Wall Solitons: Gliding along sapphire boundaries
                rand_x = random.uniform(x_coords[0], x_coords[-1])
                rand_y = random.uniform(y_coords[0], y_coords[-1])
                screen_px = (rand_x - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
                screen_py = (rand_y - y_coords[0]) / (y_coords[-1] - y_coords[0]) * py5.height

                # Chiral direction aligned with hexagonal axes
                drift_ang = rot_angle + random.choice([0.0, np.pi / 3.0, 2.0 * np.pi / 3.0, np.pi])
                spd = random.uniform(2.5, 6.0)
                particles.append(MoireParticle(
                    screen_px,
                    screen_py,
                    ptype="soliton",
                    vx=np.cos(drift_ang) * spd,
                    vy=np.sin(drift_ang) * spd,
                    life=random.uniform(40.0, 90.0),
                    radius=random.uniform(1.6, 3.0)
                ))

            else:
                # Interlayer Tunneling Bursts: Incandescent sparks at nodal points
                center_offset = random.gauss(0.0, 300.0)
                screen_px = py5.width * 0.5 + center_offset
                screen_py = py5.height * 0.5 + random.gauss(0.0, 180.0)
                ang = random.uniform(0.0, 2.0 * np.pi)
                spd = random.uniform(4.0, 9.0)
                particles.append(MoireParticle(
                    screen_px,
                    screen_py,
                    ptype="burst",
                    vx=np.cos(ang) * spd,
                    vy=np.sin(ang) * spd,
                    life=random.uniform(25.0, 60.0),
                    radius=random.uniform(2.0, 3.6)
                ))

    # 5. Update and Draw Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        p.update()
        if not p.is_dead:
            active_particles.append(p)
            progress = p.life / p.max_life
            alpha = int(progress * 255)

            if p.ptype == "exciton":
                # Exciton: Molten copper and warm gold (#f97316, #fbbf24)
                py5.no_stroke()
                py5.fill(249, 115, 22, int(alpha * 0.38))
                py5.circle(p.px, p.py, p.radius * 3.4)
                py5.fill(254, 240, 138, alpha)
                py5.circle(p.px, p.py, p.radius * 0.95)
                py5.stroke(251, 146, 60, int(alpha * 0.75))
                py5.stroke_weight(1.3)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "soliton":
                # Soliton: Electric sapphire and iris violet (#6366f1, #818cf8)
                py5.no_stroke()
                py5.fill(99, 102, 241, int(alpha * 0.40))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(224, 231, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.9)
                py5.stroke(129, 140, 248, int(alpha * 0.80))
                py5.stroke_weight(1.5)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "burst":
                # Tunneling burst: Incandescent diamond-white and gold (#ffffff, #fef08a)
                py5.no_stroke()
                py5.fill(254, 240, 138, int(alpha * 0.45))
                py5.circle(p.px, p.py, p.radius * 3.6)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.1)
                py5.stroke(255, 255, 255, int(alpha * 0.85))
                py5.stroke_weight(1.7)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

    particles = active_particles

    # 6. Central Superlattice Core Nodes (breathing central quantum dots)
    cx, cy = py5.width * 0.5, py5.height * 0.5
    py5.no_stroke()
    # Central macro breathing aura
    py5.fill(249, 115, 22, 40)
    py5.circle(cx, cy, 80.0 + 20.0 * np.sin(t * 1.6))
    py5.fill(251, 146, 60, 90)
    py5.circle(cx, cy, 40.0 + 10.0 * np.sin(t * 1.6))
    py5.fill(255, 255, 255, 220)
    py5.circle(cx, cy, 14.0)

    py5.blend_mode(py5.BLEND)

    # 7. Fail-safe: Blank screen detection
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # 8. Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Particles: {len(particles)}")

    # 9. Finalize render on completion
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


if __name__ == "__main__":
    py5.run_sketch()
