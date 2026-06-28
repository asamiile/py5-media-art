from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw_slice(t):
    num_shapes = 24
    
    for i in range(num_shapes):
        hue = (i * 15 + t * 50) % 360
        py5.stroke(hue, 80, 100, 40)
        py5.fill(hue, 90, 80, 5)
        py5.stroke_weight(2)
        
        r1 = 50 + i * 40 + np.sin(t + i*0.2) * 50
        r2 = r1 + 80 + np.cos(t * 1.5 + i*0.3) * 40
        angle_offset = np.sin(t * 0.5 + i*0.1) * py5.PI / 12
        
        py5.begin_shape()
        py5.vertex(r1 * np.cos(angle_offset), r1 * np.sin(angle_offset))
        py5.vertex(r2 * np.cos(angle_offset * 2), r2 * np.sin(angle_offset * 2))
        py5.vertex(r2 * np.cos(-angle_offset * 2), r2 * np.sin(-angle_offset * 2))
        py5.vertex(r1 * np.cos(-angle_offset), r1 * np.sin(-angle_offset))
        py5.end_shape(py5.CLOSE)
        
        py5.no_stroke()
        py5.fill(hue, 60, 100, 80)
        py5.ellipse(r2 * np.cos(angle_offset), r2 * np.sin(angle_offset), 8, 8)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 15) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    t = py5.frame_count * 0.01
    
    slices = 12
    angle_step = py5.TWO_PI / slices
    
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(t * 0.2) 
    
    for i in range(slices):
        py5.push_matrix()
        py5.rotate(i * angle_step)
        draw_slice(t)
        
        py5.scale(1, -1)
        draw_slice(t)
        py5.pop_matrix()
        
    py5.pop_matrix()

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
