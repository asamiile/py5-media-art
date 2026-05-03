import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(20, 25, 35)
    py5.no_loop()

def subdivide(poly, depth):
    if depth == 0 or py5.random(1) > 0.9:
        return [poly]
    
    # Pick two points on edges to slice
    # For simplicity, we'll slice using a random line through the centroid
    centroid = np.mean(poly, axis=0)
    angle = py5.random(py5.TWO_PI)
    normal = np.array([np.cos(angle), np.sin(angle)])
    
    poly1, poly2 = [], []
    for i in range(len(poly)):
        p1 = poly[i]
        p2 = poly[(i + 1) % len(poly)]
        
        d1 = np.dot(p1 - centroid, normal)
        d2 = np.dot(p2 - centroid, normal)
        
        if d1 >= 0:
            poly1.append(p1)
        if d1 < 0:
            poly2.append(p1)
            
        # Intersection
        if (d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0):
            t = d1 / (d1 - d2)
            inter = p1 + t * (p2 - p1)
            poly1.append(inter)
            poly2.append(inter)
            
    # Clean up and recurse
    res = []
    if len(poly1) >= 3: res.extend(subdivide(np.array(poly1), depth - 1))
    if len(poly2) >= 3: res.extend(subdivide(np.array(poly2), depth - 1))
    return res

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Generate Shards
    print("Shattering time into crystals...")
    initial_polys = [
        np.array([[0,0], [w,0], [w,h], [0,h]])
    ]
    
    shards = []
    for p in initial_polys:
        shards.extend(subdivide(p, depth=7))
    
    # Filter out tiny shards
    def poly_area(poly):
        return 0.5 * np.abs(np.dot(poly[:,0], np.roll(poly[:,1], 1)) - np.dot(poly[:,1], np.roll(poly[:,0], 1)))
    
    shards = [s for s in shards if poly_area(s) > 100]
        
    # 2. Render Shards
    py5.blend_mode(py5.SCREEN)
    py5.stroke_join(py5.MITER)
    
    # Palette
    colors = [
        (100, 150, 255), # Ice Blue
        (150, 100, 255), # Prism Violet
        (200, 230, 255), # Arctic Cyan
        (255, 255, 255)  # Diamond White
    ]
    
    spectral = [
        (255, 100, 100), (255, 200, 100), (100, 255, 100), 
        (100, 255, 255), (100, 100, 255), (200, 100, 255)
    ]
    
    for s in shards:
        centroid = np.mean(s, axis=0)
        c_idx = int(py5.random(len(colors)))
        col = colors[c_idx]
        alpha = py5.random(15, 70)
        
        # Draw shard body
        py5.begin_shape()
        py5.fill(col[0], col[1], col[2], alpha)
        py5.no_stroke()
        for p in s:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
            
        # Specular edges + Rainbow Diffraction
        if py5.random(1) > 0.3:
            idx = int(py5.random(len(s)))
            p1, p2 = s[idx], s[(idx+1)%len(s)]
            
            # Main white edge
            py5.stroke(255, 255, 255, alpha * 2)
            py5.stroke_weight(py5.random(0.5, 1.5))
            py5.line(p1[0], p1[1], p2[0], p2[1])
            
            # Diffraction (tiny rainbow offset)
            if py5.random(1) > 0.6:
                for i in range(3):
                    sc = spectral[int(py5.random(len(spectral)))]
                    py5.stroke(sc[0], sc[1], sc[2], alpha * 0.5)
                    py5.stroke_weight(0.5)
                    off = (i + 1) * 0.8
                    py5.line(p1[0]+off, p1[1]+off, p2[0]+off, p2[1]+off)

    # 3. Add Prism Flares (Enhanced)
    for _ in range(30):
        x, y = py5.random(w), py5.random(h)
        flare_w = py5.random(150, 500)
        py5.no_stroke()
        for r in range(15):
            py5.fill(255, 255, 255, 3)
            py5.ellipse(x, y, flare_w * (1-r/15), 1)
            py5.ellipse(x, y, 1, flare_w * (1-r/15))
            # Tiny center glint
            py5.fill(255, 255, 255, 20)
            py5.circle(x, y, 2)


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
