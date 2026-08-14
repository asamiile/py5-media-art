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
CENTER_X = SIM_W / 2
CENTER_Y = SIM_H / 2

# N-Body stars parameters (6 stars)
M = 6
star_pos = np.zeros((M, 2), dtype=np.float32)
star_vel = np.zeros((M, 2), dtype=np.float32)
star_base_mass = np.array([12000.0, 10000.0, 11000.0, 9000.0, 10000.0, 8000.0], dtype=np.float32)
star_mass = star_base_mass.copy()

# Initialize stars in slow orbital configuration around center
angles = np.linspace(0, 2 * np.pi, M, endpoint=False)
r_orbit = 280.0
star_pos[:, 0] = CENTER_X + np.cos(angles) * r_orbit
star_pos[:, 1] = CENTER_Y + np.sin(angles) * r_orbit

# Perpendicular velocity for orbits
star_vel[:, 0] = -np.sin(angles) * 1.8
star_vel[:, 1] =  np.cos(angles) * 1.8

# Test particles (massless tracers)
P = 1200
p_pos = np.zeros((P, 2), dtype=np.float32)
p_vel = np.zeros((P, 2), dtype=np.float32)

# Distribute test particles in a ring
p_angles = np.random.rand(P) * 2.0 * np.pi
p_radii = 200.0 + np.random.rand(P) * 180.0
p_pos[:, 0] = CENTER_X + np.cos(p_angles) * p_radii
p_pos[:, 1] = CENTER_Y + np.sin(p_angles) * p_radii

# Set initial velocity tangent to orbits
p_vel[:, 0] = -np.sin(p_angles) * 1.5
p_vel[:, 1] =  np.cos(p_angles) * 1.5

# Particle colors: HSB
p_colors = np.zeros((P, 3), dtype=np.float32)
for i in range(P):
    # Gradients of green-teal-blue
    p_colors[i] = [140.0 + np.random.rand() * 80.0, 85.0, 95.0]

# Telemetry: total mechanical energy of the stars
energy_history = []
img_rgb_mid = None


def update_n_body_physics(dt=0.2):
    """
    Computes gravity interactions between the stars and updates test particles.
    """
    global star_pos, star_vel, p_pos, p_vel, star_mass
    
    # 1. Modulate star masses over time using LFOs
    t = py5.frame_count * 0.015
    for i in range(M):
        star_mass[i] = star_base_mass[i] * (1.0 + 0.45 * np.sin(t + i * (2.0 * np.pi / M)))
        
    # Softening factor to prevent infinite division at singularities
    softening = 25.0
    
    # 2. Update Star-to-Star interactions
    for i in range(M):
        acc = np.zeros(2, dtype=np.float32)
        for j in range(M):
            if i == j:
                continue
            diff = star_pos[j] - star_pos[i]
            dist_sq = np.sum(diff ** 2) + softening
            dist = np.sqrt(dist_sq)
            # F = G * m1 * m2 / r^2 -> acc_i = G * m_j * r_dir / r^2
            acc += (diff / dist) * (star_mass[j] / dist_sq)
        star_vel[i] += acc * dt
        
    star_pos += star_vel * dt
    
    # Center containment: damp any drift of the system center of mass
    com_pos = np.mean(star_pos, axis=0)
    star_pos -= (com_pos - np.array([CENTER_X, CENTER_Y])) * 0.05
    
    # 3. Update Test Particle velocities from star gravity
    for i in range(M):
        diff = star_pos[i][None, :] - p_pos
        dist_sq = np.sum(diff ** 2, axis=1)[:, None] + softening
        dist = np.sqrt(dist_sq)
        p_vel += (diff / dist) * (star_mass[i] / dist_sq) * dt
        
    p_pos += p_vel * dt
    
    # Limit max particle speed to prevent extreme warp jumps
    p_speed = np.linalg.norm(p_vel, axis=1)
    max_speed = 12.0
    warp_mask = p_speed > max_speed
    p_vel[warp_mask] = (p_vel[warp_mask] / p_speed[warp_mask][:, None]) * max_speed
    
    # Contain test particles
    out_of_bounds = (p_pos[:, 0] < -200) | (p_pos[:, 0] > SIM_W + 200) | (p_pos[:, 1] < -200) | (p_pos[:, 1] > SIM_H + 200)
    # Respawn out-of-bound particles back in center ring
    if np.any(out_of_bounds):
        cnt = np.sum(out_of_bounds)
        p_angles_new = np.random.rand(cnt) * 2.0 * np.pi
        p_radii_new = 250.0 + np.random.rand(cnt) * 150.0
        p_pos[out_of_bounds, 0] = CENTER_X + np.cos(p_angles_new) * p_radii_new
        p_pos[out_of_bounds, 1] = CENTER_Y + np.sin(p_angles_new) * p_radii_new
        p_vel[out_of_bounds] = np.stack([-np.sin(p_angles_new) * 1.5, np.cos(p_angles_new) * 1.5], axis=-1)


def calculate_star_energy():
    """
    Computes total kinetic and gravitational potential energy of the stars.
    """
    ke = 0.5 * np.sum(star_mass * np.sum(star_vel ** 2, axis=1))
    pe = 0.0
    M_count = len(star_mass)
    for i in range(M_count):
        for j in range(i + 1, M_count):
            dist = np.linalg.norm(star_pos[i] - star_pos[j]) + 10.0
            pe -= (star_mass[i] * star_mass[j]) / dist
    return ke + pe


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 1, 8)


def draw():
    global img_rgb_mid
    
    # --- 1. Physics update ---
    update_n_body_physics()
    
    # Calculate energy telemetry
    total_energy = calculate_star_energy()
    energy_history.append(total_energy)
    if len(energy_history) > 300:
        energy_history.pop(0)
        
    # --- 2. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Slow fading trail overlay
    py5.fill(2, 1, 8, 14)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scale coordinates to 4K
    py5.push_matrix()
    py5.scale(SIZE[0] / SIM_W, SIZE[1] / SIM_H)
    
    # Additive blend mode for luminous orbits
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Draw star positions (tiny glowing cores)
    for i in range(M):
        py5.fill(40.0, 70.0, 95.0, 60)
        m_radius = np.sqrt(star_mass[i]) * 0.18
        py5.ellipse(star_pos[i, 0], star_pos[i, 1], m_radius, m_radius)
        
    # Draw test particles
    for i in range(P):
        px, py = p_pos[i]
        vx, vy = p_vel[i]
        
        # Color mapping: base hue modified by current particle velocity magnitude
        speed = np.sqrt(vx**2 + vy**2)
        h, s, b = p_colors[i]
        
        # Speed accent shifts towards Solar Amber Gold (Hue ~40) at high speed
        h_speed = h - min(speed * 12.0, 100.0)
        alpha = np.clip(100.0 + speed * 12.0, 100, 255)
        
        py5.stroke(h_speed, s, b, alpha)
        py5.stroke_weight(1.8)
        py5.line(px, py, px - vx * 1.5, py - vy * 1.5)
        
    py5.pop_matrix()
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("CHAOTIC N-BODY GRAVITY SIMULATOR // 2D MASSLESS PARTICLES", 50, 50)
    py5.text(f"TRACER COUNT: {P} | HEAVY ATTRACTORS (STARS): {M}", 50, 85)
    py5.text(f"MASS OSCILLATORS: {', '.join([f'{m/1000.0:.1f}k' for m in star_mass[:3]])}...", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"SYSTEM MECHANICAL ENERGY: {total_energy/1e5:.4f} kJ", SIZE[0] - 50, 85)
    
    # Energy Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("STARS TOTAL MECHANICAL ENERGY", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(0, 255, 187, 180)
    py5.begin_shape()
    for idx, val in enumerate(energy_history):
        xx = gx + idx * (graph_w / 300)
        # Normalize energy range to fit graph
        yy = gy + graph_h - ((val + 1.2e8) / 8e7) * (graph_h - 15) - 5
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
