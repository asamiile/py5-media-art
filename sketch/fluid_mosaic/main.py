import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(240, 245, 240)
    py5.no_loop()

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Simulation Setup
    num_lipids = 1200
    num_proteins = 25
    
    # Positions and Velocities
    l_pos = np.stack([np.random.rand(num_lipids) * w, np.random.rand(num_lipids) * h], axis=-1)
    p_pos = np.stack([np.random.rand(num_proteins) * w, np.random.rand(num_proteins) * h], axis=-1)
    
    # Radii
    l_rad = np.random.uniform(3, 8, num_lipids)
    p_rad = np.random.uniform(40, 100, num_proteins)
    
    print("Simulating cellular membrane fluidity...")
    
    # Run simulation for a few hundred steps to "equilibrate" and create motion trails
    steps = 180
    dt = 0.5
    
    py5.no_stroke()
    
    # Initial state background
    py5.fill(220, 230, 225, 20)
    py5.rect(0, 0, w, h)

    for s in range(steps):
        # Apply noise-based fluid flow
        t = s * 0.01
        
        # Lipids
        for i in range(num_lipids):
            n = py5.os_noise(l_pos[i,0] * 0.002, l_pos[i,1] * 0.002, t)
            angle = n * py5.TWO_PI * 4
            l_pos[i] += np.array([np.cos(angle), np.sin(angle)]) * 2.0
            
            # Boundary check (toroidal)
            l_pos[i,0] %= w
            l_pos[i,1] %= h
            
            # Render lipid with low alpha to build up texture
            py5.fill(150, 200, 180, 5)
            py5.circle(l_pos[i,0], l_pos[i,1], l_rad[i])
            
        # Proteins
        for j in range(num_proteins):
            n = py5.os_noise(p_pos[j,0] * 0.001, p_pos[j,1] * 0.001, t + 100)
            angle = n * py5.TWO_PI * 2
            p_pos[j] += np.array([np.cos(angle), np.sin(angle)]) * 1.5
            
            p_pos[j,0] %= w
            p_pos[j,1] %= h
            
            # Render protein with slightly higher alpha
            col_type = j % 3
            if col_type == 0: col = (255, 120, 100) # Coral
            elif col_type == 1: col = (255, 180, 80) # Amber
            else: col = (100, 180, 220) # Sky
            
            py5.fill(col[0], col[1], col[2], 2)
            py5.circle(p_pos[j,0], p_pos[j,1], p_rad[j])

    # Final crisp layer
    print("Adding final molecular detail...")
    
    # Background: Extracellular Matrix
    py5.stroke_weight(0.5)
    for _ in range(30):
        py5.no_fill()
        py5.stroke(100, 150, 130, 20)
        x1, y1 = py5.random(w), py5.random(h)
        py5.begin_shape()
        py5.vertex(x1, y1)
        py5.bezier_vertex(x1+py5.random(-200,200), y1+py5.random(-200,200), 
                          x1+py5.random(-200,200), y1+py5.random(-200,200),
                          x1+py5.random(-200,200), y1+py5.random(-200,200))
        py5.end_shape()

    # Final Lipids
    py5.no_stroke()
    for i in range(num_lipids):
        # Vary teal/seafoam shades
        l_col = (130 + py5.random(-20, 20), 180 + py5.random(-15, 15), 160 + py5.random(-10, 30))
        py5.fill(l_col[0], l_col[1], l_col[2], 160)
        py5.circle(l_pos[i,0], l_pos[i,1], l_rad[i] * 0.8)
        # Highlight
        py5.fill(255, 255, 255, 120)
        py5.circle(l_pos[i,0] - 1, l_pos[i,1] - 1, l_rad[i] * 0.3)
        
    # Final Proteins
    for j in range(num_proteins):
        col_type = j % 3
        if col_type == 0: col = (255, 120, 100)
        elif col_type == 1: col = (255, 180, 80)
        else: col = (100, 180, 220)
        
        # Protein body (layered for depth)
        py5.fill(col[0], col[1], col[2], 180)
        py5.circle(p_pos[j,0], p_pos[j,1], p_rad[j])
        py5.fill(col[0]*1.1, col[1]*1.1, col[2]*1.1, 100)
        py5.circle(p_pos[j,0], p_pos[j,1], p_rad[j]*0.9)
        
        # Internal structure (simulated subunits/domains)
        num_subunits = int(py5.random(4, 10))
        for _ in range(num_subunits):
            angle = py5.random(py5.TWO_PI)
            dist = py5.random(p_rad[j] * 0.1, p_rad[j] * 0.7)
            # Brighter subunit highlight
            py5.fill(255, 255, 255, 60)
            py5.circle(p_pos[j,0] + np.cos(angle) * dist, p_pos[j,1] + np.sin(angle) * dist, p_rad[j] * 0.2)
            # Darker detail
            py5.fill(col[0]*0.5, col[1]*0.5, col[2]*0.5, 40)
            py5.circle(p_pos[j,0] + np.cos(angle) * dist + 1, p_pos[j,1] + np.sin(angle) * dist + 1, p_rad[j] * 0.1)


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
