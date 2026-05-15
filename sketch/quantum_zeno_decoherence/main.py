from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Simulation Parameters ---
GRID_SIZE = (135, 240)  # (h, w) Internal simulation grid
PARTICLE_COUNT = 100000 # Adjusted for performance
GLITCH_CHANCE = 0.03
OBSERVATION_INTERVAL = 90

class QuantumSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.field = np.zeros(GRID_SIZE, dtype=np.float32)
        self.particles = np.random.rand(PARTICLE_COUNT, 2).astype(np.float32)
        self.particles[:, 0] *= w
        self.particles[:, 1] *= h
        self.vel = np.zeros_like(self.particles)
        self.colors = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.lifetimes = np.random.rand(PARTICLE_COUNT).astype(np.float32)
        
    def update(self, frame_count):
        t = frame_count * 0.02
        y = np.linspace(0, 5, GRID_SIZE[0])
        x = np.linspace(0, 5, GRID_SIZE[1])
        xx, yy = np.meshgrid(x, y)
        
        # State Field: Evolving noise
        self.field = (np.sin(xx + t) * np.cos(yy - t * 0.5) + 
                      np.sin(xx * 2.1 - t * 1.2) * 0.5 + 
                      np.cos(yy * 1.7 + t * 0.8) * 0.5)
        self.field = (self.field + 2) / 4
        
        obs_phase = (frame_count % OBSERVATION_INTERVAL) / OBSERVATION_INTERVAL
        obs_intensity = np.exp(-100 * (obs_phase - 0.1)**2)
        
        if obs_intensity > 0.1:
            grid_mask = (np.sin(xx * 8) * np.sin(yy * 8))**2
            self.field = self.field * (1 - obs_intensity) + grid_mask * obs_intensity
            
        gy, gx = np.gradient(self.field)
        
        # Map particles to grid
        px = (self.particles[:, 0] / self.w * (GRID_SIZE[1]-1)).astype(np.int32)
        py = (self.particles[:, 1] / self.h * (GRID_SIZE[0]-1)).astype(np.int32)
        px = np.clip(px, 0, GRID_SIZE[1]-1)
        py = np.clip(py, 0, GRID_SIZE[0]-1)
        
        force_x = gx[py, px]
        force_y = gy[py, px]
        
        burst = 1.0 - obs_intensity
        self.vel[:, 0] += force_x * 0.8 * burst
        self.vel[:, 1] += force_y * 0.8 * burst
        self.vel *= 0.94
        
        self.particles += self.vel
        
        self.lifetimes -= 0.008
        reset = (self.lifetimes <= 0) | (self.particles[:, 0] < 0) | (self.particles[:, 0] >= self.w) | \
                (self.particles[:, 1] < 0) | (self.particles[:, 1] >= self.h)
        
        num_reset = np.sum(reset)
        if num_reset > 0:
            self.particles[reset] = np.random.rand(num_reset, 2).astype(np.float32)
            self.particles[reset, 0] *= self.w
            self.particles[reset, 1] *= self.h
            self.vel[reset] = 0
            self.lifetimes[reset] = np.random.rand(num_reset).astype(np.float32) * 2.0
            
            # Color: Amethyst (280) to Cobalt (230)
            self.colors[reset, 0] = 230 + np.random.rand(num_reset) * 50
            self.colors[reset, 1] = 60 + np.random.rand(num_reset) * 20
            self.colors[reset, 2] = 40 + np.random.rand(num_reset) * 60

qs = None

def setup():
    global qs
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    qs = QuantumSystem(py5.width, py5.height)

def draw():
    global qs
    py5.background(260, 80, 10)
    
    qs.update(py5.frame_count)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.5)
    
    # Pass 1: Render particles in batches to simulate spectral variety
    for h_bin in range(230, 290, 15):
        mask = (qs.colors[:, 0] >= h_bin) & (qs.colors[:, 0] < h_bin + 15)
        if np.any(mask):
            py5.stroke(h_bin + 7, 75, 80, 40)
            py5.points(qs.particles[mask])
            
    # Pass 2: Observation Flash
    obs_phase = (py5.frame_count % OBSERVATION_INTERVAL) / OBSERVATION_INTERVAL
    obs_intensity = np.exp(-120 * (obs_phase - 0.1)**2)
    
    if obs_intensity > 0.02:
        py5.stroke(45, 10, 100, obs_intensity * 70)
        py5.stroke_weight(1 + obs_intensity * 2)
        step = 120
        for x in range(0, py5.width + step, step):
            py5.line(x, 0, x, py5.height)
        for y in range(0, py5.height + step, step):
            py5.line(0, y, py5.width, y)
    py5.blend_mode(py5.BLEND)
    
    # Glitch Overlay
    if np.random.rand() < GLITCH_CHANCE:
        py5.load_np_pixels()
        # Row shifting
        for _ in range(8):
            y_start = np.random.randint(0, py5.height - 30)
            h = np.random.randint(1, 10)
            shift = np.random.randint(-100, 100)
            py5.np_pixels[y_start:y_start+h, :] = np.roll(py5.np_pixels[y_start:y_start+h, :], shift, axis=1)
        
        # Block corruption (magenta/cyan)
        if np.random.rand() < 0.4:
            y = np.random.randint(0, py5.height - 10)
            x = np.random.randint(0, py5.width - 150)
            color = [300, 90, 90] if np.random.rand() > 0.5 else [180, 90, 90] # HSB
            # We are in HSB mode, but np_pixels is usually RGB/ARGB. 
            # In py5, np_pixels is ARGB (uint32) or uint8 depending on renderer.
            # Let's use a simpler approach: just XOR some pixels
            py5.np_pixels[y:y+3, x:x+100, 1:3] ^= 255 # XOR G and B channels
            
        py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "12M",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        subprocess.run(["cp", str(SKETCH_DIR / f"{WORK_NAME}.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
