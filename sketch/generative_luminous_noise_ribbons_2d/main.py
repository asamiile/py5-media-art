import os
import py5
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

# Simulation Settings
NUM_RIBBONS = 500
POINTS_PER_RIBBON = 50

# State
state = {
    "frame_count": 0,
    "positions": None,
    "velocities": None,
    "colors": None,
    "completed": False
}

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Very dark blue background
    py5.background(220, 90, 5)
    
    # Initialize ribbons
    # positions will be an array of shape (NUM_RIBBONS, 2)
    # They start randomly spread out or in a circle
    angles = np.random.uniform(0, 2 * np.pi, NUM_RIBBONS)
    radii = np.random.uniform(100, 800, NUM_RIBBONS)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    px = cx + np.cos(angles) * radii
    py = cy + np.sin(angles) * radii
    
    state["positions"] = np.column_stack((px, py))
    state["velocities"] = np.zeros((NUM_RIBBONS, 2))
    
    # Assign a hue for each ribbon based on its starting angle
    # Hues from 150 to 330 (Cyan to Magenta to Pink)
    base_hue = (angles / (2 * np.pi)) * 180 + 150
    state["colors"] = base_hue

def draw():
    if state["completed"]:
        return

    # Additive blend mode for luminous effect
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.5)
    
    t = state["frame_count"] * 0.005
    pos = state["positions"]
    vel = state["velocities"]
    
    # For each ribbon, we want to trace it forward by evaluating the noise field
    # But since it's a particle simulation, we just draw lines from previous to current
    prev_pos = pos.copy()
    
    # Compute noise-based force
    forces = np.zeros_like(pos)
    for i in range(NUM_RIBBONS):
        x, y = pos[i, 0], pos[i, 1]
        
        # Curl noise approximation using 3D noise
        # Scale down coordinates
        nx = x * 0.002
        ny = y * 0.002
        
        # Evaluate noise at two different offset Z planes
        n1 = py5.os_noise(nx, ny, t)
        n2 = py5.os_noise(nx + 100, ny + 100, t + 100)
        
        # Map noise (0-1) to angle (-PI to PI)
        angle = n1 * 4 * np.pi
        mag = n2 * 2.0
        
        forces[i, 0] = np.cos(angle) * mag
        forces[i, 1] = np.sin(angle) * mag
        
    # Update physics
    vel += forces
    vel *= 0.96 # Friction / dampening
    pos += vel
    
    # Wrap around bounds smoothly or just let them fly off?
    # Let's wrap them around but not draw the connecting line
    wrapped = False
    for i in range(NUM_RIBBONS):
        # We draw individually to apply color
        x, y = pos[i, 0], pos[i, 1]
        px, py = prev_pos[i, 0], prev_pos[i, 1]
        
        hue = state["colors"][i]
        
        # Shift hue over time
        hue = (hue + state["frame_count"] * 0.2) % 360
        
        # Alpha is low because we have many overlapping lines over many frames
        py5.stroke(hue, 90, 80, 8)
        
        # Only draw if it didn't wrap around the screen
        dist_sq = (x - px)**2 + (y - py)**2
        if dist_sq < 10000:
            py5.line(float(px), float(py), float(x), float(y))
            
        # Wrap
        if x < 0: pos[i, 0] += SIZE[0]
        if x > SIZE[0]: pos[i, 0] -= SIZE[0]
        if y < 0: pos[i, 1] += SIZE[1]
        if y > SIZE[1]: pos[i, 1] -= SIZE[1]

    # Save frame
    frame_filename = os.path.join(OUTPUT_DIR, f"frame-{state['frame_count']:04d}.png")
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
