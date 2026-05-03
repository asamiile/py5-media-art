from pathlib import Path
import subprocess
import numpy as np
import py5
from scipy.spatial import Voronoi

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
SIZE = PREVIEW_SIZE

# Simulation params
NUM_PLATES = 32
sites = np.random.uniform(-100, 2020, (NUM_PLATES, 2))
velocities = np.random.normal(0, 0.7, (NUM_PLATES, 2))
plate_shades = np.random.uniform(12, 28, NUM_PLATES)

# Magma particles
particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(2, 2, 2)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    global sites, particles
    
    py5.background(1, 1, 1)
    
    # Update sites
    sites += velocities
    # Wrap/Bound check
    sites = np.clip(sites, -300, py5.width + 300)
    
    # Voronoi
    vor = Voronoi(sites)
    
    # Draw Plates
    for i, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]
        if not -1 in region and len(region) > 0:
            shade = plate_shades[i]
            py5.fill(shade, shade, shade + 3)
            polygon = [vor.vertices[idx] for idx in region]
            py5.begin_shape()
            for p in polygon:
                py5.vertex(p[0], p[1])
            py5.end_shape(py5.CLOSE)
            
            # Subtle plate texture (grain)
            py5.fill(255, 5)
            for _ in range(10):
                px = np.random.uniform(sites[i][0]-100, sites[i][0]+100)
                py5.rect(px, np.random.uniform(sites[i][1]-100, sites[i][1]+100), 2, 2)

    # Draw Tension and Magma
    py5.blend_mode(py5.ADD)
    for point_indices, ridge_vertices in vor.ridge_dict.items():
        if -1 in ridge_vertices: continue
        
        p1_idx, p2_idx = point_indices
        v1_idx, v2_idx = ridge_vertices
        v1, v2 = vor.vertices[v1_idx], vor.vertices[v2_idx]
        
        rel_vel = velocities[p1_idx] - velocities[p2_idx]
        tension = np.linalg.norm(rel_vel)
        
        # Glow layers
        for layer in range(4):
            w = (4 - layer) * (1.5 + tension * 10)
            alpha = np.clip(tension * 70 / (layer + 1.5), 0, 150)
            py5.stroke(255, 40 + layer * 40, 0, alpha)
            py5.stroke_weight(w)
            py5.line(v1[0], v1[1], v2[0], v2[1])
        
        # Spawn particles
        if np.random.random() < tension * 0.5:
            num_p = int(tension * 12)
            for _ in range(num_p):
                interp = np.random.random()
                p_pos = v1 * interp + v2 * (1 - interp)
                ridge_vec = v2 - v1
                normal = np.array([-ridge_vec[1], ridge_vec[0]])
                normal /= (np.linalg.norm(normal) + 1e-6)
                p_vel = normal * np.random.uniform(-1.5, 1.5) * 2.0 + rel_vel * 0.4
                particles.append({'pos': p_pos, 'vel': p_vel, 'life': np.random.uniform(20, 50), 'col': py5.color(255, np.random.uniform(60, 220), 0)})

    # Magma Particles
    new_particles = []
    for p in particles:
        p['pos'] += p['vel']
        p['life'] -= 1
        if p['life'] > 0:
            py5.stroke(p['col'], p['life'] * 5)
            py5.stroke_weight(np.random.uniform(1.5, 3.5))
            py5.point(p['pos'][0], p['pos'][1])
            new_particles.append(p)
    particles = new_particles

    # Fixed Smoke: No stroke, very transparent
    py5.no_stroke()
    py5.fill(15, 3, 0, 4)
    for _ in range(5):
        py5.ellipse(np.random.uniform(0, py5.width), np.random.uniform(0, py5.height), 600, 600)

    py5.blend_mode(py5.BLEND)
    
    # Global grain
    py5.fill(255, 3)
    for _ in range(200):
        py5.rect(np.random.uniform(0, py5.width), np.random.uniform(0, py5.height), 1, 1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4")
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        mid = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", "-f", mid, str(SKETCH_DIR / "preview.png")], check=True)

py5.run_sketch()
