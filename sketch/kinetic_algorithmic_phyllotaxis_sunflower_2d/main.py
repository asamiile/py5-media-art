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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    
    py5.background(140, 80, 4) 
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    base_angle = 137.507764 * (py5.PI / 180.0)
    angle_offset = math.sin(loop_t) * 0.0006 
    
    angle = base_angle + angle_offset
    
    c = 18.0
    
    num_nodes = 9000
    
    py5.rotate(loop_t * 0.25)
    
    py5.no_stroke()
    
    for n in range(1, num_nodes + 1):
        r = c * math.sqrt(n)
        theta = n * angle
        
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        
        hue = (n * 0.08 + r * 0.06 - t * 360 * 2) % 360
        
        node_size = 4 + (r / SIZE[1]) * 18
        
        size_pulse = 1.0 + math.sin(loop_t * 4 + n * 0.02) * 0.5
        
        alpha = py5.remap(n, 1, num_nodes, 255, 0)
        if alpha < 0: alpha = 0
        
        py5.fill(hue, 85, 100, alpha)
        
        py5.push_matrix()
        py5.translate(x, y)
        
        py5.rotate(theta + loop_t * 3)
        
        # Diamond shape
        py5.begin_shape()
        py5.vertex(0, -node_size * size_pulse)
        py5.vertex(node_size * size_pulse * 0.6, 0)
        py5.vertex(0, node_size * size_pulse)
        py5.vertex(-node_size * size_pulse * 0.6, 0)
        py5.end_shape(py5.CLOSE)
        
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
