from pathlib import Path
import math
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

# Particle parameters for Chladni sand grains
N_PARTICLES = 300000
particles_pos = None
particles_vel = None


def setup():
    global particles_pos, particles_vel
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize acoustic particles uniformly on screen [-1, 1]
    np.random.seed(42)
    particles_pos = np.random.uniform(-1.0, 1.0, (N_PARTICLES, 2)).astype(np.float32)
    particles_vel = np.zeros((N_PARTICLES, 2), dtype=np.float32)


def get_amplitude_and_gradients(px, py, t):
    """
    Compute Chladni amplitude and exact gradients with respect to screen px and py
    using 4D embedding and rotation.
    """
    # 4D standing wave modes
    m1 = 3.0 + 2.0 * math.sin(t * 0.45)
    n1 = 5.0 + 3.0 * math.cos(t * 0.3)
    m2 = 4.0 + 1.5 * math.cos(t * 0.5)
    n2 = 6.0 + 2.0 * math.sin(t * 0.4)
    
    rot1 = t * 0.4
    rot2 = t * 0.3
    
    def compute_amp(x, y):
        # 4D embedding
        z = np.sin(x * 2.0 + rot1) * np.cos(y * 2.0)
        w = np.cos(x * 1.5 - rot2) * np.sin(y * 2.5)
        
        # 4D rotation
        x_rot = x * math.cos(rot1) - z * math.sin(rot1)
        z_rot = x * math.sin(rot1) + z * math.cos(rot1)
        y_rot = y * math.cos(rot2) - w * math.sin(rot2)
        w_rot = y * math.sin(rot2) + w * math.cos(rot2)
        
        # Standing waves
        amp1 = np.cos(n1 * np.pi * x_rot) * np.cos(m1 * np.pi * y_rot) - np.cos(m1 * np.pi * x_rot) * np.cos(n1 * np.pi * y_rot)
        amp2 = np.cos(n2 * np.pi * z_rot) * np.cos(m2 * np.pi * w_rot) - np.cos(m2 * np.pi * z_rot) * np.cos(n2 * np.pi * w_rot)
        return amp1 + 0.55 * amp2

    amp = compute_amp(px, py)
    
    # Finite differences for gradients with respect to screen coordinates
    eps = 0.004
    amp_dx = compute_amp(px + eps, py)
    amp_dy = compute_amp(px, py + eps)
    
    grad_x = (np.abs(amp_dx) - np.abs(amp)) / eps
    grad_y = (np.abs(amp_dy) - np.abs(amp)) / eps
    
    return amp, grad_x, grad_y


def draw():
    global particles_pos, particles_vel
    py5.background(4, 3, 12)  # Deep cosmic void
    
    t = py5.frame_count / 60.0
    w, h = float(SIZE[0]), float(SIZE[1])
    aspect = w / h
    
    # Scale screen coordinates to aspect ratio for gradient calculation
    px = particles_pos[:, 0] * aspect
    py = particles_pos[:, 1]
    
    amp, grad_x, grad_y = get_amplitude_and_gradients(px, py, t)
    
    # Clip gradients to prevent numeric explosion
    grad_x = np.clip(grad_x, -20.0, 20.0)
    grad_y = np.clip(grad_y, -20.0, 20.0)
    
    # Accelerate particles towards nodal lines (|amp| -> 0)
    # The force is in unrotated screen coordinate space
    particles_vel[:, 0] -= grad_x * 0.0005 + np.random.normal(0, 0.0004, N_PARTICLES)
    particles_vel[:, 1] -= grad_y * 0.0005 + np.random.normal(0, 0.0004, N_PARTICLES)
    
    # Viscous drag / damping
    particles_vel *= 0.86
    
    # Cap velocity magnitude to screen speed limit (max 0.015 per frame)
    vel_mag = np.hypot(particles_vel[:, 0], particles_vel[:, 1])
    max_speed = 0.015
    too_fast = vel_mag > max_speed
    particles_vel[too_fast, 0] = (particles_vel[too_fast, 0] / vel_mag[too_fast]) * max_speed
    particles_vel[too_fast, 1] = (particles_vel[too_fast, 1] / vel_mag[too_fast]) * max_speed
    
    # Update position
    particles_pos += particles_vel
    
    # Boundary wrap-around
    out_x = np.abs(particles_pos[:, 0]) > 1.0
    out_y = np.abs(particles_pos[:, 1]) > 1.0
    particles_pos[out_x, 0] = np.random.uniform(-1.0, 1.0, np.sum(out_x))
    particles_pos[out_y, 1] = np.random.uniform(-1.0, 1.0, np.sum(out_y))
    
    # Map back to screen pixel space
    screen_x = ((particles_pos[:, 0] + 1.0) / 2.0 * w).astype(np.int32)
    screen_y = ((particles_pos[:, 1] + 1.0) / 2.0 * h).astype(np.int32)
    
    # Keep only valid screen coords
    valid = (screen_x >= 0) & (screen_x < w) & (screen_y >= 0) & (screen_y < h)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Accumulate particle density on screen grid
    density_map = np.zeros((int(h), int(w)), dtype=np.float32)
    np.add.at(density_map, (sy, sx), 1.0)
    
    # Fast Box Blur on density map for beautiful glow/halo effect
    glow_map = density_map.copy()
    glow_map[1:-1, 1:-1] += (
        density_map[:-2, 1:-1] + density_map[2:, 1:-1] +
        density_map[1:-1, :-2] + density_map[1:-1, 2:]
    ) * 0.6
    
    # Log compression and normalization
    glow_map = np.log1p(glow_map * 12.0)
    max_d = np.max(glow_map) + 1e-5
    norm_d = glow_map / max_d
    
    # Vibrant hyperdimensional palette mapping:
    # High-contrast space dust: Deep Indigo -> Neon Cyan -> Hot Pink -> Solar Amber -> Pure White
    r_chan = np.clip(255.0 * (norm_d ** 1.1 * 1.6 - norm_d ** 3.0 * 0.6), 0, 255)
    g_chan = np.clip(255.0 * (norm_d ** 2.0 * 1.3 + norm_d ** 0.5 * 0.1), 0, 255)
    b_chan = np.clip(255.0 * (norm_d ** 0.6 * 1.5 - norm_d ** 1.8 * 0.7), 0, 255)
    
    # Mix ambient cosmic blue glow for low density dust fields
    glow_r = 12.0 * norm_d
    glow_g = 6.0 * norm_d
    glow_b = 36.0 * norm_d
    
    r_chan = np.clip(r_chan + glow_r, 0, 255)
    g_chan = np.clip(g_chan + glow_g, 0, 255)
    b_chan = np.clip(b_chan + glow_b, 0, 255)
    
    img_array = np.dstack((r_chan.astype(np.uint8), g_chan.astype(np.uint8), b_chan.astype(np.uint8)))
    img = py5.create_image_from_numpy(img_array, 'RGB')
    py5.image(img, 0, 0, w, h)
    
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
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
