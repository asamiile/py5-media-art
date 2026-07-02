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
    py5.sphere_detail(8)

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    t = py5.frame_count * 0.05
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.5)
    py5.rotate_z(py5.sin(t * 0.2) * 0.5)
    
    p = 3 # Torus knot parameter p
    q = 7 # Torus knot parameter q
    
    num_points = 2000
    py5.no_stroke()
    
    # Draw glowing torus knot
    for i in range(num_points):
        theta = py5.TWO_PI * i / num_points
        
        # Add time to theta to make pulses travel
        anim_theta = theta + t * 0.5
        
        # Torus knot equations
        r = py5.cos(q * theta) + 2
        x = r * py5.cos(p * theta) * 150
        y = r * py5.sin(p * theta) * 150
        z = py5.sin(q * theta) * 150
        
        # Color pulsing effect
        pulse = py5.sin(anim_theta * 10) * 0.5 + 0.5
        hue = (py5.degrees(anim_theta) * 0.5 + t * 10) % 360
        
        py5.push_matrix()
        py5.translate(x, y, z)
        
        # Core
        py5.fill(hue, 80, 100, 80 + pulse * 20)
        py5.sphere(4 + pulse * 4)
        
        # Outer glow
        py5.fill(hue, 90, 100, 10)
        py5.sphere(15 + pulse * 10)
        
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
