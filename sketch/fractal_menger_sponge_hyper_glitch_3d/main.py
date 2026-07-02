from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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

def draw_sponge(x, y, z, size, depth, glitch_intensity):
    if depth == 0:
        # Glitch logic
        # High frequency noise for glitch trigger
        noise_val = py5.os_noise(x * 0.05, y * 0.05, py5.frame_count * 0.5)
        
        # If noise_val is high, apply glitch displacement and color
        is_glitch = noise_val > (0.6 - glitch_intensity * 0.4)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        
        if is_glitch:
            # Chromatic aberration colors
            color_choice = py5.random(3)
            if color_choice < 1:
                py5.fill(255, 0, 50) # Red
            elif color_choice < 2:
                py5.fill(0, 255, 100) # Green
            else:
                py5.fill(0, 50, 255) # Blue
                
            # Random displacement
            py5.translate(py5.random(-20, 20) * glitch_intensity, 
                          py5.random(-5, 5) * glitch_intensity, 
                          py5.random(-20, 20) * glitch_intensity)
            
            # Random rotation
            py5.rotate_x(py5.random(-0.5, 0.5) * glitch_intensity)
            py5.rotate_y(py5.random(-0.5, 0.5) * glitch_intensity)
            
            # Remove stroke for glitch shards to look distinct
            py5.no_stroke()
        else:
            # Normal concrete grey
            py5.fill(150, 150, 150)
            py5.stroke(50)
            py5.stroke_weight(1)

        py5.box(size)
        py5.pop_matrix()
        return

    new_size = size / 3.0
    for i in range(-1, 2):
        for j in range(-1, 2):
            for k in range(-1, 2):
                # The Menger sponge rule: skip the center cross
                if abs(i) + abs(j) + abs(k) <= 1:
                    continue # Skip central blocks
                if (i == 0 and j == 0) or (j == 0 and k == 0) or (i == 0 and k == 0):
                    continue
                
                nx = x + i * new_size
                ny = y + j * new_size
                nz = z + k * new_size
                
                draw_sponge(nx, ny, nz, new_size, depth - 1, glitch_intensity)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    # Dynamic harsh lighting
    py5.ambient_light(50, 50, 50)
    py5.directional_light(255, 255, 255, -1, 1, -1)
    py5.point_light(200, 200, 250, py5.width/2, py5.height/2, 200)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Base slow rotation
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_y(py5.frame_count * 0.01)
    
    # Calculate glitch intensity
    # Pulse the glitch periodically
    pulse = np.sin(py5.frame_count * 0.05)
    macro_glitch = 1.0 if (py5.frame_count % 120 > 110) else 0.0 # Huge glitch every 2s
    
    # Base glitch intensity depends on high frequency noise and the pulse
    glitch_intensity = max(0, pulse * 0.5) + macro_glitch * 2.0
    
    # If macro glitch, shake the whole camera
    if macro_glitch > 0:
        py5.translate(py5.random(-20, 20), py5.random(-20, 20), py5.random(-20, 20))
    
    # Draw level 3 sponge (3^3 = 27, level 3 is manageable performance-wise)
    draw_sponge(0, 0, 0, py5.height * 0.6, 3, glitch_intensity)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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
