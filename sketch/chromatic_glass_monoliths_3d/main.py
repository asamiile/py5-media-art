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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()

def draw():
    py5.background(240, 90, 10)  # Very dark indigo
    
    # Set up lights for the glass reflection effect
    py5.ambient_light(240, 50, 30)
    py5.directional_light(180, 100, 80, 1, 1, -1)  # Cyan light
    py5.directional_light(320, 100, 80, -1, -1, -1)  # Magenta light
    py5.point_light(45, 100, 100, 0, 0, 200)  # Gold accent light
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    t = py5.frame_count / TOTAL_FRAMES
    py5.rotate_y(t * py5.TWO_PI)
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.2)
    
    # Draw monoliths
    num_monoliths = 12
    for i in range(num_monoliths):
        py5.push_matrix()
        angle = (i / num_monoliths) * py5.TWO_PI
        radius = 400 + py5.sin(angle * 3 + t * py5.TWO_PI) * 100
        py5.translate(py5.cos(angle) * radius, py5.sin(angle * 2) * 200, py5.sin(angle) * radius)
        py5.rotate_y(angle + t * py5.TWO_PI)
        py5.rotate_x(t * py5.PI)
        
        py5.fill(200, 40, 90, 80)  # Semi-transparent glass
        py5.specular(0, 0, 100)
        py5.shininess(50)
        
        py5.box(100, 800, 100)
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
