import numpy as np
from pathlib import Path
import subprocess
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1280, 720) # Slightly smaller for faster pixel-array manipulation
OUTPUT_SIZE  = (1920, 1080)
SIZE = PREVIEW_SIZE

# Palette (Iridescent)
def get_iridescent(t):
    # Oscillating RGB for rainbow effect
    r = 127 + 127 * np.sin(t * 2.0 + 0)
    g = 127 + 127 * np.sin(t * 2.1 + 2)
    b = 127 + 127 * np.sin(t * 1.9 + 4)
    return r, g, b

class Defect:
    def __init__(self, w, h):
        self.pos = np.random.rand(2) * [w, h]
        self.vel = np.random.randn(2) * 1.5
        self.phase = np.random.rand() * 100

    def update(self, w, h):
        t = py5.frame_count * 0.01
        self.vel[0] += (py5.noise(self.pos[0]*0.01, t) - 0.5) * 0.5
        self.vel[1] += (py5.noise(t, self.pos[1]*0.01) - 0.5) * 0.5
        self.vel *= 0.98
        self.pos += self.vel
        self.pos[0] %= w
        self.pos[1] %= h

def setup():
    py5.size(*SIZE)
    global defects
    defects = [Defect(py5.width, py5.height) for _ in range(8)]
    
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True)
    
    py5.background(0)

def draw():
    # Use NumPy to generate the Schlieren texture
    t = py5.frame_count * 0.015
    
    # Downsample for performance, then scale up
    res = 10
    cols = py5.width // res
    rows = py5.height // res
    
    # Grid of coordinates
    x = np.linspace(0, 1, cols)
    y = np.linspace(0, 1, rows)
    xv, yv = np.meshgrid(x, y)
    
    # Multi-octave noise (using sine approximations for speed if necessary, 
    # but py5.noise is okay for grids)
    noise_field = np.zeros((rows, cols))
    for r in range(rows):
        for c in range(cols):
            # Sample noise driven by time and position
            val = py5.noise(c * 0.04, r * 0.04, t)
            # Add influence from defects
            for d in defects:
                dist = np.hypot(c*res - d.pos[0], r*res - d.pos[1])
                val += 50.0 / (dist + 50.0)
            noise_field[r, c] = val
    
    # Theta (orientation)
    theta = noise_field * py5.TWO_PI * 2
    
    # Schlieren intensity (cross polarizers)
    # Intensity = sin^2(2*theta)
    intensity = np.sin(2 * theta)**2
    
    # Draw the grid
    py5.no_stroke()
    for r in range(rows):
        for c in range(cols):
            # Iridescent mapping
            it = noise_field[r, c] * 3.0 + t
            r_val, g_val, b_val = get_iridescent(it)
            
            # Multiply by Schlieren intensity
            bright = 50 + 205 * intensity[r, c]
            py5.fill(r_val * bright/255, g_val * bright/255, b_val * bright/255)
            py5.rect(c * res, r * res, res, res)
            
    # Draw defects as bright points
    py5.blend_mode(py5.ADD)
    for d in defects:
        d.update(py5.width, py5.height)
        py5.fill(255, 255, 255, 150)
        py5.ellipse(d.pos[0], d.pos[1], 8, 8)
    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print("Rendering video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4")
        ], check=True)
        # Capture a frame
        mid_frame = int(TOTAL_FRAMES * 0.7)
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / "preview.png")], check=True)
        print("Done.")

if __name__ == "__main__":
    py5.run_sketch()
