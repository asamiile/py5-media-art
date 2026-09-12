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

# Spatial Simulation Grid (16:9 aspect ratio, vertical glass wall)
Nx, Ny = 640, 360
x_coords = np.linspace(-3.6, 3.6, Nx, dtype=np.float32)
# Row 0 is top of glass wall (Y = 3.6), Row Ny-1 is bulk reservoir base (Y = -0.2)
y_coords = np.linspace(3.60, -0.20, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[0] - y_coords[1])  # positive step for Cartesian gradient

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Directions for 3D Specular Liquid Glass Shading
light1 = np.array([0.45, -0.55, 0.70], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.60, 0.40, 0.68], dtype=np.float32)
light2 /= np.linalg.norm(light2)

# Lagrangian Particles: Climbing Film Tracers & Cascading Tear Droplets
MAX_PARTICLES = 1600
particles = []


class WineTearParticle:
    def __init__(self, px, py, ptype="climbing", vx=0.0, vy=0.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "climbing", "tear_drop", or "vapor"
        self.vx = vx
        self.vy = vy

        if ptype == "climbing":
            self.life = random.uniform(90.0, 240.0)
            self.radius = random.uniform(1.4, 2.8)
        elif ptype == "tear_drop":
            self.life = random.uniform(120.0, 280.0)
            self.radius = random.uniform(2.2, 4.4)
        else:  # alcohol vapor
            self.life = random.uniform(45.0, 110.0)
            self.radius = random.uniform(1.0, 2.2)

        self.max_life = self.life

    def update(self, flow_vx, flow_vy, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "climbing":
            # Pulled upward by solutal Marangoni film velocity
            self.px += flow_vx * 4.0 * dt
            self.py += flow_vy * 4.0 * dt
        elif self.ptype == "tear_drop":
            # Gravity-driven weeping tear sliding down along rivulet
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vy = min(13.5, self.vy + 0.16 * dt)
            self.vx *= 0.96
        else:
            # Evaporating alcohol vapor wisp diffusing into ambient air
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.95
            self.vy *= 0.95

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


def compute_solutal_marangoni_fields(frame):
    """
    Computes 2D solutal Marangoni hydrodynamics:
    - Meniscus climbing film pulled upward by d(gamma)/dY
    - Rim accumulation ridge with finger contact-line instability
    - Periodically weeping tears cascading down in vertical rivulets
    - 3D specular liquid chrome height map and Blinn-Phong reflections
    """
    t = frame / 60.0  # seconds

    # 1. Horizontal Rim Ridge with Contact-Line Finger Instability
    k_finger = 4.2
    finger_mode1 = 0.28 * np.sin(k_finger * X_grid - 0.4 * t)
    finger_mode2 = 0.16 * np.sin(2.0 * k_finger * X_grid + 0.8 * t + 1.2)
    finger_mode3 = 0.08 * np.cos(3.0 * k_finger * X_grid - 1.2 * t)
    Y_rim_base = 2.45 + finger_mode1 + finger_mode2 + finger_mode3

    # Upward climbing film region: smooth continuous transition
    dist_to_rim = Y_grid - Y_rim_base
    climbing_film = (
        np.exp(- (np.maximum(0.0, dist_to_rim)**2) / 0.08)
        * (1.0 / (1.0 + np.exp(-14.0 * (Y_grid - 0.25))))
        * np.clip(1.0 - (dist_to_rim / 2.6)**2, 0.0, 1.0)
    ).astype(np.float32)

    # Dual-layer rim crest: Sharp caustic core + soft luminous halo
    rim_sharp = np.exp(- (dist_to_rim**2) / (2.0 * (0.024**2)))
    rim_halo = np.exp(- (dist_to_rim**2) / (2.0 * (0.078**2)))

    # 2. Weeping Tears of Wine: Periodic pendant droplets sliding downward
    tear_x_positions = [-2.85, -1.95, -0.95, 0.05, 1.05, 2.05, 2.95]
    tears_sum = np.zeros_like(X_grid)
    rivulets_sum = np.zeros_like(X_grid)
    v_tear_field_y = np.zeros_like(X_grid)

    for i, x_pos in enumerate(tear_x_positions):
        period = 3.6 + 0.4 * np.sin(i * 1.5)
        phase = (t + i * 1.1) % period
        accumulate_time = 1.4

        if phase < accumulate_time:
            # Swelling pendant tear at the rim cusp
            swelling = phase / accumulate_time
            tear_y = Y_rim_base[0, int(np.clip((x_pos - x_coords[0]) / dx, 0, Nx - 1))] - 0.06 * swelling
            dist_sq = (X_grid - x_pos)**2 + (Y_grid - tear_y)**2
            tear_bead = np.exp(- dist_sq / (2.0 * (0.08 + 0.05 * swelling)**2)) * (0.6 + 0.6 * swelling)
            tears_sum += tear_bead
        else:
            # Falling tear sliding down towards bulk reservoir
            fall_progress = (phase - accumulate_time) / (period - accumulate_time)
            y_start = 2.45
            tear_y = y_start - (y_start - 0.18) * (fall_progress**1.6)

            # Teardrop shape: elongated vertically
            dx_tear = (X_grid - x_pos)
            dy_tear = (Y_grid - tear_y)
            teardrop_metric = dx_tear**2 / (0.075**2) + dy_tear**2 / (0.15**2)
            tear_bead = np.exp(- teardrop_metric / 2.0) * 1.35
            tears_sum += tear_bead

            # Smoothly tapered trailing wet rivulet
            vert_taper = (
                (1.0 / (1.0 + np.exp(16.0 * (Y_grid - y_start))))
                * (1.0 / (1.0 + np.exp(-16.0 * (Y_grid - tear_y))))
            )
            rivulet = (
                np.exp(- (dx_tear**2) / (2.0 * (0.035**2)))
                * vert_taper
                * (0.5 + 0.5 * np.exp(- np.abs(Y_grid - tear_y) * 1.2))
            )
            rivulets_sum += rivulet
            v_tear_field_y += rivulet * 4.5

    # 3. Bulk Liquid Reservoir at Bottom (Smooth Continuous Sigmoidal Meniscus)
    # Replaces previous hard rectangular cutoff with asymptotic capillary curve
    bulk_reservoir = (
        1.0 / (1.0 + np.exp(np.clip(14.0 * (Y_grid - 0.28), -20.0, 20.0)))
        + 0.25 * np.exp(- (np.maximum(0.0, Y_grid - 0.28)**2) / 0.12)
    ).astype(np.float32)

    # 4. Solutal Marangoni Surface Velocity Field
    v_marangoni_y = np.where(
        climbing_film > 0.08,
        2.5 * (1.0 - (np.clip(Y_grid, 0.0, 2.5) / 2.6)**2) + 0.4 * finger_mode1,
        0.0
    ) - v_tear_field_y

    v_marangoni_x = 0.6 * np.cos(k_finger * X_grid - 0.4 * t) * climbing_film

    # 5. 3D Surface Height Profile & Blinn-Phong Specular Reflections
    H_fluid = (
        bulk_reservoir * 0.90
        + climbing_film * 0.32
        + rim_sharp * 0.85
        + rim_halo * 0.35
        + tears_sum * 1.35
        + rivulets_sum * 0.42
    )

    grad_y, grad_x = np.gradient(H_fluid, dy, dx)
    norm_denom = np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    Nx_surf = -grad_x / norm_denom
    Ny_surf = -grad_y / norm_denom
    Nz_surf = 1.0 / norm_denom

    view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
    h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

    spec1 = np.maximum(0.0, Nx_surf * h1[0] + Ny_surf * h1[1] + Nz_surf * h1[2])**28 * np.clip(H_fluid, 0.0, 1.0)
    spec2 = np.maximum(0.0, Nx_surf * h2[0] + Ny_surf * h2[1] + Nz_surf * h2[2])**36 * np.clip(H_fluid, 0.0, 1.0)

    return (
        bulk_reservoir,
        climbing_film,
        rim_sharp,
        rim_halo,
        tears_sum,
        rivulets_sum,
        spec1,
        spec2,
        v_marangoni_x,
        v_marangoni_y,
        Y_rim_base,
        tear_x_positions,
        t,
    )


def render_wine_canvas(
    bulk_reservoir,
    climbing_film,
    rim_sharp,
    rim_halo,
    tears_sum,
    rivulets_sum,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Wine-Cellar Obsidian Void & Deep Cabernet Violet (#040108, #0c0312, #180620)
    - 30% Solutal Fluid Ribbon Burgundy, Ruby & Glacial Azure Meniscus (#991b1b, #e11d48, #0284c7)
    - 10% Incandescent Meniscus White-Gold & Alcohol Vapor Wisps (#ffffff, #fef08a, #fbbf24)
    """
    # 1. Background 60%: Wine-Cellar Obsidian Void & Glass Gradient
    r_bg = 4.0 + np.maximum(0.0, Y_grid) * 0.7
    g_bg = 1.0 + np.maximum(0.0, Y_grid) * 0.3
    b_bg = 8.0 + np.maximum(0.0, Y_grid) * 2.2

    # 2. Secondary 30%: Solutal Fluid Ribbon Burgundy & Ruby Red
    fluid_intensity = (
        bulk_reservoir * 1.15
        + climbing_film * 0.65
        + rivulets_sum * 0.85
        + tears_sum * 1.45
    )

    # Deep cabernet absorption gradient
    r_wine = np.clip(fluid_intensity * 165.0, 0.0, 235.0)
    g_wine = np.clip(fluid_intensity * 22.0, 0.0, 105.0)
    b_wine = np.clip(fluid_intensity * 42.0, 0.0, 135.0)

    # Glacial Azure alcohol refraction tint along thin climbing meniscus
    azure_rim = climbing_film * (1.0 - np.clip(bulk_reservoir * 1.2, 0.0, 1.0)) * 0.48
    r_wine += azure_rim * 12.0
    g_wine += azure_rim * 110.0
    b_wine += azure_rim * 195.0

    # 3. Accent 10%: Incandescent Meniscus Caustics, Specular Beads & Rim Crest
    # Specular reflections on liquid droplets and rivulets
    spec_r = spec1 * 245.0 + spec2 * 200.0
    spec_g = spec1 * 220.0 + spec2 * 225.0
    spec_b = spec1 * 135.0 + spec2 * 245.0

    # Refined Dual-Layer Rim Crest: Sharp caustic line + golden halo
    r_caustic = rim_sharp * 240.0 + rim_halo * 110.0
    g_caustic = rim_sharp * 225.0 + rim_halo * 80.0
    b_caustic = rim_sharp * 185.0 + rim_halo * 165.0

    # Final Additive Composite
    r_final = np.clip(r_bg + r_wine + spec_r + r_caustic, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_bg + g_wine + spec_g + g_caustic, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_bg + b_wine + spec_b + b_caustic, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute solutal Marangoni fields
    (
        bulk_reservoir,
        climbing_film,
        rim_sharp,
        rim_halo,
        tears_sum,
        rivulets_sum,
        spec1,
        spec2,
        v_marangoni_x,
        v_marangoni_y,
        Y_rim_base,
        tear_x_positions,
        t,
    ) = compute_solutal_marangoni_fields(py5.frame_count)

    # 2. Render pixel buffer
    render_wine_canvas(
        bulk_reservoir,
        climbing_film,
        rim_sharp,
        rim_halo,
        tears_sum,
        rivulets_sum,
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

    # 4. Lagrangian Particle Spawning
    x_min, x_max = x_coords[0], x_coords[-1]
    y_top, y_bottom = y_coords[0], y_coords[-1]

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(55, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.55:
                # Upward climbing film tracer
                x_spawn = random.uniform(x_min + 0.2, x_max - 0.2)
                y_spawn = random.uniform(0.28, 1.9)
                px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((y_top - y_spawn) / (y_top - y_bottom)) * py5.height
                particles.append(WineTearParticle(px, py_screen, ptype="climbing"))

            elif roll < 0.82:
                # Weeping tear droplet bead rolling down
                x_tear = random.choice(tear_x_positions) + random.gauss(0.0, 0.04)
                y_spawn = random.uniform(1.0, 2.38)
                px = ((x_tear - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((y_top - y_spawn) / (y_top - y_bottom)) * py5.height
                vy_init = random.uniform(4.2, 8.8)
                particles.append(WineTearParticle(px, py_screen, ptype="tear_drop", vy=vy_init))

            else:
                # Evaporating alcohol vapor wisp near rim
                x_spawn = random.uniform(x_min + 0.2, x_max - 0.2)
                y_spawn = random.uniform(2.35, 2.7)
                px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((y_top - y_spawn) / (y_top - y_bottom)) * py5.height
                vx = random.uniform(-0.8, 0.8)
                vy = random.uniform(-1.5, -0.4)
                particles.append(WineTearParticle(px, py_screen, ptype="vapor", vx=vx, vy=vy))

    # 5. Advect and Render Lagrangian Particles
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        norm_x = p.px / py5.width
        norm_y = p.py / py5.height

        gx = int(np.clip(norm_x * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip(norm_y * (Ny - 1), 0, Ny - 1))

        # Cartesian velocity to screen: +Y Cartesian is UPWARDS, screen +Y is DOWNWARDS
        vx_flow = float(v_marangoni_x[gy, gx])
        vy_flow = -float(v_marangoni_y[gy, gx])

        p.update(vx_flow, vy_flow)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.ptype == "tear_drop":
                # Weeping tear pearl: Glistening ruby and solar white-gold highlight
                cr, cg, cb = 255, 220, 160
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.45))
                py5.circle(p.px, p.py, p.radius * 3.6)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(cr, cg, cb, int(alpha * 0.88))
                py5.stroke_weight(2.0)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "climbing":
                # Upward climbing tracer: Glacial azure & rose crimson (#38bdf8, #f43f5e)
                cr, cg, cb = 245, 95, 125
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 2.8)
                py5.fill(255, 230, 240, alpha)
                py5.circle(p.px, p.py, p.radius * 0.85)
                py5.stroke(cr, cg, cb, int(alpha * 0.72))
                py5.stroke_weight(1.4)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            else:
                # Vapor wisp: Alcohol vapor violet & iridescent rose (#e879f9)
                cr, cg, cb = 225, 140, 245
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.22))
                py5.circle(p.px, p.py, p.radius * 3.0)
                py5.fill(255, 235, 255, int(alpha * 0.7))
                py5.circle(p.px, p.py, p.radius * 1.0)

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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Particles: {len(particles)}")

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
