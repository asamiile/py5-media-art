import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(15, 15, 18)
    py5.no_loop()

def expand_lsystem(axiom, rules, gens):
    curr = axiom
    for _ in range(gens):
        next_str = ""
        for char in curr:
            next_str += rules.get(char, char)
        curr = next_str
    return curr

def draw_subdivision(x, y, w, h, depth):
    if depth == 0 or py5.random(1) > 0.8:
        # Draw tile
        py5.fill(220, 200, 150, 180) # Gold
        if py5.random(1) > 0.7: py5.fill(255, 255, 255, 200) # White
        py5.no_stroke()
        py5.rect(x+1, y+1, w-2, h-2)
        return
    
    if w > h:
        split = w * py5.random(0.3, 0.7)
        draw_subdivision(x, y, split, h, depth - 1)
        draw_subdivision(x + split, y, w - split, h, depth - 1)
    else:
        split = h * py5.random(0.3, 0.7)
        draw_subdivision(x, y, w, split, depth - 1)
        draw_subdivision(x, y + split, w, h - split, depth - 1)

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Background Depth
    print("Adding structural depth...")
    for _ in range(30):
        rx, ry = py5.random(w), py5.random(h)
        rw, rh = py5.random(200, 600), py5.random(200, 600)
        py5.fill(40, 30, 20, 40) # Deep Bronze
        draw_subdivision(rx, ry, rw, rh, 2)

    # 2. L-System Setup
    axiom = "F"
    rules = {"F": "F[+F][-F]F"}
    instructions = expand_lsystem(axiom, rules, 4)
    
    # Multiple seeds
    num_seeds = 5
    print(f"Growing {num_seeds} geometric structures...")
    
    for s in range(num_seeds):
        py5.push_matrix()
        py5.translate(w * (s + 1) / (num_seeds + 1), h * 0.9)
        py5.rotate(py5.PI + py5.random(-0.5, 0.5))
        
        stack = []
        step_len = py5.random(60, 100)
        angle = py5.radians(py5.random(20, 30))
        
        for char in instructions:
            if char == "F":
                # Draw architectural segment
                py5.stroke(220, 200, 150, 180) # Gold
                py5.stroke_weight(max(1, step_len * 0.06))
                py5.line(0, 0, 0, step_len)
                
                # Occasionally subdivide along the path
                if py5.random(1) > 0.8:
                    py5.push_matrix()
                    py5.translate(-10, step_len/2)
                    draw_subdivision(0, 0, 20, 20, 2)
                    py5.pop_matrix()
                    
                py5.translate(0, step_len)
                step_len *= 0.85
            elif char == "+":
                py5.rotate(angle + py5.random(-0.1, 0.1))
            elif char == "-":
                py5.rotate(-angle + py5.random(-0.1, 0.1))
            elif char == "[":
                py5.push_matrix()
                stack.append(step_len)
            elif char == "]":
                py5.pop_matrix()
                step_len = stack.pop()
        py5.pop_matrix()
    
    # 3. Global Detail
    print("Applying final structural detail...")
    for _ in range(40):
        rx, ry = py5.random(w), py5.random(h)
        rw, rh = py5.random(30, 120), py5.random(30, 120)
        draw_subdivision(rx, ry, rw, rh, 3)

            
    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
