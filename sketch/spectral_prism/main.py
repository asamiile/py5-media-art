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

class SpectralPrism:
    def __init__(self):
        self.radius = 180.0
        self.center = np.array([SIZE[0]*0.55, SIZE[1]*0.5]) # Slightly off-center for better sweep
        self.angle = 0.0
        
        # Starfield
        self.num_stars = 2000
        self.stars = np.random.rand(self.num_stars, 3)
        self.stars[:, 0] *= SIZE[0]
        self.stars[:, 1] *= SIZE[1]
        
        # Wavelengths for dispersion (R to V)
        self.wavelengths = np.linspace(400, 700, 12) # 12 bands
        # Refractive indices (Cauchy approx: n = n0 + B/lambda^2)
        # n0 = 1.5, B = 0.004 um^2
        self.indices = 1.5 + 0.01 * ( (700 / self.wavelengths)**2 )

    def get_prism_edges(self):
        # Equilateral triangle
        angles = np.linspace(0, 2 * np.pi, 4, endpoint=False) + self.angle
        pts = np.stack([
            self.center[0] + self.radius * np.cos(angles),
            self.center[1] + self.radius * np.sin(angles)
        ], axis=1)
        return pts

    def intersect_segment(self, p1, p2, p3, p4):
        # Line intersection: (p1, p2) and (p3, p4)
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = p3; x4, y4 = p4
        denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
        if denom == 0: return None
        ua = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / denom
        ub = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / denom
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            return np.array([x1 + ua*(x2-x1), y1 + ua*(y2-y1)]), ua
        return None

    def refract(self, incident, normal, n1, n2):
        # Snell's law in 2D
        # incident, normal must be normalized
        cos_i = -np.dot(incident, normal)
        sin_t2 = (n1/n2)**2 * (1.0 - cos_i**2)
        if sin_t2 > 1.0: return None # Total internal reflection
        cos_t = np.sqrt(1.0 - sin_t2)
        return (n1/n2) * incident + ( (n1/n2) * cos_i - cos_t ) * normal

    def update(self, frame_count):
        # Slow elegant rotation
        self.angle = frame_count * 0.012

    def draw(self, frame_count):
        py5.background(3, 4, 12)
        
        # 1. Starfield
        py5.stroke_weight(1)
        t = frame_count * 0.05
        for i in range(self.num_stars):
            x, y, mag = self.stars[i]
            tw = 150 + 105 * np.sin(t + i)
            py5.stroke(200, 220, 255, tw * mag)
            py5.point(x, y)
            
        # 2. Draw Prism (Obsidian)
        pts = self.get_prism_edges()
        py5.fill(10, 10, 20, 240)
        py5.stroke(100, 120, 200, 80)
        py5.stroke_weight(2)
        py5.begin_shape()
        for x, y in pts[:3]:
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)
        
        # 3. Rays
        py5.blend_mode(py5.ADD)
        
        # Input Beam (Horizontal from left)
        num_input_rays = 40
        for r in range(num_input_rays):
            # Spread rays vertically
            sy = SIZE[1]/2 - 100 + r * 5.0
            p1 = np.array([-100.0, sy])
            p2 = np.array([SIZE[0] + 100.0, sy])
            
            # Draw input ray segment up to prism
            # (Finding the first intersection with any edge)
            best_hit = None
            best_ua = 2.0
            best_edge = None
            
            for i in range(3):
                e1, e2 = pts[i], pts[(i+1)%3]
                hit = self.intersect_segment(p1, p2, e1, e2)
                if hit and hit[1] < best_ua:
                    best_hit, best_ua = hit[0], hit[1]
                    best_edge = (e1, e2)
            
            if best_hit is not None:
                # White input beam
                py5.stroke(255, 255, 255, 15)
                py5.line(p1[0], p1[1], best_hit[0], best_hit[1])
                
                # Refraction for each wavelength
                for idx, wl in enumerate(self.wavelengths):
                    n_prism = self.indices[idx]
                    
                    # Normal at intersection
                    edge_vec = best_edge[1] - best_edge[0]
                    normal = np.array([-edge_vec[1], edge_vec[0]])
                    normal /= np.linalg.norm(normal)
                    # Ensure normal points outwards
                    if np.dot(normal, best_hit - self.center) < 0: normal = -normal
                    
                    # Incident vector
                    incident = np.array([1.0, 0.0])
                    
                    # First Refraction (Air to Prism)
                    refracted = self.refract(incident, normal, 1.0, n_prism)
                    
                    if refracted is not None:
                        # Find exit intersection
                        exit_hit = None
                        exit_edge = None
                        p_in = best_hit + refracted * 1.0 # nudge inside
                        p_out = p_in + refracted * 1000.0
                        
                        best_exit_ua = 2.0
                        for i in range(3):
                            e1, e2 = pts[i], pts[(i+1)%3]
                            # Don't intersect with the entry edge
                            if np.array_equal(e1, best_edge[0]): continue
                            
                            hit = self.intersect_segment(p_in, p_out, e1, e2)
                            if hit and hit[1] < best_exit_ua:
                                exit_hit, best_exit_ua = hit[0], hit[1]
                                exit_edge = (e1, e2)
                        
                        if exit_hit is not None:
                            # Internal segment
                            # color mapping (HSB)
                            hue = 280 * (idx / len(self.wavelengths))
                            py5.color_mode(py5.HSB, 360, 100, 100, 100)
                            py5.stroke(hue, 70, 100, 10)
                            py5.line(best_hit[0], best_hit[1], exit_hit[0], exit_hit[1])
                            
                            # Second Refraction (Prism to Air)
                            edge_vec_exit = exit_edge[1] - exit_edge[0]
                            normal_exit = np.array([-edge_vec_exit[1], edge_vec_exit[0]])
                            normal_exit /= np.linalg.norm(normal_exit)
                            if np.dot(normal_exit, exit_hit - self.center) < 0: normal_exit = -normal_exit
                            
                            refracted_exit = self.refract(refracted, -normal_exit, n_prism, 1.0)
                            
                            if refracted_exit is not None:
                                # Outgoing ray
                                py5.stroke(hue, 80, 100, 30)
                                py5.line(exit_hit[0], exit_hit[1], 
                                         exit_hit[0] + refracted_exit[0]*2000, 
                                         exit_hit[1] + refracted_exit[1]*2000)
                            
                            py5.color_mode(py5.RGB, 255, 255, 255, 255)
            else:
                # Ray doesn't hit prism
                py5.stroke(255, 255, 255, 5)
                py5.line(p1[0], p1[1], p2[0], p2[1])

        py5.blend_mode(py5.BLEND)

simulation = SpectralPrism()

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
