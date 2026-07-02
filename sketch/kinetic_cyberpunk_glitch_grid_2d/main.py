import os
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import py5
from lib.safety import apply_anti_flicker_filter
import numpy as np

# ----------------------------------------------------------------------------
# Configuration & Constants
# ----------------------------------------------------------------------------
SIZE = (1920, 1080)
WORK_NAME = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Video settings
FPS = 60
DURATION_SEC = 15
TOTAL_FRAMES = FPS * DURATION_SEC

# State
state = {
    "frame_count": 0,
    "completed": False,
    "grid_rows": 40,
    "grid_cols": 60
}

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 80, 10)
    
def draw():
    if state["completed"]:
        return

    # Heavy motion blur fade using subtractive/darkening alpha
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 80, 10, 15)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = state["frame_count"] * 0.05
    
    cell_w = SIZE[0] / state["grid_cols"]
    cell_h = SIZE[1] / state["grid_rows"]
    
    # We will randomly select a "glitch block" on the screen and draw intense neon bars
    num_glitches = int(py5.random(5, 15))
    
    for _ in range(num_glitches):
        # Pick a random cell
        col = int(py5.random(state["grid_cols"]))
        row = int(py5.random(state["grid_rows"]))
        
        # Calculate base position
        x = col * cell_w
        y = row * cell_h
        
        # Glitch width can span multiple columns
        span = int(py5.random(1, 10))
        w = span * cell_w
        h = cell_h
        
        # Determine glitch offset and jitter using noise
        noise_val = py5.noise(row * 0.1, t)
        offset_x = (noise_val - 0.5) * 200
        
        # Sometimes snap completely off grid
        if py5.random(1) < 0.1:
            offset_x += py5.random(-300, 300)
            
        final_x = x + offset_x
        final_y = y
        
        # Pick a cyberpunk color (cyan, magenta, yellow, or white)
        color_choice = int(py5.random(4))
        if color_choice == 0:
            py5.fill(180, 100, 100, 80) # Cyan
        elif color_choice == 1:
            py5.fill(300, 100, 100, 80) # Magenta
        elif color_choice == 2:
            py5.fill(60, 100, 100, 80) # Yellow
        else:
            py5.fill(0, 0, 100, 80) # White
            
        # Glitch height might vary
        h_mod = h * py5.random(0.1, 1.0)
        final_y += (h - h_mod) / 2
        
        py5.rect(final_x, final_y, w, h_mod)
        
        # Occasionally draw scanlines inside the glitch
        if py5.random(1) < 0.3:
            py5.stroke(0, 0, 100, 50)
            py5.stroke_weight(2)
            for l_y in np.arange(final_y, final_y + h_mod, 4):
                py5.line(final_x, l_y, final_x + w, l_y)
            py5.no_stroke()
            
    # Add some random digital "snow" dots
    py5.fill(0, 0, 100, 60)
    for _ in range(100):
        sx = py5.random(SIZE[0])
        sy = py5.random(SIZE[1])
        py5.rect(sx, sy, py5.random(2, 6), py5.random(2, 6))

    # Save frame
    frame_filename = os.path.join(OUTPUT_DIR, f"frame-{state['frame_count']:04d}.png")
    apply_anti_flicker_filter(0.5)
    py5.save_frame(frame_filename)
    
    # Safety Check
    if state["frame_count"] == 30:
        py5.load_np_pixels()
        if py5.np_pixels.shape[:2] == (SIZE[1], SIZE[0]):
            std_dev = np.std(py5.np_pixels)
            if std_dev < 0.1:
                print(f"Warning: Screen is empty. std_dev={std_dev}")
                os._exit(1)

    if state["frame_count"] >= TOTAL_FRAMES:
        state["completed"] = True
        py5.no_loop()
        
        print("Rendering complete. Generating video...")
        video_path = os.path.join(os.path.dirname(OUTPUT_DIR), f"{WORK_NAME}.mp4")
        
        # Save a preview frame
        preview_path = os.path.join(os.path.dirname(OUTPUT_DIR), f"{WORK_NAME}_p1.png")
        os.system(f"cp {os.path.join(OUTPUT_DIR, 'frame-0450.png')} {preview_path}")

        ffmpeg_cmd = (
            f"ffmpeg -y -framerate {FPS} -i '{OUTPUT_DIR}/frame-%04d.png' "
            f"-c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow "
            f"'{video_path}'"
        )
        print("Executing ffmpeg:", ffmpeg_cmd)
        os.system(ffmpeg_cmd)
        
        # Clean up frames
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith(".png"):
                os.remove(os.path.join(OUTPUT_DIR, f))
        os.rmdir(OUTPUT_DIR)
        print("Video compilation and cleanup complete.")
        os._exit(0)

    state["frame_count"] += 1

if __name__ == "__main__":
    py5.run_sketch()
