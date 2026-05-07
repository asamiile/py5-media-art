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
NUM_VORTICES = 19 # Hexagonal lattice: 1 (center) + 6 + 12
VORTEX_HEIGHT = 800
NUM_PARTICLES_PER_VORTEX = 1500
TOTAL_PARTICLES = NUM_VORTICES * NUM_PARTICLES_PER_VORTEX

# Vortex positions (Hexagonal lattice)
vortex_base_pos = []
vortex_base_pos.append([0, 0]) # Center
for i in range(6):
    ang = i * (2 * np.pi / 6)
    vortex_base_pos.append([200 * np.cos(ang), 200 * np.sin(ang)])
for i in range(12):
    ang = i * (2 * np.pi / 12)
    vortex_base_pos.append([400 * np.cos(ang), 400 * np.sin(ang)])
vortex_base_pos = np.array(vortex_base_pos, dtype=np.float32)

# Particle states
particles_pos = np.zeros((TOTAL_PARTICLES, 3), dtype=np.float32)
# Initialize particles along the vortex lines
for v in range(NUM_VORTICES):
    for p in range(NUM_PARTICLES_PER_VORTEX):
        idx = v * NUM_PARTICLES_PER_VORTEX + p
        z = np.random.uniform(-VORTEX_HEIGHT/2, VORTEX_HEIGHT/2)
        particles_pos[idx] = [vortex_base_pos[v, 0], vortex_base_pos[v, 1], z]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    f = py5.frame_count
    t = f / TOTAL_FRAMES
    
    py5.background(5, 5, 25) # Deep navy
    
    # Camera
    py5.translate(py5.width / 2, py5.height / 2, -1000)
    py5.rotate_x(0.6 + 0.2 * np.sin(f * 0.01))
    py5.rotate_z(f * 0.005)
    
    # Superfluid Phase Transition Logic
    # Transition to turbulence starts at frame 300
    turbulence = 0.0
    if f > 300:
        turbulence = (f - 300) / (TOTAL_FRAMES - 300)
    
    # Update Vortices and Particles
    # Kelvin waves + Turbulence
    for v in range(NUM_VORTICES):
        v_base = vortex_base_pos[v]
        p_idx = np.arange(v * NUM_PARTICLES_PER_VORTEX, (v + 1) * NUM_PARTICLES_PER_VORTEX)
        
        # Helical Kelvin Waves
        z = particles_pos[p_idx, 2]
        wave_freq = 0.02 + turbulence * 0.1
        wave_amp = 10 + turbulence * 150
        
        phase = z * wave_freq + f * 0.2
        offset_x = wave_amp * np.cos(phase)
        offset_y = wave_amp * np.sin(phase)
        
        # Turbulent drift
        if turbulence > 0:
            offset_x += turbulence * 200 * np.sin(z * 0.005 + f * 0.05 + v)
            offset_y += turbulence * 200 * np.cos(z * 0.005 + f * 0.04 + v)
            
        # Circular rotation around vortex core
        rot_phase = f * 0.1 + z * 0.01
        rot_r = 5 + turbulence * 20
        rot_x = rot_r * np.cos(rot_phase)
        rot_y = rot_r * np.sin(rot_phase)
        
        particles_pos[p_idx, 0] = v_base[0] + offset_x + rot_x
        particles_pos[p_idx, 1] = v_base[1] + offset_y + rot_y
        # Particles drift upward slowly
        particles_pos[p_idx, 2] += 2
        # Wrap particles
        particles_pos[p_idx, 2] = ((particles_pos[p_idx, 2] + VORTEX_HEIGHT/2) % VORTEX_HEIGHT) - VORTEX_HEIGHT/2

    # Render Particles
    # Ordered phase: Cyan/Indigo. Turbulent phase: Gold sparkles.
    py5.stroke_weight(1.5)
    
    # Sub-sample for performance
    step = 2
    for v in range(NUM_VORTICES):
        p_idx = np.arange(v * NUM_PARTICLES_PER_VORTEX, (v + 1) * NUM_PARTICLES_PER_VORTEX, step)
        
        # Color based on turbulence
        if turbulence < 0.2:
            py5.stroke(150, 220, 255, 180) # Pale Cyan
        elif turbulence < 0.6:
            py5.stroke(180, 150, 255, 180) # Pale Violet
        else:
            # Shimmering Gold
            if np.random.rand() > 0.5:
                py5.stroke(255, 220, 150, 200)
            else:
                py5.stroke(255, 255, 255, 200)
        
        py5.points(particles_pos[p_idx])
        
    # Render Vortex Lines (only in ordered phase)
    if turbulence < 0.5:
        py5.no_fill()
        py5.stroke(255, 255, 255, 50 * (1.0 - turbulence * 2))
        py5.stroke_weight(1)
        for v in range(NUM_VORTICES):
            v_base = vortex_base_pos[v]
            py5.begin_shape()
            for z_val in np.linspace(-VORTEX_HEIGHT/2, VORTEX_HEIGHT/2, 20):
                wave_amp = 10 + turbulence * 150
                phase = z_val * (0.02 + turbulence * 0.1) + f * 0.2
                off_x = wave_amp * np.cos(phase)
                off_y = wave_amp * np.sin(phase)
                py5.vertex(v_base[0] + off_x, v_base[1] + off_y, z_val)
            py5.end_shape()

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
            # Use a frame in the turbulent phase for preview
            mid = str(FRAMES_DIR / f"frame-{450:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error during video encoding: {e}")

if __name__ == "__main__":
    py5.run_sketch()
