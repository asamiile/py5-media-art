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

# Simulation Space (1920x1080)
SIM_W = 1920
SIM_H = 1080

# Particles Parameters
N = 18000
# Initial positions: horizontal bands near the shear layer (center Y = 540)
pos = np.zeros((N, 2), dtype=np.float32)
colors = np.zeros((N, 4), dtype=np.float32)  # H, S, B, A

# Distribute particles
for i in range(N):
    pos[i, 0] = np.random.rand() * SIM_W
    # Seed closer to the shear center (540)
    pos[i, 1] = SIM_H / 2 + np.random.normal(0, 120.0)
    
    # Color distribution: top vs bottom bands
    # Upper band: Amber Gold. Lower band: Deep Cobalt Teal. Transition: Electric Rose.
    y_rel = pos[i, 1] - SIM_H / 2
    if y_rel < -30:
        # Amber Gold: Hue ~35
        colors[i] = [35.0 + np.random.normal(0, 4), 85.0, 95.0, 160.0]
    elif y_rel > 30:
        # Cobalt Teal: Hue ~195
        colors[i] = [195.0 + np.random.normal(0, 4), 90.0, 90.0, 160.0]
    else:
        # Electric Rose Accent: Hue ~330
        colors[i] = [330.0 + np.random.normal(0, 3), 95.0, 95.0, 220.0]

# Turbulence Kinetic Energy (TKE) history for HUD
tke_history = []
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    # Recreate clean frames directory
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Dark Abyss Indigo background
    py5.background(4, 2, 10)


def get_velocity(p, t):
    """
    Computes Kelvin-Helmholtz shear flow velocity at point p at time t.
    We model the velocity as:
    U_x = U_0 * tanh((y - y_0) / delta) + perturbation_x
    U_y = perturbation_y
    """
    x = p[:, 0]
    y = p[:, 1]
    
    # Center y
    y0 = SIM_H / 2
    
    # Shear layer width (slowly increases as it diffuses/mixes)
    delta = 50.0 + t * 4.0
    
    # Base shear velocities (top moves right, bottom moves left)
    U0 = 12.0
    u_base = U0 * np.tanh((y - y0) / delta)
    
    # Perturbations: sum of sine waves to trigger roll-up instabilities
    # Multiple modes to create organic mixing
    k1 = 2.0 * np.pi / (SIM_W / 2.0)  # Primary wave mode (2 rolls)
    k2 = 2.0 * np.pi / (SIM_W / 4.0)  # Secondary sub-harmonic
    
    # Amplitude of perturbations grow over time then saturate
    amp = 3.5 * np.minimum(t * 1.5, 6.0) * np.exp(-t * 0.05)
    
    # Perturbation field
    u_pert = amp * np.cos(k1 * x) * np.exp(-np.abs(y - y0) / delta)
    v_pert = amp * 2.0 * np.sin(k1 * x) * np.exp(-np.abs(y - y0) / delta)
    
    # Subharmonic secondary wrinkles
    u_pert += 0.8 * amp * np.cos(k2 * x + t * 0.1) * np.exp(-np.abs(y - y0) / (delta * 1.5))
    v_pert += 0.8 * amp * np.sin(k2 * x + t * 0.1) * np.exp(-np.abs(y - y0) / (delta * 1.5))
    
    vx = u_base + u_pert
    vy = v_pert
    
    return np.stack([vx, vy], axis=-1)


def draw():
    global pos, img_rgb_mid
    
    t = py5.frame_count / 60.0
    
    # --- 1. Physics: Advection & Boundary Wrapping ---
    vel = get_velocity(pos, t)
    
    # Integrate using simple Euler
    pos += vel
    
    # Toroidal wrap horizontally
    pos[:, 0] = pos[:, 0] % SIM_W
    
    # Soft vertical bounce/containment
    out_top = pos[:, 1] < 0
    out_bottom = pos[:, 1] > SIM_H
    pos[out_top, 1] = 0
    pos[out_bottom, 1] = SIM_H
    
    # --- 2. Telemetry: Turbulence Kinetic Energy (TKE) estimation ---
    # TKE is calculated as the variance of velocities around the mean shear flow
    mean_vel = np.mean(vel, axis=0)
    fluctuations = vel - mean_vel
    tke = 0.5 * np.mean(np.sum(fluctuations ** 2, axis=1))
    tke_history.append(tke)
    if len(tke_history) > 300:
        tke_history.pop(0)
        
    # --- 3. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Low-alpha background rect creates long, organic mixing trails
    py5.fill(4, 2, 10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw containment border
    py5.stroke(255, 255, 255, 12)
    py5.stroke_weight(1)
    py5.no_fill()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scale coordinates to 4K
    py5.push_matrix()
    py5.scale(SIZE[0] / SIM_W, SIZE[1] / SIM_H)
    
    # Draw shear layer boundary guide lines (dashed/faint)
    py5.stroke(255, 255, 255, 6)
    py5.line(0, SIM_H / 2 - 100, SIM_W, SIM_H / 2 - 100)
    py5.line(0, SIM_H / 2 + 100, SIM_W, SIM_H / 2 + 100)
    
    # Additive blend mode for luminous particles
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Draw advected filaments
    for i in range(N):
        px, py = pos[i]
        h, s, b, a = colors[i]
        
        # Slightly modulate alpha with velocity magnitude for dynamic feel
        v_mag = np.linalg.norm(vel[i])
        alpha = np.clip(a * (0.4 + v_mag / 15.0), 30, 255)
        
        py5.stroke(h, s, b, alpha)
        py5.stroke_weight(2.0)
        # Small line along velocity vector to show flow direction
        vx, vy = vel[i]
        py5.line(px, py, px - vx * 1.5, py - vy * 1.5)
        
    py5.pop_matrix()
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("KELVIN-HELMHOLTZ SHEAR FLOW SIMULATOR // 2D FILAMENTS", 50, 50)
    py5.text(f"PARTICLE COUNT: {N} | RESOLUTION: 3840 x 2160 (4K)", 50, 85)
    py5.text(f"SHEAR INTENSITY: {12.0:.1f} m/s | MIXING WIDTH (DELTA): {50.0 + t * 4.0:.1f} px", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"TKE DISSIPATION INDEX: {tke:.4f} J/kg", SIZE[0] - 50, 85)
    
    # TKE Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("TURBULENT KINETIC ENERGY", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(255, 110, 0, 180)
    py5.begin_shape()
    for idx, val in enumerate(tke_history):
        xx = gx + idx * (graph_w / 300)
        # Normalize dynamically to fit the graph box
        yy = gy + graph_h - (val / 100.0) * (graph_h - 10) - 5
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
