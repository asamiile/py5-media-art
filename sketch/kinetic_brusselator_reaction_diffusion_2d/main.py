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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid size for reaction-diffusion (16:9 ratio)
GRID_W = 384
GRID_H = 216

# Brusselator Parameters
a = 1.0
b = 2.6
Du = 0.12
Dv = 0.03
dt = 0.4

# State grids
u_grid = None
v_grid = None

# Particles
N_PARTICLES = 40000
particles_pos = None
particles_color_type = None


def setup():
    global u_grid, v_grid, particles_pos, particles_color_type
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(4, 3, 15)
    
    # Initialize grids to steady state (u=a, v=b/a)
    u_grid = np.full((GRID_H, GRID_W), a, dtype=np.float32)
    v_grid = np.full((GRID_H, GRID_W), b / a, dtype=np.float32)
    
    # Seed uniform noise everywhere to trigger homogenous self-organizing Turing waves
    np.random.seed(42)
    u_grid += np.random.uniform(-0.15, 0.15, (GRID_H, GRID_W)).astype(np.float32)
    v_grid += np.random.uniform(-0.15, 0.15, (GRID_H, GRID_W)).astype(np.float32)
                
    # Initialize trace particles
    particles_pos = np.zeros((N_PARTICLES, 2), dtype=np.float32)
    particles_pos[:, 0] = np.random.uniform(0, GRID_W, N_PARTICLES)
    particles_pos[:, 1] = np.random.uniform(0, GRID_H, N_PARTICLES)
    
    # Divide particles into three distinct visual filament layers
    particles_color_type = np.random.randint(0, 3, N_PARTICLES).astype(np.uint8)


def laplacian(f):
    """
    Five-point stencil periodic Laplacian.
    """
    return (
        np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
        np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) -
        4.0 * f
    )


def update_simulation():
    global u_grid, v_grid
    # Multiple integration steps per frame to speed up chemical dynamics
    for _ in range(4):
        lu = laplacian(u_grid)
        lv = laplacian(v_grid)
        
        # Brusselator equations
        u_next = u_grid + (Du * lu + a - (b + 1) * u_grid + (u_grid ** 2) * v_grid) * dt
        v_next = v_grid + (Dv * lv + b * u_grid - (u_grid ** 2) * v_grid) * dt
        
        # Clip to prevent numerical divergence
        u_grid = np.clip(u_next, 0.0, 10.0)
        v_grid = np.clip(v_next, 0.0, 10.0)


def draw():
    global particles_pos
    # 1. Update reaction-diffusion simulation
    update_simulation()
    
    # Compute concentration gradient
    # Centered finite differences with periodic wrapping
    grad_y = 0.5 * (np.roll(u_grid, -1, axis=0) - np.roll(u_grid, 1, axis=0))
    grad_x = 0.5 * (np.roll(u_grid, -1, axis=1) - np.roll(u_grid, 1, axis=1))
    
    # Construct divergence-free curl velocity field
    vx = grad_y
    vy = -grad_x
    
    # 2. Update and advect particles
    px = particles_pos[:, 0]
    py = particles_pos[:, 1]
    
    # Find nearest grid indices (with periodic wrapping)
    ix = np.clip(px.astype(np.int32), 0, GRID_W - 1)
    iy = np.clip(py.astype(np.int32), 0, GRID_H - 1)
    
    # Look up velocities
    pvx = vx[iy, ix]
    pvy = vy[iy, ix]
    
    # Advect with curl velocity + noise
    particles_pos[:, 0] += pvx * 2.8 + np.random.normal(0, 0.08, N_PARTICLES)
    particles_pos[:, 1] += pvy * 2.8 + np.random.normal(0, 0.08, N_PARTICLES)
    
    # Wrap particles at grid boundaries
    particles_pos[:, 0] %= GRID_W
    particles_pos[:, 1] %= GRID_H
    
    # 3. Draw background glow image (Brusselator u-concentration)
    u_min, u_max = np.min(u_grid), np.max(u_grid)
    u_norm = (u_grid - u_min) / (u_max - u_min + 1e-5)
    
    # Deep analog-like space colors: Black/Indigo -> Deep Purple -> Crimson Red
    bg_r = np.clip(130.0 * (u_norm ** 1.8), 0, 255).astype(np.uint8)
    bg_g = np.clip(35.0 * u_norm, 0, 255).astype(np.uint8)
    bg_b = np.clip(200.0 * (u_norm ** 0.9), 0, 255).astype(np.uint8)
    
    # Stack channels to create RGB image
    bg_img_data = np.dstack((bg_r, bg_g, bg_b))
    bg_img = py5.create_image_from_numpy(bg_img_data, 'RGB')
    
    # Draw background with tint/fade to allow beautiful particle trails
    py5.tint(255, 20)
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])
    py5.no_tint()
    
    # Draw translucent rectangle overlay for trail fade
    py5.fill(4, 3, 15, 12)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # 4. Map particle positions to 4K screen
    sx = (particles_pos[:, 0] / GRID_W * SIZE[0]).astype(np.float32)
    sy = (particles_pos[:, 1] / GRID_H * SIZE[1]).astype(np.float32)
    
    # Get local chemical concentration at particle positions for dynamic brightness
    p_u_norm = u_norm[iy, ix]
    
    # Draw particle streams in three neon color bands
    colors = [
        (13, 242, 201),  # Luminous Teal
        (189, 21, 250),  # Electric Lavender
        (250, 190, 21)   # Solar Gold
    ]
    
    py5.stroke_weight(2.0)
    for c_idx in range(3):
        mask = (particles_color_type == c_idx)
        xs = sx[mask]
        ys = sy[mask]
        brightness = p_u_norm[mask]
        
        c = colors[c_idx]
        for i in range(len(xs)):
            alpha = int(110 + 145 * brightness[i])
            py5.stroke(c[0], c[1], c[2], alpha)
            py5.point(xs[i], ys[i])
            
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
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
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
