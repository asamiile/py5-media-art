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
# Pre-collision: frame 0 to 240
# Post-collision: frame 240 to 600
COLLISION_FRAME = 240
NUM_PARTICLES = 300000

# Binary state
phase = 0
radius = 400
decay_rate = 0.992 # Spirals in

# Ejecta state
ejecta_pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
ejecta_vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
ejecta_active = np.zeros(NUM_PARTICLES, dtype=bool)

# Starfield
NUM_STARS = 8000
stars_pos = np.random.uniform(-2000, 2000, (NUM_STARS, 3)).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global phase, radius
    f = py5.frame_count
    t_collision = f / COLLISION_FRAME
    
    py5.background(10, 5, 25) # Deep night
    
    # Camera
    py5.translate(py5.width / 2, py5.height / 2, -1000)
    py5.rotate_x(0.5) # Slight tilt
    py5.rotate_y(f * 0.005)
    
    # 1. Background Stars with Space-time Ripples
    # Frequency of ripples increases as stars get closer
    ripple_freq = 0.05 if f < COLLISION_FRAME else 0.02
    ripple_amp = 30 * (1.0 - radius/400.0) if f < COLLISION_FRAME else 10 * np.exp(-(f-COLLISION_FRAME)/100)
    
    py5.stroke(200, 200, 255, 150)
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    for p in stars_pos:
        # Distortion
        dist = np.linalg.norm(p)
        offset = ripple_amp * np.sin(dist * ripple_freq - f * 0.5)
        py5.vertex(p[0] + offset, p[1] + offset, p[2])
    py5.end_shape()

    if f < COLLISION_FRAME:
        # Binary phase
        phase += 0.05 + (1.0 - radius/400.0) * 0.5
        radius *= decay_rate
        
        x1 = radius * np.cos(phase)
        y1 = radius * np.sin(phase)
        z1 = 0
        
        x2 = -x1
        y2 = -y1
        z2 = 0
        
        # Draw neutron stars
        py5.no_stroke()
        py5.fill(200, 220, 255)
        py5.push_matrix()
        py5.translate(x1, y1, z1)
        py5.sphere(10)
        py5.pop_matrix()
        
        py5.push_matrix()
        py5.translate(x2, y2, z2)
        py5.sphere(10)
        py5.pop_matrix()
        
        # Accretion tail/bridge
        py5.stroke(150, 180, 255, 100)
        py5.stroke_weight(2)
        py5.line(x1, y1, z1, x2, y2, z2)

    elif f == COLLISION_FRAME:
        # Trigger Ejection
        # Toroidal ejecta + polar jets
        for i in range(NUM_PARTICLES):
            # Polar vs Toroidal
            if np.random.rand() > 0.8: # Polar jets
                side = 1 if np.random.rand() > 0.5 else -1
                ejecta_vel[i] = [np.random.normal(0, 1), np.random.normal(0, 1), side * np.random.uniform(15, 30)]
            else: # Toroidal
                ang = np.random.uniform(0, 2 * np.pi)
                tilt = np.random.uniform(-0.5, 0.5)
                mag = np.random.uniform(5, 15)
                ejecta_vel[i] = [mag * np.cos(ang), mag * np.sin(ang), mag * tilt]
            ejecta_active[i] = True
            ejecta_pos[i] = [0, 0, 0]

    else:
        # Post-collision expansion
        ejecta_pos[ejecta_active] += ejecta_vel[ejecta_active]
        # Deceleration/cooling
        ejecta_vel[ejecta_active] *= 0.99
        
        # Render Ejecta
        # Platinum/Rose Gold colors
        py5.begin_shape(py5.POINTS)
        # Step for performance
        active_indices = np.where(ejecta_active)[0][::3]
        t_post = (f - COLLISION_FRAME) / (TOTAL_FRAMES - COLLISION_FRAME)
        
        # Color shift: Blue -> White -> Rose Gold -> Platinum
        if t_post < 0.2:
            r, g, b = 255, 255, 255 # Blinding
        elif t_post < 0.6:
            r, g, b = 255, 180, 200 # Rose Gold
        else:
            r, g, b = 220, 220, 240 # Platinum
            
        for idx in active_indices:
            p = ejecta_pos[idx]
            alpha = (1.0 - t_post) * 200
            py5.stroke(r, g, b, alpha)
            py5.stroke_weight(1.2)
            py5.vertex(*p)
        py5.end_shape()
        
        # Central Fireball
        fireball_size = 50 * np.exp(-(f - COLLISION_FRAME)/50)
        if fireball_size > 1:
            py5.no_stroke()
            py5.fill(255, 255, 255, 255 * (fireball_size/50))
            py5.sphere(fireball_size)

    # Video & Preview Save
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if f >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            # Use a frame post-collision for preview
            mid = str(FRAMES_DIR / f"frame-{COLLISION_FRAME + 100:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error during video encoding: {e}")

if __name__ == "__main__":
    py5.run_sketch()
