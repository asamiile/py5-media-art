from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import cv2
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

# Simulation Coordinates (1920x1080)
SIM_W = 1920
SIM_H = 1080

# Convection Parcel Agents
N = 1500
pos = np.zeros((N, 2), dtype=np.float32)
vel = np.zeros((N, 2), dtype=np.float32)

# Parcel properties: Temperature (T) and Salinity (S)
T = np.zeros(N, dtype=np.float32)
S = np.zeros(N, dtype=np.float32)

# Distribute parcels: warm/fresh at bottom, cold/salty at top
half = N // 2
# Top half: cold (T ~ 0.1), salty (S ~ 0.9)
pos[:half, 0] = np.random.rand(half) * SIM_W
pos[:half, 1] = np.random.rand(half) * (SIM_H * 0.4)
T[:half] = 0.1 + np.random.normal(0, 0.05, half)
S[:half] = 0.9 + np.random.normal(0, 0.05, half)

# Bottom half: warm (T ~ 0.9), fresh (S ~ 0.1)
pos[half:, 0] = np.random.rand(half) * SIM_W
pos[half:, 1] = SIM_H - np.random.rand(half) * (SIM_H * 0.4)
T[half:] = 0.9 + np.random.normal(0, 0.05, half)
S[half:] = 0.1 + np.random.normal(0, 0.05, half)

# Damping and diffusion rates
damping = 0.94
dt = 0.5
# Heat diffuses much faster than salt (double diffusion)
diff_T = 0.15
diff_S = 0.02
interaction_radius = 50.0

# Telemetry: Convective heat flux history
heat_flux_history = []
img_rgb_mid = None


def update_convection_physics():
    """
    Updates double-diffusion convection:
    - Buoyant force: F_y = buoyancy_coeff * (alpha * T - beta * S)
    - Local diffusion of T and S between close parcels
    """
    global pos, vel, T, S
    
    # 1. Local neighbor interactions (diffusion of T and S + collision repulsion)
    # Vectorized neighbor search using distance matrix
    # Compute distance matrix between all parcels
    diff = pos[:, None, :] - pos[None, :, :]
    dist = np.linalg.norm(diff, axis=-1)
    
    # Neighbors mask
    neighbors = (dist < interaction_radius) & (dist > 0.0)
    
    # Preallocate updates
    dT = np.zeros(N, dtype=np.float32)
    dS = np.zeros(N, dtype=np.float32)
    repulsion = np.zeros((N, 2), dtype=np.float32)
    
    for i in range(N):
        nb_mask = neighbors[i]
        if np.any(nb_mask):
            # Heat diffusion
            dT[i] = diff_T * np.mean(T[nb_mask] - T[i])
            # Salt diffusion (much slower)
            dS[i] = diff_S * np.mean(S[nb_mask] - S[i])
            
            # Repulsion force to prevent collapse
            nb_diff = diff[i, nb_mask]
            nb_dist = dist[i, nb_mask][:, None]
            rep = -nb_diff / (nb_dist**2 + 1.0)
            repulsion[i] = np.sum(rep, axis=0) * 0.6
            
    # Apply diffusion updates
    T += dT * dt
    S += dS * dt
    
    # Boundary source reinforcement: warm fresh at bottom, cold salty at top
    # Bottom boundaries keep heating up
    bottom_mask = pos[:, 1] > SIM_H - 120.0
    T[bottom_mask] = np.clip(T[bottom_mask] + 0.08 * dt, 0.0, 1.0)
    S[bottom_mask] = np.clip(S[bottom_mask] - 0.05 * dt, 0.0, 1.0)
    
    # Top boundaries keep cooling down and salting
    top_mask = pos[:, 1] < 120.0
    T[top_mask] = np.clip(T[top_mask] - 0.08 * dt, 0.0, 1.0)
    S[top_mask] = np.clip(S[top_mask] + 0.05 * dt, 0.0, 1.0)
    
    # Clip T and S
    np.clip(T, 0.0, 1.0, out=T)
    np.clip(S, 0.0, 1.0, out=S)
    
    # 2. Buoyancy forces
    # Warm T decreases density (upwards buoyancy)
    # Salty S increases density (downwards buoyancy)
    alpha = 6.5
    beta = 5.0
    buoyancy = alpha * T - beta * S
    
    # Accelerate parcels based on buoyancy
    vel[:, 1] -= buoyancy * 0.3 * dt  # y is down, so upwards is negative y
    vel += repulsion * dt
    
    # Simple Euler integration
    pos += vel * dt
    vel *= damping
    
    # Containing boundaries
    # Horizontal wrap
    pos[:, 0] = pos[:, 0] % SIM_W
    
    # Vertical bounds bounce
    pos[:, 1] = np.clip(pos[:, 1], 10.0, SIM_H - 10.0)
    vel[pos[:, 1] <= 10.0, 1] *= -0.5
    vel[pos[:, 1] >= SIM_H - 10.0, 1] *= -0.5


def calculate_heat_flux():
    """
    Computes convective heat flux: average of T * vel_y (upward velocity is negative y)
    """
    # Negative vel_y is upward velocity
    upward_vel = -vel[:, 1]
    return np.mean(T * upward_vel)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 2, 7)


def draw():
    global img_rgb_mid
    
    # --- 1. Physics update ---
    update_convection_physics()
    
    # Calculate heat flux telemetry
    heat_flux = calculate_heat_flux()
    heat_flux_history.append(heat_flux)
    if len(heat_flux_history) > 300:
        heat_flux_history.pop(0)
        
    t = py5.frame_count / 60.0
    
    # --- 2. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Slow fading background rect (long trails)
    py5.fill(2, 2, 7, 12)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scale coordinates to 4K
    py5.push_matrix()
    py5.scale(SIZE[0] / SIM_W, SIZE[1] / SIM_H)
    
    # Additive neon glow for warm/salty parcels
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Draw convection parcels
    for i in range(N):
        px, py = pos[i]
        vx, vy = vel[i]
        
        # Color mapping:
        # Warm/fresh is orange (Hue ~15), cold/salty is cyan (Hue ~190)
        # Mixing zone (average T and S) is violet (Hue ~280)
        h = 190.0 - T[i] * 175.0
        if h < 0:
            h += 360.0
            
        s = 85.0
        b = 50.0 + T[i] * 40.0
        
        py5.stroke(h, s, b, 130)
        py5.stroke_weight(2.2)
        
        # Line trail along velocity
        py5.line(px, py, px - vx * 1.8, py - vy * 1.8)
        
    py5.pop_matrix()
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("DOUBLE-DIFFUSION CONVECTION // MULTI-AGENT SALT FINGERS", 50, 50)
    py5.text(f"PARCEL COUNT: {N} | RESOLUTION: 3840 x 2160 (4K)", 50, 85)
    py5.text(f"DIFFUSION COEFFICIENTS: Heat (DT) = {diff_T:.2f}, Salt (DS) = {diff_S:.2f}", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"NET CONVECTIVE HEAT FLUX: {heat_flux:.4f} W/m²", SIZE[0] - 50, 85)
    
    # Heat Flux Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("CONVECTIVE HEAT FLUX HIST", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(255, 85, 0, 180)
    py5.begin_shape()
    for idx, val in enumerate(heat_flux_history):
        xx = gx + idx * (graph_w / 300)
        # Scale to fit graph box
        yy = gy + graph_h - (val / 0.15) * (graph_h - 10) - 5
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Blank screen check
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
        
        # Save preview mid-frame (grab from screen buffer)
        py5.load_np_pixels()
        img_rgb_mid = py5.np_pixels[:, :, :3].copy()
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
