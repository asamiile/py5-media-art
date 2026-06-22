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

def draw():
    py5.background(10, 10, 15)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    time_val = py5.frame_count * 0.03
    
    # Global spin
    py5.rotate(time_val * 0.1)
    
    num_segments = 12
    angle_step = py5.TWO_PI / num_segments
    
    py5.no_stroke()
    
    # Draw radial segments
    for i in range(num_segments):
        py5.push_matrix()
        py5.rotate(i * angle_step)
        
        # Mirror every other segment for true kaleidoscope effect
        if i % 2 == 1:
            py5.scale(1, -1)
            
        # Draw tessellating shapes within the slice
        # The slice is bounded by angle 0 and angle_step
        
        num_layers = 8
        for j in range(num_layers, 0, -1):
            radius = SIZE[1] * 0.5 * (j / num_layers)
            
            # Breathing effect
            breath = py5.sin(time_val + j * 0.5) * 0.2 + 0.8
            radius *= breath
            
            # Sub-angles within the slice
            ang1 = 0
            ang2 = angle_step * py5.remap(py5.sin(time_val * 2 + j), -1, 1, 0.2, 0.8)
            ang3 = angle_step
            
            # Color
            hue = (time_val * 20 + j * 40 + i * 10) % 360
            
            # Shadow
            py5.fill(0, 0, 0, 50)
            py5.begin_shape()
            py5.vertex(0, 0)
            py5.vertex(py5.cos(ang1) * radius * 1.05, py5.sin(ang1) * radius * 1.05)
            py5.vertex(py5.cos(ang2) * radius * 1.2, py5.sin(ang2) * radius * 1.2)
            py5.vertex(py5.cos(ang3) * radius * 1.05, py5.sin(ang3) * radius * 1.05)
            py5.end_shape(py5.CLOSE)
            
            # Main shape
            py5.fill(hue, 80, 90)
            py5.begin_shape()
            py5.vertex(0, 0)
            py5.vertex(py5.cos(ang1) * radius, py5.sin(ang1) * radius)
            py5.vertex(py5.cos(ang2) * radius * 1.1, py5.sin(ang2) * radius * 1.1)
            py5.vertex(py5.cos(ang3) * radius, py5.sin(ang3) * radius)
            py5.end_shape(py5.CLOSE)
            
            # Inner accent
            py5.fill((hue + 180) % 360, 60, 100)
            py5.begin_shape()
            py5.vertex(py5.cos(ang2) * radius * 0.5, py5.sin(ang2) * radius * 0.5)
            py5.vertex(py5.cos(ang1) * radius * 0.8, py5.sin(ang1) * radius * 0.8)
            py5.vertex(py5.cos(ang2) * radius * 0.9, py5.sin(ang2) * radius * 0.9)
            py5.vertex(py5.cos(ang3) * radius * 0.8, py5.sin(ang3) * radius * 0.8)
            py5.end_shape(py5.CLOSE)

        py5.pop_matrix()

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
