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
    py5.rect_mode(py5.CENTER)

def draw_mandala_ring(radius, num_elements, speed_mult, shape_type, frame):
    py5.push_matrix()
    
    # Base rotation
    py5.rotate(frame * 0.01 * speed_mult)
    
    for i in range(num_elements):
        angle = py5.TWO_PI / num_elements * i
        
        py5.push_matrix()
        py5.rotate(angle)
        py5.translate(0, -radius)
        
        # Pulse size based on angle and frame
        pulse = py5.sin(frame * 0.05 + i * 0.5) * 0.5 + 0.5
        size = SIZE[1] * 0.02 + pulse * SIZE[1] * 0.03
        
        hue = (180 + radius * 0.2 + frame * 0.5 + i * 5) % 360
        py5.stroke(hue, 80, 100, 80)
        py5.stroke_weight(2)
        
        if py5.frame_count % 30 < 15:
            py5.fill(hue, 100, 100, 30 * pulse)
        else:
            py5.no_fill()
            
        if shape_type == 0:
            py5.rect(0, 0, size, size)
        elif shape_type == 1:
            py5.circle(0, 0, size)
        elif shape_type == 2:
            py5.triangle(-size/2, size/2, size/2, size/2, 0, -size/2)
        elif shape_type == 3:
            py5.line(0, -size, 0, size)
            py5.line(-size, 0, size, 0)
            
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    py5.background(0, 0, 5, 20) # Slight trail effect
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    num_rings = 10
    max_radius = SIZE[1] * 0.45
    
    for r in range(1, num_rings + 1):
        radius = (max_radius / num_rings) * r
        # Distort radius with sine wave
        radius += py5.sin(py5.frame_count * 0.02 + r) * 20
        
        num_elements = r * 6
        speed_mult = 1 if r % 2 == 0 else -1
        speed_mult *= 1 + (r * 0.1)
        
        shape_type = r % 4
        
        draw_mandala_ring(radius, num_elements, speed_mult, shape_type, py5.frame_count)
        
    py5.blend_mode(py5.BLEND)

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
