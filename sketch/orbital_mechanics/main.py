import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(5, 5, 15)
    py5.no_loop()

def get_acceleration(pos, planets):
    acc = np.zeros_like(pos)
    G = 1.5
    for p_pos, p_mass in planets:
        rel = p_pos - pos
        dist2 = np.sum(rel**2)
        dist = np.sqrt(dist2)
        if dist < 5: continue
        force = G * p_mass / (dist2 * dist)
        acc += rel * force
    return acc

def rk4_step(pos, vel, planets, dt):
    # k1
    v1 = vel
    a1 = get_acceleration(pos, planets)
    
    # k2
    v2 = vel + a1 * (dt/2)
    a2 = get_acceleration(pos + v1 * (dt/2), planets)
    
    # k3
    v3 = vel + a2 * (dt/2)
    a3 = get_acceleration(pos + v2 * (dt/2), planets)
    
    # k4
    v4 = vel + a3 * dt
    a4 = get_acceleration(pos + v3 * dt, planets)
    
    new_pos = pos + (v1 + 2*v2 + 2*v3 + v4) * (dt/6)
    new_vel = vel + (a1 + 2*a2 + 2*a3 + a4) * (dt/6)
    return new_pos, new_vel

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # 1. Planets Setup
    num_planets = 3
    planets = [
        (np.array([w*0.5, h*0.5]), 5000.0),
        (np.array([w*0.3, h*0.4]), 2000.0),
        (np.array([w*0.7, h*0.6]), 2000.0)
    ]
    
    # 2. Satellites Setup
    num_satellites = 400
    s_pos = []
    s_vel = []
    for _ in range(num_satellites):
        # Orbiting positions
        angle = py5.random(py5.TWO_PI)
        rad = py5.random(100, 600)
        p = np.array([w/2 + np.cos(angle)*rad, h/2 + np.sin(angle)*rad])
        
        # Tangential velocity (simplified)
        v_mag = py5.random(1.5, 3.5)
        v = np.array([-np.sin(angle), np.cos(angle)]) * v_mag
        
        s_pos.append(p)
        s_vel.append(v)
        
    s_pos = np.array(s_pos)
    s_vel = np.array(s_vel)
    
    # 3. Simulation & Rendering
    steps = 1500
    dt = 1.0
    
    print("Simulating gravitational dance...")
    
    # Background stars
    for _ in range(500):
        py5.stroke(255, 255, 255, py5.random(10, 80))
        py5.point(py5.random(w), py5.random(h))

    py5.blend_mode(py5.ADD)
    
    # Track paths for rendering
    paths = [[] for _ in range(num_satellites)]
    
    for _ in range(steps):
        for i in range(num_satellites):
            paths[i].append(s_pos[i].copy())
            s_pos[i], s_vel[i] = rk4_step(s_pos[i], s_vel[i], planets, dt)
            
    # Render paths
    for i in range(num_satellites):
        path = np.array(paths[i])
        
        # Determine color based on initial distance
        start_dist = np.linalg.norm(path[0] - np.array([w/2, h/2]))
        if start_dist < 200: col = [255, 220, 150] # Gold
        elif start_dist < 400: col = [180, 255, 230] # Seafoam
        elif start_dist < 600: col = [200, 200, 255] # Violet
        else: col = [150, 180, 255] # Sky
            
        alpha_base = py5.random(3, 10)
        py5.no_fill()
        
        # Draw path segments with varying thickness
        py5.begin_shape()
        for j in range(0, len(path)-1, 3):
            p1 = path[j]
            p2 = path[min(j+3, len(path)-1)]
            
            # Velocity-based thickness (heuristic for depth/speed)
            vel = np.linalg.norm(p2 - p1)
            weight = np.clip(1.5 / (vel + 0.5), 0.2, 1.2)
            
            py5.stroke_weight(weight)
            py5.stroke(col[0], col[1], col[2], alpha_base)
            py5.vertex(p1[0], p1[1])
        py5.end_shape()

    # Draw Planets (Enhanced)
    py5.blend_mode(py5.ADD)
    for idx, (p_pos, _) in enumerate(planets):
        # Layered Atmospheric Glow
        for r in range(25, 0, -3):
            py5.fill(100, 150, 255, 3)
            py5.no_stroke()
            py5.circle(p_pos[0], p_pos[1], r*2)
            
        # Primary Planet Rings
        if idx == 0:
            py5.no_fill()
            py5.stroke(255, 255, 255, 20)
            py5.stroke_weight(1.0)
            py5.ellipse(p_pos[0], p_pos[1], 40, 12)
            py5.stroke(255, 255, 255, 10)
            py5.ellipse(p_pos[0], p_pos[1], 48, 15)
            
        py5.blend_mode(py5.BLEND)
        py5.fill(15, 15, 40)
        py5.no_stroke()
        py5.circle(p_pos[0], p_pos[1], 10)
        # Surface highlight
        py5.fill(255, 255, 255, 100)
        py5.circle(p_pos[0]-2, p_pos[1]-2, 3)


    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
