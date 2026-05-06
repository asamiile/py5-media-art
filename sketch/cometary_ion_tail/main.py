from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Nucleus orbit: Elliptical
# Tail particles: [x, y, z, vx, vy, vz, type, life]
# type: 0 = Dust, 1 = Ion
NUM_PARTICLES = 60000
particles = np.zeros((NUM_PARTICLES, 8))
# Pointer to next particle to emit
p_idx = 0

def setup():
    global particles
    py5.size(*SIZE, py5.P3D)
    py5.background(2, 2, 10)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles as dead
    particles[:, 7] = -1.0

def draw():
    global particles, p_idx
    py5.background(0, 0, 4)
    
    t = py5.frame_count / FPS
    
    # Background stars
    np.random.seed(42)
    for _ in range(300):
        x_s, y_s = np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])
        z_s = np.random.uniform(-1000, -200)
        py5.stroke(0, 0, 100, 30)
        py5.stroke_weight(np.random.uniform(0.5, 1.5))
        py5.point(x_s, y_s, z_s)
    np.random.seed(None)

    # Nucleus position (Orbit)
    # Slow movement across the screen
    nx = py5.remap(t, 0, DURATION_SEC, -600, 600)
    ny = 150 * np.sin(t * 0.5)
    nz = 100 * np.cos(t * 0.5)
    n_pos = np.array([nx, ny, nz])
    
    # Nucleus velocity
    dt = 1/FPS
    nx_next = py5.remap(t + dt, 0, DURATION_SEC, -600, 600)
    ny_next = 150 * np.sin((t + dt) * 0.5)
    nz_next = 100 * np.cos((t + dt) * 0.5)
    n_vel = (np.array([nx_next, ny_next, nz_next]) - n_pos) / dt
    
    # Emit particles (Denser)
    emit_count = 450
    for _ in range(emit_count):
        particles[p_idx, 0:3] = n_pos + np.random.normal(0, 3, 3)
        p_type = 0 if np.random.random() < 0.75 else 1 # 75% Dust
        particles[p_idx, 6] = p_type
        
        if p_type == 0: # Dust
            particles[p_idx, 3:6] = n_vel * 0.75 + np.random.normal(0, 2.5, 3)
            particles[p_idx, 7] = np.random.uniform(150, 400) # Longer life
        else: # Ion
            particles[p_idx, 3:6] = n_vel * 1.3 + np.random.normal(0, 0.8, 3)
            particles[p_idx, 7] = np.random.uniform(80, 200) # Life
            
        p_idx = (p_idx + 1) % NUM_PARTICLES

    # Simulation
    active = particles[:, 7] > 0
    pos = particles[active, 0:3]
    vel = particles[active, 3:6]
    p_type = particles[active, 6]
    life = particles[active, 7]
    
    # Forces
    solar_dir = np.array([0, -1, -0.2])
    solar_dir /= np.linalg.norm(solar_dir)
    
    # Ion tail "wispiness" (Noise-driven solar wind)
    ion_mask = (p_type == 1)
    if np.any(ion_mask):
        # Adding some "turbulence" to ion tail
        noise_vec = np.array([
            py5.noise(t * 2.0, 10) - 0.5,
            py5.noise(t * 2.0, 20) - 0.5,
            py5.noise(t * 2.0, 30) - 0.5
        ]) * 0.4
        vel[ion_mask] += (solar_dir + noise_vec) * 1.2
    
    # Dust tail (Inertia + weak pressure)
    dust_mask = (p_type == 0)
    if np.any(dust_mask):
        vel[dust_mask] += solar_dir * 0.18
    
    vel *= 0.985 # Drag
    pos += vel
    life -= 1.0
    
    particles[active, 0:3] = pos
    particles[active, 3:6] = vel
    particles[active, 7] = life
    
    # Rendering
    py5.push_matrix()
    py5.translate(SIZE[0]//2, SIZE[1]//2, 0)
    py5.rotate_y(t * 0.05)
    
    # Render Coma (Glow around nucleus)
    py5.no_stroke()
    for i in range(12):
        py5.fill(200, 20, 100, 12 - i)
        py5.push_matrix()
        py5.translate(*n_pos)
        py5.sphere(4 + i * 5)
        py5.pop_matrix()
    
    # Render Tail
    # Dust Tail: Golden/Amber
    mask_dust = active & (particles[:, 6] == 0)
    if np.any(mask_dust):
        d_life = particles[mask_dust, 7]
        # Multi-pass for shimmer
        py5.stroke(45, 80, 90, 4)
        py5.stroke_weight(3.5)
        py5.points(particles[mask_dust, 0:3])
        
        py5.stroke(45, 40, 100, 15)
        py5.stroke_weight(1.0)
        py5.points(particles[mask_dust, 0:3])
        
    # Ion Tail: Electric Blue
    mask_ion = active & (particles[:, 6] == 1)
    if np.any(mask_ion):
        py5.stroke(200, 100, 100, 8)
        py5.stroke_weight(4.5)
        py5.points(particles[mask_ion, 0:3])
        
        py5.stroke(190, 40, 100, 35)
        py5.stroke_weight(1.5)
        py5.points(particles[mask_ion, 0:3])
        
    py5.pop_matrix()

    # Save frames and exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
