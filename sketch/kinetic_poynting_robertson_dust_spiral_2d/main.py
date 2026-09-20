"""
kinetic_poynting_robertson_dust_spiral_2d
Astrophysical kinetic simulation of Poynting-Robertson radiation drag,
circumstellar resonant dust trapping, and solar sublimation flashes.

1920x1080 @ 60fps, 900 frames (15 seconds).
"""

from pathlib import Path
import os
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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

WIDTH, HEIGHT = SIZE

# Coordinates & Physics parameters
CX = WIDTH / 2.0
CY = HEIGHT / 2.0
G_M = 1.6e5            # Central stellar gravitational parameter (G * M_star)
C_LIGHT = 2200.0        # Effective speed of light in simulation scaling
R_STAR = 38.0           # Physical radius of central star
R_SUB = 95.0            # Dust sublimation boundary radius
R_PLANET = 365.0        # Orbital radius of perturber protoplanet
M_PLANET = 420.0        # Perturber gravitational mass parameter
OMEGA_PLANET = float(np.sqrt(G_M / (R_PLANET**3)))  # Keplerian angular frequency

# Particle Swarm
N_PARTICLES = 7000
GRID_W = 480
GRID_H = 270

# Storage for particle swarm
# Pos (x, y), Vel (vx, vy), Beta (radiation pressure factor), Age, Sublimation state
p_pos = np.zeros((N_PARTICLES, 2), dtype=np.float32)
p_vel = np.zeros((N_PARTICLES, 2), dtype=np.float32)
p_beta = np.zeros(N_PARTICLES, dtype=np.float32)
p_temp = np.zeros(N_PARTICLES, dtype=np.float32)
p_phase = np.zeros(N_PARTICLES, dtype=np.float32)

# Sublimation flash particles (temporary spark bursts)
MAX_FLASHES = 600
flash_pos = np.zeros((MAX_FLASHES, 2), dtype=np.float32)
flash_vel = np.zeros((MAX_FLASHES, 2), dtype=np.float32)
flash_life = np.zeros(MAX_FLASHES, dtype=np.float32)
flash_max_life = np.zeros(MAX_FLASHES, dtype=np.float32)
flash_idx = 0

# Grid coordinates for optical density & Blinn-Phong surface sheen
gx = np.linspace(-WIDTH / 2.0, WIDTH / 2.0, GRID_W, dtype=np.float32)
gy = np.linspace(-HEIGHT / 2.0, HEIGHT / 2.0, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(gx, gy)
R_GRID = np.sqrt(GX**2 + GY**2) + 1e-4

# Precompute optical sheen base arrays
DENSITY_BUFFER = np.zeros((GRID_H, GRID_W), dtype=np.float32)
pixel_buffer = np.zeros((GRID_H, GRID_W, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255


def spawn_particles(indices, initial=False):
    """Spawn or replenish dust grains in circumstellar orbits."""
    n = len(indices)
    if n == 0:
        return
    
    # Outer dust ring injection belt: 420px to 880px
    if initial:
        r = np.random.uniform(R_SUB * 1.05, 880.0, n).astype(np.float32)
    else:
        r = np.random.uniform(550.0, 890.0, n).astype(np.float32)
        
    theta = np.random.uniform(0.0, 2.0 * np.pi, n).astype(np.float32)
    
    # Position
    p_pos[indices, 0] = r * np.cos(theta)
    p_pos[indices, 1] = r * np.sin(theta)
    
    # Grain radiation pressure ratio beta: F_rad / F_grav (0.008 to 0.042)
    p_beta[indices] = np.random.uniform(0.008, 0.042, n).astype(np.float32)
    
    # Circular Keplerian velocity adjusted for radiation pressure: v = sqrt(G M (1 - beta) / r)
    v_circ = np.sqrt(G_M * (1.0 - p_beta[indices]) / r)
    # Add small dispersion / eccentricity
    v_rad = np.random.normal(0.0, 0.02 * v_circ, n).astype(np.float32)
    v_tan = v_circ * (1.0 + np.random.normal(0.0, 0.02, n).astype(np.float32))
    
    # Counter-clockwise orbital velocity
    p_vel[indices, 0] = -v_tan * np.sin(theta) + v_rad * np.cos(theta)
    p_vel[indices, 1] = v_tan * np.cos(theta) + v_rad * np.sin(theta)
    
    p_temp[indices] = np.clip((350.0 / r)**0.5, 0.2, 1.0)
    p_phase[indices] = np.random.uniform(0.0, 2.0 * np.pi, n).astype(np.float32)


def add_sublimation_flash(x, y, vx, vy):
    """Trigger an incandescent sublimation flash burst when a grain vaporizes."""
    global flash_idx
    count = np.random.randint(4, 9)
    for _ in range(count):
        idx = flash_idx % MAX_FLASHES
        flash_pos[idx, 0] = x + np.random.normal(0.0, 2.0)
        flash_pos[idx, 1] = y + np.random.normal(0.0, 2.0)
        
        # Outward explosive repulsion + stellar wind
        angle = np.random.uniform(0.0, 2.0 * np.pi)
        speed = np.random.uniform(1.5, 5.0)
        flash_vel[idx, 0] = vx * 0.3 + np.cos(angle) * speed
        flash_vel[idx, 1] = vy * 0.3 + np.sin(angle) * speed
        
        life = np.random.uniform(12.0, 28.0)
        flash_life[idx] = life
        flash_max_life[idx] = life
        flash_idx += 1


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize all particles
    spawn_particles(np.arange(N_PARTICLES), initial=True)


def draw_frame():
    frame = py5.frame_count
    t_sec = frame / float(FPS)
    
    # =========================================================================
    # 1. ORBITAL MECHANICS & POYNTING-ROBERTSON NUMERICAL INTEGRATION
    # =========================================================================
    # Planet position and velocity
    theta_planet = OMEGA_PLANET * frame * 0.55  # Harmonically timed
    planet_x = R_PLANET * np.cos(theta_planet)
    planet_y = R_PLANET * np.sin(theta_planet)
    
    # Sub-stepping for smooth symplectic integration
    SUBSTEPS = 2
    dt = 1.0 / SUBSTEPS
    
    for _ in range(SUBSTEPS):
        px = p_pos[:, 0]
        py_ = p_pos[:, 1]
        vx = p_vel[:, 0]
        vy = p_vel[:, 1]
        
        # Radius to central star
        r_sq = px * px + py_ * py_ + 1e-4
        r = np.sqrt(r_sq)
        
        # Central star gravity (effective: G M * (1 - beta))
        eff_gm = G_M * (1.0 - p_beta)
        inv_r3 = 1.0 / (r * r_sq)
        ax = -eff_gm * px * inv_r3
        ay = -eff_gm * py_ * inv_r3
        
        # Protoplanet gravitational perturbation (softened potential)
        dx_p = px - planet_x
        dy_p = py_ - planet_y
        dist_p_sq = dx_p * dx_p + dy_p * dy_p + 450.0  # softening epsilon^2
        inv_dist_p3 = M_PLANET / (dist_p_sq * np.sqrt(dist_p_sq))
        ax -= dx_p * inv_dist_p3
        ay -= dy_p * inv_dist_p3
        
        # Poynting-Robertson Radiation Drag:
        # F_PR = - (beta * G_M / (c * r^2)) * [ v + (v . r_hat) * r_hat ]
        v_dot_r = (vx * px + vy * py_) / r
        inv_c = 1.0 / C_LIGHT
        pr_coeff = (p_beta * G_M * inv_c) / (r_sq + 100.0)
        
        drag_x = -pr_coeff * (vx + v_dot_r * (px / r))
        drag_y = -pr_coeff * (vy + v_dot_r * (py_ / r))
        
        ax += drag_x
        ay += drag_y
        
        # Velocity Verlet / Leapfrog step
        p_vel[:, 0] += ax * dt
        p_vel[:, 1] += ay * dt
        p_pos[:, 0] += p_vel[:, 0] * dt
        p_pos[:, 1] += p_vel[:, 1] * dt
    
    # Current distances
    r_current = np.sqrt(p_pos[:, 0]**2 + p_pos[:, 1]**2)
    
    # Check for dust sublimation (r < R_SUB) or ejections (r > 980)
    sublimated = np.where(r_current < R_SUB)[0]
    for idx in sublimated[:30]:  # Cap flash creations per frame
        add_sublimation_flash(p_pos[idx, 0], p_pos[idx, 1], p_vel[idx, 0], p_vel[idx, 1])
        
    dead = np.where((r_current < R_SUB) | (r_current > 980.0) | np.isnan(r_current))[0]
    if len(dead) > 0:
        spawn_particles(dead, initial=False)
        
    # Update temperatures based on distance: T ~ (R_SUB / r)^0.65
    p_temp[:] = np.clip((R_SUB / (r_current + 1e-4))**0.65, 0.05, 1.0)
    
    # =========================================================================
    # 2. ZODIACAL OPTICAL DENSITY & SPECULAR SHEEN SURFACE
    # =========================================================================
    valid = np.where(r_current > R_STAR * 1.2)[0]
    xs = p_pos[valid, 0]
    ys = p_pos[valid, 1]
    
    # Normalize coordinates to grid indices
    ix = np.clip(((xs + WIDTH / 2.0) / WIDTH * (GRID_W - 1)).astype(np.int32), 0, GRID_W - 1)
    iy = np.clip(((ys + HEIGHT / 2.0) / HEIGHT * (GRID_H - 1)).astype(np.int32), 0, GRID_H - 1)
    
    # Accumulate optical density
    DENSITY_BUFFER.fill(0.0)
    np.add.at(DENSITY_BUFFER, (iy, ix), 1.0)
    
    # Smooth density with spatial box filter
    d_smooth = (
        DENSITY_BUFFER +
        np.roll(DENSITY_BUFFER, 1, axis=0) + np.roll(DENSITY_BUFFER, -1, axis=0) +
        np.roll(DENSITY_BUFFER, 1, axis=1) + np.roll(DENSITY_BUFFER, -1, axis=1) +
        np.roll(np.roll(DENSITY_BUFFER, 1, axis=0), 1, axis=1) +
        np.roll(np.roll(DENSITY_BUFFER, -1, axis=0), -1, axis=1) +
        np.roll(np.roll(DENSITY_BUFFER, 1, axis=0), -1, axis=1) +
        np.roll(np.roll(DENSITY_BUFFER, -1, axis=0), 1, axis=1)
    ) / 9.0
    
    # Compute normal gradients of density for Blinn-Phong specular lighting
    grad_y, grad_x = np.gradient(d_smooth)
    norm_len = np.sqrt(grad_x**2 + grad_y**2 + 0.1)
    nx = grad_x / norm_len
    ny = grad_y / norm_len
    
    # Stellar ray vector from origin
    ray_x = GX / R_GRID
    ray_y = GY / R_GRID
    
    # Forward Mie scattering alignment
    dot_ray = np.clip(ray_x * nx + ray_y * ny, 0.0, 1.0)
    specular_sheen = dot_ray**8 * np.clip(d_smooth / 4.0, 0.0, 1.0)
    
    # Radial falloff of stellar light
    stellar_flux = 120.0 / (R_GRID + 70.0)
    zodiacal_diffuse = np.clip(d_smooth * 0.12 * stellar_flux, 0.0, 1.0)
    
    # Color synthesis on downsampled grid:
    # Deep obsidian-indigo vacuum (60%)
    # Copper & amber zodiacal sheen (30%)
    # Specular platinum caustics (10%)
    bg_r = (0.015 + zodiacal_diffuse * 0.85 + specular_sheen * 0.95)
    bg_g = (0.025 + zodiacal_diffuse * 0.45 + specular_sheen * 0.85)
    bg_b = (0.060 + zodiacal_diffuse * 0.15 + specular_sheen * 0.70)
    
    # Add subtle central stellar glow
    star_glow = np.exp(-R_GRID / 180.0) * 0.55
    bg_r += star_glow * 1.0
    bg_g += star_glow * 0.82
    bg_b += star_glow * 0.45
    
    pixel_buffer[..., 1] = np.clip(bg_r * 255.0, 0.0, 255.0).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(bg_g * 255.0, 0.0, 255.0).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(bg_b * 255.0, 0.0, 255.0).astype(np.uint8)
    
    # Blit upscaled pixel buffer to canvas
    bg_img = py5.create_image(GRID_W, GRID_H, py5.ARGB)
    bg_img.load_np_pixels()
    if bg_img.np_pixels is not None:
        bg_img.np_pixels[:] = pixel_buffer
        bg_img.update_np_pixels()
    else:
        a = pixel_buffer[..., 0].astype(np.int32)
        r = pixel_buffer[..., 1].astype(np.int32)
        g = pixel_buffer[..., 2].astype(np.int32)
        b = pixel_buffer[..., 3].astype(np.int32)
        bg_img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        bg_img.update_pixels()

    py5.image(bg_img, 0, 0, WIDTH, HEIGHT)
    
    # =========================================================================
    # 3. FOREGROUND VECTOR RENDERING: ORBITS, DUST STREAMLINES, RESIDUAL TRACERS
    # =========================================================================
    py5.push_matrix()
    py5.translate(CX, CY)
    
    # --- Mean Motion Resonance (MMR) Guides & Horseshoe Boundaries ---
    py5.no_fill()
    res_radii = [
        (R_PLANET * (2.0)**(2.0/3.0), 35, 75, 140, 40),      # 2:1 outer resonance
        (R_PLANET * (1.5)**(2.0/3.0), 45, 110, 180, 50),     # 3:2 outer resonance
        (R_PLANET * (4.0/3.0)**(2.0/3.0), 60, 140, 210, 60), # 4:3 outer resonance
        (R_PLANET, 240, 160, 50, 70),                         # Protoplanet orbit
        (R_SUB, 120, 220, 255, 90)                            # Sublimation line
    ]
    
    for r_res, cr, cg, cb, ca in res_radii:
        py5.stroke(cr, cg, cb, ca)
        py5.stroke_weight(1.0)
        py5.circle(0, 0, r_res * 2.0)
        
    # --- Protoplanet Gravitational Wake Ribbon ---
    wake_angles = np.linspace(0.0, -1.8, 40)
    py5.no_fill()
    py5.begin_shape()
    for w_a in wake_angles:
        ang = theta_planet + w_a
        rad = R_PLANET + np.sin(w_a * 3.0) * 14.0 * np.exp(w_a * 0.8)
        alpha = int(np.clip((1.0 + w_a / 1.8) * 120.0, 0, 120))
        py5.stroke(255, 190, 80, alpha)
        py5.stroke_weight(2.0)
        py5.vertex(rad * np.cos(ang), rad * np.sin(ang))
    py5.end_shape()
    
    # --- Dust Grain Swarm with Speed Streaks ---
    py5.stroke_cap(py5.ROUND)
    
    px = p_pos[:, 0]
    py_ = p_pos[:, 1]
    vx = p_vel[:, 0]
    vy = p_vel[:, 1]
    temps = p_temp
    
    for i in range(0, N_PARTICLES):
        t = temps[i]
        tail_x = px[i] - vx[i] * 1.8
        tail_y = py_[i] - vy[i] * 1.8
        
        if t < 0.25:
            # Outer cold dust: subtle bronze / sienna
            alpha = int(120 * (t / 0.25) + 30)
            py5.stroke(180, 95, 30, alpha)
            py5.stroke_weight(1.0)
        elif t < 0.60:
            # Resonant band dust: radiant amber / gold
            norm_t = (t - 0.25) / 0.35
            r_c = int(210 + 40 * norm_t)
            g_c = int(120 + 80 * norm_t)
            b_c = int(30 + 40 * norm_t)
            alpha = int(160 + 70 * norm_t)
            py5.stroke(r_c, g_c, b_c, alpha)
            py5.stroke_weight(1.3)
        else:
            # Inner hot dust nearing sublimation: incandescent white-gold
            norm_t = (t - 0.60) / 0.40
            r_c = int(250 + 5 * norm_t)
            g_c = int(220 + 35 * norm_t)
            b_c = int(120 + 135 * norm_t)
            alpha = int(210 + 45 * norm_t)
            py5.stroke(r_c, g_c, b_c, alpha)
            py5.stroke_weight(1.8)
            
        py5.line(tail_x, tail_y, px[i], py_[i])
        
    # --- Sublimation Spark Bursts ---
    active_flashes = np.where(flash_life > 0.0)[0]
    if len(active_flashes) > 0:
        for idx in active_flashes:
            flash_pos[idx, 0] += flash_vel[idx, 0]
            flash_pos[idx, 1] += flash_vel[idx, 1]
            flash_life[idx] -= 1.0
            
            life_frac = flash_life[idx] / flash_max_life[idx]
            fx = flash_pos[idx, 0]
            fy = flash_pos[idx, 1]
            
            alpha = int(life_frac * 255)
            spark_size = 2.0 + (1.0 - life_frac) * 4.0
            
            py5.no_stroke()
            py5.fill(80, 230, 255, alpha)
            py5.circle(fx, fy, spark_size * 2.2)
            
            py5.fill(255, 255, 255, int(alpha * 0.9))
            py5.circle(fx, fy, spark_size)
            
    # --- Protoplanet Rendering ---
    py5.no_stroke()
    py5.fill(255, 180, 60, 45)
    py5.circle(planet_x, planet_y, 48.0)
    py5.fill(255, 220, 140, 90)
    py5.circle(planet_x, planet_y, 24.0)
    py5.fill(255, 250, 210, 255)
    py5.circle(planet_x, planet_y, 9.0)
    
    # --- Sublimation Boundary Glow Ring ---
    py5.no_fill()
    py5.stroke_weight(2.5)
    py5.stroke(255, 235, 180, 180)
    py5.circle(0, 0, R_SUB * 2.0)
    
    py5.stroke_weight(5.0)
    py5.stroke(255, 170, 60, 60)
    py5.circle(0, 0, (R_SUB - 4.0) * 2.0)
    
    # --- Central Star: Pulsating Solar Furnace & Coronal Loops ---
    n_rays = 48
    ray_phase = t_sec * 1.4
    for r_idx in range(n_rays):
        ang = r_idx * (2.0 * np.pi / n_rays) + ray_phase * 0.15
        length = R_STAR * (1.6 + 0.4 * np.sin(ang * 5.0 - ray_phase * 2.0))
        py5.stroke(255, 190, 80, 55)
        py5.stroke_weight(1.5)
        py5.line(R_STAR * 0.9 * np.cos(ang), R_STAR * 0.9 * np.sin(ang),
                 length * np.cos(ang), length * np.sin(ang))
                 
    # Magnetic prominence loops
    n_prominences = 6
    for p_idx in range(n_prominences):
        base_ang = p_idx * (2.0 * np.pi / n_prominences) + t_sec * 0.3
        loop_span = 0.35
        p_peak = R_STAR * (1.5 + 0.3 * np.sin(base_ang * 2.0 + t_sec))
        
        py5.no_fill()
        py5.stroke(255, 100, 30, 140)
        py5.stroke_weight(2.0)
        py5.begin_shape()
        for step_i in np.linspace(0, 1, 15):
            curr_ang = base_ang + (step_i - 0.5) * loop_span
            curr_r = R_STAR + np.sin(step_i * np.pi) * (p_peak - R_STAR)
            py5.vertex(curr_r * np.cos(curr_ang), curr_r * np.sin(curr_ang))
        py5.end_shape()
        
    # Concentric glowing solar layers
    py5.no_stroke()
    py5.fill(255, 160, 40, 40)
    py5.circle(0, 0, R_STAR * 3.8)
    py5.fill(255, 200, 80, 80)
    py5.circle(0, 0, R_STAR * 2.8)
    py5.fill(255, 235, 140, 160)
    py5.circle(0, 0, R_STAR * 2.2)
    py5.fill(255, 255, 240, 255)
    py5.circle(0, 0, R_STAR * 1.7)
    py5.fill(255, 255, 255, 255)
    py5.circle(0, 0, R_STAR * 1.1)
    
    py5.pop_matrix()
    
    # =========================================================================
    # 4. SAVE FRAME & PROGRESS REPORT
    # =========================================================================
    frame_path = FRAMES_DIR / f"frame-{frame:04d}.png"
    py5.save_frame(str(frame_path))
    
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame * 100.0 / TOTAL_FRAMES:.1f}%)")
        
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print("\n[Render Complete] Compiling H.264 video with FFmpeg...")
        mp4_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
        output_mp4 = SKETCH_DIR / "output.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            str(mp4_path)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"[Video Compiled] Master MP4 saved: {mp4_path}")
            shutil.copyfile(mp4_path, output_mp4)
            print(f"[Video Copied] Duplicated to: {output_mp4}")
        except subprocess.CalledProcessError as e:
            print(f"[FFmpeg Error] Failed to encode video: {e}")
            sys.exit(1)
            
        # Save midpoint preview frame (frame 450)
        midpoint_frame = FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png"
        if midpoint_frame.exists():
            shutil.copyfile(midpoint_frame, SKETCH_DIR / PREVIEW_FILENAME)
            print(f"[Preview Saved] Saved preview image: {SKETCH_DIR / PREVIEW_FILENAME}")
        else:
            last_frame = FRAMES_DIR / f"frame-{TOTAL_FRAMES:04d}.png"
            if last_frame.exists():
                shutil.copyfile(last_frame, SKETCH_DIR / PREVIEW_FILENAME)
                print(f"[Preview Saved] Saved fallback preview image: {SKETCH_DIR / PREVIEW_FILENAME}")
                
        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.\n")
            
        # Terminate process safely
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
