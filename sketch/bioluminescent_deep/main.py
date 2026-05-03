import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(5, 5, 20)
    py5.no_loop()

def draw_creature(x, y, size, col):
    # Organic pulsating body
    num_pts = 100
    py5.begin_shape()
    py5.fill(col[0], col[1], col[2], 25)
    py5.stroke(col[0], col[1], col[2], 120)
    py5.stroke_weight(1.2)
    
    for i in range(num_pts):
        angle = py5.TWO_PI * i / num_pts
        n = py5.os_noise(x * 0.01 + np.cos(angle), y * 0.01 + np.sin(angle))
        r = size * (0.8 + 0.3 * n)
        py5.vertex(x + np.cos(angle) * r, y + np.sin(angle) * r)
    py5.end_shape(py5.CLOSE)
    
    # Internal "Organs"
    for _ in range(3):
        ox, oy = x + py5.random(-size*0.3, size*0.3), y + py5.random(-size*0.3, size*0.3)
        for r in range(int(size*0.4), 0, -5):
            py5.fill(255, 255, 255, 5)
            py5.no_stroke()
            py5.circle(ox, oy, r)
            
    # Tentacles (Enhanced with curling and variable length)
    num_tentacles = int(py5.random(8, 16))
    for _ in range(num_tentacles):
        py5.no_fill()
        py5.stroke_weight(0.7)
        
        tx, ty = x + py5.random(-size*0.6, size*0.6), y + size * 0.4
        py5.begin_shape()
        py5.vertex(tx, ty)
        
        segments = int(py5.random(30, 60))
        curl_phase = py5.random(100)
        for s in range(segments):
            # Noise + Curling force
            n = py5.os_noise(tx * 0.01, ty * 0.01, s * 0.05)
            tx += (n - 0.5) * 8.0 + np.sin(s * 0.2 + curl_phase) * 2.0
            ty += py5.random(4, 12)
            
            py5.stroke(col[0], col[1], col[2], 50 * (1 - s/segments))
            py5.vertex(tx, ty)
        py5.end_shape()

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Background Atmosphere
    # Marine Snow
    for _ in range(1000):
        py5.stroke(200, 230, 255, py5.random(5, 60))
        py5.stroke_weight(py5.random(0.5, 1.5))
        py5.point(py5.random(w), py5.random(h))
            
    # 2. Creatures
    num_creatures = 18
    colors = [
        (255, 80, 180), # Neon Magenta
        (80, 255, 240), # Electric Cyan
        (160, 120, 255), # Violet
        (220, 255, 120)  # Phosphor Green
    ]
    
    print("Populating the deep sea...")
    py5.blend_mode(py5.ADD)
    
    creature_pos = []
    for _ in range(num_creatures):
        cx = py5.random(100, w-100)
        cy = py5.random(100, h-300)
        c_size = py5.random(25, 75)
        c_col = colors[int(py5.random(len(colors)))]
        creature_pos.append((cx, cy, c_size))
        
        for i in range(2):
            draw_creature(cx, cy, c_size * (1 - i*0.2), c_col)

    # 3. Clustered Bioluminescence (Plankton)
    for cx, cy, c_size in creature_pos:
        for _ in range(80):
            dist = py5.random(c_size * 1.5, c_size * 5)
            angle = py5.random(py5.TWO_PI)
            px = cx + np.cos(angle) * dist
            py = cy + np.sin(angle) * dist
            py5.stroke(120, 255, 255, py5.random(40, 120))
            py5.stroke_weight(py5.random(1, 2.5))
            py5.point(px, py)
            
    # Scattered extras
    for _ in range(1000):
        py5.stroke(100, 255, 255, py5.random(10, 40))
        py5.stroke_weight(1)
        py5.point(py5.random(w), py5.random(h))


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
