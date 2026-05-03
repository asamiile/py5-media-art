import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(10, 15, 20)
    py5.blend_mode(py5.ADD)
    py5.no_loop()

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Network Structure
    num_somas = 15
    somas = np.stack([np.random.rand(num_somas) * w, np.random.rand(num_somas) * h], axis=-1)
    
    # Each edge is (start_pos, end_pos, intensity)
    edges = []
    
    print("Growing neural network...")
    
    for i in range(num_somas):
        start = somas[i]
        # Grow dendrites
        num_branches = int(py5.random(4, 8))
        for _ in range(num_branches):
            pos = start.copy()
            angle = py5.random(py5.TWO_PI)
            segments = int(py5.random(20, 60))
            
            for _ in range(segments):
                prev_pos = pos.copy()
                # Stochastic walk
                angle += py5.random(-0.5, 0.5)
                step = py5.random(5, 15)
                pos += np.array([np.cos(angle), np.sin(angle)]) * step
                
                # Boundary check
                if pos[0] < 0 or pos[0] > w or pos[1] < 0 or pos[1] > h:
                    break
                    
                edges.append((prev_pos, pos.copy(), py5.random(0.3, 1.0)))
                
                # Probability to branch
                if py5.random(1) > 0.98:
                    angle += py5.random(-1, 1)

    # 2. Rendering
    # Base network
    for start, end, intensity in edges:
        # Tapering weight based on index in edges (heuristic for distance)
        py5.stroke_weight(py5.random(0.5, 1.5))
        py5.stroke(40, 85, 130, 30 * intensity)
        py5.line(start[0], start[1], end[0], end[1])
        
    # Action Potentials (Signals)
    num_signals = 1200
    print("Simulating action potentials...")
    
    for _ in range(num_signals):
        # Pick a random "root" edge and follow a few
        edge_idx = int(py5.random(len(edges)))
        path_len = int(py5.random(5, 15))
        
        # Signal color palette
        col_type = py5.random(1)
        if col_type > 0.8: col = [255, 230, 150] # Gold
        elif col_type > 0.3: col = [100, 220, 255] # Cyan
        else: col = [200, 150, 255] # Violet
        
        alpha = py5.random(150, 255)
        
        for i in range(path_len):
            idx = (edge_idx + i) % len(edges)
            start, end, _ = edges[idx]
            
            # Multi-scale glow for electrical look
            for weight, a_mult in [(5.0, 0.1), (2.5, 0.4), (1.0, 1.0)]:
                py5.stroke_weight(weight)
                py5.stroke(col[0], col[1], col[2], alpha * a_mult * (1 - i/path_len))
                py5.line(start[0], start[1], end[0], end[1])
            
            # Chance to jump or end
            if py5.random(1) > 0.92: break

    # Draw Somas (Irregular organic shapes)
    py5.blend_mode(py5.ADD)
    for s in somas:
        # Glowing nucleus
        num_pts = 8
        for r_mult in [2.5, 1.5, 1.0]:
            py5.begin_shape()
            py5.fill(120, 200, 255, 20 if r_mult > 1 else 150)
            py5.no_stroke()
            for a in np.linspace(0, py5.TWO_PI, num_pts):
                r = (10 + py5.random(-3, 3)) * r_mult
                py5.vertex(s[0] + np.cos(a) * r, s[1] + np.sin(a) * r)
            py5.end_shape(py5.CLOSE)


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
