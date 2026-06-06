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

def draw_sponge(x, y, z, r, depth, max_depth, t):
    if depth == max_depth:
        # Breathing effect based on time and position
        scale_mod = py5.remap(py5.sin(t * 2 + (x+y+z)*0.01), -1, 1, 0.2, 1.0)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        
        hue = (180 + (x+y+z)*0.2 + t*20) % 360
        py5.fill(hue, 80, 90)
        
        py5.box(r * scale_mod)
        py5.pop_matrix()
    else:
        new_r = r / 3.0
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    # Skip the center pieces to make it a sponge
                    if abs(i) + abs(j) + abs(k) > 1:
                        draw_sponge(x + i * new_r, y + j * new_r, z + k * new_r, new_r, depth + 1, max_depth, t)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(10)
    py5.lights()
    py5.directional_light(0, 0, 100, 1, 1, -1)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    py5.rotate_x(t * 0.2)
    py5.rotate_y(t * 0.3)
    py5.rotate_z(t * 0.1)
    
    py5.no_stroke()
    
    # Draw sponge (depth 3 means 20 * 20 = 400 boxes, let's do depth 2 (20 boxes, too small) or depth 3 (400 boxes, perfect))
    draw_sponge(0, 0, 0, 1200, 1, 3, py5.frame_count * 0.05)

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2. Aborting.")
            import os
            os._exit(1)

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
