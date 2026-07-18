from pathlib import Path
import shutil
import subprocess
import sys
import math
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

def draw_mandala(radius, num_points, noise_offset, t_loop):
    py5.begin_shape(py5.LINES)
    for i in range(num_points):
        angle1 = i * py5.TWO_PI / num_points
        
        for j in range(1, 6): 
            angle2 = (i + j * (num_points // 6)) * py5.TWO_PI / num_points
            
            tx = math.cos(t_loop)
            ty = math.sin(t_loop)
            
            n1 = py5.noise(math.cos(angle1) + noise_offset, math.sin(angle1) + noise_offset, tx * 0.5)
            n2 = py5.noise(math.cos(angle2) + noise_offset, math.sin(angle2) + noise_offset, ty * 0.5)
            
            r1 = radius + py5.remap(n1, 0, 1, -radius*0.1, radius*0.1)
            r2 = radius + py5.remap(n2, 0, 1, -radius*0.1, radius*0.1)
            
            x1 = math.cos(angle1) * r1
            y1 = math.sin(angle1) * r1
            x2 = math.cos(angle2) * r2
            y2 = math.sin(angle2) * r2
            
            py5.vertex(x1, y1)
            py5.vertex(x2, y2)
    py5.end_shape()

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(5, 5, 10)
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.stroke_weight(2)
    
    py5.push_matrix()
    py5.rotate(t * py5.TWO_PI / 3) 
    py5.stroke(200, 90, 80, 50)
    draw_mandala(max(SIZE) * 0.35, 90, 100, loop_t) 
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate(-t * py5.TWO_PI / 2) 
    py5.stroke(320, 90, 80, 50)
    draw_mandala(max(SIZE) * 0.3, 120, 200, loop_t) 
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate(t * py5.TWO_PI) 
    py5.stroke(50, 90, 80, 50)
    draw_mandala(max(SIZE) * 0.25, 60, 300, loop_t) 
    py5.pop_matrix()
    
    # Extra inner detailed mandala
    py5.push_matrix()
    py5.rotate(-t * py5.TWO_PI * 2) 
    py5.stroke(180, 90, 100, 60) # Cyan
    draw_mandala(max(SIZE) * 0.15, 30, 400, loop_t) 
    py5.pop_matrix()

    py5.color_mode(py5.RGB, 255)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
