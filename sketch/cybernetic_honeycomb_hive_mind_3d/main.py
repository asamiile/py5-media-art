import py5
import numpy as np
import os
import shutil

WIDTH = 1920
HEIGHT = 1080
FPS = 60
DURATION_SECS = 15
TOTAL_FRAMES = FPS * DURATION_SECS
FRAMES_DIR = "frames"

def setup():
    py5.size(WIDTH, HEIGHT, py5.P3D)
    py5.pixel_density(2)
    py5.smooth()
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.frame_rate(FPS)
    
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)

def draw_hexagon(r):
    py5.begin_shape()
    for i in range(6):
        angle = i * py5.TWO_PI / 6
        py5.vertex(r * np.cos(angle), r * np.sin(angle))
    py5.end_shape(py5.CLOSE)

def draw_hex_prism(r, h):
    # Top and bottom faces
    py5.push_matrix()
    py5.translate(0, 0, h/2)
    draw_hexagon(r)
    py5.translate(0, 0, -h)
    draw_hexagon(r)
    py5.pop_matrix()
    
    # Side faces
    py5.begin_shape(py5.QUADS)
    for i in range(6):
        a1 = i * py5.TWO_PI / 6
        a2 = ((i+1)%6) * py5.TWO_PI / 6
        x1, y1 = r * np.cos(a1), r * np.sin(a1)
        x2, y2 = r * np.cos(a2), r * np.sin(a2)
        
        py5.vertex(x1, y1, h/2)
        py5.vertex(x2, y2, h/2)
        py5.vertex(x2, y2, -h/2)
        py5.vertex(x1, y1, -h/2)
    py5.end_shape()

def draw():
    t = py5.frame_count * 0.02
    py5.background(20, 10, 5) # very dark amber
    
    py5.ambient_light(40, 60, 40)
    py5.directional_light(50, 80, 100, 0.5, 0.5, -1)
    py5.directional_light(20, 90, 80, -0.5, -0.5, -0.5)
    py5.light_specular(45, 50, 100)
    
    py5.translate(WIDTH/2, HEIGHT/2 + 200, -600)
    py5.rotate_x(py5.PI/2.5)
    py5.rotate_z(t * 0.1)
    
    # Hex grid
    hex_radius = 50
    hex_height_base = 250
    row_h = hex_radius * 1.5
    col_w = hex_radius * np.sqrt(3)
    
    grid_size = 22
    
    py5.no_stroke()
    py5.specular(45, 80, 100)
    py5.shininess(25)
    
    for row in range(-grid_size, grid_size):
        for col in range(-grid_size, grid_size):
            x = col * col_w + (col_w/2 if row % 2 != 0 else 0)
            y = row * row_h
            
            # Distance from center
            dist = np.sqrt(x*x + y*y)
            if dist > 1400:
                continue
                
            # Wave mechanics
            wave1 = np.sin(dist * 0.008 - t * 3.0)
            wave2 = np.cos((x+y) * 0.004 + t * 1.5)
            noise_val = py5.os_noise(x * 0.002, y * 0.002, t * 0.5)
            
            h_mod = (wave1 + wave2 + (noise_val - 0.5) * 2) * 180
            h = hex_height_base + h_mod
            if h < 20: h = 20
            
            # Calculate glow and color
            hue = 45 + wave1 * 10 + noise_val * 20
            sat = 85 + wave2 * 15
            bri = 60 + (h_mod / 360) * 40
            
            py5.push_matrix()
            py5.translate(x, y, 0)
            
            py5.fill(hue, sat, bri, 100)
            draw_hex_prism(hex_radius * 0.92, h)
            py5.pop_matrix()

    # Save frame
    frame_filename = os.path.join(FRAMES_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_filename)
    
    # Stop when done
    if py5.frame_count >= TOTAL_FRAMES:
        generate_video()

def generate_video():
    print("Generation complete. Compiling video...")
    video_path = "output.mp4"
    if os.path.exists(video_path):
        os.remove(video_path)
        
    cmd = f"ffmpeg -framerate {FPS} -i {FRAMES_DIR}/frame-%04d.png -c:v libx264 -pix_fmt yuv420p {video_path}"
    os.system(cmd)
    
    # Save a preview still
    shutil.copyfile(os.path.join(FRAMES_DIR, "frame-0001.png"), "preview_p1.png")
    
    # Clean up frames
    shutil.rmtree(FRAMES_DIR)
    
    print(f"Video saved as {video_path}")
    os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
