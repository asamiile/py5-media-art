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
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.background(16, 11, 32)
    py5.blend_mode(py5.ADD)

def draw():
    # Subtle fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(16, 11, 32, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2)
    
    time = py5.frame_count * 0.05
    R = 800
    r = 210 + py5.sin(time * 0.2) * 50
    d = 400 + py5.cos(time * 0.3) * 100
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw three distinct spirograph lines for CMY
    colors = [
        (0, 255, 255), # Cyan
        (255, 0, 255), # Magenta
        (255, 255, 0)  # Yellow
    ]
    
    for c_idx, col in enumerate(colors):
        py5.stroke(*col, 150)
        py5.begin_shape()
        
        # Draw a partial curve that progresses over time
        for i in range(150):
            theta = time + i * 0.1 + c_idx * py5.PI / 3
            
            # Hypotrochoid equations
            x = (R - r) * py5.cos(theta) + d * py5.cos((R - r) / r * theta)
            y = (R - r) * py5.sin(theta) - d * py5.sin((R - r) / r * theta)
            
            # Apply an overall slow rotation
            rx = x * py5.cos(time * 0.1) - y * py5.sin(time * 0.1)
            ry = x * py5.sin(time * 0.1) + y * py5.cos(time * 0.1)
            
            py5.curve_vertex(rx, ry)
            
        py5.end_shape()

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
