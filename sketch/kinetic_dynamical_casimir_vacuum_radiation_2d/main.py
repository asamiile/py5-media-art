"""
kinetic_dynamical_casimir_vacuum_radiation_2d
Quantum electrodynamics simulation of the Dynamical Casimir Effect (DCE):
converting zero-point vacuum fluctuations into real, entangled photon pairs
via a relativistic oscillating boundary mirror.

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
CX = WIDTH / 2.0
CY = HEIGHT / 2.0

# Simulation Grid (800x450 for high-fidelity quantum wave dynamics)
Nx, Ny = 800, 450
x_grid = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_grid = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_mesh, Y_mesh = np.meshgrid(x_grid, y_grid)

# Physics parameters
C_LIGHT = 1.0           # Normalized light speed
OMEGA_0 = 4.4           # Primary parametric drive frequency
AMP_MIRROR = 0.14       # Relativistic mirror displacement amplitude
CAVITY_HALF_WIDTH = 3.65 # Fixed outer cavity boundary walls at x = +/- 3.65

# Specular lighting vectors for liquid chrome quantum field shading
light1 = np.array([0.55, -0.65, 0.52], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.60, 0.62], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Entangled Photon Pairs
MAX_PHOTONS = 600
photon_pos = np.zeros((MAX_PHOTONS, 2), dtype=np.float32)
photon_vel = np.zeros((MAX_PHOTONS, 2), dtype=np.float32)
photon_life = np.zeros(MAX_PHOTONS, dtype=np.float32)
photon_max_life = np.zeros(MAX_PHOTONS, dtype=np.float32)
photon_pair_id = np.zeros(MAX_PHOTONS, dtype=np.int32)
photon_phase = np.zeros(MAX_PHOTONS, dtype=np.float32)
photon_head = 0
pair_counter = 0


def spawn_entangled_pair(x_mirror, y_pos, mirror_vel):
    """Spawn a pair of entangled photons radiating symmetrically into left & right cavities."""
    global photon_head, pair_counter
    pair_counter += 1
    p_id = pair_counter
    
    speed = np.random.uniform(0.95, 1.10) * C_LIGHT * 0.038
    life = np.random.uniform(40.0, 75.0)
    
    # Left photon (radiating toward x < 0)
    idx_L = photon_head % MAX_PHOTONS
    photon_pos[idx_L, 0] = x_mirror - 0.06
    photon_pos[idx_L, 1] = y_pos + np.random.normal(0.0, 0.03)
    v_angle_L = np.pi + np.random.normal(0.0, 0.15)
    photon_vel[idx_L, 0] = np.cos(v_angle_L) * speed
    photon_vel[idx_L, 1] = np.sin(v_angle_L) * speed
    photon_life[idx_L] = life
    photon_max_life[idx_L] = life
    photon_pair_id[idx_L] = p_id
    photon_phase[idx_L] = np.random.uniform(0.0, 2.0 * np.pi)
    photon_head += 1
    
    # Right photon (radiating toward x > 0)
    idx_R = photon_head % MAX_PHOTONS
    photon_pos[idx_R, 0] = x_mirror + 0.06
    photon_pos[idx_R, 1] = y_pos + np.random.normal(0.0, 0.03)
    v_angle_R = np.random.normal(0.0, 0.15)
    photon_vel[idx_R, 0] = np.cos(v_angle_R) * speed
    photon_vel[idx_R, 1] = np.sin(v_angle_R) * speed
    photon_life[idx_R] = life
    photon_max_life[idx_R] = life
    photon_pair_id[idx_R] = p_id
    photon_phase[idx_R] = np.random.uniform(0.0, 2.0 * np.pi)
    photon_head += 1


def compute_dce_fields(frame_idx):
    """Compute 2D quantum vacuum radiation and smooth parabolic wavefronts."""
    t = frame_idx / float(FPS)
    
    # Mirror kinematics (relativistic parametric vibration)
    omega_mod = OMEGA_0 * (1.0 + 0.04 * np.sin(t * 0.7))
    x_mirror = AMP_MIRROR * np.sin(omega_mod * t * 2.0 * np.pi)
    v_mirror = AMP_MIRROR * omega_mod * 2.0 * np.pi * np.cos(omega_mod * t * 2.0 * np.pi)
    
    # Distance from oscillating mirror with smooth transverse curvature
    dx_m = X_mesh - x_mirror
    r_eff = np.sqrt(dx_m**2 + 0.10 * Y_mesh**2 + 1e-4)
    abs_dx = np.abs(dx_m)
    
    # Boundary cutoff: inside cavity bounds [-CAVITY_HALF_WIDTH, CAVITY_HALF_WIDTH]
    cavity_mask = np.clip(1.0 - (np.abs(X_mesh) / CAVITY_HALF_WIDTH)**12, 0.0, 1.0)
    
    # --- 1. Squeezed Vacuum Field Modes ---
    # Radiation wavenumber k_rad
    k_rad = 3.8
    phase = k_rad * r_eff - omega_mod * 0.5 * t * 2.0 * np.pi
    
    # Radiating wave crests with smooth exponential falloff
    wave_primary = np.cos(phase) * np.exp(-0.32 * r_eff)
    wave_harmonic = 0.28 * np.cos(2.0 * phase + 0.4) * np.exp(-0.45 * r_eff)
    
    # Transverse cavity waveguide envelope (smooth cosine)
    transverse_env = np.cos(np.pi * Y_mesh / 4.6)
    
    squeezed_field = (wave_primary + wave_harmonic) * transverse_env * cavity_mask
    
    # --- 2. Zero-Point Quantum Vacuum Foam (Soft organic undulating modes) ---
    qf_1 = np.sin(X_mesh * 2.2 + t * 1.6) * np.cos(Y_mesh * 2.4 - t * 1.3)
    qf_2 = np.cos(X_mesh * 3.4 - t * 2.2 + Y_mesh * 1.5)
    quantum_foam = (qf_1 * 0.65 + qf_2 * 0.35) * 0.18 * cavity_mask
    
    # --- 3. Relativistic Mirror Blade Luminescence ---
    mirror_glow = np.exp(-(dx_m / 0.075)**2) * (1.0 + 0.65 * np.abs(v_mirror))
    
    # --- 4. Blinn-Phong Specular Normal Shading ---
    # Normal mapping computed strictly from macro field + mirror blade (no high-frequency noise)
    spec_surface = squeezed_field * 0.75 + mirror_glow * 0.60
    grad_y, grad_x = np.gradient(spec_surface, 4.5 / Ny, 8.0 / Nx)
    grad_norm = np.sqrt(grad_x**2 + grad_y**2 + 0.08)
    
    normal_x = -grad_x / grad_norm
    normal_y = -grad_y / grad_norm
    normal_z = 1.0 / grad_norm
    
    spec1 = np.clip(normal_x * h1[0] + normal_y * h1[1] + normal_z * h1[2], 0.0, 1.0)**20
    spec2 = np.clip(normal_x * h2[0] + normal_y * h2[1] + normal_z * h2[2], 0.0, 1.0)**24
    
    # Glint mask: specular light reflects off wave crests and mirror blade
    glint_mask = np.clip(np.abs(squeezed_field) * 1.2 + mirror_glow * 0.8, 0.0, 1.0)
    spec1 *= glint_mask
    spec2 *= glint_mask
    
    return (
        squeezed_field,
        quantum_foam,
        mirror_glow,
        spec1,
        spec2,
        x_mirror,
        v_mirror,
        cavity_mask
    )


def render_casimir_buffer(squeezed_field, quantum_foam, mirror_glow, spec1, spec2, cavity_mask):
    """Synthesize the RGB pixel buffer adhering to 60-30-10 palette rules."""
    # 60% Quantum Vacuum Void & Deep Navy (#02040a, #050814, #0a1024)
    r_bg = 2.0 + np.exp(-(X_mesh**2 + Y_mesh**2) / 6.0) * 3.0
    g_bg = 4.0 + np.exp(-(X_mesh**2 + Y_mesh**2) / 6.0) * 5.0
    b_bg = 11.0 + np.exp(-(X_mesh**2 + Y_mesh**2) / 6.0) * 24.0
    
    # Subtle organic quantum foam shimmer
    q_foam_pos = np.maximum(0.0, quantum_foam)
    r_bg += q_foam_pos * 15.0
    g_bg += q_foam_pos * 35.0
    b_bg += q_foam_pos * 85.0
    
    # 30% Squeezed Radiation Wavefronts (Electric Cyan & Cosmic Violet-Indigo)
    # Sharp power curves ensure clean dark troughs between crests
    wave_pos = np.clip(squeezed_field * 1.7, 0.0, 2.5)**1.35
    wave_neg = np.clip(-squeezed_field * 1.7, 0.0, 2.5)**1.35
    
    # Positive quadrature wave crests: Radiant Electric Cyan (#06b6d4, #38bdf8)
    r_cyan = wave_pos * 14.0
    g_cyan = wave_pos * 180.0
    b_cyan = wave_pos * 235.0
    
    # Negative quadrature wave crests: Cosmic Indigo-Violet (#6366f1, #818cf8)
    r_violet = wave_neg * 105.0
    g_violet = wave_neg * 95.0
    b_violet = wave_neg * 245.0
    
    # Specular liquid chrome highlights (Light 1: ice platinum, Light 2: electric violet-rose)
    spec_r = spec1 * 160.0 + spec2 * 230.0
    spec_g = spec1 * 220.0 + spec2 * 130.0
    spec_b = spec1 * 255.0 + spec2 * 255.0
    
    # 10% Accent: Relativistic Mirror Core Diamond-White & Solar Platinum
    core_lum = mirror_glow * 255.0
    r_core = core_lum * 1.0
    g_core = core_lum * 0.96
    b_core = core_lum * 1.0
    
    # Combine layers into final buffer
    r_final = (r_bg + (r_cyan + r_violet) * 1.25 + spec_r * 0.40 + r_core * 0.85) * cavity_mask
    g_final = (g_bg + (g_cyan + g_violet) * 1.25 + spec_g * 0.40 + g_core * 0.85) * cavity_mask
    b_final = (b_bg + (b_cyan + b_violet) * 1.25 + spec_b * 0.40 + b_core * 0.85) * cavity_mask
    
    pixel_buffer[..., 1] = np.clip(r_final, 0.0, 255.0).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_final, 0.0, 255.0).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_final, 0.0, 255.0).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global photon_pos, photon_vel, photon_life
    frame = py5.frame_count
    
    # 1. Compute Dynamical Casimir quantum vacuum fields
    (
        squeezed_field,
        quantum_foam,
        mirror_glow,
        spec1,
        spec2,
        x_mirror,
        v_mirror,
        cavity_mask
    ) = compute_dce_fields(frame)
    
    # 2. Render pixel buffer
    render_casimir_buffer(squeezed_field, quantum_foam, mirror_glow, spec1, spec2, cavity_mask)
    
    # 3. Blit upscaled pixel buffer to 1920x1080 canvas
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

    py5.image(img, 0, 0, WIDTH, HEIGHT)
    
    # 4. Convert physical coordinates to screen space
    screen_x_mirror = (x_mirror - x_grid[0]) / (x_grid[-1] - x_grid[0]) * WIDTH
    
    # 5. Spawn Entangled Photon Pairs at high acceleration turning points
    accel = np.abs(x_mirror) / AMP_MIRROR  # Maximum acceleration near oscillation extrema
    if np.random.random() < (0.50 + 0.45 * accel):
        y_spawn = np.random.uniform(-1.75, 1.75)
        spawn_entangled_pair(x_mirror, y_spawn, v_mirror)
        
    # 6. Update and Render Lagrangian Entangled Photon Pairs
    active_mask = photon_life > 0.0
    active_indices = np.where(active_mask)[0]
    
    if len(active_indices) > 0:
        # Physical integration
        photon_pos[active_indices] += photon_vel[active_indices]
        photon_life[active_indices] -= 1.0
        
        # Convert to screen space
        sx = (photon_pos[active_indices, 0] - x_grid[0]) / (x_grid[-1] - x_grid[0]) * WIDTH
        sy = (photon_pos[active_indices, 1] - y_grid[0]) / (y_grid[-1] - y_grid[0]) * HEIGHT
        lifes = photon_life[active_indices]
        max_lifes = photon_max_life[active_indices]
        p_ids = photon_pair_id[active_indices]
        
        # Draw entanglement correlation links between paired photons
        unique_ids, counts = np.unique(p_ids, return_counts=True)
        paired_ids = unique_ids[counts == 2]
        
        py5.stroke_weight(1.2)
        for pid in paired_ids[:24]:
            pair_members = np.where(p_ids == pid)[0]
            m1, m2 = pair_members[0], pair_members[1]
            frac = min(lifes[m1] / max_lifes[m1], lifes[m2] / max_lifes[m2])
            link_alpha = int(frac * 85)
            if link_alpha > 5:
                # Magenta-violet quantum entanglement filament connecting twin partners
                py5.stroke(244, 114, 182, link_alpha)
                # Curved connection bowing slightly
                mid_x = (sx[m1] + sx[m2]) * 0.5
                mid_y = (sy[m1] + sy[m2]) * 0.5 + np.sin(frac * np.pi) * 8.0
                py5.no_fill()
                py5.begin_shape()
                py5.vertex(sx[m1], sy[m1])
                py5.quadratic_vertex(mid_x, mid_y, sx[m2], sy[m2])
                py5.end_shape()
                
        # Draw individual photon wavepackets with speed streaks
        for i in range(len(active_indices)):
            frac = lifes[i] / max_lifes[i]
            alpha = int(frac * 245)
            p_size = 2.8 + (1.0 - frac) * 3.5
            
            vx_scr = photon_vel[active_indices[i], 0] / (x_grid[-1] - x_grid[0]) * WIDTH
            vy_scr = photon_vel[active_indices[i], 1] / (y_grid[-1] - y_grid[0]) * HEIGHT
            
            # Velocity streak tail
            py5.stroke_weight(1.5)
            if vx_scr > 0:
                # Rightward photon: Electric Cyan
                py5.stroke(6, 182, 212, int(alpha * 0.7))
                py5.line(sx[i] - vx_scr * 4.0, sy[i] - vy_scr * 4.0, sx[i], sy[i])
                
                py5.no_stroke()
                py5.fill(6, 182, 212, int(alpha * 0.40))
                py5.circle(sx[i], sy[i], p_size * 2.8)
                py5.fill(165, 243, 252, alpha)
                py5.circle(sx[i], sy[i], p_size * 1.2)
            else:
                # Leftward photon: Cosmic Violet
                py5.stroke(139, 92, 246, int(alpha * 0.7))
                py5.line(sx[i] - vx_scr * 4.0, sy[i] - vy_scr * 4.0, sx[i], sy[i])
                
                py5.no_stroke()
                py5.fill(139, 92, 246, int(alpha * 0.40))
                py5.circle(sx[i], sy[i], p_size * 2.8)
                py5.fill(221, 214, 254, alpha)
                py5.circle(sx[i], sy[i], p_size * 1.2)
                
            # Incandescent core
            py5.fill(255, 255, 255, alpha)
            py5.circle(sx[i], sy[i], p_size * 0.6)
            
    # 7. Foreground Vector Accents: Relativistic Mirror Blade & Cavity Calipers
    # Mirror Blade at screen_x_mirror
    py5.no_fill()
    
    # Outer luminescence halo of the vibrating mirror
    py5.stroke(147, 197, 253, 55)
    py5.stroke_weight(14.0)
    py5.line(screen_x_mirror, 55, screen_x_mirror, HEIGHT - 55)
    
    py5.stroke(224, 231, 255, 120)
    py5.stroke_weight(5.0)
    py5.line(screen_x_mirror, 55, screen_x_mirror, HEIGHT - 55)
    
    # Razor-sharp incandescent diamond-white mirror blade core
    py5.stroke(255, 255, 255, 245)
    py5.stroke_weight(2.0)
    py5.line(screen_x_mirror, 55, screen_x_mirror, HEIGHT - 55)
    
    # Mirror mounting node calipers at top and bottom
    py5.no_stroke()
    py5.fill(255, 255, 255, 235)
    py5.circle(screen_x_mirror, 55, 10.0)
    py5.circle(screen_x_mirror, HEIGHT - 55, 10.0)
    
    # Fixed outer cavity walls at x = +/- CAVITY_HALF_WIDTH
    wall_left_x = (-CAVITY_HALF_WIDTH - x_grid[0]) / (x_grid[-1] - x_grid[0]) * WIDTH
    wall_right_x = (CAVITY_HALF_WIDTH - x_grid[0]) / (x_grid[-1] - x_grid[0]) * WIDTH
    
    py5.stroke(75, 85, 99, 130)
    py5.stroke_weight(2.0)
    py5.line(wall_left_x, 70, wall_left_x, HEIGHT - 70)
    py5.line(wall_right_x, 70, wall_right_x, HEIGHT - 70)
    
    # 8. Save Frame & Progress Monitoring
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
            
        # Save midpoint preview frame
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
