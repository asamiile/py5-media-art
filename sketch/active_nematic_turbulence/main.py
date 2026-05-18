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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15 seconds is perfect for developing turbulent patterns
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
N = 128  # Grid resolution
alpha = -2.5  # Extensile active stress coefficient (drives instability)
lambda_screen = 6.0  # Hydrodynamic screening length in grid cells
K_elastic = 0.04  # Frank elastic constant (diffusion)
beta_align = 0.8  # Flow alignment parameter
dt = 0.1  # Physics time step
dt_particles = 0.8  # Particle movement scaling

# Grid Setup
kx = np.fft.fftfreq(N) * 2 * np.pi
ky = np.fft.fftfreq(N) * 2 * np.pi
KX, KY = np.meshgrid(kx, ky)
K2 = KX**2 + KY**2
K_inv = np.zeros_like(K2)
K_inv[K2 > 0] = 1.0 / K2[K2 > 0]

# Pre-calculate screened Stokes filter denominator
filter_denom = 1.0 + (lambda_screen * 2.0 * np.pi / N)**2 * K2

# Allocate Simulation Fields
# We evolve Q-tensor components Q1 = cos(2*theta), Q2 = sin(2*theta)
# to avoid phase wrapping and singular derivatives.
Q1 = np.zeros((N, N))
Q2 = np.zeros((N, N))
ux = np.zeros((N, N))
uy = np.zeros((N, N))

# Particles
NUM_PARTICLES = 120000
particles = np.zeros((NUM_PARTICLES, 2))
particle_bins = np.zeros(NUM_PARTICLES, dtype=np.int32)

# Color Palette (Midnight Prussian Blue, Luminous Teal, Amethyst Violet, Sun-Gold, Hot Pink)
COLOR_BACKGROUND = (5, 8, 19)
COLOR_TEAL_LIGHT = (30, 213, 217, 35)   # Bin 0
COLOR_TEAL_DARK = (11, 141, 168, 35)    # Bin 1
COLOR_AMETHYST = (120, 30, 184, 25)     # Bin 2


def dx(A):
    """Central finite difference in x with periodic boundaries."""
    return (np.roll(A, -1, axis=1) - np.roll(A, 1, axis=1)) / 2.0


def dy(A):
    """Central finite difference in y with periodic boundaries."""
    return (np.roll(A, -1, axis=0) - np.roll(A, 1, axis=0)) / 2.0


def laplacian(A):
    """5-point discrete Laplacian with periodic boundaries."""
    return np.roll(A, -1, axis=1) + np.roll(A, 1, axis=1) + np.roll(A, -1, axis=0) + np.roll(A, 1, axis=0) - 4.0 * A


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Q-tensor with low-pass filtered random noise for smooth initial domains
    r1 = np.random.uniform(-1.0, 1.0, (N, N))
    r2 = np.random.uniform(-1.0, 1.0, (N, N))
    
    # Smooth them via FFT low pass
    smooth_kernel = 1.0 / (1.0 + 4.0 * K2)
    Q1_init = np.real(np.fft.ifft2(np.fft.fft2(r1) * smooth_kernel))
    Q2_init = np.real(np.fft.ifft2(np.fft.fft2(r2) * smooth_kernel))
    
    # Normalize Q-tensor
    norm = np.sqrt(Q1_init**2 + Q2_init**2)
    norm[norm == 0] = 1.0
    global Q1, Q2
    Q1 = Q1_init / norm
    Q2 = Q2_init / norm
    
    # Initialize Particles
    particles[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    
    # Assign persistent color bins (0: Light Teal, 1: Dark Teal, 2: Amethyst)
    global particle_bins
    particle_bins = np.random.choice([0, 1, 2], size=NUM_PARTICLES, p=[0.4, 0.35, 0.25])
    
    py5.background(*COLOR_BACKGROUND)


def draw():
    global Q1, Q2, ux, uy, particles
    
    # 1. Physics Step: Active Nematodynamics
    # Active force density: f = alpha * div(Q)
    # Since Q = [[Q1, Q2], [Q2, -Q1]], div(Q)_x = dx(Q1) + dy(Q2), div(Q)_y = dx(Q2) - dy(Q1)
    fx = alpha * (dx(Q1) + dy(Q2))
    fy = alpha * (dx(Q2) - dy(Q1))
    
    # Solve screened Stokes equation via FFT
    hat_fx = np.fft.fft2(fx)
    hat_fy = np.fft.fft2(fy)
    
    k_dot_f = KX * hat_fx + KY * hat_fy
    proj_x = hat_fx - KX * k_dot_f * K_inv
    proj_y = hat_fy - KY * k_dot_f * K_inv
    
    hat_ux = proj_x / filter_denom
    hat_uy = proj_y / filter_denom
    
    # Remove zero-mode drift
    hat_ux[0, 0] = 0.0
    hat_uy[0, 0] = 0.0
    
    ux = np.real(np.fft.ifft2(hat_ux))
    uy = np.real(np.fft.ifft2(hat_uy))
    
    # Vorticity & Shear Strain components
    omega = dx(uy) - dy(ux)
    Dxx = dx(ux)
    Dxy = 0.5 * (dx(uy) + dy(ux))
    
    # Director rotation rate due to fluid flow
    S_rot = 0.5 * omega + beta_align * (Dxy * Q1 - Dxx * Q2)
    
    # Q-tensor Evolution (Advection + Elastic Relaxation + Flow Rotation)
    Q1_adv = -(ux * dx(Q1) + uy * dy(Q1))
    Q2_adv = -(ux * dx(Q2) + uy * dy(Q2))
    
    Q1_diff = K_elastic * laplacian(Q1)
    Q2_diff = K_elastic * laplacian(Q2)
    
    Q1_rot = -2.0 * S_rot * Q2
    Q2_rot = 2.0 * S_rot * Q1
    
    # Update
    Q1 += dt * (Q1_adv + Q1_diff + Q1_rot)
    Q2 += dt * (Q2_adv + Q2_diff + Q2_rot)
    
    # Normalize Q-tensor to keep order parameter S=1
    norm = np.sqrt(Q1**2 + Q2**2)
    norm[norm == 0] = 1.0
    Q1 /= norm
    Q2 /= norm
    
    # Reconstruct Director Angle for particles and defect analysis
    theta = 0.5 * np.arctan2(Q2, Q1)
    
    # 2. Particle Movement & Advection
    px_grid = (particles[:, 0] / py5.width * N) % N
    py_grid = (particles[:, 1] / py5.height * N) % N
    
    x0 = np.floor(px_grid).astype(np.int32)
    y0 = np.floor(py_grid).astype(np.int32)
    x1 = (x0 + 1) % N
    y1 = (y0 + 1) % N
    
    xd = px_grid - x0
    yd = py_grid - y0
    
    # Interpolate Velocity Field at particle positions
    vpx = (ux[y0, x0] * (1 - xd) * (1 - yd) +
           ux[y0, x1] * xd * (1 - yd) +
           ux[y1, x0] * (1 - xd) * yd +
           ux[y1, x1] * xd * yd)
    vpy = (uy[y0, x0] * (1 - xd) * (1 - yd) +
           uy[y0, x1] * xd * (1 - yd) +
           uy[y1, x0] * (1 - xd) * yd +
           uy[y1, x1] * xd * yd)
    
    # Interpolate Director Angle at particle positions
    vp_theta = (theta[y0, x0] * (1 - xd) * (1 - yd) +
                theta[y0, x1] * xd * (1 - yd) +
                theta[y1, x0] * (1 - xd) * yd +
                theta[y1, x1] * xd * yd)
    
    # Move particles
    particles[:, 0] = (particles[:, 0] + vpx * dt_particles) % py5.width
    particles[:, 1] = (particles[:, 1] + vpy * dt_particles) % py5.height
    
    # 3. Rendering
    # Dynamic background draw with low alpha for long, elegant flow trails
    py5.no_stroke()
    py5.fill(*COLOR_BACKGROUND, 16)  # Alpha 16 creates a gorgeous deep fluid trail
    py5.rect(0, 0, py5.width, py5.height)
    
    # Particle Filaments: we draw two points per particle to form a short, aligned fiber segment
    px = particles[:, 0]
    py = particles[:, 1]
    cos_t = np.cos(vp_theta)
    sin_t = np.sin(vp_theta)
    
    # Shifted points to represent fibers
    px_f0 = px - 2.5 * cos_t
    py_f0 = py - 2.5 * sin_t
    px_f1 = px + 2.5 * cos_t
    py_f1 = py + 2.5 * sin_t
    
    # Draw particle bins with additive blending
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.0)
    
    for bin_idx, color in enumerate([COLOR_TEAL_LIGHT, COLOR_TEAL_DARK, COLOR_AMETHYST]):
        mask = (particle_bins == bin_idx)
        py5.stroke(*color)
        
        # Combine fiber end points to render them in a single fast points call
        xs = np.concatenate([px_f0[mask], px_f1[mask]])
        ys = np.concatenate([py_f0[mask], py_f1[mask]])
        py5.points(np.column_stack((xs, ys)))
        
    py5.blend_mode(py5.BLEND)
    
    # 4. Topological Defect Detection & Rendering
    # Winding number around 2x2 grid cell loop:
    # dtheta = wrap(theta_neighbor - theta)
    # Summing dtheta around a closed square path gives 2*pi*q where q is defect charge (+1/2 or -1/2).
    theta_i_j = theta
    theta_i_jp1 = np.roll(theta, -1, axis=1)
    theta_ip1_jp1 = np.roll(np.roll(theta, -1, axis=0), -1, axis=1)
    theta_ip1_j = np.roll(theta, -1, axis=0)

    def wrap(diff):
        return (diff + np.pi/2) % np.pi - np.pi/2

    d1 = wrap(theta_i_jp1 - theta_i_j)
    d2 = wrap(theta_ip1_jp1 - theta_i_jp1)
    d3 = wrap(theta_ip1_j - theta_ip1_jp1)
    d4 = wrap(theta_i_j - theta_ip1_j)

    q = (d1 + d2 + d3 + d4) / (2.0 * np.pi)
    
    # Locate defect indices on the grid
    pos_plus = np.argwhere(q > 0.38)
    pos_minus = np.argwhere(q < -0.38)
    
    # Draw Defects
    # +1/2 defects (Sun-Gold, comet-shaped, swimming in direction of head)
    for y_idx, x_idx in pos_plus:
        cx = (x_idx / N) * py5.width
        cy = (y_idx / N) * py5.height
        
        # Local director angle determines the comet's heading direction
        ang = theta[y_idx, x_idx]
        dx_comet = np.cos(ang)
        dy_comet = np.sin(ang)
        
        # Draw comet head (glowing sun-gold core)
        py5.fill(255, 215, 0, 160)
        py5.no_stroke()
        py5.ellipse(cx, cy, 14, 14)
        
        # Draw comet tail along the director
        py5.stroke(255, 215, 0, 140)
        py5.stroke_weight(2.5)
        py5.line(cx, cy, cx - 18 * dx_comet, cy - 18 * dy_comet)
        
    # -1/2 defects (Hot Pink, three-pointed stars)
    for y_idx, x_idx in pos_minus:
        cx = (x_idx / N) * py5.width
        cy = (y_idx / N) * py5.height
        
        # Draw star core
        py5.fill(255, 20, 147, 160)
        py5.no_stroke()
        py5.ellipse(cx, cy, 12, 12)
        
        # Draw three spokes pointing at angles theta, theta + 120, theta + 240
        ang = theta[y_idx, x_idx]
        py5.stroke(255, 20, 147, 140)
        py5.stroke_weight(2.5)
        for offset_ang in [0, 2.0 * np.pi / 3.0, 4.0 * np.pi / 3.0]:
            spoke_ang = ang + offset_ang
            py5.line(cx, cy, cx + 12 * np.cos(spoke_ang), cy + 12 * np.sin(spoke_ang))
            
    # Progress & Rendering output
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save standard preview snapshot (mid-frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        print(f"[Render Preview] Saved preview to {SKETCH_DIR}/{PREVIEW_FILENAME}")
        
        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")


py5.run_sketch()
