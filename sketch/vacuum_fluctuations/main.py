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

class VacuumFluctuations:
    def __init__(self):
        # Grid for field sampling
        self.res = 64
        x = np.linspace(-50, SIZE[0] + 50, self.res)
        y = np.linspace(-50, SIZE[1] + 50, self.res)
        self.X, self.Y = np.meshgrid(x, y)
        
        # Field parameters (sum of sines to simulate noise)
        self.num_waves = 12
        self.kx = np.random.uniform(-0.015, 0.015, self.num_waves)
        self.ky = np.random.uniform(-0.015, 0.015, self.num_waves)
        self.w = np.random.uniform(0.1, 0.4, self.num_waves)
        self.p = np.random.uniform(0, 2*np.pi, self.num_waves)
        
        # Starfield
        self.num_stars = 2500
        self.stars = np.random.rand(self.num_stars, 3)
        self.stars[:, 0] *= SIZE[0]
        self.stars[:, 1] *= SIZE[1]

    def update(self, frame_count):
        pass

    def draw(self, frame_count):
        # Deep vacuum background
        py5.background(2, 2, 8)
        
        # 1. Starfield
        py5.stroke_weight(1)
        t_stars = frame_count * 0.05
        for i in range(self.num_stars):
            x, y, mag = self.stars[i]
            tw = 130 + 110 * np.sin(t_stars + i)
            py5.stroke(200, 215, 255, tw * mag)
            py5.point(x, y)
            
        # 2. Field Excitation
        t = frame_count * 0.2
        field = np.zeros_like(self.X)
        for i in range(self.num_waves):
            field += np.sin(self.kx[i] * self.X + self.ky[i] * self.Y + self.w[i] * t + self.p[i])
        
        # Normalize and threshold
        field = (field - field.min()) / (field.max() - field.min() + 1e-6)
        
        # 3. Fluctuations & Entanglement
        py5.blend_mode(py5.ADD)
        
        # Find excited regions
        threshold = 0.82
        mask = field > threshold
        if np.any(mask):
            excitations = (field[mask] - threshold) / (1.0 - threshold)
            ex_x = self.X[mask]
            ex_y = self.Y[mask]
            
            # Points
            # py5.points is fast
            py5.stroke_weight(2.0)
            # Group by magnitude for color/alpha
            py5.stroke(160, 100, 255, 80) # Violet base
            py5.points(np.stack([ex_x, ex_y], axis=1))
            
            # 4. Connections (Transient Entanglement)
            # We sample a few points to connect to avoid O(N^2)
            indices = np.where(mask.flatten())[0]
            if len(indices) > 5:
                # Randomly sample pairs for lines
                num_links = min(len(indices) * 2, 800)
                idx1 = np.random.choice(indices, num_links)
                idx2 = np.random.choice(indices, num_links)
                
                for k in range(num_links):
                    p1 = np.array([self.X.flatten()[idx1[k]], self.Y.flatten()[idx1[k]]])
                    p2 = np.array([self.X.flatten()[idx2[k]], self.Y.flatten()[idx2[k]]])
                    
                    dist_sq = np.sum((p1 - p2)**2)
                    if 0 < dist_sq < 100**2:
                        dist = np.sqrt(dist_sq)
                        alpha = (1.0 - dist / 100) * 30
                        py5.stroke(100, 220, 255, alpha) # Cyan links
                        py5.stroke_weight(1.0)
                        py5.line(p1[0], p1[1], p2[0], p2[1])
                        
        py5.blend_mode(py5.BLEND)

simulation = VacuumFluctuations()

def setup():
    py5.size(*SIZE)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
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
            preview_filename=PREVIEW_FILENAME
        )
        py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
