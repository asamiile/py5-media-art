from pathlib import Path
import sys
import py5
import numpy as np

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

# Downsampling for performance
CALC_SCALE = 4
CALC_SIZE = (SIZE[0] // CALC_SCALE, SIZE[1] // CALC_SCALE)

class QuadCell:
    def __init__(self, x, y, w, h, depth):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.depth = depth
        self.children = []
        self.center = np.array([x + w/2, y + h/2])
        self.freq = 0.03 + depth * 0.015
        self.phase = py5.random(py5.TWO_PI)
        self.amp = 1.0 / (depth + 1)
        self.hue = (200 + depth * 30) % 360

    def subdivide(self, noise_field, threshold):
        if self.depth >= 6: # Increased depth
            return
        
        nx = int(self.center[0] / SIZE[0] * 99)
        ny = int(self.center[1] / SIZE[1] * 99)
        if noise_field[nx, ny] > threshold / (self.depth + 1):
            hw = self.w / 2
            hh = self.h / 2
            self.children = [
                QuadCell(self.x, self.y, hw, hh, self.depth + 1),
                QuadCell(self.x + hw, self.y, hw, hh, self.depth + 1),
                QuadCell(self.x, self.y + hh, hw, hh, self.depth + 1),
                QuadCell(self.x + hw, self.y + hh, hw, hh, self.depth + 1)
            ]
            for child in self.children:
                child.subdivide(noise_field, threshold)

    def get_leaves(self):
        if not self.children: return [self]
        leaves = []
        for child in self.children: leaves.extend(child.get_leaves())
        return leaves

# --- Global State ---

stars = []
glow_layer = None

def setup():
    global glow_layer
    py5.size(*SIZE, py5.P2D)
    glow_layer = py5.create_graphics(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    glow_layer.begin_draw()
    glow_layer.color_mode(py5.HSB, 360, 100, 100, 100)
    glow_layer.background(0, 0)
    glow_layer.end_draw()
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # High-density starfield
    for _ in range(2000):
        stars.append({
            'pos': np.array([py5.random(SIZE[0]), py5.random(SIZE[1])]),
            'size': py5.random(0.5, 2.0),
            'bright': py5.random(100, 255),
            'offset': py5.random(1000)
        })

def draw():
    py5.background(240, 40, 5) # Deep navy night
    
    # 1. Starfield
    py5.no_stroke()
    for star in stars:
        twinkle = py5.noise(star['offset'] + py5.frame_count * 0.01)
        py5.fill(0, 0, 100, star['bright'] * twinkle)
        py5.circle(star['pos'][0], star['pos'][1], star['size'])
        
    # 2. Quadtree update
    time = py5.frame_count * 0.005
    noise_grid = np.zeros((100, 100))
    for i in range(100):
        for j in range(100):
            noise_grid[i, j] = py5.noise(i * 0.04, j * 0.04, time)
            
    root = QuadCell(0, 0, SIZE[0], SIZE[1], 0)
    root.subdivide(noise_grid, 0.35)
    leaves = root.get_leaves()
    
    # 3. Draw to Glow Layer (Accumulation)
    glow_layer.begin_draw()
    glow_layer.blend_mode(py5.BLEND)
    glow_layer.fill(0, 0, 0, 15) # Fade
    glow_layer.rect(0, 0, SIZE[0], SIZE[1])
    glow_layer.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    for leaf in leaves:
        pulse = py5.sin(t * leaf.freq + leaf.phase) * 0.5 + 0.5
        # Draw interference "shards"
        glow_layer.stroke(leaf.hue, 70, 100, pulse * 30)
        glow_layer.stroke_weight(1)
        angle = leaf.phase + t * 0.1
        for a in range(3):
            cur_a = angle + a * py5.TWO_PI / 3
            glow_layer.line(
                leaf.center[0], leaf.center[1],
                leaf.center[0] + py5.cos(cur_a) * leaf.w * 0.8,
                leaf.center[1] + py5.sin(cur_a) * leaf.h * 0.8
            )
    glow_layer.end_draw()
    
    # 4. Composite
    py5.blend_mode(py5.BLEND)
    py5.image(glow_layer, 0, 0)
    
    # 5. Core Highlights
    py5.blend_mode(py5.ADD)
    for leaf in leaves:
        if leaf.depth > 3:
            pulse = py5.sin(t * leaf.freq + leaf.phase) * 0.5 + 0.5
            py5.no_stroke()
            py5.fill(leaf.hue, 80, 100, pulse * 60)
            py5.circle(leaf.center[0], leaf.center[1], leaf.w * 0.1)

    save_animation_frame(FRAMES_DIR)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_frame=TOTAL_FRAMES // 2,
            preview_filename=PREVIEW_FILENAME
        )

if __name__ == "__main__":
    py5.run_sketch()
