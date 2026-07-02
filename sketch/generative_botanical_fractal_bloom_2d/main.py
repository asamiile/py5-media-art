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
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_cap(py5.ROUND)

def draw_branch(length, depth, max_depth, time_val):
    if depth == 0:
        # Bloom
        bloom_factor = py5.constrain((time_val - (max_depth - depth) * 0.5) * 2.0, 0, 1)
        if bloom_factor > 0:
            py5.no_stroke()
            py5.fill(330, 80, 100, 200)
            py5.circle(0, 0, 20 * bloom_factor)
        return

    # Growth factor for this branch
    # Time needs to reach a certain threshold before this branch starts growing
    start_time = (max_depth - depth) * 0.8
    growth = py5.constrain(time_val - start_time, 0, 1)
    
    if growth <= 0:
        return
        
    current_len = length * growth
    
    sway = py5.sin(time_val * 2.0 + depth) * 0.05
    
    py5.stroke(120, 60, 80, 200)
    py5.stroke_weight(depth * 1.5)
    py5.line(0, 0, 0, -current_len)
    
    py5.translate(0, -current_len)
    
    # Only branch if this segment is fully grown
    if growth >= 1.0:
        # Branch 1
        py5.push_matrix()
        py5.rotate(py5.PI / 6 + sway)
        draw_branch(length * 0.75, depth - 1, max_depth, time_val)
        py5.pop_matrix()
        
        # Branch 2
        py5.push_matrix()
        py5.rotate(-py5.PI / 5 + sway * 1.2)
        draw_branch(length * 0.7, depth - 1, max_depth, time_val)
        py5.pop_matrix()
        
        # Branch 3 (sometimes)
        if depth % 2 == 0:
            py5.push_matrix()
            py5.rotate(sway * 0.8)
            draw_branch(length * 0.6, depth - 1, max_depth, time_val)
            py5.pop_matrix()

def draw():
    py5.background(15, 10, 15)
    
    time_val = py5.frame_count * 0.02
    
    py5.translate(SIZE[0] / 2, SIZE[1] - 100)
    
    # Main trunk
    draw_branch(300, 9, 9, time_val)

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
