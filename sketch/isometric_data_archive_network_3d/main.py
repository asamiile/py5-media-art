from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    # Set isometric projection
    py5.ortho(-py5.width/2, py5.width/2, -py5.height/2, py5.height/2, -5000, 5000)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_x(-py5.asin(1 / py5.sqrt(3)))
    py5.rotate_y(py5.QUARTER_PI)
    
    t = py5.frame_count * 0.05
    
    grid_size = 15
    spacing = 100
    
    # Translate to center the grid
    py5.translate(-grid_size * spacing / 2, 0, -grid_size * spacing / 2)
    
    for i in range(grid_size):
        for j in range(grid_size):
            x = i * spacing
            z = j * spacing
            
            # Dynamic height using noise
            h = 50 + 200 * py5.os_noise(i * 0.1, j * 0.1, t * 0.2)
            
            py5.push_matrix()
            py5.translate(x, h/2, z)
            
            # Draw server block
            py5.fill(220, 80, 20 + h * 0.1)
            py5.stroke(200, 90, 80)
            py5.stroke_weight(2)
            py5.box(spacing * 0.6, h, spacing * 0.6)
            
            # Draw data pulses
            if py5.os_noise(i * 0.5, j * 0.5, t) > 0.6:
                py5.stroke(180, 100, 100, 90)
                py5.stroke_weight(4)
                # Vertical pulse
                pulse_y = h * (py5.os_noise(i, j, t * 2) - 0.5)
                py5.line(0, pulse_y - 10, 0, 0, pulse_y + 10, 0)
                
            py5.pop_matrix()
            
            # Draw network connections
            if i < grid_size - 1:
                next_h = 50 + 200 * py5.os_noise((i+1) * 0.1, j * 0.1, t * 0.2)
                py5.stroke(200, 60, 40, 50)
                py5.stroke_weight(1)
                py5.line(x, 0, z, x + spacing, 0, z)
                if py5.os_noise(i, j, t * 0.5) > 0.7:
                    # Data packet moving
                    px = py5.lerp(x, x + spacing, (t + i) % 1.0)
                    py5.push_matrix()
                    py5.translate(px, 0, z)
                    py5.fill(160, 100, 100)
                    py5.no_stroke()
                    py5.sphere(4)
                    py5.pop_matrix()

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
            
        import os
        os._exit(0)

py5.run_sketch()
