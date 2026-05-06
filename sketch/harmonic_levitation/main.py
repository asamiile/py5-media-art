from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes
from lib.animation import frames_dir, save_animation_frame, render_video_and_preview

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = frames_dir(SKETCH_DIR)
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 60000
NUM_SOURCES = 8

class HarmonicLevitation:
    def __init__(self):
        # Initialize particles randomly
        self.particles = np.random.rand(NUM_PARTICLES, 2) * np.array(SIZE)
        self.vel = np.zeros((NUM_PARTICLES, 2))
        
        # Sources positioned in a circle outside the viewport
        angles = np.linspace(0, 2 * np.pi, NUM_SOURCES, endpoint=False)
        radius = max(SIZE) * 0.7
        self.sources = np.stack([
            SIZE[0]/2 + radius * np.cos(angles),
            SIZE[1]/2 + radius * np.sin(angles)
        ], axis=1)
        
        # Base frequencies and random phases for oscillators
        self.base_freqs = np.random.uniform(0.015, 0.025, NUM_SOURCES)
        self.phases = np.random.uniform(0, 2 * np.pi, NUM_SOURCES)
        
        # Precompute Starfield for "beautiful night sky"
        self.num_stars = 2500
        self.stars = np.random.rand(self.num_stars, 3) # x, y, magnitude
        self.stars[:, 0] *= SIZE[0]
        self.stars[:, 1] *= SIZE[1]
        self.star_colors = np.random.uniform(0.8, 1.0, (self.num_stars, 3)) # subtle color variation

    def update(self, frame_count):
        t = frame_count / FPS
        
        # Slowly modulate frequencies to create evolving patterns
        # We use a mix of global and individual modulation
        global_mod = np.sin(t * 0.3) * 0.2
        curr_freqs = self.base_freqs * (1.0 + global_mod + 0.1 * np.sin(t * 1.5 + self.phases))
        
        # Vectorized wave field computation
        # 1. Distances from each source to each particle
        # particles: (N, 2), sources: (S, 2) -> dists: (N, S)
        diffs = self.particles[:, None, :] - self.sources[None, :, :]
        dists = np.linalg.norm(diffs, axis=2) # (N, S)
        
        # Avoid division by zero
        dists = np.maximum(dists, 1.0)
        
        # 2. Compute Wave Amplitude and its Gradient
        # Wave P = sum( sin(k*d - w*t + phi) )
        # We want particles to assemble at nodes (min |P|) or antinodes.
        # Let's use P^2 as the potential field.
        k = 0.04 # Wave number (spatial frequency)
        omega = 2 * np.pi * curr_freqs # Angular frequency
        
        wave_arg = k * dists - omega[None, :] * t + self.phases[None, :]
        sin_vals = np.sin(wave_arg)
        cos_vals = np.cos(wave_arg)
        
        total_amp = np.sum(sin_vals, axis=1) # (N,)
        
        # Gradient of total amplitude
        # grad(sin(k*d - w*t + phi)) = k * cos(...) * grad(d)
        # grad(d) = (p - s) / d
        # grad_total = sum( k * cos_i * (p - s_i)/d_i )
        grads_i = k * cos_vals[:, :, None] * (diffs / dists[:, :, None]) # (N, S, 2)
        grad_total = np.sum(grads_i, axis=1) # (N, 2)
        
        # Force F = -grad(Potential)
        # If Potential = total_amp^2, F = -2 * total_amp * grad_total
        # If Potential = |total_amp|, F = -sign(total_amp) * grad_total
        # Let's use a non-linear scaling for "snapping" into place
        force = -2.0 * total_amp[:, None] * grad_total
        
        # 3. Apply Physics
        # High friction to ensure they stay in traps
        friction = 0.92
        self.vel = self.vel * friction + force * 0.4
        
        # Add a bit of Brownian motion/noise for organic feel
        noise = np.random.normal(0, 0.08, (NUM_PARTICLES, 2))
        self.vel += noise
        
        self.particles += self.vel
        
        # Boundary constraints (gentle push back)
        margin = 50
        mask_left = self.particles[:, 0] < margin
        mask_right = self.particles[:, 0] > SIZE[0] - margin
        mask_top = self.particles[:, 1] < margin
        mask_bottom = self.particles[:, 1] > SIZE[1] - margin
        
        self.vel[mask_left, 0] += 1.0
        self.vel[mask_right, 0] -= 1.0
        self.vel[mask_top, 1] += 1.0
        self.vel[mask_bottom, 1] -= 1.0

    def draw(self, frame_count):
        # Clear with deep indigo trail (slight persistence)
        # We use a dark semi-transparent rect for "silken" effect if P2D,
        # but in standard renderer we can use background() for clean frames.
        # Since this is an animation, we might want some trail within the frame 
        # or just rely on motion blur in the viewer's eye. 
        # Actually, for "silken assembly", persistent trails across frames are better.
        # But for video sketches, we usually draw clean frames and let the motion do the work.
        # Wait, the template says "choose intentionally whether to call background()".
        # Let's call background() every frame for clarity, but use high particle density.
        py5.background(4, 4, 12) # Near-black deep indigo
        
        # 1. Draw Starfield (Static Background)
        py5.stroke_weight(1)
        t = frame_count * 0.05
        for i in range(self.num_stars):
            x, y, mag = self.stars[i]
            # Twinkle effect
            twinkle = 150 + 100 * np.sin(t + i)
            c = self.star_colors[i] * twinkle * mag
            py5.stroke(c[0], c[1], c[2], 200)
            py5.point(x, y)
            
        # 2. Draw Particles
        py5.blend_mode(py5.ADD)
        
        # Color based on potential/energy
        # We'll use HSB-like mapping for the particles
        # Fast particles (moving to traps) vs slow particles (trapped)
        speeds = np.linalg.norm(self.vel, axis=1)
        max_speed = 5.0
        
        # Use py5.points() for efficiency
        # Group by color/energy level
        
        # Level 1: Trapped / Low Energy (Deep Violet)
        mask1 = speeds < 0.8
        py5.stroke(120, 60, 255, 80) # Amethyst
        py5.stroke_weight(1.0)
        py5.points(self.particles[mask1])
        
        # Level 2: Transition (Electric Cyan)
        mask2 = (speeds >= 0.8) & (speeds < 2.5)
        py5.stroke(0, 220, 255, 120) # Cyan
        py5.stroke_weight(1.5)
        py5.points(self.particles[mask2])
        
        # Level 3: High Energy / Moving (White-Gold)
        mask3 = speeds >= 2.5
        py5.stroke(255, 240, 200, 180) # Gold
        py5.stroke_weight(2.0)
        py5.points(self.particles[mask3])
        
        py5.blend_mode(py5.BLEND)

simulation = HarmonicLevitation()

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    simulation.update(py5.frame_count)
    simulation.draw(py5.frame_count)
    
    save_animation_frame(FRAMES_DIR)
    
    if py5.frame_count >= TOTAL_FRAMES:
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_frame=TOTAL_FRAMES // 2,
            preview_filename=PREVIEW_FILENAME
        )
        py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
