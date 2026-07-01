import py5
import numpy as np
import os

# ----------------------------------------------------------------------------
# 9. kinetic_crystalline_fractal_canopy_2d
# ----------------------------------------------------------------------------
# Concept: A recursive geometric tree/canopy made of crystalline structures
#          that breathe and sway mathematically with a faux wind.
# Technique: Recursive drawing of polygons (not just lines) to form branches.
#            Branch angles and lengths modulated by Perlin noise over time.
# Palette: Amethyst and Gold (Deep purple, lavender, bright gold, white
#          highlights on a very dark charcoal background).
# ----------------------------------------------------------------------------

WORK_NAME = "kinetic_crystalline_fractal_canopy_2d"
FRAMES_DIR = f"sketch/{WORK_NAME}/frames"
OUTPUT_MP4 = f"sketch/{WORK_NAME}/{WORK_NAME}.mp4"
TOTAL_FRAMES = 900
FPS = 30
SIZE = (1920, 1080)

def get_palette():
    return [
        "#111116", # Dark Charcoal / Near Black
        "#4a235a", # Deep Purple
        "#8e44ad", # Bright Amethyst
        "#d2b4de", # Lavender
        "#f1c40f", # Bright Gold
        "#fcf3cf", # Pale Gold/White
    ]

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.color_mode(py5.RGB, 255)
    
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)

def draw_branch(length, depth, max_depth):
    if depth == 0:
        return
        
    # Taper thickness based on depth
    thickness = py5.remap(depth, 1, max_depth, 1, 25)
    
    # Calculate color based on depth
    palette = get_palette()
    if depth > max_depth * 0.6:
        color_hex = palette[1] # Deep purple
    elif depth > max_depth * 0.3:
        color_hex = palette[2] # Amethyst
    elif depth > max_depth * 0.1:
        color_hex = palette[3] # Lavender
    else:
        color_hex = palette[4] # Gold tips
        
    c = py5.color(color_hex)
    
    # Add alpha to make it crystalline and overlapping
    alpha_val = py5.remap(depth, 1, max_depth, 150, 220)
    
    py5.fill(c, alpha_val)
    py5.no_stroke()
    
    # Draw crystalline polygon instead of line
    py5.begin_shape()
    py5.vertex(-thickness/2, 0)
    py5.vertex(thickness/2, 0)
    py5.vertex(thickness * 0.3, -length)
    py5.vertex(-thickness * 0.3, -length)
    py5.end_shape(py5.CLOSE)
    
    # Highlight edge
    py5.stroke(py5.color(palette[5]), alpha_val * 0.5)
    py5.stroke_weight(1)
    py5.line(-thickness * 0.3, -length, 0, -length * 1.1)
    py5.line(thickness * 0.3, -length, 0, -length * 1.1)

    # Move to the end of this branch
    py5.translate(0, -length)
    
    # Wind and branching logic
    t = py5.frame_count * 0.015
    
    # Base angles
    angle_spread = py5.PI / 4.5
    
    # Noise offsets for wind
    noise_val_1 = py5.noise(depth * 0.1, t)
    noise_val_2 = py5.noise(depth * 0.1 + 100, t)
    
    wind_angle_1 = py5.remap(noise_val_1, 0, 1, -py5.PI/6, py5.PI/6)
    wind_angle_2 = py5.remap(noise_val_2, 0, 1, -py5.PI/6, py5.PI/6)
    
    # Length shrinking factor
    shrink = 0.75
    
    # Recursive calls
    py5.push_matrix()
    py5.rotate(-angle_spread + wind_angle_1)
    draw_branch(length * shrink, depth - 1, max_depth)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate(angle_spread + wind_angle_2)
    draw_branch(length * shrink, depth - 1, max_depth)
    py5.pop_matrix()
    
    # Occasional middle branch
    if depth % 2 == 0 and depth > 2:
        py5.push_matrix()
        noise_val_3 = py5.noise(depth * 0.1 + 200, t)
        wind_angle_3 = py5.remap(noise_val_3, 0, 1, -py5.PI/12, py5.PI/12)
        py5.rotate(wind_angle_3)
        draw_branch(length * shrink * 0.8, depth - 1, max_depth)
        py5.pop_matrix()

def draw():
    palette = get_palette()
    
    # Clear background with trailing alpha
    py5.blend_mode(py5.BLEND)
    py5.fill(py5.color(palette[0]), 60)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.BLEND) # Or ADD if it gets too dark
    
    max_depth = 9
    start_length = 250
    
    # Draw three distinct trees to form a canopy
    trees = [
        {"x": py5.width * 0.2, "len": 200, "depth": 8},
        {"x": py5.width * 0.5, "len": 250, "depth": 9},
        {"x": py5.width * 0.8, "len": 200, "depth": 8}
    ]
    
    for tree in trees:
        py5.push_matrix()
        py5.translate(tree["x"], py5.height + 20)
        
        # Adding a base sway to the entire tree
        base_sway = py5.remap(py5.noise(tree["x"] * 0.01, py5.frame_count * 0.01), 0, 1, -0.1, 0.1)
        py5.rotate(base_sway)
        
        draw_branch(tree["len"], tree["depth"], tree["depth"])
        py5.pop_matrix()
    
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
