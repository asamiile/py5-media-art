from pathlib import Path
import shutil
import subprocess
import sys
import random
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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_fill()


def draw():
    py5.background(0, 0, 5)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_y(py5.frame_count * 0.007)
    
    num_strands = 150
    for i in range(num_strands):
        py5.push_matrix()
        
        # Distribute evenly using golden ratio
        phi = 1.618033988749895
        y = 1 - (i / float(num_strands - 1)) * 2
        radius = py5.sqrt(1 - y * y)
        theta = phi * i * py5.TWO_PI
        
        x = py5.cos(theta) * radius
        z = py5.sin(theta) * radius
        
        py5.translate(x * 100, y * 100, z * 100)
        
        # Calculate dynamic rotation based on position and time
        noise_val = py5.os_noise(x, y, z, py5.frame_count * 0.01)
        py5.rotate_x(noise_val * py5.TWO_PI)
        py5.rotate_y(noise_val * py5.TWO_PI)
        
        hue = (py5.frame_count * 0.5 + i * 2) % 360
        py5.stroke(hue, 80, 80, 40)
        py5.stroke_weight(2)
        
        py5.begin_shape(py5.LINE_STRIP)
        length = 400 + 200 * py5.sin(py5.frame_count * 0.05 + i)
        for j in range(20):
            t = j / 19.0
            cur_r = t * length
            cur_ang = t * py5.PI * 4 + py5.frame_count * 0.1
            px = py5.cos(cur_ang) * cur_r * 0.2
            py_pos = t * length
            pz = py5.sin(cur_ang) * cur_r * 0.2
            py5.vertex(px, py_pos, pz)
        py5.end_shape()
        
        # Glowing tip
        py5.push_matrix()
        py5.translate(py5.cos(py5.PI * 4 + py5.frame_count * 0.1) * length * 0.2, length, py5.sin(py5.PI * 4 + py5.frame_count * 0.1) * length * 0.2)
        py5.stroke(hue, 60, 100, 80)
        py5.stroke_weight(8)
        py5.point(0, 0, 0)
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
