import py5
import numpy as np
import os
import shutil
import random

WIDTH = 1920
HEIGHT = 1080
FPS = 60
DURATION_SECS = 15
TOTAL_FRAMES = FPS * DURATION_SECS
FRAMES_DIR = "frames"

lines = []
nodes = []

def generate_lsystem():
    py5.random_seed(42)
    random.seed(42)
    
    def branch(pos, dir, length, depth):
        if depth == 0 or length < 5:
            return
            
        end_pos = pos + dir * length
        lines.append((pos, end_pos, depth, length))
        
        if depth > 1:
            nodes.append((end_pos, depth, length))
        
        # Continue straight
        if py5.random(1) > 0.1:
            branch(end_pos, dir, length * py5.random(0.5, 0.9), depth - 1)
            
        # Branch orthogonally
        num_branches = int(py5.random(1, 4))
        axes = [np.array([1,0,0]), np.array([-1,0,0]), np.array([0,0,1]), np.array([0,0,-1]), np.array([0,1,0]), np.array([0,-1,0])]
        
        for _ in range(num_branches):
            valid_axes = [a for a in axes if abs(np.dot(a, dir)) < 0.1]
            if not valid_axes: continue
            
            chosen_dir = random.choice(valid_axes)
            branch(end_pos, chosen_dir, length * py5.random(0.3, 0.7), depth - 1)

    grid_size = 4
    spacing = 200
    for x in range(-grid_size, grid_size + 1):
        for z in range(-grid_size, grid_size + 1):
            if py5.random(1) > 0.2:
                # Add random jitter to base
                pos = np.array([x * spacing + py5.random(-50, 50), 0.0, z * spacing + py5.random(-50, 50)])
                branch(pos, np.array([0.0, -1.0, 0.0]), py5.random(150, 500), 7)

def setup():
    py5.size(WIDTH, HEIGHT, py5.P3D)
    py5.pixel_density(2)
    py5.smooth()
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.frame_rate(FPS)
    
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)
    
    generate_lsystem()

def draw():
    t = py5.frame_count * 0.01
    py5.background(220, 80, 5) # Dark cyber blue background
    
    py5.ambient_light(200, 60, 40)
    py5.directional_light(180, 80, 100, 0.5, 0.5, -1)
    py5.directional_light(320, 90, 80, -0.5, -0.5, -0.5)
    
    py5.translate(WIDTH/2, HEIGHT/2 + 300, -500)
    py5.rotate_x(py5.PI/6)
    py5.rotate_y(t * 0.5)
    
    # Draw L-system
    # To animate the growth, we only draw lines up to a certain "growth" factor based on time
    growth_limit = py5.frame_count * 15 # Reveal 15 lines per frame
    
    drawn = 0
    for start, end, depth, length in lines:
        if drawn > growth_limit: break
        
        hue = (200 + depth * 25 + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 90, 100, 90)
        py5.stroke_weight(depth * 1.2)
        py5.line(start[0], start[1], start[2], end[0], end[1], end[2])
        drawn += 1
        
    drawn = 0
    py5.no_stroke()
    for pos, depth, length in nodes:
        if drawn > growth_limit: break
        
        py5.push_matrix()
        py5.translate(pos[0], pos[1], pos[2])
        hue = (280 - depth * 15 + py5.frame_count * 1.0) % 360
        py5.fill(hue, 80, 100, 85)
        box_size = depth * 3
        
        # Animate rotation of nodes
        py5.rotate_y(t * depth)
        py5.rotate_x(t * depth * 0.5)
        py5.box(box_size)
        py5.pop_matrix()
        drawn += 1

    frame_filename = os.path.join(FRAMES_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_filename)
    
    if py5.frame_count >= TOTAL_FRAMES:
        generate_video()

def generate_video():
    print("Generation complete. Compiling video...")
    video_path = "output.mp4"
    if os.path.exists(video_path):
        os.remove(video_path)
        
    cmd = f"ffmpeg -framerate {FPS} -i {FRAMES_DIR}/frame-%04d.png -c:v libx264 -pix_fmt yuv420p {video_path}"
    os.system(cmd)
    
    shutil.copyfile(os.path.join(FRAMES_DIR, "frame-0001.png"), "preview_p1.png")
    
    # Let's save the last frame as preview as well since it has the full grown city
    last_frame = os.path.join(FRAMES_DIR, f"frame-{TOTAL_FRAMES:04d}.png")
    if os.path.exists(last_frame):
        shutil.copyfile(last_frame, "preview_p2.png")
        
    shutil.rmtree(FRAMES_DIR)
    print(f"Video saved as {video_path}")
    os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
