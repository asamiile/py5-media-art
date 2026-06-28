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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw():
    # Motion blur effect
    py5.no_stroke()
    py5.fill(10, 5, 15, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Recursive fractal bloom
    depth = 6
    branches = 6
    radius = SIZE[1] * 0.2
    
    draw_branch(0, 0, radius, 0, depth, branches, t)

    py5.blend_mode(py5.BLEND)
    
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

def draw_branch(x, y, r, angle, depth, max_branches, t):
    if depth == 0:
        return
        
    hue = (t * 50 + depth * 30 + py5.degrees(angle)) % 360
    py5.stroke(hue, 80, 100, 100)
    py5.stroke_weight(depth)
    
    py5.push_matrix()
    py5.translate(x, y)
    py5.rotate(angle)
    
    # Pulsing length
    pulse = py5.sin(t * 2 + depth) * 0.2 + 1.0
    current_r = r * pulse
    
    py5.line(0, 0, 0, -current_r)
    
    # Sub-branches
    new_r = r * 0.6
    py5.translate(0, -current_r)
    
    for i in range(max_branches):
        a = (py5.TWO_PI / max_branches) * i + t * (1 if depth % 2 == 0 else -1)
        draw_branch(0, 0, new_r, a, depth - 1, 3 if depth < 4 else max_branches, t)
        
    py5.pop_matrix()

py5.run_sketch()
