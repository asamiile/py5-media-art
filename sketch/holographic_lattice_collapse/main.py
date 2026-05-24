from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

BG_COLOR = (2, 2, 8)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(*BG_COLOR)
    py5.color_mode(py5.RGB, 255)
    
def draw():
    py5.background(*BG_COLOR)
    
    t = py5.frame_count / 60.0
    progress = py5.frame_count / TOTAL_FRAMES
    
    # Glitch intensity peaks towards the middle/end
    glitch_factor = (np.sin(progress * py5.PI - py5.HALF_PI) + 1) * 0.5
    glitch_factor = glitch_factor ** 3
    
    py5.translate(py5.width / 2, py5.height / 2 + 200, -200)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.2)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    grid_size = 40
    spacing = 30
    
    for x in range(-grid_size, grid_size):
        for y in range(-grid_size, grid_size):
            # Calculate distance from center
            d = np.sqrt(x*x + y*y)
            if d > grid_size * 0.8:
                continue
                
            px = x * spacing
            py = y * spacing
            
            # Base wave height
            wave = np.sin(d * 0.2 - t * 2) * 50 + np.cos(x * 0.3 + t) * 30 + np.sin(y * 0.3 + t * 1.5) * 30
            
            pz = wave
            
            # Color based on height and position
            r = (np.sin(x * 0.1 + t) * 127 + 128)
            g = (np.sin(y * 0.1 + t + py5.TWO_PI/3) * 127 + 128)
            b = (np.sin(pz * 0.05 + t + 2*py5.TWO_PI/3) * 127 + 128)
            
            # Apply glitch displacement
            if np.random.random() < glitch_factor * 0.2:
                pz += np.random.uniform(-300, 300) * glitch_factor
                px += np.random.uniform(-50, 50) * glitch_factor
                py += np.random.uniform(-50, 50) * glitch_factor
                
                # Saturated colors on glitch
                c_choice = np.random.randint(0, 3)
                if c_choice == 0: r, g, b = 255, 0, 0
                elif c_choice == 1: r, g, b = 0, 255, 0
                else: r, g, b = 0, 0, 255
            
            py5.push_matrix()
            py5.translate(px, py, pz)
            
            py5.stroke(r, g, b, 200)
            py5.stroke_weight(2)
            
            # Draw connecting lines or shapes
            if np.random.random() > 0.5:
                py5.box(spacing * 0.6)
            else:
                py5.sphere_detail(4)
                py5.sphere(spacing * 0.4)
                
            py5.pop_matrix()
            
    py5.blend_mode(py5.BLEND)

    # Global NumPy datamosh / scanline tear overlay
    if np.random.random() < glitch_factor * 0.5:
        py5.load_np_pixels()
        px_array = py5.np_pixels
        h, w = px_array.shape[:2]
        
        # Horizontal shift blocks
        for _ in range(int(glitch_factor * 5)):
            y1 = np.random.randint(0, h - 20)
            y2 = y1 + np.random.randint(5, 50)
            shift = np.random.randint(-150, 150)
            
            if shift > 0:
                px_array[y1:y2, shift:] = px_array[y1:y2, :-shift]
                px_array[y1:y2, :shift] = 0
            elif shift < 0:
                px_array[y1:y2, :shift] = px_array[y1:y2, -shift:]
                px_array[y1:y2, shift:] = 0
                
        py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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

py5.run_sketch()
