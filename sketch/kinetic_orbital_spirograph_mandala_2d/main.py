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

# State
state = {
    "frame_count": 0,
    "completed": False
}

def setup():
    py5.size(SIZE[0], SIZE[1]) # Default renderer
    py5.frame_rate(FPS)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.background(0)
    # Using additive blending for glowing effect
    py5.blend_mode(py5.ADD)

def draw():
    if state["completed"]:
        return

    # Create a trailing motion blur effect by drawing a semi-transparent black rect in BLEND mode
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = state["frame_count"] * 0.015
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    num_points = 200
    
    py5.translate(cx, cy)
    py5.no_fill()
    py5.stroke_weight(1)
    
    # Base breathing radius
    base_r = 300 + 100 * np.sin(t * 0.5)
    
    # We will connect each point to point + offset
    offset = int(num_points * 0.3)
    
    # We want to do it in pure Python for py5 calls to avoid the P2D + Numpy type casting crash
    for i in range(num_points):
        # Calculate angle 1
        angle1 = i * (2 * np.pi / num_points) + t * 0.2
        
        # Calculate radius 1 with some noise or sine modulation
        r1 = base_r + 150 * np.sin(angle1 * 5 + t * 2)
        x1 = r1 * np.cos(angle1)
        y1 = r1 * np.sin(angle1)
        
        # Calculate angle 2
        j = (i + offset) % num_points
        angle2 = j * (2 * np.pi / num_points) - t * 0.3
        
        # Calculate radius 2 with different modulation
        r2 = base_r + 150 * np.cos(angle2 * 7 - t * 1.5)
        x2 = r2 * np.cos(angle2)
        y2 = r2 * np.sin(angle2)
        
        # Dynamic hue
        hue = (i * (360 / num_points) + t * 50) % 360
        py5.stroke(hue, 80, 100, 40)
        
        # Draw a bezier curve between the points
        # Control points will be pulled towards the center
        cx1 = x1 * 0.5
        cy1 = y1 * 0.5
        cx2 = x2 * 0.5
        cy2 = y2 * 0.5
        
        py5.bezier(float(x1), float(y1), float(cx1), float(cy1), float(cx2), float(cy2), float(x2), float(y2))

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
