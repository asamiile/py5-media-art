import py5
import numpy as np
import os

# --- CONVENTIONS ---
# Resolution & Output
SIZE = (3840, 2160)
FPS = 60
DURATION_SEC = 15
TOTAL_FRAMES = FPS * DURATION_SEC

# Output configuration
WORK_NAME = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")

# --- GRID CONFIGURATION ---
COLS, ROWS = 120, 160
SCL = 60 # Size of each grid square
W = COLS * SCL
H = ROWS * SCL

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 90, 10) # Deep dark purple/blue
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def draw():
    # Motion blur / clear
    py5.fill(240, 90, 8, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    time_offset = py5.frame_count * 0.05
    
    # Calculate noise values for the terrain
    # We use numpy for fast evaluation
    # Generate X and Y coordinates
    x_idx = np.arange(COLS)
    y_idx = np.arange(ROWS)
    X_grid, Y_grid = np.meshgrid(x_idx, y_idx)
    
    # Noise offsets
    X_noise = X_grid * 0.08
    Y_noise = Y_grid * 0.08 - time_offset
    
    # Use py5.os_noise for the grid (vectorized would be better, but we can do it via a quick loop or numpy noise if available)
    # Since py5.os_noise is per-point, we can use a pre-calculated noise field or quickly iterate
    # For speed, we will approximate using sine waves and a few noise queries if needed, 
    # but 120x160 = 19200 points. A loop might take 5-10ms, which is fine for rendering.
    
    # Actually, we can just use 1D numpy arrays and vectorized math to generate a pseudo-noise landscape
    # to keep it entirely in numpy and blazingly fast.
    
    # Terrain height Z
    # Base undulating hills
    Z = np.sin(X_grid * 0.1) * np.cos(Y_grid * 0.1 - time_offset * 0.5) * 200
    Z += np.sin(X_grid * 0.03 - time_offset * 0.2) * np.sin(Y_grid * 0.04) * 400
    
    # Add sharp peaks using absolute sine waves (like a ridged multifractal)
    Z += (1.0 - np.abs(np.sin(X_grid * 0.15 + Y_grid * 0.05))) * 150
    
    # Flatten the center to make a "valley" or "road"
    center_dist = np.abs(X_grid - COLS / 2)
    valley_mask = np.clip(center_dist / (COLS * 0.2), 0, 1)
    # Smoothstep the mask
    valley_mask = valley_mask * valley_mask * (3 - 2 * valley_mask)
    Z = Z * valley_mask - 100 * (1 - valley_mask)
    
    # Real-world X, Y coordinates relative to camera
    real_X = (X_grid - COLS / 2) * SCL
    real_Y = (ROWS - Y_grid) * SCL - (ROWS * SCL * 0.3) # Move camera down
    real_Z = Z
    
    # Simple perspective projection
    # camera at (0, -2000, 1000), looking towards +Y
    cam_z_offset = 800
    cam_y_offset = -400
    
    fov = 800
    
    # Y is depth in this 3D coordinate system, Z is height (up/down)
    # Translate relative to camera
    rel_x = real_X
    rel_y = real_Y - cam_y_offset
    # Prevent div by zero
    rel_y = np.maximum(rel_y, 1.0)
    
    rel_z = real_Z - cam_z_offset
    
    # Project to 2D
    # Using typical projection: x2d = x * fov / z_depth
    # Here, depth is rel_y
    proj_X = (rel_x * fov) / rel_y + SIZE[0] / 2
    # Inverted Y on screen
    proj_Y = (rel_z * fov) / rel_y + SIZE[1] / 2 + 300
    
    # Render the wireframe
    py5.stroke_weight(2.5)
    py5.blend_mode(py5.ADD)
    
    # Render horizontal lines (rows)
    for y in range(ROWS - 1):
        # Fade out rows in the distance (large y_idx = distance)
        # y_idx=0 is far, y_idx=ROWS-1 is near
        dist_factor = y / ROWS
        alpha = 100 * (dist_factor ** 1.5)
        
        # Color based on height and distance
        # Cyan to Magenta gradient
        hue = 300 - (1 - dist_factor) * 100 
        
        py5.stroke(hue, 90, 100, alpha)
        
        # We can draw each row as a single shape
        py5.begin_shape()
        for x in range(COLS):
            px = float(proj_X[y, x])
            py = float(proj_Y[y, x])
            # Clip bounds roughly to avoid drawing crazy lines behind camera
            if rel_y[y, x] > 10: 
                py5.vertex(px, py)
        py5.end_shape()

    # Render vertical lines (cols)
    for x in range(0, COLS, 2):
        # Draw vertical lines segment by segment
        for y in range(ROWS - 1):
            dist_factor = y / ROWS
            alpha = 80 * (dist_factor ** 1.5)
            hue = 300 - (1 - dist_factor) * 100
            py5.stroke(hue, 90, 100, alpha)
            
            px1, py1 = float(proj_X[y, x]), float(proj_Y[y, x])
            px2, py2 = float(proj_X[y+1, x]), float(proj_Y[y+1, x])
            
            if rel_y[y, x] > 10 and rel_y[y+1, x] > 10:
                py5.line(px1, py1, px2, py2)
                
    py5.blend_mode(py5.BLEND)

    # Save frames
    frame_filename = os.path.join(OUTPUT_DIR, f"frame-{py5.frame_count:04d}.png")
    py5.save_frame(frame_filename)
    
    # Progress log
    if py5.frame_count % 30 == 0:
        print(f"Rendered {py5.frame_count}/{TOTAL_FRAMES} frames")

    if py5.frame_count >= TOTAL_FRAMES:
        print("Rendering complete. Generating video...")
        py5.no_loop()
        
        # Run ffmpeg to compile the video
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

py5.run_sketch()
