import py5
import numpy as np
import os
from pathlib import Path

# Size Configuration
def get_sizes():
    # 4K for final, but let's use a manageable size for dev if needed
    # Standard for this project is 4K
    return (1920, 1080), (3840, 2160), (3840, 2160)

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 180000
NUM_STARS = 12000
LATTICE_CONSTANT = 45.0
TWIST_SPEED = 0.01
TIME_STEP = 0.5
FRICTION = 0.95

# State
pos = None
vel = None
stars = None
saved_frames = 0

def setup():
    global pos, vel, stars
    py5.size(*SIZE, py5.P2D) 
    py5.color_mode(py5.RGB, 255) # Use RGB for clear background
    
    # Initialize particles
    pos = np.random.uniform(0, [SIZE[0], SIZE[1]], (NUM_PARTICLES, 2))
    vel = np.zeros((NUM_PARTICLES, 2))
    
    # Initialize starfield
    stars = np.random.uniform(0, [SIZE[0], SIZE[1]], (NUM_STARS, 2))
    
    # Create frames directory
    Path("sketch/moire_lattice_resonance/frames").mkdir(parents=True, exist_ok=True)

def get_moire_force(p, theta):
    # Reciprocal lattice vectors for hexagonal lattice
    k0 = 2 * np.pi / LATTICE_CONSTANT
    
    # Basis vectors for two layers
    def get_k_vecs(angle):
        return k0 * np.array([
            [np.cos(angle), np.sin(angle)],
            [np.cos(angle + 2*np.pi/3), np.sin(angle + 2*np.pi/3)],
            [np.cos(angle + 4*np.pi/3), np.sin(angle + 4*np.pi/3)]
        ])
    
    k1 = get_k_vecs(theta/2)
    k2 = get_k_vecs(-theta/2)
    
    # Potential is sum of cosines
    # We use vectorization: p is (N, 2), k is (3, 2)
    # dot product: (N, 2) @ (2, 3) -> (N, 3)
    v1 = np.sum(np.cos(p @ k1.T), axis=1)
    v2 = np.sum(np.cos(p @ k2.T), axis=1)
    
    # The interference pattern (Moiré)
    potential = v1 + v2
    
    # Gradient (force)
    # d/dx cos(k.x) = -k_x sin(k.x)
    s1 = np.sin(p @ k1.T) # (N, 3)
    s2 = np.sin(p @ k2.T) # (N, 3)
    
    # force = -grad(potential)
    # f_x = sum(k_x * sin(k.x))
    f1 = s1 @ k1 # (N, 2)
    f2 = s2 @ k2 # (N, 2)
    
    return -(f1 + f2)

def draw():
    global pos, vel
    t = py5.frame_count
    
    # 1. Clear background
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    
    # 2. Draw starfield
    py5.stroke(220, 20, 90, 40)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # 3. Physics update
    theta = 0.02 + 0.015 * np.sin(t * TWIST_SPEED)
    force = get_moire_force(pos, theta)
    
    vel += force * TIME_STEP
    vel *= FRICTION
    pos += vel * TIME_STEP
    
    # Boundary (toroidal)
    pos[:, 0] %= py5.width
    pos[:, 1] %= py5.height
    
    # 4. Rendering
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    speed = np.linalg.norm(vel, axis=1)
    # Hue: Emerald(150) -> Cyan(190) -> Purple(280)
    h_vals = 160 + 120 * np.clip(speed / 4.0, 0, 1)
    
    # Batch by hue for speed
    num_buckets = 8
    for i in range(num_buckets):
        h_min = 160 + i * (120/num_buckets)
        h_max = h_min + (120/num_buckets)
        mask = (h_vals >= h_min) & (h_vals < h_max)
        if not np.any(mask): continue
        
        py5.stroke(h_min, 80, 90, 15) # Low alpha, ADD mode
        py5.stroke_weight(1.1)
        py5.points(pos[mask])
    
    # 5. Save Frame
    global saved_frames
    saved_frames += 1
    py5.save_frame(f"sketch/moire_lattice_resonance/frames/frame-{saved_frames:04d}.png")
    
    if saved_frames >= 1200:
        py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
