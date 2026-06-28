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

# Set rendering duration in seconds (between 15 and 30 seconds)
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
    "frequencies": [],
    "amplitudes": [],
    "phases": [],
    "centers": [],
    "num_waves": 8
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
    
    # Initialize cymatic wave parameters
    for i in range(state["num_waves"]):
        # Base frequency (how dense the rings are)
        state["frequencies"].append(random.uniform(0.01, 0.05))
        # Amplitude / strength
        state["amplitudes"].append(random.uniform(0.5, 2.0))
        # Phase shift (animated over time)
        state["phases"].append(random.uniform(0, py5.TWO_PI))
        # Centers for the waves, arranged symmetrically
        angle = (i / state["num_waves"]) * py5.TWO_PI
        radius = random.uniform(0, 300)
        cx = py5.width / 2 + np.cos(angle) * radius
        cy = py5.height / 2 + np.sin(angle) * radius
        state["centers"].append((cx, cy))

    print(f"Starting cymatic render. Target: {TOTAL_FRAMES} frames ({DURATION_SEC}s).")

# ----------------------------------------------------------------------------
# 4. Draw
# ----------------------------------------------------------------------------
def draw():
    if state["completed"]:
        return

    # Clear background slightly for motion blur
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)

    # Time variable for animation
    t = state["frame_count"] * 0.05
    
    num_rings = 200
    points_per_ring = 400
    
    # Pre-calculate base colors
    hue_base = (state["frame_count"] * 0.5) % 360
    
    # Vectorized evaluation using meshgrid
    r = np.linspace(1, py5.width * 0.6, num_rings)
    theta = np.linspace(0, py5.TWO_PI, points_per_ring)
    R, Theta = np.meshgrid(r, theta)
    
    X = py5.width / 2 + R * np.cos(Theta)
    Y = py5.height / 2 + R * np.sin(Theta)
    
    interference = np.zeros_like(X)
    
    for i in range(state["num_waves"]):
        cx, cy = state["centers"][i]
        
        rot_angle = t * 0.2 * (1 if i % 2 == 0 else -1)
        dx = X - (py5.width/2 + (cx - py5.width/2)*np.cos(rot_angle) - (cy - py5.height/2)*np.sin(rot_angle))
        dy = Y - (py5.height/2 + (cx - py5.width/2)*np.sin(rot_angle) + (cy - py5.height/2)*np.cos(rot_angle))
        
        dist = np.sqrt(dx**2 + dy**2)
        
        freq = state["frequencies"][i]
        amp = state["amplitudes"][i]
        phase = state["phases"][i] + t * 0.5 * (1 if i%3==0 else -1)
        
        wave = np.sin(dist * freq + phase) * amp * np.exp(-dist * 0.002)
        interference += wave
        
    magnitude = np.abs(interference)
    
    # Filter points where magnitude > 1.0
    mask = magnitude > 1.0
    valid_x = X[mask]
    valid_y = Y[mask]
    valid_mag = magnitude[mask]
    
    for x, y, mag in zip(valid_x, valid_y, valid_mag):
        hue = (hue_base + mag * 50) % 360
        brightness = min(mag * 50, 100)
        alpha = min(mag * 20, 255)
        py5.fill(hue, 80, brightness, alpha)
        py5.circle(float(x), float(y), float(mag * 2))
            
    # ------------------------------------------------------------------------
    # 5. Output Frame & Completion Check
    # ------------------------------------------------------------------------
    frame_filename = os.path.join(OUTPUT_DIR, f"frame-{state['frame_count']:04d}.png")
    py5.save_frame(frame_filename)
    
    # ------------------------------------------------------------------------
    # 6. Safety Blank Screen Check (Every 30 frames)
    # ------------------------------------------------------------------------
    if state["frame_count"] % 30 == 0:
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
        
        # Compile MP4 using ffmpeg
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
            
            # Save the last frame as preview
            preview_filename = os.path.join(os.path.dirname(__file__), f"{os.path.basename(os.path.dirname(__file__))}_p1.png")
            Image.open(frame_filename).save(preview_filename)
            
            # Clean up frames
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
