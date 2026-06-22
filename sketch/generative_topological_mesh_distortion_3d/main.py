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

COLS = 120
ROWS = 120
SCALE = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 10, 5)
    
    time_val = py5.frame_count * 0.02
    
    # Position camera
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 400, -500)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(time_val * 0.1) # Slowly rotate the entire mesh
    
    py5.translate(-COLS*SCALE/2, -ROWS*SCALE/2, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Calculate Z for current row
            noise_val1 = py5.os_noise(x * 0.05, y * 0.05, time_val)
            z1 = py5.remap(noise_val1, 0, 1, -600, 600)
            
            # Calculate Z for next row
            noise_val2 = py5.os_noise(x * 0.05, (y + 1) * 0.05, time_val)
            z2 = py5.remap(noise_val2, 0, 1, -600, 600)
            
            # Distance from center for coloring
            dist_x = x - COLS/2
            dist_y = y - ROWS/2
            dist = py5.sqrt(dist_x*dist_x + dist_y*dist_y)
            
            hue = (time_val * 30 + dist * 3 + z1 * 0.1) % 360
            
            # Fade out at the edges
            alpha = py5.remap(dist, 0, COLS/2, 255, 0)
            alpha = max(0, min(255, alpha))
            
            py5.stroke(hue, 80, 100, alpha)
            py5.vertex(x * SCALE, y * SCALE, z1)
            py5.vertex(x * SCALE, (y + 1) * SCALE, z2)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
