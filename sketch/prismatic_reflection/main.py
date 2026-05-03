from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
SIZE = PREVIEW_SIZE

def setup():
    py5.size(*SIZE)
    py5.background(2, 2, 8)
    py5.no_loop()

def intersect_line_segment(p, v, a, b):
    seg = b - a
    det = v[0] * (-seg[1]) - v[1] * (-seg[0])
    if abs(det) < 1e-6:
        return None
    rhs = a - p
    t = (rhs[0] * (-seg[1]) - rhs[1] * (-seg[0])) / det
    u = (v[0] * rhs[1] - v[1] * rhs[0]) / det
    if t > 0.001 and 0 <= u <= 1:
        return t
    return None

def draw():
    py5.background(2, 2, 8)
    py5.blend_mode(py5.ADD) # Additive for prismatic feel
    
    center = np.array([py5.width / 2, py5.height / 2])
    # Larger, more complex mirror maze
    radius = 520
    sides = 12
    poly_points = np.array([[center[0] + radius * np.cos(a), center[1] + radius * np.sin(a)] 
                            for a in np.linspace(0, 2*np.pi, sides + 1)])
    
    segments = []
    for i in range(sides):
        segments.append((poly_points[i], poly_points[i+1]))
        
    # Internal structured mirrors (Star pattern)
    for i in range(sides):
        p1 = poly_points[i]
        p2 = poly_points[(i + 5) % sides]
        segments.append((p1, p2))
        
    # Light Sources (at the periphery)
    num_sources = 6
    num_rays_per_source = 40
    max_bounces = 20
    num_spectrum = 15
    
    # Prismatic dispersion factor
    dispersion_base = 0.003
    
    for s in range(num_sources):
        src_angle = (s / num_sources) * 2 * np.pi
        # Source just inside the boundary
        src_p = center + (radius - 20) * np.array([np.cos(src_angle), np.sin(src_angle)])
        
        # Pointing roughly toward center with some spread
        base_angle = src_angle + np.pi + np.random.uniform(-0.2, 0.2)
        
        for r in range(num_rays_per_source):
            ray_angle = base_angle + (r / num_rays_per_source - 0.5) * 0.8
            
            for spec_idx in range(num_spectrum):
                # Spectral color with very low alpha
                h = i = spec_idx / num_spectrum
                py5.color_mode(py5.HSB, 1.0)
                # Lower alpha (0.04) to prevent saturation
                py5.stroke(h, 0.9, 1.0, 0.04)
                py5.color_mode(py5.RGB, 255)
                py5.stroke_weight(0.5)
                
                p = src_p.copy()
                angle = ray_angle + (spec_idx - num_spectrum/2) * dispersion_base
                v = np.array([np.cos(angle), np.sin(angle)])
                
                for bounce in range(max_bounces):
                    min_t = float('inf')
                    hit_seg = None
                    for seg in segments:
                        t = intersect_line_segment(p, v, seg[0], seg[1])
                        if t and t < min_t:
                            min_t = t
                            hit_seg = seg
                            
                    if hit_seg:
                        hit_p = p + min_t * v
                        # Draw ray segment
                        py5.line(p[0], p[1], hit_p[0], hit_p[1])
                        
                        # Reflection
                        edge = hit_seg[1] - hit_seg[0]
                        normal = np.array([-edge[1], edge[0]])
                        normal /= np.linalg.norm(normal)
                        if np.dot(v, normal) > 0: normal = -normal
                        
                        v = v - 2 * np.dot(v, normal) * normal
                        # Cumulative dispersion shift
                        v_angle = np.arctan2(v[1], v[0]) + (spec_idx - num_spectrum/2) * 0.0002
                        v = np.array([np.cos(v_angle), np.sin(v_angle)])
                        p = hit_p
                    else:
                        break

    # Save
    py5.save_frame(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()

py5.run_sketch()
