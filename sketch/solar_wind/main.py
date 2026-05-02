import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(5, 5, 15)
    py5.blend_mode(py5.ADD)
    py5.no_loop()

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # Vector Field Components
    # 1. Solar Wind (Horizontal Flow)
    v_solar = np.array([2.0, 0.0])
    
    # 2. Magnetic Dipole
    center = np.array([w * 0.4, h * 0.5])
    
    def get_velocity(pos):
        # Relative position
        rel = pos - center
        r2 = np.sum(rel**2)
        r = np.sqrt(r2)
        
        # Dipole Field Formula: B = (3(m·r)r - m*r^2) / r^5
        # For simplicity, we'll use a simplified 2D version
        # m = [0, 1] (vertical magnetic moment)
        if r < 10: return v_solar
        
        # Magnetic influence (inverse cube law for dipole)
        strength = 500000.0 / (r2 * r + 100)
        v_dipole = np.array([
            3 * rel[0] * rel[1] / r2,
            (3 * rel[1]**2 - r2) / r2
        ]) * strength
        
        # Add turbulence
        n = py5.os_noise(pos[0] * 0.005, pos[1] * 0.005)
        angle = n * py5.TWO_PI * 2
        v_noise = np.array([np.cos(angle), np.sin(angle)]) * 0.8
        
        return v_solar + v_dipole + v_noise

    # Simulation Parameters
    num_particles = 7000
    steps = 180
    dt = 1.3
    
    print("Simulating solar wind interaction...")
    
    # Background cosmic grain
    py5.blend_mode(py5.ADD)
    for _ in range(2000):
        py5.stroke(100, 150, 255, py5.random(2, 10))
        py5.stroke_weight(py5.random(0.5, 1.5))
        py5.point(py5.random(w), py5.random(h))

    # Seed particles on the left edge and around the dipole
    particles = []
    # ... (seed logic)
    for _ in range(num_particles // 3):
        particles.append(np.array([-50.0, py5.random(h)]))
    for _ in range(num_particles * 2 // 3):
        angle = py5.random(py5.TWO_PI)
        rad = py5.random(50, 500)
        particles.append(center + np.array([np.cos(angle), np.sin(angle)]) * rad)
        
    py5.stroke_weight(0.8)
    
    for p in particles:
        pos = p.copy()
        
        # Determine color based on initial position or angle
        dist_to_center = np.linalg.norm(pos - center)
        if dist_to_center < 350:
            # Magnetospheric plasma (Violet/Magenta/Blue)
            r_shift = py5.random(0.8, 1.2)
            base_col = np.array([160 * r_shift, 60, 255])
        else:
            # Solar wind plasma (Cyan/Teal/White)
            base_col = np.array([40, 220, 240])
            
        alpha = py5.random(3, 12)
        
        py5.no_fill()
        py5.begin_shape()
        for s in range(steps):
            v = get_velocity(pos)
            new_pos = pos + v * dt
            
            # Color shifts slightly along the path
            t = s / steps
            col = base_col * (1 - t*0.4) + np.array([255, 255, 255]) * t * 0.1
            py5.stroke(col[0], col[1], col[2], alpha * (1 - t))
            
            py5.vertex(pos[0], pos[1])
            pos = new_pos
            
            # Boundary check
            if pos[0] > w + 100 or pos[0] < -150 or pos[1] > h + 100 or pos[1] < -100:
                break
        py5.end_shape()


    # Draw the "planet" core
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 10, 30)
    py5.no_stroke()
    py5.circle(center[0], center[1], 40)
    
    # Inner glow
    for r in range(40, 60, 2):
        py5.fill(100, 150, 255, 5)
        py5.circle(center[0], center[1], r)

    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
