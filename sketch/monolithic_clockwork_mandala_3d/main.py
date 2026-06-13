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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()


def draw():
    py5.background(10, 80, 10)
    
    # Lighting setup for metallic look
    py5.ambient_light(200, 40, 20)
    py5.directional_light(45, 80, 90, 0, 0, -1)
    py5.directional_light(210, 60, 100, 1, 1, -1)
    py5.light_specular(60, 20, 100)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_x(py5.PI / 4 + py5.sin(py5.frame_count * 0.005) * 0.2)
    py5.rotate_y(py5.frame_count * 0.002)
    
    num_rings = 12
    for i in range(num_rings):
        py5.push_matrix()
        
        radius = 200 + i * 80
        num_segments = 12 + i * 4
        
        # Alternate rotation speeds and directions
        rot_speed = (0.01 + 0.005 * i) * (1 if i % 2 == 0 else -1)
        py5.rotate_z(py5.frame_count * rot_speed)
        
        # Tilt some rings dynamically
        if i % 3 == 0:
            py5.rotate_x(py5.sin(py5.frame_count * 0.01 + i) * 0.5)
            
        py5.specular(50, 50, 100)
        py5.shininess(10.0)
        
        for j in range(num_segments):
            py5.push_matrix()
            angle = (py5.TWO_PI / num_segments) * j
            py5.rotate_z(angle)
            py5.translate(radius, 0, 0)
            
            # Gold and cyan alternate colors
            if i % 2 == 0:
                py5.fill(45, 80, 90) # Gold
            else:
                py5.fill(210, 80, 80) # Cyan
                
            # Pulsing height
            h = 40 + py5.sin(py5.frame_count * 0.05 + i + j) * 20
            py5.box(30, 20, h)
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
