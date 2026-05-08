from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

# Add project root to path for lib imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Configuration
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PAIRS = 1200  # Pairs generated per frame
MAX_PARTICLES = 200000
RS = 180  # Schwarzschild radius in pixels
HORIZON_SHELL = RS * 1.1

# State
particles_pos = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)
particles_vel = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)
particles_life = np.zeros(MAX_PARTICLES, dtype=np.float32)
particles_type = np.zeros(MAX_PARTICLES, dtype=np.int8)  # 1: escaping, -1: falling
active_mask = np.zeros(MAX_PARTICLES, dtype=bool)

# Starfield
NUM_STARS = 10000
stars_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize background stars
    stars_pos[:, 0] = np.random.uniform(-py5.width * 2, py5.width * 2, NUM_STARS)
    stars_pos[:, 1] = np.random.uniform(-py5.height * 2, py5.height * 2, NUM_STARS)
    stars_pos[:, 2] = np.random.uniform(-2000, -500, NUM_STARS)

def update_simulation():
    global particles_pos, particles_vel, particles_life, active_mask, particles_type
    
    # 1. Emit new pairs at the horizon
    inactive_indices = np.where(~active_mask)[0]
    if len(inactive_indices) >= NUM_PAIRS * 2:
        new_indices = inactive_indices[:NUM_PAIRS * 2]
        
        # Random positions on a shell slightly outside RS
        phi = np.random.uniform(0, 2 * np.pi, NUM_PAIRS)
        theta = np.arccos(np.random.uniform(-1, 1, NUM_PAIRS))
        
        r = RS * (1.0 + np.random.uniform(0.01, 0.05, NUM_PAIRS))
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        
        # Set positions for both members of the pair
        particles_pos[new_indices[::2]] = np.stack([x, y, z], axis=1)
        particles_pos[new_indices[1::2]] = np.stack([x, y, z], axis=1)
        
        # Types: one escapes, one falls
        particles_type[new_indices[::2]] = 1
        particles_type[new_indices[1::2]] = -1
        
        # Initial velocities
        # Escaping: mostly radial out + some swirl
        # Falling: mostly radial in
        rad_vec = particles_pos[new_indices[::2]] / r[:, np.newaxis]
        # Swirl depends on latitude to create twisted "yarn" effect
        swirl_axis = np.array([0, 1, 0])
        swirl = np.cross(rad_vec, swirl_axis)
        
        # Escaping member: Stronger radial push + modulated swirl
        particles_vel[new_indices[::2]] = rad_vec * np.random.uniform(4, 8, (NUM_PAIRS, 1)) + \
                                          swirl * np.random.uniform(2, 6, (NUM_PAIRS, 1))
        
        # Falling member
        particles_vel[new_indices[1::2]] = -rad_vec * np.random.uniform(1, 4, (NUM_PAIRS, 1))
        
        particles_life[new_indices] = 1.0
        active_mask[new_indices] = True

    # 2. Update existing particles
    if np.any(active_mask):
        pos = particles_pos[active_mask]
        vel = particles_vel[active_mask]
        p_type = particles_type[active_mask]
        
        r_sq = np.sum(pos**2, axis=1)
        r = np.sqrt(r_sq)
        
        # Gravitational force (simplified 1/r^2)
        # In reality, near RS it's more complex, but we want aesthetic "escape vs consume"
        force_mag = 5000 / (r_sq + 100)
        accel = -pos * (force_mag / (r + 1e-5))[:, np.newaxis]
        
        # Escaping particles have "quantum boost" to overcome gravity
        accel[p_type == 1] *= 0.2 
        
        particles_vel[active_mask] += accel
        particles_pos[active_mask] += particles_vel[active_mask]
        
        # Decay life
        particles_life[active_mask] -= 0.005
        
        # Deactivate if:
        # - life <= 0
        # - falls inside RS
        # - goes too far away
        deactivate = (particles_life[active_mask] <= 0) | \
                     (r < RS * 0.5) | \
                     (r > 2000)
        
        # Map back to global mask
        active_indices = np.where(active_mask)[0]
        active_mask[active_indices[deactivate]] = False

def draw():
    update_simulation()
    
    py5.background(5, 5, 15) # Deep obsidian indigo
    
    # Camera
    py5.translate(py5.width / 2, py5.height / 2, -500)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.002)
    
    # 1. Draw Starfield
    py5.stroke(255, 255, 255, 150)
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    for p in stars_pos:
        py5.vertex(*p)
    py5.end_shape()
    
    # 2. Draw Black Hole Shadow (Sphere)
    py5.no_stroke()
    py5.fill(0)
    py5.push_matrix()
    # Shadow is actually RS * (something > 1) due to lensing, 
    # but for this abstract piece, let's keep it near RS.
    py5.sphere(RS * 0.9) 
    py5.pop_matrix()
    
    # 3. Draw Particles (Hawking Radiation)
    if np.any(active_mask):
        pos = particles_pos[active_mask]
        life = particles_life[active_mask]
        p_type = particles_type[active_mask]
        
        # Escaping particles: White-Gold
        # Falling particles: Indigo/Amethyst
        
        py5.begin_shape(py5.POINTS)
        for i in range(len(pos)):
            alpha = life[i] * 230
            if p_type[i] == 1:
                # White-Gold (Escaping)
                py5.stroke(255, 245, 220, alpha)
                py5.stroke_weight(2.0)
            else:
                # Electric Indigo (Falling)
                py5.stroke(140, 80, 255, alpha * 0.7)
                py5.stroke_weight(1.2)
            py5.vertex(*pos[i])
        py5.end_shape()
        
    # 4. Stretched Horizon Glow (Volumetric pulses)
    py5.push_matrix()
    py5.no_stroke()
    for i in range(3):
        # Pulsing shells of light
        s_r = RS * (1.0 + 0.1 * np.sin(py5.frame_count * 0.05 + i))
        alpha = 20 + 10 * np.sin(py5.frame_count * 0.03 + i)
        py5.fill(150, 100, 255, alpha)
        py5.sphere(s_r)
    py5.pop_matrix()

    # Video & Preview Save
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure ffmpeg is available and run
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            # Save middle frame as preview
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error during video encoding: {e}")

if __name__ == "__main__":
    py5.run_sketch()
