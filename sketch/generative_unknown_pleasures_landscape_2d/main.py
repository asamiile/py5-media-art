import py5
import os

# ----------------------------------------------------------------------------
# 12. generative_unknown_pleasures_landscape_2d
# ----------------------------------------------------------------------------
# Concept: A shifting, mountainous landscape made entirely of parallel horizontal 
#          lines, inspired by the iconic pulsar radio emissions album cover.
# Technique: A grid of horizontal lines drawn from back to front. Vertices are 
#            displaced upwards on the Y-axis based on 3D Perlin noise. The polygons 
#            are filled with black to obscure lines behind them (faux occlusion).
# Palette: Deep space black with glowing silver/white lines. The highest peaks 
#          are tinted with an electric cyan-to-magenta gradient.
# ----------------------------------------------------------------------------

WORK_NAME = "generative_unknown_pleasures_landscape_2d"
FRAMES_DIR = f"sketch/{WORK_NAME}/frames"
OUTPUT_MP4 = f"sketch/{WORK_NAME}/{WORK_NAME}.mp4"
TOTAL_FRAMES = 900
FPS = 30
SIZE = (1920, 1080)

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)

def draw():
    py5.background(0) # Deep black
    
    py5.stroke_weight(2)
    py5.stroke_join(py5.ROUND)
    
    t = py5.frame_count * 0.015
    
    # Grid parameters
    num_lines = 100
    points_per_line = 150
    margin_x = 200
    margin_y = 200
    
    y_spacing = (py5.height - margin_y * 2) / num_lines
    x_spacing = (py5.width - margin_x * 2) / points_per_line
    
    # We draw from back (top of screen) to front (bottom) to handle occlusion
    for i in range(num_lines):
        base_y = margin_y + i * y_spacing
        
        py5.fill(0) # Black fill for occlusion
        py5.begin_shape()
        
        # Add bottom corners so the fill drops all the way down and covers lines below
        py5.vertex(margin_x, py5.height)
        py5.vertex(margin_x, base_y)
        
        max_displacement = 0
        
        for j in range(points_per_line + 1):
            x = margin_x + j * x_spacing
            
            # Use noise to calculate displacement
            # We want the middle to have more displacement than the edges (like a mountain)
            dist_to_center = abs((points_per_line / 2) - j) / (points_per_line / 2)
            edge_falloff = 1.0 - (dist_to_center ** 2) # Parabolic falloff
            
            nx = j * 0.05
            ny = i * 0.08 - t # Subtracting t makes it look like we are moving forward over the terrain
            
            n_val = py5.noise(nx, ny, t * 0.5)
            
            # Displacement is upwards (negative Y)
            displacement = py5.remap(n_val, 0.2, 0.8, 0, 300) * edge_falloff
            displacement = max(0, displacement) # Ensure it only goes up
            
            if displacement > max_displacement:
                max_displacement = displacement
                
            y = base_y - displacement
            py5.vertex(x, y)
            
        py5.vertex(py5.width - margin_x, py5.height)
        
        # Color the stroke based on the maximum height of this line
        # If it's a high peak, give it a cyan to magenta hue. If low, make it white.
        if max_displacement > 50:
            hue = py5.remap(max_displacement, 50, 300, 180, 300) # Cyan to Magenta
            saturation = py5.remap(max_displacement, 50, 300, 50, 100)
            py5.stroke(hue, saturation, 100)
        else:
            py5.stroke(0, 0, py5.remap(max_displacement, 0, 50, 40, 100)) # Gray to White
            
        py5.end_shape(py5.CLOSE)

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_path)
    
    if py5.frame_count == TOTAL_FRAMES // 2:
        preview_path = f"sketch/{WORK_NAME}/{WORK_NAME}_p1.png"
        py5.save_frame(preview_path)
        
    if py5.frame_count % 30 == 0:
        print(f"Rendered {py5.frame_count}/{TOTAL_FRAMES} frames")
        
    if py5.frame_count >= TOTAL_FRAMES:
        compile_video()
        py5.exit_sketch()

def compile_video():
    print("Compiling video with ffmpeg...")
    os.system(f"ffmpeg -y -framerate {FPS} -i {FRAMES_DIR}/frame-%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 {OUTPUT_MP4}")
    print(f"Video saved to {OUTPUT_MP4}")

if __name__ == '__main__':
    py5.run_sketch()
    os._exit(0)
