import py5
import numpy as np
import os

# ----------------------------------------------------------------------------
# 11. kinetic_harmonic_pendulum_web_2d
# ----------------------------------------------------------------------------
# Concept: Simulates multiple interconnected pendulums swinging in harmonic
#          motion, tracing continuous silky trails. The trails fade out slowly,
#          creating an intricate, evolving web of light.
# Technique: Uses partial screen clearing (drawing a semi-transparent black
#            rectangle) to produce motion blur/trails. Points trace complex
#            Lissajous-like paths defined by combinations of drifting sine waves.
# Palette: Neon Cyan, Magenta, Yellow (CMYK-like brights) on a pitch-black canvas.
# ----------------------------------------------------------------------------

WORK_NAME = "kinetic_harmonic_pendulum_web_2d"
FRAMES_DIR = f"sketch/{WORK_NAME}/frames"
OUTPUT_MP4 = f"sketch/{WORK_NAME}/{WORK_NAME}.mp4"
TOTAL_FRAMES = 900
FPS = 30
SIZE = (1920, 1080)
NUM_PENDULUMS = 20

# We'll store frequencies and phases for 4 cascaded oscillators per pendulum
pendulums_x_freqs = None
pendulums_y_freqs = None
pendulums_x_phases = None
pendulums_y_phases = None
pendulums_colors = None
prev_positions = None

def get_palette():
    return [
        "#00FFFF", # Cyan
        "#FF00FF", # Magenta
        "#FFFF00", # Yellow
        "#FFFFFF", # White
        "#00FF88", # Spring Green
    ]

def setup():
    global pendulums_x_freqs, pendulums_y_freqs, pendulums_x_phases, pendulums_y_phases
    global pendulums_colors, prev_positions
    
    py5.size(SIZE[0], SIZE[1])
    py5.color_mode(py5.RGB, 255)
    py5.background(0) # Start with black
    
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)
        
    palette = get_palette()
    
    # 4 oscillators per pendulum to create complex nested motion
    pendulums_x_freqs = np.random.uniform(0.5, 3.5, (NUM_PENDULUMS, 4))
    pendulums_y_freqs = np.random.uniform(0.5, 3.5, (NUM_PENDULUMS, 4))
    
    pendulums_x_phases = np.random.uniform(0, py5.TWO_PI, (NUM_PENDULUMS, 4))
    pendulums_y_phases = np.random.uniform(0, py5.TWO_PI, (NUM_PENDULUMS, 4))
    
    pendulums_colors = []
    for _ in range(NUM_PENDULUMS):
        c = py5.color(palette[int(py5.random(len(palette)))])
        pendulums_colors.append(c)
        
    prev_positions = np.zeros((NUM_PENDULUMS, 2))

def draw():
    global prev_positions
    
    # Motion blur effect: draw a very faint black rectangle over everything
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 10) # Heavy motion blur / long trails
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD) # Additive blending for the glowing trails
    py5.stroke_weight(2)
    py5.no_fill()
    
    t = py5.frame_count * 0.02
    
    center_x = py5.width / 2
    center_y = py5.height / 2
    
    # Base radius for the oscillators (shrinks as we go deeper into nested oscillators)
    radii = [py5.height * 0.25, py5.height * 0.15, py5.height * 0.08, py5.height * 0.04]
    
    for i in range(NUM_PENDULUMS):
        px = center_x
        py = center_y
        
        # Calculate current position by summing the nested oscillators
        for j in range(4):
            # Slowly drift the frequencies and phases using noise
            xf = pendulums_x_freqs[i, j] + py5.remap(py5.noise(i, j, t*0.1), 0, 1, -0.2, 0.2)
            yf = pendulums_y_freqs[i, j] + py5.remap(py5.noise(i+50, j+50, t*0.1), 0, 1, -0.2, 0.2)
            
            px += radii[j] * py5.sin(t * xf + pendulums_x_phases[i, j])
            py += radii[j] * py5.cos(t * yf + pendulums_y_phases[i, j])
            
        # Draw line from previous position to current position
        if py5.frame_count > 1:
            py5.stroke(pendulums_colors[i], 150) # 150 alpha for smooth additive blending
            py5.line(prev_positions[i, 0], prev_positions[i, 1], px, py)
            
        prev_positions[i, 0] = px
        prev_positions[i, 1] = py

    # Save frame
    py5.blend_mode(py5.BLEND) # reset for saving
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
