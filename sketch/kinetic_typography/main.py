import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE)
    py5.background(5, 10, 5)
    py5.no_loop()
    
    # Use a monospaced font if available, or default
    font = py5.create_font("Monospaced", 24)
    py5.text_font(font)

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Particle Setup
    num_particles = 3000
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=-/<>:;?!πΩΣλ∞√∫≈≠±×÷"
    
    # ... (grid and targets)
    cols, rows = 75, 40
    gx, gy = np.meshgrid(np.linspace(50, w-50, cols), np.linspace(50, h-50, rows))
    targets = np.stack([gx.flatten(), gy.flatten()], axis=-1)
    
    if num_particles > len(targets):
        num_particles = len(targets)
    
    target_indices = np.random.choice(len(targets), num_particles, replace=False)
    p_targets = targets[target_indices]
    p_pos = p_targets + np.random.normal(0, 400, (num_particles, 2))
    
    print("Animating kinetic typography...")
    
    steps = 150
    center = np.array([w/2, h/2])
    
    for s in range(steps):
        t = s / steps
        for i in range(num_particles):
            pos = p_pos[i]
            target = p_targets[i]
            
            # Enhanced Vortex
            rel = pos - center
            dist = np.linalg.norm(rel)
            vortex_strength = 25.0 * (1 - t*0.5)
            vortex = np.array([-rel[1], rel[0]]) / (dist + 30) * vortex_strength
            
            # Multi-frequency Noise
            n = py5.os_noise(pos[0] * 0.004, pos[1] * 0.004, s * 0.015)
            angle = n * py5.TWO_PI * 5
            noise_force = np.array([np.cos(angle), np.sin(angle)]) * 6.0
            
            # Attraction
            attraction = (target - pos) * (0.01 + t * 0.08)
            p_pos[i] += vortex + noise_force + attraction
            
            # Boundary check
            p_pos[i,0] = np.clip(p_pos[i,0], -100, w+100)
            p_pos[i,1] = np.clip(p_pos[i,1], -100, h+100)
            
            # Trails
            if s % 12 == 0 and py5.random(1) > 0.5:
                char = chars[int(py5.random(len(chars)))]
                py5.fill(0, 180, 120, 15 * (1-t))
                py5.text_size(py5.random(6, 12))
                py5.text(char, p_pos[i,0], p_pos[i,1])

    # Final Layer + Glitch
    print("Finalizing data visualization...")
    for i in range(num_particles):
        char = chars[i % len(chars)]
        dist_to_target = np.linalg.norm(p_pos[i] - p_targets[i])
        
        # Glitch shift
        x, y = p_pos[i]
        if py5.random(1) > 0.98:
            x += py5.random(-20, 20)
            
        if dist_to_target < 25:
            # Chromatic aberration effect (faint red/blue offsets)
            py5.fill(255, 50, 50, 80)
            py5.text(char, x-1, y)
            py5.fill(50, 50, 255, 80)
            py5.text(char, x+1, y)
            
            py5.fill(255, 255, 255, 230)
            py5.text_size(13)
        else:
            py5.fill(0, 255, 120, 150)
            py5.text_size(9)
            
        py5.text(char, x, y)


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
