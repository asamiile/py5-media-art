from pathlib import Path
import sys
import numpy as np
import py5

# Standard imports for the repo
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE)
    py5.background(5, 8, 18)  # Deep midnight navy
    py5.blend_mode(py5.SCREEN)
    py5.no_loop()


def draw():
    w, h = SIZE
    
    # Pre-generate noise field for speed
    noise_res = 100
    noise_field = np.zeros((noise_res, noise_res))
    for i in range(noise_res):
        for j in range(noise_res):
            noise_field[i, j] = py5.noise(i * 0.1, j * 0.1)
    
    def get_noise_grad(px, py):
        # Map x, y to noise field indices
        ix = int((px / w) * (noise_res - 2)) % (noise_res - 2)
        iy = int((py / h) * (noise_res - 2)) % (noise_res - 2)
        grad_x = noise_field[ix + 1, iy] - noise_field[ix, iy]
        grad_y = noise_field[ix, iy + 1] - noise_field[ix, iy]
        return grad_x, grad_y

    num_rays = 1200
    steps = 200
    dt = 3.0
    
    # Tonal mood: Cold/Precise
    # Spectral dispersion colors
    wavelengths = [
        (0.65, 255, 215, 0, 25),    # Burning Gold (Accent)
        (0.55, 224, 242, 255, 35),  # Frost White (Dominant)
        (0.45, 138, 43, 226, 40),   # Prism Violet (Secondary)
        (0.35, 100, 180, 255, 45),  # Electric Blue (Secondary)
    ]
    
    py5.no_fill()
    
    # Draw frost background texture
    py5.stroke_weight(0.5)
    for _ in range(8000):
        rx = np.random.uniform(0, w)
        ry = np.random.uniform(0, h)
        py5.stroke(100, 150, 255, 10)
        py5.point(rx, ry)

    # Ray tracing - Structured beams
    num_beams = 25
    rays_per_beam = 80
    
    for b in range(num_beams):
        # Beam starting area - Spread across the canvas
        bx = np.random.uniform(-w * 0.2, w * 1.0)
        by = np.random.uniform(-h * 0.2, h * 1.0)
        beam_base_angle = py5.QUARTER_PI + np.random.normal(0, 0.4)
        
        for r in range(rays_per_beam):
            # Spread rays within the beam
            start_x = bx + np.random.normal(0, 50)
            start_y = by + np.random.normal(0, 50)
            base_angle = beam_base_angle + np.random.normal(0, 0.05)
            
            for n_factor, r_col, g_col, b_col, alpha in wavelengths:
                curr_x, curr_y = start_x, start_y
                curr_angle = base_angle
                
                # Multi-pass glow for each ray
                for pass_idx in range(2):
                    p_alpha = alpha if pass_idx == 0 else alpha * 0.4
                    p_weight = (0.6 + n_factor * 0.8) if pass_idx == 0 else (2.0 + n_factor * 2.0)
                    
                    py5.stroke(r_col, g_col, b_col, p_alpha)
                    py5.stroke_weight(p_weight)
                    py5.begin_shape()
                    
                    # Reset state for each pass to trace the same path
                    curr_x, curr_y = start_x, start_y
                    curr_angle = base_angle
                    
                    for _ in range(steps):
                        py5.vertex(curr_x, curr_y)
                        
                        gx, gy = get_noise_grad(curr_x, curr_y)
                        # Increased n_factor influence for better dispersion
                        curr_angle += (gx * np.sin(curr_angle) - gy * np.cos(curr_angle)) * 30.0 * n_factor
                        
                        curr_x += np.cos(curr_angle) * dt
                        curr_y += np.sin(curr_angle) * dt
                        
                        if curr_x < -100 or curr_x > w + 100 or curr_y < -100 or curr_y > h + 100:
                            break
                    py5.end_shape()

    # Add a final vignette/bloom
    py5.blend_mode(py5.MULTIPLY)
    for i in range(10):
        alpha = 25 - i * 2
        py5.fill(0, 0, 0, alpha)
        py5.no_stroke()
        py5.rect(0, 0, w, h)
    
    # Final preview save and exit
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


if __name__ == "__main__":
    py5.run_sketch()
