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
GRID_RES = 64
COLS, ROWS = GRID_RES, GRID_RES

class FerrofluidSpikes:
    def __init__(self):
        # Initialize grid
        x = np.linspace(-SIZE[0]*0.45, SIZE[0]*0.45, COLS)
        y = np.linspace(-SIZE[1]*0.45, SIZE[1]*0.45, ROWS)
        self.X, self.Y = np.meshgrid(x, y)
        self.Z = np.zeros_like(self.X)
        
        # Magnetic Poles
        self.num_poles = 3
        # Path parameters for poles
        self.pole_params = np.random.uniform(0.5, 2.0, (self.num_poles, 4))
        
        # Starfield
        self.num_stars = 2500
        self.stars = np.random.rand(self.num_stars, 3)
        self.stars[:, 0] *= SIZE[0]
        self.stars[:, 1] *= SIZE[1]

    def update(self, frame_count):
        t = frame_count / FPS
        
        # Compute Magnetic Field Intensity
        self.Z.fill(0)
        for i in range(self.num_poles):
            # Lissajous paths for poles
            px = SIZE[0]*0.25 * np.cos(t * self.pole_params[i, 0] + self.pole_params[i, 1])
            py = SIZE[1]*0.25 * np.sin(t * self.pole_params[i, 2] + self.pole_params[i, 3])
            
            dx = self.X - px
            dy = self.Y - py
            dist_sq = dx**2 + dy**2
            
            # Sharp field falloff + spikes
            intensity = 1.0 / (dist_sq / 8000.0 + 1.0)
            
            # High-frequency spike noise based on distance to pole
            spike_noise = np.sin(dx*0.12 + t*8) * np.cos(dy*0.12 + t*5)
            self.Z += 180 * (intensity**1.5) * (1.0 + 0.6 * spike_noise)
            
        # Global viscous ripple
        self.Z += 15 * np.sin(np.sqrt(self.X**2 + self.Y**2)*0.04 - t*6)

    def draw(self, frame_count):
        py5.background(2, 3, 10) # Dark navy
        
        # 1. Draw Starfield (2D Background)
        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.stroke_weight(1)
        t_stars = frame_count * 0.05
        for i in range(self.num_stars):
            x, y, mag = self.stars[i]
            twinkle = 140 + 100 * np.sin(t_stars + i)
            py5.stroke(200, 220, 255, twinkle * mag)
            py5.point(x, y)
        py5.hint(py5.ENABLE_DEPTH_TEST)
        
        # 2. 3D Ferrofluid Mesh
        py5.push_matrix()
        py5.translate(SIZE[0]/2, SIZE[1]/2, -100)
        py5.rotate_x(py5.radians(55))
        py5.rotate_z(frame_count * 0.003)
        
        # Lighting
        py5.ambient_light(30, 30, 60)
        py5.directional_light(150, 200, 255, 0, 1, -1)
        py5.directional_light(100, 50, 200, 1, 0, -0.5)
        py5.light_specular(255, 255, 255)
        
        # Mesh Surface
        py5.no_stroke()
        py5.specular(180, 180, 255)
        py5.shininess(30)
        
        # Draw strips
        for i in range(ROWS - 1):
            py5.begin_shape(py5.TRIANGLE_STRIP)
            for j in range(COLS):
                # Gradient based on height
                h = self.Z[i, j]
                h_next = self.Z[i+1, j]
                
                # Material: Obsidian with cobalt peaks
                py5.fill(10, 15 + h*0.2, 30 + h*0.6)
                py5.vertex(self.X[i, j], self.Y[i, j], h)
                
                py5.fill(10, 15 + h_next*0.2, 30 + h_next*0.6)
                py5.vertex(self.X[i+1, j], self.Y[i+1, j], h_next)
            py5.end_shape()
            
        # 3. Peak Glimmers
        py5.blend_mode(py5.ADD)
        py5.stroke_weight(2.0)
        # Use a high-pass mask for peaks
        mask = self.Z > 120
        if np.any(mask):
            pts = np.stack([self.X[mask], self.Y[mask], self.Z[mask]], axis=1)
            # Sample highlights for performance and sparkle effect
            step = max(1, len(pts) // 120)
            py5.stroke(200, 240, 255, 150)
            for x, y, z in pts[::step]:
                py5.point(x, y, z)
        py5.blend_mode(py5.BLEND)
        
        py5.pop_matrix()

simulation = FerrofluidSpikes()

def setup():
    py5.size(*SIZE, py5.P3D)
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
