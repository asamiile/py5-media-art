import numpy as np
from scipy.spatial import Voronoi
from pathlib import Path
import subprocess
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Palette
CLR_BG = (2, 4, 8)
CLR_UV = (153, 0, 255)
CLR_MAGENTA = (255, 0, 170)
CLR_WHITE = (255, 255, 255)

class QuantumFoam:
    def __init__(self, w, h, n_seeds=120):
        self.w, self.h = w, h
        self.n_seeds = n_seeds
        # Random initial seeds
        self.seeds = np.random.rand(n_seeds, 2) * [w, h]
        self.energies = np.zeros(n_seeds)
        self.base_offsets = np.random.rand(n_seeds, 2) * 1000

    def update(self):
        t = py5.frame_count * 0.015
        for i in range(self.n_seeds):
            # Noise-driven movement
            nx = py5.noise(self.base_offsets[i, 0] + t * 0.5) - 0.5
            ny = py5.noise(self.base_offsets[i, 1] + t * 0.5) - 0.5
            
            # Swarm toward mouse or center
            target = np.array([self.w / 2, self.h / 2])
            to_target = target - self.seeds[i]
            dist = np.linalg.norm(to_target)
            if dist > 0:
                to_target /= dist
            
            self.seeds[i] += [nx * 8, ny * 8] + to_target * 0.5
            
            # Boundary wrap
            self.seeds[i, 0] %= self.w
            self.seeds[i, 1] %= self.h
            
        # Spontaneous energy bursts
        if np.random.rand() > 0.85:
            idx = np.random.randint(self.n_seeds)
            self.energies[idx] = 1.0
            
        self.energies *= 0.94

    def draw(self):
        # Add boundary padding points for a cleaner Voronoi at edges
        padding = 200
        boundary_points = [
            [-padding, -padding], [self.w/2, -padding], [self.w+padding, -padding],
            [-padding, self.h/2], [self.w+padding, self.h/2],
            [-padding, self.h+padding], [self.w/2, self.h+padding], [self.w+padding, self.h+padding]
        ]
        all_points = np.vstack([self.seeds, boundary_points])
        
        try:
            vor = Voronoi(all_points)
        except Exception:
            return

        py5.blend_mode(py5.ADD)
        
        for i in range(self.n_seeds):
            region_idx = vor.point_region[i]
            region = vor.regions[region_idx]
            if not region or -1 in region: continue
            
            verts = vor.vertices[region]
            energy = self.energies[i]
            
            # Base color based on position and energy
            t = py5.frame_count * 0.01
            d_to_center = np.linalg.norm(self.seeds[i] - [self.w/2, self.h/2]) / (self.w/2)
            
            # Interpolate between UV and Magenta
            c1 = np.array(CLR_UV)
            c2 = np.array(CLR_MAGENTA)
            base_clr = c1 * (1 - d_to_center) + c2 * d_to_center
            
            # Flash to white with energy
            final_clr = base_clr * (1 - energy) + np.array(CLR_WHITE) * energy
            
            # Draw glow cell
            py5.fill(*final_clr, 20 + energy * 60)
            py5.stroke(*final_clr, 50 + energy * 150)
            py5.stroke_weight(0.5 + energy * 4)
            
            py5.begin_shape()
            for v in verts:
                py5.vertex(v[0], v[1])
            py5.end_shape(py5.CLOSE)
            
            # Occasional internal "nucleus"
            if energy > 0.5:
                py5.no_stroke()
                py5.fill(255, energy * 200)
                py5.ellipse(self.seeds[i,0], self.seeds[i,1], energy*20, energy*20)

        py5.blend_mode(py5.BLEND)

def setup():
    py5.size(*SIZE)
    global foam
    foam = QuantumFoam(py5.width, py5.height)
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True)
    py5.background(*CLR_BG)

def draw():
    # Subtle background clearing
    py5.fill(*CLR_BG, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    foam.update()
    foam.draw()
    
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
        mid_frame = int(TOTAL_FRAMES * 0.7)
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / "preview.png")], check=True)
        print("Done.")

if __name__ == "__main__":
    py5.run_sketch()
