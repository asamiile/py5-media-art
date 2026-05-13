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
DA, DB = 1.0, 0.5
F, K = 0.020, 0.050 # Classic stable regime
CHIRALITY = 0.1 # Subtle twist

class ChiralTuringSimulation:
    def __init__(self, size):
        self.size = size
        self.A = np.ones((size, size), dtype=np.float32)
        self.B = np.zeros((size, size), dtype=np.float32)
        
        # Seed with random noise
        r = 10
        self.B[size//2-r:size//2+r, size//2-r:size//2+r] = 1.0
        self.B += np.random.random((size, size)) * 0.05
        
    def laplacian(self, field):
        # Standard laplacian
        l = (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
             np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
             4 * field)
        return l
    
    def chiral_gradient_cross(self, field):
        # Cross product of gradient with Z-axis (rotational flow)
        # grad_perp = (-dy, dx)
        dy = (np.roll(field, -1, axis=0) - np.roll(field, 1, axis=0)) * 0.5
        dx = (np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1)) * 0.5
        # We simulate the effect by shifting the field in a biased way?
        # Better: add a term proportional to (grad_perp . grad) field? No.
        # Let's just use an asymmetric laplacian.
        l_chiral = (np.roll(field, 1, axis=0) - np.roll(field, -1, axis=0) + # Bias y
                    np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1)) # Bias x
        return l_chiral

    def update(self, t):
        # Gray-Scott with Chiral Bias
        for _ in range(10): # High sub-steps for stability
            lA = self.laplacian(self.A) + CHIRALITY * self.chiral_gradient_cross(self.A)
            lB = self.laplacian(self.B) + CHIRALITY * self.chiral_gradient_cross(self.B)
            
            abb = self.A * self.B * self.B
            self.A += DA * lA - abb + F * (1.0 - self.A)
            self.B += DB * lB + abb - (K + F) * self.B
            
            self.A = np.clip(self.A, 0, 1)
            self.B = np.clip(self.B, 0, 1)

sim = ChiralTuringSimulation(GRID_SIZE)

def setup():
    py5.size(*SIZE, py5.P2D) # P2D is faster for image-based
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    
    sim.update(t)
    
    # Render to image
    py5.load_np_pixels()
    
    # Midnight Indigo background (10, 5, 20)
    # Emerald (0, 255, 150) for B, Amethyst (150, 50, 255) for A/B mix
    # We'll map B intensity to Emerald/Amethyst
    
    b_field = sim.B
    # Resize to full resolution for rendering?
    # No, we'll draw it as a scaled image or use np_pixels
    
    # For now, let's just use high-res np_pixels indexing
    # We need to map 256x256 to 1920x1080 (or 4K)
    # Better to use py5.set_np_pixels() on a scaled version
    
    from PIL import Image
    
    # Scale and resize using PIL
    target_w, target_h = py5.np_pixels.shape[1], py5.np_pixels.shape[0]
    img_b_pil = Image.fromarray(b_field)
    img_b_pil = img_b_pil.resize((target_w, target_h), resample=Image.LANCZOS)
    img_b = np.array(img_b_pil)
    
    # Colors
    # Emerald: 0, 255, 150
    # Amethyst: 150, 50, 255
    # Background: 10, 5, 20
    
    # RGB mapping
    r = 10 + img_b * 140
    g = 5 + img_b * 250
    b = 20 + img_b * 130
    
    # Add some Amethyst (magenta-ish) based on A*B
    img_ab_pil = Image.fromarray(sim.A * sim.B)
    img_ab_pil = img_ab_pil.resize((target_w, target_h), resample=Image.LANCZOS)
    img_ab = np.array(img_ab_pil)
    r += img_ab * 50
    b += img_ab * 100
    
    pixels = np.stack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)], axis=-1).astype(np.uint8)
    py5.set_np_pixels(pixels, 'RGB')

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "28",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
