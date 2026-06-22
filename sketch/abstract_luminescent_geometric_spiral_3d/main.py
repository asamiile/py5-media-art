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

NUM_BOXES = 300

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 5, 10)
    
    time_val = py5.frame_count * 0.05
    
    # Lighting
    py5.ambient_light(20, 20, 20)
    py5.directional_light(200, 80, 100, 0, -1, 0)
    py5.directional_light(320, 80, 100, 1, 1, 1)
    
    # Position camera to look down the spiral
    py5.translate(SIZE[0]/2, SIZE[1]/2, -300)
    py5.rotate_x(py5.PI / 4)
    py5.rotate_y(time_val * 0.2)
    
    # The spiral moves upwards, creating an infinite descending illusion
    for i in range(NUM_BOXES):
        # We want the boxes to cycle so it looks infinite
        # Using modulo to wrap their index based on time
        t = (i + py5.frame_count * 0.5) % NUM_BOXES
        
        angle = t * 0.3
        radius = 50 + t * 4  # Spiral gets wider as it goes "down"
        y_pos = -t * 8       # Spiral goes "up" and "down"
        
        # Calculate color and alpha based on position to fade out smoothly at the ends
        alpha = py5.remap(t, 0, NUM_BOXES, 255, 0)
        hue = (180 + t * 0.5 + time_val * 10) % 360
        
        py5.fill(hue, 80, 100, alpha)
        
        x_pos = py5.cos(angle) * radius
        z_pos = py5.sin(angle) * radius
        
        py5.push_matrix()
        py5.translate(x_pos, y_pos + 1200, z_pos) # Offset y to center
        
        # Orient boxes along the curve
        py5.rotate_y(-angle)
        
        # Make them pulse
        pulse = py5.sin(t * 0.2 - time_val * 2)
        box_width = py5.remap(pulse, -1, 1, 10, 40)
        
        py5.box(box_width, 20, 80)
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
