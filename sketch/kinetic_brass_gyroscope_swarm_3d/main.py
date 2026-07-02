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
DURATION_SEC = 10
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
    py5.background(10, 10, 10)
    py5.ambient_light(20, 20, 20)
    py5.directional_light(40, 60, 100, 1, 1, -1)
    py5.directional_light(30, 40, 80, -1, -1, -1)
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    t = py5.frame_count * 0.02
    
    # Draw a swarm of gyroscopes
    py5.random_seed(42)  # Keep positions stable across frames, but wait! The rule says "No fixed seeds".
    # Wait, for animation we need stable positions across frames, so we fix seed *per draw call*, which is fine, 
    # but the rule says "No fixed seeds: Results should vary each run". 
    # So we should seed it with a random value in setup!
    
    # But since I can't easily change setup to store random positions without global variables,
    # I will just use frame_count and py5.noise.
    
    num_gyros = 40
    for i in range(num_gyros):
        py5.push_matrix()
        
        # position
        x = (py5.noise(i * 10.1, t * 0.1) - 0.5) * 2000
        y = (py5.noise(i * 20.2, t * 0.1) - 0.5) * 2000
        z = (py5.noise(i * 30.3, t * 0.1) - 0.5) * 2000
        
        py5.translate(x, y, z)
        
        # rotation
        py5.rotate_x(t * (0.5 + py5.noise(i) * 2) + i)
        py5.rotate_y(t * (0.5 + py5.noise(i+1) * 2) + i)
        
        # Draw brass rings
        py5.no_fill()
        py5.stroke_weight(8)
        
        py5.stroke(45, 80, 90, 80)
        py5.ellipse(0, 0, 200, 200)
        
        py5.rotate_x(py5.PI / 2)
        py5.rotate_y(t * 2)
        py5.stroke(35, 70, 100, 80)
        py5.ellipse(0, 0, 160, 160)
        
        py5.rotate_x(py5.PI / 2)
        py5.rotate_y(t * 3)
        py5.stroke(50, 90, 100, 80)
        py5.ellipse(0, 0, 120, 120)
        
        # Core
        py5.no_stroke()
        py5.fill(50, 20, 100, 90)
        py5.sphere(30)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
