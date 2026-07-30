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

# Fluid grid / simulation scale
CYLINDER_X = 400.0
CYLINDER_Y = 1080.0
CYLINDER_R = 140.0

# Flow parameters
U_FLOW = 7.0
VORTEX_CORE = 40.0
SHED_INTERVAL = 30  # Frames between vortex shedding

# Vortices list
vortices = []
shed_side = 0  # 0 = Top, 1 = Bottom

# Particles
N_PARTICLES = 40000
particles_pos = None
particles_vel = None


def setup():
    global particles_pos, particles_vel
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles uniformly in the channel
    np.random.seed(42)
    particles_pos = np.zeros((N_PARTICLES, 2), dtype=np.float32)
    particles_pos[:, 0] = np.random.uniform(0, SIZE[0], N_PARTICLES)
    particles_pos[:, 1] = np.random.uniform(0, SIZE[1], N_PARTICLES)
    particles_vel = np.zeros((N_PARTICLES, 2), dtype=np.float32)


def get_velocity_and_vorticity(px, py):
    """
    Vectorized computation of fluid velocity and local vortex proximity.
    """
    dx = px - CYLINDER_X
    dy = py - CYLINDER_Y
    r2 = dx * dx + dy * dy + 1e-5
    
    # 1. Potential Flow around Cylinder
    factor = (CYLINDER_R ** 2) / r2
    vx = U_FLOW * (1.0 - factor * (dx * dx - dy * dy) / r2)
    vy = U_FLOW * (-factor * 2.0 * dx * dy / r2)
    
    # Inside the cylinder, force velocity to zero
    inside = r2 < (CYLINDER_R ** 2)
    vx[inside] = 0.0
    vy[inside] = 0.0
    
    # 2. Point Vortex Street Induction + Vorticity signature tracking
    vorticity_sig = np.zeros_like(px, dtype=np.float32)
    
    for v in vortices:
        vdx = px - v["x"]
        vdy = py - v["y"]
        vr2 = vdx * vdx + vdy * vdy + 1e-5
        
        # Core-smoothed velocity: v = gamma * (-y, x) / (2 * pi * (r^2 + core^2))
        factor_v = v["gamma"] / (2.0 * np.pi * (vr2 + VORTEX_CORE ** 2))
        vx += factor_v * (-vdy)
        vy += factor_v * vdx
        
        # Accumulate localized vorticity field influence for coloring
        influence = np.exp(-vr2 / (3.0 * CYLINDER_R) ** 2)
        vorticity_sig += (v["gamma"] / 5000.0) * influence
        
    return vx, vy, vorticity_sig


def update_vortices():
    global shed_side
    # 1. Spawn a new vortex at shed interval
    if py5.frame_count % SHED_INTERVAL == 0:
        if shed_side == 0:
            # Spawn top: clockwise vortex (negative gamma)
            vortices.append({
                "x": CYLINDER_X + 1.1 * CYLINDER_R,
                "y": CYLINDER_Y + 0.8 * CYLINDER_R,
                "gamma": -7500.0,
            })
            shed_side = 1
        else:
            # Spawn bottom: counter-clockwise vortex (positive gamma)
            vortices.append({
                "x": CYLINDER_X + 1.1 * CYLINDER_R,
                "y": CYLINDER_Y - 0.8 * CYLINDER_R,
                "gamma": 7500.0,
            })
            shed_side = 0
            
    # 2. Advect existing vortices based on velocity field induced by cylinder and other vortices
    for i, v in enumerate(vortices):
        dx = v["x"] - CYLINDER_X
        dy = v["y"] - CYLINDER_Y
        r2 = dx * dx + dy * dy + 1e-5
        
        # Background potential flow velocity
        factor = (CYLINDER_R ** 2) / r2
        vx = U_FLOW * (1.0 - factor * (dx * dx - dy * dy) / r2)
        vy = U_FLOW * (-factor * 2.0 * dx * dy / r2)
        
        # Induced velocity from all other vortices
        for j, other in enumerate(vortices):
            if i == j:
                continue
            vdx = v["x"] - other["x"]
            vdy = v["y"] - other["y"]
            vr2 = vdx * vdx + vdy * vdy + 1e-5
            factor_v = other["gamma"] / (2.0 * np.pi * (vr2 + VORTEX_CORE ** 2))
            vx += factor_v * (-vdy)
            vy += factor_v * vdx
            
        v["x"] += vx
        v["y"] += vy
        
        # Slow decay of circulation strength as vortex advects downstream
        v["gamma"] *= 0.993
        
    # Remove old vortices that go off screen
    vortices[:] = [v for v in vortices if v["x"] < SIZE[0] + 300]


def draw():
    global particles_pos, particles_vel
    
    # Translucent deep void overlay for long glowing ribbon trails
    py5.fill(4, 3, 15, 14)  # Low alpha creates smooth, persistent streamlines
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # 1. Update physics
    update_vortices()
    
    px = particles_pos[:, 0]
    py = particles_pos[:, 1]
    
    vx, vy, vorticity_sig = get_velocity_and_vorticity(px, py)
    
    # Advect particles
    particles_pos[:, 0] += vx
    particles_pos[:, 1] += vy
    
    # Subtle random thermal drift
    particles_pos[:, 0] += np.random.normal(0, 0.2, N_PARTICLES)
    particles_pos[:, 1] += np.random.normal(0, 0.2, N_PARTICLES)
    
    # Wrap particles that exit right, top, or bottom
    off_screen = (particles_pos[:, 0] > SIZE[0]) | (particles_pos[:, 1] < -50) | (particles_pos[:, 1] > SIZE[1] + 50)
    particles_pos[off_screen, 0] = np.random.uniform(-100.0, 0.0, np.sum(off_screen))
    particles_pos[off_screen, 1] = np.random.uniform(0, SIZE[1], np.sum(off_screen))
    
    # Draw cylinder obstacle as dark solid circle with hot pink glowing boundary
    py5.fill(2, 2, 8)
    py5.stroke(255, 45, 85, 200)  # Neon crimson border
    py5.stroke_weight(7.0)
    py5.ellipse(CYLINDER_X, CYLINDER_Y, CYLINDER_R * 2.0, CYLINDER_R * 2.0)
    
    # Draw particles with color mapped dynamically based on vorticity signature:
    # Clockwise vortices (vorticity < 0) -> Glowing Coral/Crimson
    # Counter-Clockwise vortices (vorticity > 0) -> Glowing Cyan/Blue
    # Free-stream flow (vorticity approx 0) -> Deep Indigo/Purple
    
    # Categorize particles into 3 color bands for ultra-fast vectorized drawing
    cyan_mask = vorticity_sig > 0.15
    magenta_mask = vorticity_sig < -0.15
    bg_mask = ~(cyan_mask | magenta_mask)
    
    # Draw background flow particles (Deep Sapphire / Violet)
    py5.stroke_weight(1.5)
    py5.stroke(79, 70, 229, 65)  # Indigo
    xs_bg = particles_pos[bg_mask, 0]
    ys_bg = particles_pos[bg_mask, 1]
    for i in range(len(xs_bg)):
        py5.point(xs_bg[i], ys_bg[i])
        
    # Draw counter-clockwise vortices (Electric Cyan)
    py5.stroke_weight(2.0)
    xs_cy = particles_pos[cyan_mask, 0]
    ys_cy = particles_pos[cyan_mask, 1]
    sig_cy = vorticity_sig[cyan_mask]
    for i in range(len(xs_cy)):
        alpha = int(min(80 + 175 * sig_cy[i], 255))
        py5.stroke(6, 182, 212, alpha)
        py5.point(xs_cy[i], ys_cy[i])
        
    # Draw clockwise vortices (Neon Magenta / Pink)
    py5.stroke_weight(2.0)
    xs_ma = particles_pos[magenta_mask, 0]
    ys_ma = particles_pos[magenta_mask, 1]
    sig_ma = -vorticity_sig[magenta_mask]
    for i in range(len(xs_ma)):
        alpha = int(min(80 + 175 * sig_ma[i], 255))
        py5.stroke(244, 63, 94, alpha)
        py5.point(xs_ma[i], ys_ma[i])
        
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
