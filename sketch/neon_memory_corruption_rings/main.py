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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(10, 5, 20)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    # Subtle motion blur
    py5.push_style()
    py5.fill(10, 5, 20, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_style()

    t = py5.frame_count * 0.03
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_x(py5.frame_count * 0.007)
    py5.rotate_y(py5.frame_count * 0.011)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    num_rings = 45
    for i in range(num_rings):
        radius = 150 + i * 18
        
        py5.push_matrix()
        py5.rotate_z(t * (0.4 + i * 0.02))
        
        if i % 3 == 0:
            py5.stroke(0, 255, 255, 180) # Cyan
        elif i % 3 == 1:
            py5.stroke(255, 0, 255, 180) # Magenta
        else:
            py5.stroke(40, 80, 255, 180) # Electric Blue
            
        py5.stroke_weight(3 if i % 6 == 0 else 1.5)
        
        py5.begin_shape(py5.LINE_STRIP)
        num_points = 120
        for j in range(num_points + 1):
            angle = py5.TWO_PI * j / num_points
            
            # Glitch effect
            noise_val = py5.noise(i * 0.1, j * 0.08, t * 1.5)
            glitch_offset = 0
            if noise_val > 0.65:
                glitch_offset = (noise_val - 0.65) * 600
                
            r = radius + glitch_offset
            x = r * py5.cos(angle)
            y = r * py5.sin(angle)
            z = py5.sin(angle * 4 + t * 2) * 80 * noise_val
            
            py5.vertex(x, y, z)
            
        py5.end_shape()
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
