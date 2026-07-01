import os
import py5
import numpy as np
import random
from PIL import Image

# ----------------------------------------------------------------------------
# 1. Configuration & Constants
# ----------------------------------------------------------------------------

# Set window size
SIZE = (1920, 1080)

# Set rendering duration in seconds
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

# Ensure output directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# 2. Sketch State
# ----------------------------------------------------------------------------
state = {
    "frame_count": 0,
    "completed": False,
    # Base parameters for the Clifford Attractor
    "a_base": random.uniform(-2, 2),
    "b_base": random.uniform(-2, 2),
    "c_base": random.uniform(-2, 2),
    "d_base": random.uniform(-2, 2),
    # Frequencies for how fast each parameter changes
    "a_freq": random.uniform(0.01, 0.03),
    "b_freq": random.uniform(0.01, 0.03),
    "c_freq": random.uniform(0.01, 0.03),
    "d_freq": random.uniform(0.01, 0.03),
}

# ----------------------------------------------------------------------------
# 3. Setup
# ----------------------------------------------------------------------------
def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    py5.no_stroke()
    py5.blend_mode(py5.ADD)

    print(f"Starting attractor render. Target: {TOTAL_FRAMES} frames ({DURATION_SEC}s).")

# ----------------------------------------------------------------------------
# 4. Draw
# ----------------------------------------------------------------------------
def draw():
    if state["completed"]:
        return

    # Fully clear background to prevent endless smearing of the dense points
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    
    py5.blend_mode(py5.ADD)

    t = state["frame_count"] * 0.02
    
    # Calculate current attractor parameters by modulating base with sine waves
    a = state["a_base"] + np.sin(t * state["a_freq"]) * 0.5
    b = state["b_base"] + np.cos(t * state["b_freq"]) * 0.5
    c = state["c_base"] + np.sin(t * state["c_freq"]) * 0.5
    d = state["d_base"] + np.cos(t * state["d_freq"]) * 0.5
    
    num_points = 500000
    
    # We want to iterate the attractor sequentially, but doing 500k iterations in raw Python is too slow.
    # To vectorize it, we can simulate N distinct "streams" in parallel.
    # E.g. start with 5000 random points, and iterate them 100 times.
    num_streams = 10000
    iterations = 50
    
    # Random starting points between -2 and 2
    x = np.random.uniform(-2, 2, num_streams)
    y = np.random.uniform(-2, 2, num_streams)
    
    # Arrays to accumulate all points
    all_x = np.empty(num_streams * iterations, dtype=np.float32)
    all_y = np.empty(num_streams * iterations, dtype=np.float32)
    
    for i in range(iterations):
        # Clifford Attractor equations
        x_new = np.sin(a * y) + c * np.cos(a * x)
        y_new = np.sin(b * x) + d * np.cos(b * y)
        
        # Store
        all_x[i*num_streams : (i+1)*num_streams] = x_new
        all_y[i*num_streams : (i+1)*num_streams] = y_new
        
        x = x_new
        y = y_new
        
    # Map points to screen coordinates
    # Attractor bounds are typically roughly -3 to 3
    scale = min(py5.width, py5.height) / 6.0
    screen_x = py5.width / 2.0 + all_x * scale
    screen_y = py5.height / 2.0 + all_y * scale
    
    # Filter points out of bounds
    valid = (screen_x > 0) & (screen_x < py5.width) & (screen_y > 0) & (screen_y < py5.height)
    valid_x = screen_x[valid]
    valid_y = screen_y[valid]
    
    # Color variation based on density/position or just time
    hue_base = (state["frame_count"] * 0.5) % 360
    
    # Since there are so many points, we use py5.points() if it exists or begin_shape(POINTS)
    # Py5 provides points(coordinates) for vectorized drawing!
    coords = np.column_stack((valid_x, valid_y))
    
    py5.fill(hue_base, 80, 10, 10)
    py5.stroke(hue_base, 80, 50, 15)  # low alpha, bright
    py5.stroke_weight(1.5)
    
    py5.points(coords)
    py5.no_stroke()
    
    # ------------------------------------------------------------------------
    # 5. Output Frame & Completion Check
    # ------------------------------------------------------------------------
    frame_filename = os.path.join(OUTPUT_DIR, f"frame-{state['frame_count']:04d}.png")
    py5.save_frame(frame_filename)
    
    # ------------------------------------------------------------------------
    # 6. Safety Blank Screen Check (Every 30 frames)
    # ------------------------------------------------------------------------
    if state["frame_count"] > 0 and state["frame_count"] % 30 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.shape[:2] == (SIZE[1], SIZE[0]):
            std_dev = np.std(py5.np_pixels)
            if std_dev < 1.0:
                print(f"Warning: Screen is essentially blank (std dev: {std_dev}). Aborting to prevent hanging.")
                os._exit(1)

    # ------------------------------------------------------------------------
    # 7. Post-Processing & Cleanup
    # ------------------------------------------------------------------------
    if state["frame_count"] >= TOTAL_FRAMES:
        state["completed"] = True
        print("Rendering complete. Assembling MP4...")
        
        import subprocess
        output_mp4 = os.path.join(os.path.dirname(__file__), f"{os.path.basename(os.path.dirname(__file__))}.mp4")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", os.path.join(OUTPUT_DIR, "frame-%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output_mp4
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            print(f"Successfully generated {output_mp4}")
            
            preview_filename = os.path.join(os.path.dirname(__file__), f"{os.path.basename(os.path.dirname(__file__))}_p1.png")
            Image.open(frame_filename).save(preview_filename)
            
            for f in os.listdir(OUTPUT_DIR):
                os.remove(os.path.join(OUTPUT_DIR, f))
            os.rmdir(OUTPUT_DIR)
            print("Cleanup complete.")
            
        except subprocess.CalledProcessError as e:
            print(f"Error compiling video: {e}")
            os._exit(1)
            
        print("All done. Exiting.")
        os._exit(0)

    state["frame_count"] += 1

if __name__ == "__main__":
    py5.run_sketch()
