import numpy as np
from pathlib import Path
import subprocess
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1080, 1920) # Portrait for more graceful growth
OUTPUT_SIZE  = (2160, 3840)
SIZE = PREVIEW_SIZE

# Palette
CLR_BG = (5, 5, 16)
CLR_STEM = (0, 255, 204)
CLR_PETAL = (187, 136, 255)
CLR_POLLEN = (255, 204, 0)

class Particle:
    def __init__(self, w, h):
        self.pos = np.random.rand(2) * [w, h]
        self.vel = np.random.randn(2) * 0.5
        self.life = np.random.rand()
        self.size = 1 + np.random.rand() * 2

    def update(self, w, h):
        t = py5.frame_count * 0.01
        # Noise-based wind
        wind_x = py5.noise(self.pos[0]*0.005, self.pos[1]*0.005, t) - 0.5
        wind_y = py5.noise(self.pos[0]*0.005 + 100, self.pos[1]*0.005 + 100, t) - 0.2 # Slight upward drift
        
        self.vel += [wind_x * 0.1, wind_y * 0.1]
        self.vel *= 0.98
        self.pos += self.vel
        
        # Wrap
        self.pos[0] %= w
        self.pos[1] %= h

    def draw(self):
        alpha = 100 + 155 * np.sin(py5.frame_count * 0.05 + self.life * 10)
        py5.no_stroke()
        py5.fill(*CLR_POLLEN, alpha)
        py5.ellipse(self.pos[0], self.pos[1], self.size, self.size)

class Bloom:
    def __init__(self, size):
        self.size = size
        self.petals = np.random.randint(6, 10)
        self.phase = np.random.rand() * np.pi * 2
        self.petal_ratio = 0.6 + np.random.rand() * 0.4
        
    def draw(self, growth):
        t = py5.frame_count * 0.04 + self.phase
        pulse = (np.sin(t) + 1) * 0.5
        
        # Petals
        for i in range(self.petals):
            angle = i * (np.pi * 2 / self.petals) + t * 0.1
            py5.push_matrix()
            py5.rotate(angle)
            
            py5.fill(*CLR_PETAL, 30 * growth)
            py5.stroke(*CLR_PETAL, (100 + pulse * 50) * growth)
            py5.stroke_weight(1)
            
            # Draw ethereal petal shape
            py5.begin_shape()
            py5.vertex(0, 0)
            # Quadratic-like curves for petals
            py5.bezier_vertex(self.size*0.4*growth, -self.size*self.petal_ratio*growth, 
                              self.size*0.8*growth, -self.size*0.2*growth, 
                              self.size*growth, 0)
            py5.bezier_vertex(self.size*0.8*growth, self.size*0.2*growth, 
                              self.size*0.4*growth, self.size*self.petal_ratio*growth, 
                              0, 0)
            py5.end_shape()
            py5.pop_matrix()
            
        # Core glow
        py5.no_stroke()
        for r in range(3):
            alpha = (100 + pulse * 100) * growth / (r + 1)
            py5.fill(*CLR_POLLEN, alpha)
            py5.ellipse(0, 0, (15 - r*4)*growth, (15 - r*4)*growth)

class Plant:
    def __init__(self, x, y, h):
        self.x = x
        self.y = y
        self.h = h
        self.growth = 0
        self.speed = 0.003 + np.random.rand() * 0.004
        self.bloom = Bloom(40 + np.random.rand() * 60)
        # S-curve control points
        self.cp1 = x + (np.random.rand() - 0.5) * 100
        self.cp2 = x + (np.random.rand() - 0.5) * 100
        self.offset = np.random.rand() * 1000

    def update(self):
        self.growth = min(1.0, self.growth + self.speed)
        
    def draw(self):
        t = py5.frame_count * 0.01 + self.offset
        sway = np.sin(t) * 15 * self.growth
        
        # Draw stem
        py5.no_fill()
        py5.stroke(*CLR_STEM, 150 * self.growth)
        py5.stroke_weight(1.5)
        py5.begin_shape()
        py5.vertex(self.x, self.y)
        # Dynamic swaying stem
        py5.bezier_vertex(self.cp1 + sway, self.y - self.h*0.4,
                          self.cp2 - sway, self.y - self.h*0.7,
                          self.x + sway, self.y - self.h * self.growth)
        py5.end_shape()
        
        # Bloom at the tip
        if self.growth > 0.7:
            py5.push_matrix()
            py5.translate(self.x + sway, self.y - self.h * self.growth)
            bloom_growth = (self.growth - 0.7) / 0.3
            self.bloom.draw(bloom_growth)
            py5.pop_matrix()

def setup():
    py5.size(*SIZE)
    global plants, pollen
    plants = []
    # Create plants at the bottom
    for _ in range(12):
        x = np.random.rand() * py5.width
        h = 300 + np.random.rand() * 600
        plants.append(Plant(x, py5.height + 20, h))
        
    pollen = [Particle(py5.width, py5.height) for _ in range(150)]
    
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True)
    py5.background(*CLR_BG)

def draw():
    # Maintain trails for a softer look
    py5.fill(*CLR_BG, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    for p in pollen:
        p.update(py5.width, py5.height)
        p.draw()
        
    for p in plants:
        p.update()
        p.draw()
        
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
        # Capture a frame where flowers are in full bloom
        mid_frame = int(TOTAL_FRAMES * 0.95)
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / "preview.png")], check=True)
        print("Done.")

if __name__ == "__main__":
    py5.run_sketch()
