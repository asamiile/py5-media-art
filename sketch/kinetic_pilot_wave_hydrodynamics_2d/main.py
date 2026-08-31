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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation grid configuration (16:9 ratio)
W_sim = 320
H_sim = 180
cx, cy = W_sim / 2.0, H_sim / 2.0
R_corral = 75.0

# Physical constants
c_sq = 0.16         # Wave speed squared
g_coef = 0.12       # Wave gradient coupling force
drag = 0.05         # Droplet drag
noise_amp = 0.003   # Small air perturbation noise
wave_emission_rate = 0.15  # Strength of wave generation on impact
sigma = 2.2         # Gaussian impact radius
damping_base = 0.012

# Grids
h = np.zeros((H_sim, W_sim), dtype=np.float32)
v = np.zeros((H_sim, W_sim), dtype=np.float32)

X_grid, Y_grid = np.meshgrid(np.arange(W_sim), np.arange(H_sim))
dist_grid = np.hypot(X_grid - cx, Y_grid - cy)
corral_mask = dist_grid < R_corral

# Precompute damping grid
damping_grid = np.full((H_sim, W_sim), damping_base, dtype=np.float32)
x_edge = np.maximum(0.0, (np.abs(X_grid - cx) - (W_sim / 2 - 12)) / 12.0)
y_edge = np.maximum(0.0, (np.abs(Y_grid - cy) - (H_sim / 2 - 12)) / 12.0)
edge_damp = np.maximum(x_edge, y_edge) ** 2 * 0.5
damping_grid = np.maximum(damping_grid, edge_damp)
damping_grid[dist_grid >= R_corral] = 0.55  # Absorb waves outside the corral boundary

# Setup colored image array
colored = np.zeros((H_sim, W_sim, 4), dtype=np.uint8)
colored[..., 3] = 255  # Solid alpha

# Walkers definition
class Walker:
    def __init__(self, x, y, vx, vy, phase_offset):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.phase_offset = phase_offset
        self.history = []

particles = []

def get_gradient(h_grid, px, py):
    x0 = int(np.clip(px, 1, W_sim - 2))
    y0 = int(np.clip(py, 1, H_sim - 2))
    tx = px - x0
    ty = py - y0

    def grad_at(x, y):
        gx = (h_grid[y, x + 1] - h_grid[y, x - 1]) * 0.5
        gy = (h_grid[y + 1, x] - h_grid[y - 1, x]) * 0.5
        return gx, gy

    g00_x, g00_y = grad_at(x0, y0)
    g10_x, g10_y = grad_at(x0 + 1, y0)
    g01_x, g01_y = grad_at(x0, y0 + 1)
    g11_x, g11_y = grad_at(x0 + 1, y0 + 1)

    gx = (1 - tx) * (1 - ty) * g00_x + tx * (1 - ty) * g10_x + (1 - tx) * ty * g01_x + tx * ty * g11_x
    gy = (1 - tx) * (1 - ty) * g00_y + tx * (1 - ty) * g01_y + (1 - tx) * ty * g01_x + tx * ty * g11_x
    # Fix potential typo: using same formula for gy
    gy = (1 - tx) * (1 - ty) * g00_y + tx * (1 - ty) * g10_y + (1 - tx) * ty * g01_y + tx * ty * g11_y
    return gx, gy

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize walkers inside the corral
    num_particles = 12
    for _ in range(num_particles):
        r = random.uniform(5.0, R_corral - 10.0)
        theta = random.uniform(0, 2 * np.pi)
        px = cx + r * np.cos(theta)
        py = cy + r * np.sin(theta)
        vx = random.uniform(-0.3, 0.3)
        vy = random.uniform(-0.3, 0.3)
        phase_offset = random.uniform(0, 2 * np.pi)
        particles.append(Walker(px, py, vx, vy, phase_offset))

def draw():
    global h, v
    
    # --- Update Wave Field (FDTD) ---
    lap = np.zeros_like(h)
    # 5-point stencil Laplacian
    lap[1:-1, 1:-1] = (
        h[:-2, 1:-1] + h[2:, 1:-1] + h[1:-1, :-2] + h[1:-1, 2:] - 4 * h[1:-1, 1:-1]
    )
    
    # Parametric bath vibration forcing
    forcing = 0.04 * np.cos(0.24 * py5.frame_count)
    c_sq_eff = c_sq + forcing
    
    v += c_sq_eff * lap - damping_grid * v
    h += v
    
    # --- Update Particles & Emit Waves ---
    for p in particles:
        # Bouncing phase
        bounce = np.sin(py5.frame_count * 0.28 + p.phase_offset)
        
        # When droplet is on the surface (impact phase)
        if bounce < -0.6:
            dx2 = (X_grid - p.x) ** 2
            dy2 = (Y_grid - p.y) ** 2
            d2 = dx2 + dy2
            # Add Gaussian ripple
            impact = wave_emission_rate * (-bounce - 0.6) * 4.0
            h += impact * np.exp(-d2 / (sigma ** 2))
            
            # Apply pilot-wave force from local surface gradient
            gx, gy = get_gradient(h, p.x, p.y)
            p.vx += -g_coef * gx - drag * p.vx + random.uniform(-noise_amp, noise_amp)
            p.vy += -g_coef * gy - drag * p.vy + random.uniform(-noise_amp, noise_amp)
        else:
            # Droplet is in the air, only drag and subtle noise
            p.vx += -drag * 0.2 * p.vx + random.uniform(-noise_amp * 0.5, noise_amp * 0.5)
            p.vy += -drag * 0.2 * p.vy + random.uniform(-noise_amp * 0.5, noise_amp * 0.5)
            
        # Update positions
        p.x += p.vx
        p.y += p.vy
        
        # Keep track of history for trails
        p.history.append((p.x, p.y))
        if len(p.history) > 35:
            p.history.pop(0)
            
        # Circular corral boundary check
        dx = p.x - cx
        dy = p.y - cy
        dist = np.hypot(dx, dy)
        if dist > R_corral - 2.5:
            nx = dx / dist
            ny = dy / dist
            v_dot_n = p.vx * nx + p.vy * ny
            if v_dot_n > 0:
                p.vx -= 2.0 * v_dot_n * nx
                p.vy -= 2.0 * v_dot_n * ny
            p.x = cx + nx * (R_corral - 2.6)
            p.y = cy + ny * (R_corral - 2.6)

    # --- Render Fluid Grid to ARGB Image ---
    # Map height to intensity
    h_norm = np.clip(h * 4.2, -1.0, 1.0)
    
    # Base color: deep cobalt indigo (#0b0c1b)
    # Crest color: neon cyan (#00f3ff)
    # Trough color: deep violet (#1c053a)
    
    pos_mask = h_norm > 0
    neg_mask = h_norm < 0
    neutral_mask = h_norm == 0
    
    # Positive (crests)
    p_val = h_norm
    colored[pos_mask, 0] = (11 + p_val[pos_mask] * (0 - 11)).astype(np.uint8)
    colored[pos_mask, 1] = (12 + p_val[pos_mask] * (243 - 12)).astype(np.uint8)
    colored[pos_mask, 2] = (27 + p_val[pos_mask] * (255 - 27)).astype(np.uint8)
    
    # Negative (troughs)
    n_val = -h_norm
    colored[neg_mask, 0] = (11 + n_val[neg_mask] * (28 - 11)).astype(np.uint8)
    colored[neg_mask, 1] = (12 + n_val[neg_mask] * (5 - 12)).astype(np.uint8)
    colored[neg_mask, 2] = (27 + n_val[neg_mask] * (58 - 27)).astype(np.uint8)
    
    # Neutral
    colored[neutral_mask, 0] = 11
    colored[neutral_mask, 1] = 12
    colored[neutral_mask, 2] = 27
    
    # Clear screen with background color
    py5.background(0)
    
    # Draw scaled fluid grid
    img = py5.create_image(W_sim, H_sim, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = colored
        img.update_np_pixels()
    else:
        r = colored[..., 0].astype(np.int32)
        g = colored[..., 1].astype(np.int32)
        b = colored[..., 2].astype(np.int32)
        a = colored[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # --- Draw Circular Corral Boundary in 4K ---
    scale_x = py5.width / W_sim
    scale_y = py5.height / H_sim
    
    py5.no_fill()
    py5.stroke(0, 243, 255, 60)
    py5.stroke_weight(5)
    py5.ellipse(cx * scale_x, cy * scale_y, R_corral * 2.0 * scale_x, R_corral * 2.0 * scale_y)
    
    py5.stroke(0, 243, 255, 30)
    py5.stroke_weight(12)
    py5.ellipse(cx * scale_x, cy * scale_y, R_corral * 2.0 * scale_x, R_corral * 2.0 * scale_y)
    
    # --- Draw Particles & Trails in 4K ---
    for p in particles:
        # 1. Draw trails
        if len(p.history) > 1:
            for idx in range(1, len(p.history)):
                pt1 = p.history[idx - 1]
                pt2 = p.history[idx]
                alpha = int(255 * (idx / len(p.history)))
                py5.stroke(255, 170, 0, alpha)
                py5.stroke_weight(2 + 2 * (idx / len(p.history)))
                py5.line(pt1[0] * scale_x, pt1[1] * scale_y, pt2[0] * scale_x, pt2[1] * scale_y)
                
        # 2. Draw bouncing droplet
        bounce = np.sin(py5.frame_count * 0.28 + p.phase_offset)
        # Bouncing effect translates to changing radius and alpha
        radius = 24 + 10 * bounce
        alpha = int(180 + 75 * bounce)
        
        py5.no_stroke()
        # Glowing inner core (Amber)
        py5.fill(255, 200, 0, alpha)
        py5.ellipse(p.x * scale_x, p.y * scale_y, radius * 0.7, radius * 0.7)
        # Outer soft glow halo
        py5.fill(255, 150, 0, alpha // 3)
        py5.ellipse(p.x * scale_x, p.y * scale_y, radius * 1.4, radius * 1.4)
        
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frames
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
        
        # Save preview snapshot (middle frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
