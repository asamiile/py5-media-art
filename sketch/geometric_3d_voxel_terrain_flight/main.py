from pathlib import Path
import shutil
import subprocess
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

COLS = 45
ROWS = 40
CELL_SIZE = 50

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(15)
    
    t = py5.frame_count * 0.05
    flight_speed = py5.frame_count * 0.15
    
    # Setup camera for flight simulation
    cam_x = py5.width / 2
    cam_y = py5.height / 2 - 300 - py5.sin(t * 0.5) * 100 # Hovering up and down
    cam_z = 600
    
    # Target to look at
    look_x = py5.width / 2 + py5.sin(t * 0.2) * 500 # Look left and right
    look_y = py5.height / 2 + 100
    look_z = 0
    
    py5.camera(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 1, 0)
    
    # Add dramatic atmospheric lighting
    py5.ambient_light(220, 40, 20)
    py5.directional_light(180, 80, 100, -1, 1, -1)
    py5.directional_light(320, 80, 80, 1, 0.5, 0)
    py5.point_light(50, 100, 100, cam_x, cam_y, cam_z - 200) # Headlight
    
    py5.stroke(0, 50)
    py5.stroke_weight(1.0)
    
    # Center the grid
    py5.translate(py5.width/2 - (COLS * CELL_SIZE)/2, py5.height/2 + 200, -800)
    py5.rotate_x(py5.PI / 3) # Tilt forward to see the terrain
    
    # Draw the voxel terrain
    for y in range(ROWS):
        for x in range(COLS):
            # Calculate Perlin noise with flight offset
            # y-axis in grid represents forward motion (z-axis in world)
            noise_val = py5.noise(x * 0.1, (y - flight_speed) * 0.1)
            
            # Map noise to voxel height, creating mountains and deep valleys
            h = py5.remap(noise_val ** 2, 0, 1, 10, 800)
            
            # Color mapping based on height (like a topographic map)
            hue = py5.remap(h, 10, 800, 260, 360) % 360
            saturation = py5.remap(h, 10, 800, 100, 40)
            brightness = py5.remap(h, 10, 800, 40, 100)
            
            py5.push_matrix()
            
            # Position the voxel
            py5.translate(x * CELL_SIZE, y * CELL_SIZE, h / 2)
            
            # Make the tallest peaks glow (neon lava/snow effect)
            if h > 500:
                py5.emissive(hue, 80, 100)
                py5.fill(hue, saturation, brightness)
            else:
                py5.emissive(0, 0, 0)
                py5.fill(hue, saturation, brightness)
                
            # Draw the voxel cube
            py5.box(CELL_SIZE, CELL_SIZE, h)
            
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
