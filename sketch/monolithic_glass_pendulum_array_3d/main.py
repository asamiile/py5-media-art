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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_COLS = 15
GRID_ROWS = 10
SPACING = 150
PENDULUM_LENGTH = 800

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    py5.background(0) # Pitch black void
    
    # Lighting setup for minimal/glass look
    py5.ambient_light(20, 25, 30)
    py5.directional_light(255, 255, 255, 1, 1, -1) # Stark white light
    py5.directional_light(150, 180, 255, -1, 0.5, -1) # Pale icy blue
    py5.directional_light(255, 220, 150, 0, -1, 0.5) # Faint gold accent
    
    py5.push_matrix()
    
    # Center the entire grid
    total_width = (GRID_COLS - 1) * SPACING
    total_depth = (GRID_ROWS - 1) * SPACING
    
    py5.translate(py5.width / 2, -200, -500)
    
    # Very slow camera drift
    py5.rotate_x(py5.PI / 8)
    py5.rotate_y(py5.sin(py5.frame_count * 0.005) * 0.2 - 0.1)
    
    py5.translate(-total_width / 2, 0, -total_depth / 2)
    
    t = py5.frame_count * 0.02
    
    py5.no_stroke()
    
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            py5.push_matrix()
            py5.translate(c * SPACING, 0, r * SPACING)
            
            # The phase of the pendulum swing is based on its position in the grid
            phase = (c * 0.15) + (r * 0.1)
            # The swing angle is a sine wave
            angle = py5.sin(t + phase) * (py5.PI / 4)
            
            # Draw the pivot structure (minimal)
            py5.fill(100, 100, 110)
            py5.box(20)
            
            # Rotate for the swing
            py5.rotate_z(angle)
            
            # Draw the rod
            py5.fill(200, 200, 210, 150)
            py5.translate(0, PENDULUM_LENGTH / 2, 0)
            py5.box(10, PENDULUM_LENGTH, 10)
            
            # Draw the massive glass bob at the end
            py5.translate(0, PENDULUM_LENGTH / 2, 0)
            
            # Glass-like material: highly transparent, catching highlights
            py5.fill(255, 255, 255, 80)
            py5.specular(255, 255, 255)
            py5.shininess(100.0)
            
            # A sleek, geometric monolithic bob
            py5.box(80, 160, 80)
            
            py5.pop_matrix()
            
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
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
