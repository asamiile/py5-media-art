from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
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

# Particle setup
NUM_PARTICLES = 150000
particles_x = np.zeros(NUM_PARTICLES, dtype=np.float32)
particles_y = np.zeros(NUM_PARTICLES, dtype=np.float32)
particles_age = np.zeros(NUM_PARTICLES, dtype=np.float32)
particles_life = np.zeros(NUM_PARTICLES, dtype=np.float32)

# Vortex details
vortices_x = []
vortices_y = []
vortices_strength = []
vortices_radius = []

def init_particles(indices):
    n = len(indices)
    particles_x[indices] = np.random.uniform(0, SIZE[0], n)
    particles_y[indices] = np.random.uniform(0, SIZE[1], n)
    particles_age[indices] = 0
    particles_life[indices] = np.random.uniform(60, 240, n)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles
    init_particles(np.arange(NUM_PARTICLES))
    
    # Create random swirling centers (vortices)
    num_vortices = random.randint(3, 6)
    for _ in range(num_vortices):
        vortices_x.append(random.uniform(SIZE[0] * 0.2, SIZE[0] * 0.8))
        vortices_y.append(random.uniform(SIZE[1] * 0.2, SIZE[1] * 0.8))
        vortices_strength.append(random.choice([-1.0, 1.0]) * random.uniform(8.0, 25.0))
        vortices_radius.append(random.uniform(150.0, 450.0))

def draw():
    global particles_x, particles_y, particles_age, particles_life
    
    # Custom semi-transparent background logic for elegant trails
    py5.no_stroke()
    py5.fill(0, 0, 0, 12)
    py5.rect(0, 0, *SIZE)
    
    # Calculate velocity field at particle positions using numpy vectorization
    vx = np.zeros(NUM_PARTICLES, dtype=np.float32)
    vy = np.zeros(NUM_PARTICLES, dtype=np.float32)
    
    # Apply vortex velocities
    for vx_pos, vy_pos, strength, radius in zip(vortices_x, vortices_y, vortices_strength, vortices_radius):
        dx = particles_x - vx_pos
        dy = particles_y - vy_pos
        d_sq = dx*dx + dy*dy + 1e-4
        d = np.sqrt(d_sq)
        
        # Swirling velocity vector: (-dy, dx) normalized and scaled
        influence = np.exp(-d / radius)
        speed = strength * influence * (1.0 / (d + 10.0)) * 50.0
        
        vx += (-dy / d) * speed
        vy += (dx / d) * speed

    # Add Perlin noise field components
    scale = 0.003
    for i in range(0, NUM_PARTICLES, 5000):
        chunk_size = min(5000, NUM_PARTICLES - i)
        px = particles_x[i:i+chunk_size]
        py = particles_y[i:i+chunk_size]
        
        # Querying noise field
        angles = np.array([py5.noise(x * scale, y * scale, py5.frame_count * 0.005) * py5.TWO_PI * 2.0 for x, y in zip(px, py)], dtype=np.float32)
        vx[i:i+chunk_size] += np.cos(angles) * 1.5
        vy[i:i+chunk_size] += np.sin(angles) * 1.5

    # Update particle positions
    particles_x += vx
    particles_y += vy
    particles_age += 1.0
    
    # Wrap or re-initialize dead / out of bound particles
    oob = (particles_x < 0) | (particles_x > SIZE[0]) | (particles_y < 0) | (particles_y > SIZE[1])
    dead = particles_age >= particles_life
    reset_mask = oob | dead
    
    reset_indices = np.where(reset_mask)[0]
    if len(reset_indices) > 0:
        init_particles(reset_indices)
        
    # Draw particles via load_np_pixels for extremely fast rendering at 4K
    py5.load_np_pixels()
    
    # Calculate color based on age fraction
    life_fraction = particles_age / particles_life
    
    # Vectorized color mapping (Bioluminescent Indigo, Neon Aqua, Solar Coral/Gold)
    # Background: (0, 0, 0)
    # We will draw pixels directly. Let's compute pixel flat index.
    px_int = np.clip(particles_x, 0, SIZE[0] - 1).astype(np.int32)
    py_int = np.clip(particles_y, 0, SIZE[1] - 1).astype(np.int32)
    
    # Color components
    # Indigo: #3A0CA3 -> (58, 12, 163)
    # Aqua: #72EFDD -> (114, 239, 221)
    # Coral/Gold: #FF006E -> (255, 0, 110)
    
    r = np.zeros(NUM_PARTICLES, dtype=np.uint8)
    g = np.zeros(NUM_PARTICLES, dtype=np.uint8)
    b = np.zeros(NUM_PARTICLES, dtype=np.uint8)
    
    # Phase 1: life_fraction < 0.6 -> blend Indigo to Aqua
    mask1 = life_fraction < 0.6
    t1 = life_fraction[mask1] / 0.6
    r[mask1] = (58 + (114 - 58) * t1).astype(np.uint8)
    g[mask1] = (12 + (239 - 12) * t1).astype(np.uint8)
    b[mask1] = (163 + (221 - 163) * t1).astype(np.uint8)
    
    # Phase 2: life_fraction >= 0.6 -> blend Aqua to Coral/Gold
    mask2 = ~mask1
    t2 = (life_fraction[mask2] - 0.6) / 0.4
    r[mask2] = (114 + (255 - 114) * t2).astype(np.uint8)
    g[mask2] = (239 + (0 - 239) * t2).astype(np.uint8)
    b[mask2] = (221 + (110 - 221) * t2).astype(np.uint8)
    
    # Set the pixels directly on py5's multi-channel array (shape: H x W x 4 where channel 0=Alpha, 1=Red, 2=Green, 3=Blue)
    # Assigning values coordinate by coordinate via advanced indexing
    py5.np_pixels[py_int, px_int, 0] = 255
    py5.np_pixels[py_int, px_int, 1] = r
    py5.np_pixels[py_int, px_int, 2] = g
    py5.np_pixels[py_int, px_int, 3] = b
    
    py5.update_np_pixels()
    
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
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
