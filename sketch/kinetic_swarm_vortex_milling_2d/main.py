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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation grid/coordinate space: 1920x1080 scaled to 4K
SIM_W = 1920
SIM_H = 1080
CENTER_X = SIM_W / 2
CENTER_Y = SIM_H / 2

# Swarm parameters
N = 1200
s_0 = 3.5          # Constant speed
max_steer = 0.20   # Maximum angular change per step
noise_std = 0.08   # Angular noise

# Interaction radii (Couzin model)
R_rep = 16.0       # Repulsion
R_ori = 48.0       # Orientation
R_att = 130.0      # Attraction

# Particle states
pos = np.random.rand(N, 2) * 300.0 + np.array([CENTER_X - 150, CENTER_Y - 150])
theta = np.random.rand(N) * 2.0 * np.pi
vel = s_0 * np.stack([np.cos(theta), np.sin(theta)], axis=-1)

# Telemetry data holders
polar_orders = []
angular_momenta = []
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    # Recreate clean frames directory
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial background
    py5.background(4, 3, 15)


def angle_diff(a, b):
    """Computes signed difference between angles a and b, wrapped to [-pi, pi]."""
    return (a - b + np.pi) % (2.0 * np.pi) - np.pi


def draw():
    global pos, theta, vel, img_rgb_mid
    
    # --- 1. Physics: Couzin Agent Swarm Update ---
    # Compute relative vectors and distances
    diff = pos[:, None, :] - pos[None, :, :]  # Shape: (N, N, 2)
    dist = np.linalg.norm(diff, axis=-1)      # Shape: (N, N)
    
    # Set diagonal to infinity to ignore self-interaction
    np.fill_diagonal(dist, np.inf)
    
    # Desired directions
    desired_theta = theta.copy()
    
    # Slowly modulate attraction radius to trigger dynamic state changes over time
    t_cycle = py5.frame_count * 0.003
    dynamic_R_att = R_att + 40.0 * np.sin(t_cycle)
    
    # Vectorized computation of forces
    for i in range(N):
        d_i = dist[i]
        diff_i = diff[i]
        
        # 1. Repulsion Zone
        rep_mask = d_i < R_rep
        if np.any(rep_mask):
            # Move away from close neighbors
            rep_vecs = -diff_i[rep_mask] / d_i[rep_mask][:, None]
            avg_rep = np.mean(rep_vecs, axis=0)
            desired_theta[i] = np.arctan2(avg_rep[1], avg_rep[0])
            continue
            
        # 2. Orientation & Attraction Zones
        ori_mask = (d_i >= R_rep) & (d_i < R_ori)
        att_mask = (d_i >= R_ori) & (d_i < dynamic_R_att)
        
        has_ori = np.any(ori_mask)
        has_att = np.any(att_mask)
        
        if has_ori and has_att:
            # Average orientation directions + attraction directions
            ori_vec = np.mean(vel[ori_mask], axis=0)
            att_vec = np.mean(diff_i[att_mask] / d_i[att_mask][:, None], axis=0)
            
            # Normalize vectors
            ori_vec_n = ori_vec / (np.linalg.norm(ori_vec) + 1e-6)
            att_vec_n = att_vec / (np.linalg.norm(att_vec) + 1e-6)
            
            combined = ori_vec_n + att_vec_n
            desired_theta[i] = np.arctan2(combined[1], combined[0])
        elif has_ori:
            ori_vec = np.mean(vel[ori_mask], axis=0)
            desired_theta[i] = np.arctan2(ori_vec[1], ori_vec[0])
        elif has_att:
            att_vec = np.mean(diff_i[att_mask] / d_i[att_mask][:, None], axis=0)
            desired_theta[i] = np.arctan2(att_vec[1], att_vec[0])
            
    # Steer angles towards desired directions
    diff_angles = angle_diff(desired_theta, theta)
    steer = np.clip(diff_angles, -max_steer, max_steer)
    
    # Add angular noise
    noise = np.random.normal(0.0, noise_std, N)
    theta = theta + steer + noise
    
    # Boundary steer (soft circular containment)
    to_center = np.array([CENTER_X, CENTER_Y]) - pos
    dist_to_center = np.linalg.norm(to_center, axis=-1)
    boundary_mask = dist_to_center > 420.0
    
    if np.any(boundary_mask):
        center_theta = np.arctan2(to_center[boundary_mask, 1], to_center[boundary_mask, 0])
        diff_center = angle_diff(center_theta, theta[boundary_mask])
        theta[boundary_mask] += np.clip(diff_center, -0.15, 0.15)
        
    # Update velocities and positions
    vel = s_0 * np.stack([np.cos(theta), np.sin(theta)], axis=-1)
    pos += vel
    
    # --- 2. Telemetry Calculation ---
    # Polar Order Parameter (consensus/flocking index): ||Sum(v_i)|| / (N * s_0)
    avg_vel = np.mean(vel, axis=0)
    polar_order = np.linalg.norm(avg_vel) / s_0
    polar_orders.append(polar_order)
    
    # Angular Momentum (milling vortex index) about center
    r_vec = pos - np.array([CENTER_X, CENTER_Y])
    r_norm = r_vec / (np.linalg.norm(r_vec, axis=-1)[:, None] + 1e-6)
    # Cross product r_i x v_i in 2D
    cross_p = r_norm[:, 0] * vel[:, 1] - r_norm[:, 1] * vel[:, 0]
    ang_momentum = np.abs(np.mean(cross_p)) / s_0
    angular_momenta.append(ang_momentum)
    
    # Limit telemetry arrays length
    if len(polar_orders) > 300:
        polar_orders.pop(0)
        angular_momenta.pop(0)
        
    # --- 3. Rendering ---
    # Normal blend mode to draw the semi-transparent black fade rectangle (creates trails)
    py5.blend_mode(py5.BLEND)
    py5.fill(4, 3, 15, 12)  # Low alpha for long glowing trails
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scale simulation coordinate space (1920x1080) to 4K canvas (3840x2160)
    py5.push_matrix()
    py5.scale(SIZE[0] / SIM_W, SIZE[1] / SIM_H)
    
    # Draw containment boundary ring
    py5.stroke(255, 255, 255, 8)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.ellipse(CENTER_X, CENTER_Y, 840, 840)
    
    # Additive blend mode for intense glowing particles
    py5.blend_mode(py5.ADD)
    
    # Draw particles with speed/direction dependent color mapping
    py5.stroke_weight(2.5)
    py5.color_mode(py5.HSB, 360, 100, 100)
    
    for i in range(N):
        px, py = pos[i]
        vx, vy = vel[i]
        th = theta[i]
        
        # Color mapping: Map angle of movement to HSB color wheel
        hue = (th % (2.0 * np.pi)) / (2.0 * np.pi) * 360.0
        
        # Draw a tiny glowing vector arrow
        py5.stroke(hue, 85, 95, 160)  # Semi-transparent for smooth overlapping glow
        py5.line(px, py, px - vx * 2.2, py - vy * 2.2)
        
    py5.pop_matrix()
    
    # Switch back to normal blend mode for Telemetry HUD text
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render native 4K HUD Overlay
    py5.no_stroke()
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text(f"ACTIVE MATTER SPECTROMETER // SWARM VORTEX MILLING", 50, 50)
    py5.text(f"PARTICLE COUNT: {N:04d} | BASE SPEED: {s_0:.2f}", 50, 85)
    py5.text(f"RADII: Rep={R_rep:.1f}, Ori={R_ori:.1f}, Att={dynamic_R_att:.1f}", 50, 120)
    
    # Determine current swarm phase
    phase_str = "DISORGANIZED SWARM"
    if ang_momentum > 0.65:
        phase_str = "VORTEX MILLING STATE"
    elif polar_order > 0.75:
        phase_str = "PARALLEL FLOCKING STATE"
        
    py5.text(f"CURRENT SYSTEM STATE: {phase_str}", 50, 155)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"POLAR ORDER (FLOCKING): {polar_order:.4f}", SIZE[0] - 50, 85)
    py5.text(f"ANGULAR MOMENTUM (MILLING): {ang_momentum:.4f}", SIZE[0] - 50, 120)
    
    # Draw simple HUD graphs for the parameters
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    
    # Graph 1: Polar Order history
    graph_w, graph_h = 240, 80
    gx1, gy1 = SIZE[0] - 290, 170
    py5.rect(gx1, gy1, graph_w, graph_h)
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("POLAR ORDER HIST", gx1 + 5, gy1 + 5)
    
    py5.no_fill()
    py5.stroke(255, 150, 50, 150)
    py5.begin_shape()
    for idx, val in enumerate(polar_orders):
        xx = gx1 + idx * (graph_w / 300)
        yy = gy1 + graph_h - val * (graph_h - 10) - 5
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Graph 2: Angular Momentum history
    gx2, gy2 = SIZE[0] - 290, 270
    py5.stroke(255, 255, 255, 80)
    py5.rect(gx2, gy2, graph_w, graph_h)
    py5.fill(255, 255, 255, 120)
    py5.text("ANG MOMENTUM HIST", gx2 + 5, gy2 + 5)
    
    py5.no_fill()
    py5.stroke(50, 200, 255, 150)
    py5.begin_shape()
    for idx, val in enumerate(angular_momenta):
        xx = gx2 + idx * (graph_w / 300)
        yy = gy2 + graph_h - val * (graph_h - 10) - 5
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
