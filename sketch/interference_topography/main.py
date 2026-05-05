from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation constants
NUM_SOURCES = 10
FREQ = 0.05
WAVE_SPEED = 0.15

class Source:
    def __init__(self, i):
        self.i = i
        # Use Lissajous-like parameters for movement
        self.freq_x = 0.01 + i * 0.005
        self.freq_y = 0.012 + i * 0.003
        self.phase = i * 1.5
        self.amp_x = SIZE[0] * 0.4
        self.amp_y = SIZE[1] * 0.4
        self.x = 0
        self.y = 0

    def update(self, t):
        self.x = SIZE[0] / 2 + np.cos(t * self.freq_x + self.phase) * self.amp_x
        self.y = SIZE[1] / 2 + np.sin(t * self.freq_y + self.phase) * self.amp_y

sources = [Source(i) for i in range(NUM_SOURCES)]

# Global grids will be initialized in setup to account for pixel density
X_GRID = None
Y_GRID = None
PW, PH = 0, 0
SCALE = 1

def setup():
    global X_GRID, Y_GRID, PW, PH, SCALE
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    SCALE = 1
    PW = py5.width * SCALE
    PH = py5.height * SCALE
    
    x = np.arange(PW)
    y = np.arange(PH)
    X_GRID, Y_GRID = np.meshgrid(x, y)
    
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count
    
    # Update sources (logic is in logical coordinates, but distance calculation needs pixel coords)
    for s in sources:
        s.update(t)
    
    # Convert source positions to pixel coordinates
    sx = np.array([s.x for s in sources]) * SCALE
    sy = np.array([s.y for s in sources]) * SCALE
    
    # Calculate interference field using vectorized NumPy at FULL resolution
    # (PH, PW, 1) - (1, 1, NUM_SOURCES) -> (PH, PW, NUM_SOURCES)
    dx = X_GRID[:, :, np.newaxis] - sx
    dy = Y_GRID[:, :, np.newaxis] - sy
    # Optimization: work with squared distance for sin(sqrt(...))
    dists = np.sqrt(dx**2 + dy**2)
    
    # Wave superposition
    waves = np.sin(dists * (FREQ / SCALE) - t * WAVE_SPEED)
    field = np.mean(waves, axis=2) 
    
    num_levels = 18
    field_norm = (field + 1) / 2
    field_q = (field_norm * num_levels).astype(int)
    field_q = np.clip(field_q, 0, num_levels)
    
    py5.load_np_pixels()
    
    # Palette definition
    lut = np.zeros((num_levels + 1, 4), dtype=np.uint8) # RGBA
    for i in range(num_levels + 1):
        f = i / num_levels
        if f < 0.3: # Dark Base
            lut[i] = [16 + f*20, 26 + f*30, 48 + f*50, 255]
        elif f < 0.8: # Mid Blue/Cyan
            f_mid = (f - 0.3) / 0.5
            lut[i] = [30 + f_mid*34, 64 + f_mid*169, 175 + f_mid*80, 255]
        else: # Highlight Gold
            f_high = (f - 0.8) / 0.2
            if f > 0.95:
                lut[i] = [253, 224, 71, 255]
            else:
                lut[i] = [200 + f_high*53, 180 + f_high*44, 100 - f_high*29, 255]
            
    # Apply LUT
    py5.np_pixels[:] = lut[field_q]
    
    # Glint pass
    glint_mask = (field_norm > 0.97)
    py5.np_pixels[glint_mask] = [255, 255, 255, 255]
    
    py5.update_np_pixels()
    
    # Save frame
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
