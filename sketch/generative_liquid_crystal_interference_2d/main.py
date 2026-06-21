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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.load_np_pixels()
    
    time_val = py5.frame_count * 0.05
    
    # We will use py5's vectorized operations if possible, but for simplicity and robustness
    # we can just draw shapes or use numpy arrays directly if fast enough. 
    # Since writing to np_pixels pixel-by-pixel in pure python is slow, we'll draw shapes 
    # that create an interference pattern using blend modes.
    
    py5.background(0, 0, 10)
    py5.blend_mode(py5.ADD)
    
    for i in range(12):
        # Create organic shapes
        py5.push_matrix()
        py5.translate(SIZE[0]/2, SIZE[1]/2)
        
        angle_offset = i * (py5.TWO_PI / 12) + time_val * 0.1
        radius = SIZE[1] * 0.4 + py5.sin(time_val + i) * SIZE[1] * 0.1
        
        x = py5.cos(angle_offset) * radius
        y = py5.sin(angle_offset) * radius
        
        py5.translate(x, y)
        
        hue_val = (i * 30 + time_val * 5) % 360
        py5.fill(hue_val, 80, 50, 20)
        
        # Draw a distorted rippling circle
        py5.begin_shape()
        detail = 100
        for j in range(detail):
            theta = py5.remap(j, 0, detail, 0, py5.TWO_PI)
            
            # Interference noise
            noise_val = py5.os_noise(
                py5.cos(theta) * 2 + time_val * 0.1 + i,
                py5.sin(theta) * 2 + time_val * 0.1 + i,
                time_val * 0.2
            )
            
            r = SIZE[1] * 0.4 * (0.5 + noise_val)
            
            px = py5.cos(theta) * r
            py = py5.sin(theta) * r
            py5.vertex(px, py)
            
        py5.end_shape(py5.CLOSE)
        py5.pop_matrix()
        
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

py5.run_sketch()
