import py5
import numpy as np
from pathlib import Path
from scipy.spatial import Voronoi

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(20, 15, 10)
    py5.no_loop()

def get_voronoi_plates(seeds, w, h):
    # Add dummy points to handle boundaries
    points = np.append(seeds, [[-w, -h], [-w, 2*h], [2*w, -h], [2*w, 2*h]], axis=0)
    vor = Voronoi(points)
    return vor

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Plate Setup
    num_plates = 12
    seeds = np.stack([np.random.rand(num_plates) * w, np.random.rand(num_plates) * h], axis=-1)
    velocities = (np.random.rand(num_plates, 2) - 0.5) * 50.0
    
    print("Simulating eons of tectonic drift...")
    
    # 2. Rendering Base Crust
    # We'll use a pixel-based approach to determine which plate each pixel belongs to
    # for organic blending, but Voronoi for the geometry.
    
    # Create the Voronoi structure for the final positions
    final_seeds = seeds + velocities
    vor = get_voronoi_plates(final_seeds, w, h)
    
    # Render plates
    py5.stroke_weight(2)
    py5.stroke(40, 30, 20)
    
    for i in range(num_plates):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        if not region or -1 in region: continue
        
        polygon = [vor.vertices[v] for v in region]
        
        # Plate color based on velocity magnitude (heat/activity)
        vel_mag = np.linalg.norm(velocities[i])
        col = (60 + vel_mag, 50 + vel_mag*0.5, 40)
        
        # Plate body
        py5.fill(col[0], col[1], col[2])
        py5.begin_shape()
        for p in polygon:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
        
        # Internal Texture: Cratons
        py5.fill(col[0]*0.8, col[1]*0.8, col[2]*0.8, 100)
        for _ in range(3):
            cx, cy = np.mean(polygon, axis=0) + np.random.normal(0, 50, 2)
            cr = py5.random(30, 120)
            py5.begin_shape()
            for a in np.linspace(0, py5.TWO_PI, 8):
                r = cr * (0.8 + py5.random(0.4))
                py5.vertex(cx + np.cos(a)*r, cy + np.sin(a)*r)
            py5.end_shape(py5.CLOSE)

    # 3. Collision Zones (Mountains and Rifts)
    print("Building mountain ranges and rifts...")
    
    for i in range(len(vor.ridge_points)):
        p1_idx, p2_idx = vor.ridge_points[i]
        if p1_idx >= num_plates or p2_idx >= num_plates: continue
        
        v1_idx, v2_idx = vor.ridge_vertices[i]
        if v1_idx == -1 or v2_idx == -1: continue
        
        v1, v2 = vor.vertices[v1_idx], vor.vertices[v2_idx]
        
        rel_vel = velocities[p1_idx] - velocities[p2_idx]
        dir_vec = final_seeds[p2_idx] - final_seeds[p1_idx]
        dir_vec /= np.linalg.norm(dir_vec)
        boundary_type = np.dot(rel_vel, dir_vec)
        
        if boundary_type < -5.0: # Convergent (Mountains)
            # Voluminous mountain building (layered lines)
            for layer in range(4):
                py5.stroke_weight(py5.random(2, 8))
                py5.stroke(80+layer*10, 75+layer*10, 70, 150 - layer*20)
                steps = 60
                for j in range(steps):
                    t = j / steps
                    t_next = (j + 1) / steps
                    p_curr = v1 * (1-t) + v2 * t
                    p_next = v1 * (1-t_next) + v2 * t_next
                    
                    # Fractal noise for peaks
                    n1 = py5.os_noise(p_curr[0] * 0.02, p_curr[1] * 0.02, layer)
                    n2 = py5.os_noise(p_curr[0] * 0.1, p_curr[1] * 0.1, layer)
                    off = (n1 * 20.0 + n2 * 5.0) * (1 + layer*0.5)
                    py5.line(p_curr[0] + off, p_curr[1] + off, p_next[0] + off, p_next[1] + off)
                
        elif boundary_type > 5.0: # Divergent (Rifts/Magma)
            py5.blend_mode(py5.ADD)
            # Layered magma glow
            for w_idx, alpha in [(12, 10), (6, 30), (2, 120)]:
                py5.stroke_weight(w_idx)
                py5.stroke(255, 60, 0, alpha)
                py5.line(v1[0], v1[1], v2[0], v2[1])
            py5.blend_mode(py5.BLEND)


    # 4. Geological Texture
    print("Applying geological texture...")
    py5.load_np_pixels()
    noise_vals = np.random.rand(*py5.np_pixels.shape[:2]) * 20
    # Add grain
    py5.np_pixels[:,:,:3] = np.clip(py5.np_pixels[:,:,:3] + noise_vals[:,:,None] - 10, 0, 255)
    py5.update_np_pixels()

    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
