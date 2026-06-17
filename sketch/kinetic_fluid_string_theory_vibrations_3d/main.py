from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_STRINGS = 30
STRING_POINTS = 200

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Subtle clear to leave smooth trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40)
    
    py5.push_matrix()
    py5.camera()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    
    time_t = py5.frame_count * 0.015
    
    # Camera orbit
    cam_radius = 1500
    cam_angle = time_t * 0.5
    cam_x = np.cos(cam_angle) * cam_radius
    cam_z = np.sin(cam_angle) * cam_radius
    py5.camera(cam_x, 600 * np.sin(cam_angle * 1.5), cam_z, 0, 0, 0, 0, 1, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(3)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    for i in range(NUM_STRINGS):
        base_radius = 200 + i * 15
        
        hue = (time_t * 30 + i * 12) % 360
        py5.stroke(hue, 80, 100, 150)
        
        py5.begin_shape()
        # To make it a closed loop, we need to repeat the first few vertices
        # We will compute the points first
        pts = []
        for j in range(STRING_POINTS):
            angle = py5.TWO_PI * j / STRING_POINTS
            
            # Complex vibration noise
            nx = py5.os_noise(np.cos(angle) * 1.5, np.sin(angle) * 1.5, time_t + i) * 2 - 1
            ny = py5.os_noise(np.sin(angle) * 1.5, time_t * 1.5 + i, np.cos(angle) * 1.5) * 2 - 1
            nz = py5.os_noise(time_t + i * 0.5, np.cos(angle) * 1.5, np.sin(angle) * 1.5) * 2 - 1
            
            # Macro wave
            wave = np.sin(angle * 5 + time_t * 3 + i) * 50
            
            r = base_radius + nx * 150 + wave
            
            x = r * np.cos(angle)
            y = r * np.sin(angle) * np.sin(time_t + angle) + ny * 150
            z = r * np.sin(angle) + nz * 150
            
            pts.append((x, y, z))
            
        # Add overlapping points for smooth curve closure
        pts.extend(pts[:3])
        
        for p in pts:
            py5.curve_vertex(*p)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
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
