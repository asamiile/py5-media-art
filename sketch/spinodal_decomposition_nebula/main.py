from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

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

# Simulation Parameters
GRID_SIZE = 256
DT = 0.01
KAPPA = 0.5
MOBILITY = 1.0

class CahnHilliardSimulation:
    def __init__(self, size):
        self.size = size
        # Start with random noise centered around 0
        self.C = (np.random.random((size, size)) - 0.5) * 0.05
        
    def laplacian(self, field):
        l = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
             np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
             4 * field)
        return l

    def update(self):
        # Semi-implicit or multi-stepping for stability
        for _ in range(20):
            mu = self.C**3 - self.C - KAPPA * self.laplacian(self.C)
            self.C += MOBILITY * DT * self.laplacian(mu)
            # Boundary control
            self.C = np.clip(self.C, -1.1, 1.1)

sim = CahnHilliardSimulation(GRID_SIZE)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    
    sim.update()
    
    # Rendering
    py5.load_np_pixels()
    
    from PIL import Image
    target_w, target_h = py5.np_pixels.shape[1], py5.np_pixels.shape[0]
    
    # Normalize C field for visualization (-1 to 1 -> 0 to 1)
    field = (sim.C + 1.0) * 0.5
    img_pil = Image.fromarray((field * 255).astype(np.uint8))
    img_pil = img_pil.resize((target_w, target_h), resample=Image.LANCZOS)
    img_field = np.array(img_pil) / 255.0
    
    # Palette Mapping
    # Obsidian (0, 0, 0)
    # Deep Amethyst (80, 20, 150)
    # Electric Cyan (0, 255, 255)
    # Solar White (255, 255, 240)
    
    # We map field value to these colors
    # 0.0 -> Obsidian
    # 0.3 -> Deep Amethyst
    # 0.7 -> Electric Cyan
    # 1.0 -> Solar White
    
    r = np.zeros_like(img_field)
    g = np.zeros_like(img_field)
    b = np.zeros_like(img_field)
    
    # Linear interpolation between color points
    # Point 1: 0.0 -> (0, 0, 0)
    # Point 2: 0.3 -> (80, 20, 150)
    # Point 3: 0.7 -> (0, 255, 255)
    # Point 4: 1.0 -> (255, 255, 240)
    
    m1 = img_field < 0.3
    r[m1] = (img_field[m1] / 0.3) * 80
    g[m1] = (img_field[m1] / 0.3) * 20
    b[m1] = (img_field[m1] / 0.3) * 150
    
    m2 = (img_field >= 0.3) & (img_field < 0.7)
    f = (img_field[m2] - 0.3) / 0.4
    r[m2] = 80 + f * (0 - 80)
    g[m2] = 20 + f * (255 - 20)
    b[m2] = 150 + f * (255 - 150)
    
    m3 = img_field >= 0.7
    f = (img_field[m3] - 0.7) / 0.3
    r[m3] = 0 + f * (255 - 0)
    g[m3] = 255 + f * (255 - 255)
    b[m3] = 255 + f * (240 - 255)
    
    # Add starfield
    np.random.seed(42) # Consistent starfield
    star_mask = np.random.random(img_field.shape) > 0.9995
    r[star_mask] = 255
    g[star_mask] = 255
    b[star_mask] = 255
    
    pixels = np.stack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)], axis=-1).astype(np.uint8)
    py5.set_np_pixels(pixels, 'RGB')

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "25",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
