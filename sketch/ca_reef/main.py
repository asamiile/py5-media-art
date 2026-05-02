import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
GRID_W, GRID_H = 120, 68
CELL_SIZE = 16
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(20, 40, 50)
    py5.no_loop()

def get_neighbors(grid, x, y):
    # Toroidal wrapping
    nb = grid[max(0, y-1):min(GRID_H, y+2), max(0, x-1):min(GRID_W, x+2)]
    return np.sum(nb > 0) - (1 if grid[y,x] > 0 else 0)

def draw_polyp(x, y, r, state, col):
    # Organic polyp shape
    py5.push_matrix()
    py5.translate(x, y)
    
    # Calcified vs Living
    if state == 6:
        py5.fill(220, 210, 200) # Sand/Bone
        py5.stroke(180, 170, 160)
    else:
        py5.fill(col[0], col[1], col[2], 150 + state*20)
        py5.no_stroke()
        
    num_pts = 6 if state == 6 else 10
    py5.begin_shape()
    for i in range(num_pts):
        angle = py5.TWO_PI * i / num_pts
        n = py5.os_noise(x * 0.1, y * 0.1, angle)
        pr = r * (0.8 + 0.3 * n)
        py5.vertex(np.cos(angle) * pr, np.sin(angle) * pr)
    py5.end_shape(py5.CLOSE)
    
    # Internal detail for living polyps
    if 0 < state < 6:
        py5.fill(255, 255, 255, 100)
        py5.circle(0, 0, r * 0.3)
        
    py5.pop_matrix()

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. CA Simulation
    grid = np.zeros((GRID_H, GRID_W), dtype=int)
    # Seed
    grid[GRID_H//2-5:GRID_H//2+5, GRID_W//2-5:GRID_W//2+5] = np.random.choice([0, 1], (10, 10), p=[0.7, 0.3])
    
    print("Simulating reef growth...")
    steps = 80
    for _ in range(steps):
        new_grid = grid.copy()
        for y in range(GRID_H):
            for x in range(GRID_W):
                nb = get_neighbors(grid, x, y)
                state = grid[y,x]
                
                if state == 0:
                    if nb == 3: new_grid[y,x] = 1
                elif 0 < state < 6:
                    # Age or die
                    if nb < 2 or nb > 4: new_grid[y,x] = 0
                    else: new_grid[y,x] += 1
                # State 6 remains static (calcified)
        grid = new_grid

    # 2. Rendering
    print("Rendering organic reef structure...")
    
    # Colors
    colors = [
        (255, 150, 150), # Coral
        (150, 255, 200), # Seafoam
        (255, 200, 100), # Amber
        (150, 200, 255)  # Soft Blue
    ]
    
    # Water background
    for y in range(0, h, 4):
        n = py5.os_noise(y * 0.01, 0.0)
        py5.stroke(25, 50, 65, 50)
        py5.line(0, y + n*20, w, y + n*20)


    for y in range(GRID_H):
        for x in range(GRID_W):
            state = grid[y,x]
            if state > 0:
                cx = x * CELL_SIZE + CELL_SIZE/2
                cy = y * CELL_SIZE + CELL_SIZE/2
                
                # Increased Jitter for organic look
                off_x = py5.os_noise(x * 0.2, y * 0.2, 100) * 12 - 6
                off_y = py5.os_noise(x * 0.2, y * 0.2, 200) * 12 - 6
                cx += off_x
                cy += off_y
                
                r = (CELL_SIZE/2) * (0.6 + state/6)
                col = colors[(x + y) % len(colors)]
                
                # Subtle Shadow
                py5.fill(0, 0, 0, 40)
                py5.no_stroke()
                py5.circle(cx + 2, cy + 2, r)
                
                draw_polyp(cx, cy, r, state, col)

    # 3. Final Texture & Depth
    print("Applying environmental detail...")
    # Add some "sand" texture to the bottom
    for _ in range(500):
        py5.fill(230, 220, 200, 30)
        py5.no_stroke()
        py5.circle(py5.random(w), h - py5.random(200), py5.random(2, 5))


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
