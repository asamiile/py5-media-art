import py5
import numpy as np
import os
import shutil

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
WIDTH = 1920
HEIGHT = 1080
FPS = 60
DURATION_SECS = 15
TOTAL_FRAMES = FPS * DURATION_SECS
FRAMES_DIR = "frames"

# -----------------------------------------------------------------------------
# Physics State
# -----------------------------------------------------------------------------
N_NODES = 80
pos = np.zeros((N_NODES + 1, 2))  # last node is the center nucleus
vel = np.zeros((N_NODES + 1, 2))
masses = np.ones(N_NODES + 1)
masses[-1] = 15.0  # Center is heavier

# Organelles
N_ORG = 10
org_pos = np.zeros((N_ORG, 2))
org_vel = np.zeros((N_ORG, 2))

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
def setup():
    py5.size(WIDTH, HEIGHT, py5.P2D)
    py5.pixel_density(2)
    py5.smooth()
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.frame_rate(FPS)
    
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)
    
    # Initialize amoeba in center
    radius = 600
    angles = np.linspace(0, 2*np.pi, N_NODES, endpoint=False)
    pos[:-1, 0] = WIDTH/2 + radius * np.cos(angles)
    pos[:-1, 1] = HEIGHT/2 + radius * np.sin(angles)
    pos[-1] = [WIDTH/2, HEIGHT/2]
    
    # Initialize organelles inside
    for i in range(N_ORG):
        r = py5.random(100, radius - 150)
        a = py5.random(0, 2*np.pi)
        org_pos[i] = [WIDTH/2 + r * np.cos(a), HEIGHT/2 + r * np.sin(a)]

# -----------------------------------------------------------------------------
# Physics Engine
# -----------------------------------------------------------------------------
def compute_spring(p1, p2, v1, v2, k, d, rest_l):
    diff = p2 - p1
    dist = np.linalg.norm(diff)
    if dist < 0.0001:
        return np.zeros(2)
    dir_v = diff / dist
    f_spring = k * (dist - rest_l)
    v_rel = v2 - v1
    f_damp = d * np.dot(v_rel, dir_v)
    return dir_v * (f_spring + f_damp)

def update_physics(time_t):
    global pos, vel, org_pos, org_vel
    
    forces = np.zeros_like(pos)
    base_radius = 600
    
    k_perimeter = 0.05
    d_perimeter = 0.1
    l_perimeter = 2 * base_radius * np.sin(np.pi / N_NODES)
    
    k_spoke = 0.05
    d_spoke = 0.02
    
    # Calculate forces
    for i in range(N_NODES):
        # Spoke to center - modulate rest length with noise
        angle_ratio = i / N_NODES
        pulse = py5.os_noise(angle_ratio * 3.0, time_t * 0.5) * 400 - 100
        pulse += np.sin(time_t * 3.0 + angle_ratio * np.pi * 2) * 150
        current_spoke_l = base_radius + pulse
        
        f_sp = compute_spring(pos[i], pos[-1], vel[i], vel[-1], k_spoke, d_spoke, current_spoke_l)
        forces[i] += f_sp
        forces[-1] -= f_sp
        
        # Perimeter to next
        next_i = (i + 1) % N_NODES
        f_per = compute_spring(pos[i], pos[next_i], vel[i], vel[next_i], k_perimeter, d_perimeter, l_perimeter)
        forces[i] += f_per
        forces[next_i] -= f_per
        
        # Organic wobble noise
        noise_x = py5.os_noise(pos[i,0]*0.005, pos[i,1]*0.005, time_t) - 0.5
        noise_y = py5.os_noise(pos[i,0]*0.005 + 100.0, pos[i,1]*0.005 + 100.0, time_t) - 0.5
        forces[i] += np.array([noise_x, noise_y]) * 15.0
        
    # Global drag
    forces -= vel * 0.04
    
    # Keep center gently drifting around middle
    center_pos = pos[-1]
    drift_force = np.array([WIDTH/2, HEIGHT/2]) - center_pos
    forces[-1] += drift_force * 0.01
    
    # Update state
    acc = forces / masses[:, None]
    vel += acc
    pos += vel
    
    # Update organelles
    org_forces = np.zeros_like(org_pos)
    for i in range(N_ORG):
        # Tied loosely to center
        f_c = compute_spring(org_pos[i], pos[-1], org_vel[i], vel[-1], 0.01, 0.05, 300)
        org_forces[i] += f_c
        
        # Repel from each other
        for j in range(N_ORG):
            if i != j:
                diff = org_pos[i] - org_pos[j]
                dist = np.linalg.norm(diff)
                if 0.1 < dist < 200:
                    org_forces[i] += (diff / dist) * (200 - dist) * 0.05
                    
        # Add wobble
        noise_x = py5.os_noise(org_pos[i,0]*0.01, time_t, float(i)) - 0.5
        noise_y = py5.os_noise(time_t, org_pos[i,1]*0.01, float(i)) - 0.5
        org_forces[i] += np.array([noise_x, noise_y]) * 10.0
        
    org_forces -= org_vel * 0.05
    org_vel += org_forces
    org_pos += org_vel

# -----------------------------------------------------------------------------
# Draw Loop
# -----------------------------------------------------------------------------
def draw():
    time_t = py5.frame_count * 0.02
    
    # Run physics multiple times per frame for stability
    update_physics(time_t)
    update_physics(time_t + 0.01)
    
    # Background
    py5.background(220, 95, 7) # Dark teal
    
    # Additive blending for glows
    py5.blend_mode(py5.ADD)
    
    # Draw organelles
    py5.no_stroke()
    for i in range(N_ORG):
        opos = org_pos[i]
        hue = 320 if i % 2 == 0 else 45
        
        for layer in range(4):
            py5.fill(hue, 90, 80, 10 - layer*2)
            py5.circle(opos[0], opos[1], 80 + layer*40)
            
        py5.fill(hue, 50, 100, 80)
        py5.circle(opos[0], opos[1], 40)
        
    # Draw center nucleus
    cpos = pos[-1]
    for layer in range(5):
        py5.fill(280, 80, 90, 8 - layer)
        py5.circle(cpos[0], cpos[1], 150 + layer*50)
    py5.fill(280, 40, 100, 90)
    py5.circle(cpos[0], cpos[1], 80)
    
    # Draw Membrane
    def draw_membrane(scale_offset, stroke_weight, alpha, fill_alpha=0):
        if fill_alpha > 0:
            py5.fill(185, 90, 80, fill_alpha)
        else:
            py5.no_fill()
            
        py5.stroke(185, 90, 100, alpha)
        py5.stroke_weight(stroke_weight)
        
        py5.begin_shape()
        # To close curve smoothly, we repeat the first and last few points
        # Start control point
        p_prev = pos[-1] + (pos[-1] - pos[-1]) * scale_offset # dummy for control
        p0 = pos[0] + (pos[0] - pos[-1]) * scale_offset
        py5.curve_vertex(p0[0], p0[1])
        
        for i in range(N_NODES):
            p = pos[i] + (pos[i] - pos[-1]) * scale_offset
            py5.curve_vertex(p[0], p[1])
            
        # Repeat to close
        for i in range(3):
            p = pos[i] + (pos[i] - pos[-1]) * scale_offset
            py5.curve_vertex(p[0], p[1])
            
        py5.end_shape()

    draw_membrane(scale_offset=-0.03, stroke_weight=0, alpha=0, fill_alpha=5)
    draw_membrane(scale_offset=0, stroke_weight=20, alpha=10)
    draw_membrane(scale_offset=0.015, stroke_weight=8, alpha=30)
    draw_membrane(scale_offset=0.025, stroke_weight=3, alpha=80)
    
    # Draw floating plankton
    py5.fill(185, 40, 100, 60)
    py5.no_stroke()
    for i in range(150):
        px = py5.os_noise(i * 10.0, time_t * 0.1) * WIDTH * 1.2 - WIDTH*0.1
        py_y = (HEIGHT + 200 - (py5.frame_count * (2.0 + py5.os_noise(float(i)*5.0, 0.0)*2.0))) % (HEIGHT + 400) - 200
        size = 4 + py5.os_noise(float(i)*7.0, 0.0) * 4
        py5.circle(px, py_y, size)

    # Save frame
    frame_filename = os.path.join(FRAMES_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_filename)
    
    # Stop when done
    if py5.frame_count >= TOTAL_FRAMES:
        generate_video()

def generate_video():
    print("Generation complete. Compiling video...")
    video_path = "ethereal_amoeba_soft_body_2d.mp4"
    if os.path.exists(video_path):
        os.remove(video_path)
        
    cmd = f"ffmpeg -framerate {FPS} -i {FRAMES_DIR}/frame-%04d.png -c:v libx264 -pix_fmt yuv420p {video_path}"
    os.system(cmd)
    
    # Save a preview still
    shutil.copyfile(os.path.join(FRAMES_DIR, "frame-0001.png"), "ethereal_amoeba_soft_body_2d_p1.png")
    
    # Clean up frames
    shutil.rmtree(FRAMES_DIR)
    
    print(f"Video saved as {video_path}")
    os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
