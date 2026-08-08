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

# --- Simulation Grid Size ---
GRID_W = 240
GRID_H = 135

# Grid coordinate indices
Y, X = np.indices((GRID_H, GRID_W))

# --- Stable Fluids State ---
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
v = np.zeros((GRID_H, GRID_W), dtype=np.float32)
dye_r = np.zeros((GRID_H, GRID_W), dtype=np.float32)
dye_g = np.zeros((GRID_H, GRID_W), dtype=np.float32)
dye_b = np.zeros((GRID_H, GRID_W), dtype=np.float32)
p = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# --- Gear Definitions ---
# Gear 1 (Left)
G1_CX = GRID_W // 2 - 25
G1_CY = GRID_H // 2
G1_R0 = 17.0
G1_AMP = 4.0
G1_TEETH = 8
G1_OMEGA = 0.12  # Clockwise rotation speed

# Gear 2 (Right)
G2_CX = GRID_W // 2 + 25
G2_CY = GRID_H // 2
G2_R0 = 17.0
G2_AMP = 4.0
G2_TEETH = 8
G2_OMEGA = -0.12 # Counter-clockwise rotation speed


def advect(f, u_vel, v_vel, dt):
    """Semi-Lagrangian advection with toroidal wrapping boundaries."""
    x_src = X - dt * u_vel
    y_src = Y - dt * v_vel
    
    x_src = np.mod(x_src, GRID_W)
    y_src = np.mod(y_src, GRID_H)
    
    x0 = np.floor(x_src).astype(np.int32) % GRID_W
    x1 = (x0 + 1) % GRID_W
    y0 = np.floor(y_src).astype(np.int32) % GRID_H
    y1 = (y0 + 1) % GRID_H
    
    wx = x_src - x0
    wy = y_src - y0
    
    f00 = f[y0, x0]
    f10 = f[y0, x1]
    f01 = f[y1, x0]
    f11 = f[y1, x1]
    
    return ((1.0 - wy) * ((1.0 - wx) * f00 + wx * f10) +
            wy * ((1.0 - wx) * f01 + wx * f11))


def project():
    """Jacobi relaxation to compute pressure and project velocity to divergence-free field."""
    global u, v, p
    p.fill(0)
    
    div = 0.5 * (
        np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1) +
        np.roll(v, -1, axis=0) - np.roll(v, 1, axis=0)
    )
    
    for _ in range(20):
        p = (
            np.roll(p, 1, axis=1) + np.roll(p, -1, axis=1) +
            np.roll(p, 1, axis=0) + np.roll(p, -1, axis=0) - div
        ) / 4.0
        
    u -= 0.5 * (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1))
    v -= 0.5 * (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0))


def apply_gears(theta1, theta2):
    """Enforce moving boundaries inside the rotating gears."""
    global u, v, dye_r, dye_g, dye_b
    
    # Gear 1 coords
    dx1 = X - G1_CX
    dy1 = Y - G1_CY
    r1 = np.sqrt(dx1**2 + dy1**2)
    t1 = np.arctan2(dy1, dx1) - theta1
    gear1_shape = G1_R0 + G1_AMP * np.tanh(4.0 * np.sin(G1_TEETH * t1))
    mask1 = r1 <= gear1_shape
    
    # Gear 2 coords
    dx2 = X - G2_CX
    dy2 = Y - G2_CY
    r2 = np.sqrt(dx2**2 + dy2**2)
    t2 = np.arctan2(dy2, dx2) - theta2
    gear2_shape = G2_R0 + G2_AMP * np.tanh(4.0 * np.sin(G2_TEETH * t2))
    mask2 = r2 <= gear2_shape

    # Set velocity inside the gears to match solid-body rotation
    # u_solid = -omega * dy, v_solid = omega * dx
    u[mask1] = -G1_OMEGA * dy1[mask1]
    v[mask1] = G1_OMEGA * dx1[mask1]
    
    u[mask2] = -G2_OMEGA * dy2[mask2]
    v[mask2] = G2_OMEGA * dx2[mask2]

    # Constantly inject fresh colorful dye along the gear boundaries
    edge_g1 = (r1 > gear1_shape - 1.5) & (r1 <= gear1_shape + 1.0)
    edge_g2 = (r2 > gear2_shape - 1.5) & (r2 <= gear2_shape + 1.0)
    
    # Cyan dye from Gear 1 (0, 220, 240)
    dye_r[edge_g1] = np.maximum(dye_r[edge_g1], 0.0)
    dye_g[edge_g1] = np.maximum(dye_g[edge_g1], 0.86)
    dye_b[edge_g1] = np.maximum(dye_b[edge_g1], 0.94)

    # Magenta dye from Gear 2 (180, 40, 200)
    dye_r[edge_g2] = np.maximum(dye_r[edge_g2], 0.70)
    dye_g[edge_g2] = np.maximum(dye_g[edge_g2], 0.15)
    dye_b[edge_g2] = np.maximum(dye_b[edge_g2], 0.78)


def step_simulation(theta1, theta2):
    global u, v, dye_r, dye_g, dye_b
    
    # Enforce gear velocities on the fluid solver
    apply_gears(theta1, theta2)
    
    # Advect velocities (self-advection) with viscosity damping
    dt = 0.8
    u_new = advect(u, u, v, dt)
    v_new = advect(v, u, v, dt)
    
    u = u_new * 0.99
    v = v_new * 0.99
    
    # Project to make velocity divergence-free
    project()
    
    # Advect and diffuse dye channels (decay rate for dissipating wisps)
    dye_r = advect(dye_r, u, v, dt) * 0.98
    dye_g = advect(dye_g, u, v, dt) * 0.98
    dye_b = advect(dye_b, u, v, dt) * 0.98


def draw_gear_vector(cx, cy, r0, amp, teeth, angle, scale_factor):
    """Draw a crisp vector representation of the gear on top of the fluid."""
    py5.push_matrix()
    py5.translate(cx * scale_factor, cy * scale_factor)
    py5.rotate(angle)
    
    py5.begin_shape()
    num_pts = 180
    for i in range(num_pts):
        theta = 2.0 * np.pi * i / num_pts
        r = r0 + amp * np.tanh(4.0 * np.sin(teeth * theta))
        px = r * np.cos(theta) * scale_factor
        py = r * np.sin(theta) * scale_factor
        py5.vertex(px, py)
    py5.end_shape(py5.CLOSE)
    
    # Draw central gear axle hole
    py5.fill(10, 8, 14)  # matches background
    py5.ellipse(0, 0, r0 * 0.4 * scale_factor, r0 * 0.4 * scale_factor)
    py5.pop_matrix()


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    W, H = SIZE
    frame = py5.frame_count
    t = frame / FPS
    
    # Compute gear rotation angles
    # To make them intermesh visually, we offset their starting tooth phase
    theta1 = G1_OMEGA * t * 2.0
    theta2 = G2_OMEGA * t * 2.0 + (np.pi / G2_TEETH)
    
    step_simulation(theta1, theta2)
    
    # Upscale dye fields to output resolution (using repeat expansion)
    sx = W // GRID_W
    sy = H // GRID_H
    
    # Map raw dye concentration into glowing pixel values
    r_grid = np.clip(dye_r * 255.0, 0, 255).astype(np.uint8)
    g_grid = np.clip(dye_g * 255.0, 0, 255).astype(np.uint8)
    b_grid = np.clip(dye_b * 255.0, 0, 255).astype(np.uint8)
    
    r_up = np.repeat(np.repeat(r_grid, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_grid, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_grid, sy, axis=0), sx, axis=1)[:H, :W]
    
    # Write directly to screen buffer
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_up
    py5.np_pixels[:, :, 2] = g_up
    py5.np_pixels[:, :, 3] = b_up
    py5.update_np_pixels()
    
    # Render glowing vector gears on top
    py5.stroke(250, 180, 20, 220)  # Solar Gold outline
    py5.stroke_weight(4)
    py5.fill(18, 14, 26, 180)      # Translucent dark body
    
    scale_factor = W / GRID_W
    draw_gear_vector(G1_CX, G1_CY, G1_R0, G1_AMP, G1_TEETH, theta1, scale_factor)
    draw_gear_vector(G2_CX, G2_CY, G2_R0, G2_AMP, G2_TEETH, theta2, scale_factor)
    
    # Vignette shadow
    py5.no_stroke()
    for i in range(16):
        alpha = int(3 + i * 4)
        m = i * 22
        py5.fill(8, 8, 16, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)
        
    # Telemetry HUD
    py5.fill(255, 255, 255, 140)
    py5.text_size(20)
    py5.text(f"t={t:.2f}s | omega_g1: {G1_OMEGA:.2f} rad/s | grid: {GRID_W}x{GRID_H} | method: FSI Stable Fluids", 50, H - 50)
    
    # Blank screen safety check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)
            
    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")
        
    if frame == TOTAL_FRAMES // 2:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
