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

def draw_branch(len_val, depth, t):
    # Sway based on noise
    noise_val = py5.os_noise(depth, t * 0.5) - 0.5
    sway = noise_val * 0.2
    
    py5.stroke(200, 40, 100 - depth * 8, 80)
    py5.stroke_weight(depth * 1.5)
    py5.line(0, 0, 0, 0, -len_val, 0)
    py5.translate(0, -len_val, 0)
    
    if depth > 0:
        for angle in [-py5.PI/6, py5.PI/6]:
            py5.push_matrix()
            # Rotate along different axes for 3D
            py5.rotate_z(angle + sway)
            py5.rotate_y(angle * 1.5 + sway)
            draw_branch(len_val * 0.7, depth - 1, t)
            py5.pop_matrix()
            
        # Third branch pointing differently
        py5.push_matrix()
        py5.rotate_x(py5.PI/5 + sway)
        py5.rotate_y(-py5.PI/4 + sway)
        draw_branch(len_val * 0.65, depth - 1, t)
        py5.pop_matrix()
    else:
        # Draw bloom
        py5.no_stroke()
        hue = (t * 20 + py5.random(30)) % 360
        py5.fill(hue, 90, 100, 90)
        
        bloom_size = 8 + py5.sin(t * 2) * 3
        py5.sphere(bloom_size)

def draw():
    py5.background(10, 5, 15)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height, -200)
    py5.rotate_y(t * 0.3)
    
    py5.random_seed(42) # Keep structure consistent, just animate sway
    
    # Base trunk
    py5.translate(0, 50, 0)
    draw_branch(280, 6, t)

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
