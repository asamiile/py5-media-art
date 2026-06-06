from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(15, 10, 25)
    
    # Enable additive blending
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Global camera rotation
    cam_angle = py5.frame_count * 0.005
    py5.rotate_x(py5.PI / 6 + np.sin(cam_angle) * 0.1)
    py5.rotate_y(cam_angle)
    py5.rotate_z(np.cos(cam_angle) * 0.1)
    
    bloom = (np.sin(py5.frame_count * 0.02) + 1.0) / 2.0  # 0 to 1
    
    # Mandala rings
    num_rings = 8
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    for i in range(num_rings):
        py5.push_matrix()
        
        radius = 150 + i * 150 + bloom * 50
        
        # Counter-rotation for alternate rings
        rot_dir = 1 if i % 2 == 0 else -1
        py5.rotate_z(py5.frame_count * 0.01 * rot_dir * (num_rings - i + 1))
        
        # Oscillation for Z
        z_offset = np.sin(py5.frame_count * 0.05 + i) * 100 * bloom
        py5.translate(0, 0, z_offset)
        
        hue = (220 + i * 20 + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 90, 100, 80)
        
        # Intricate starburst logic
        points = 12 + i * 4
        
        py5.begin_shape()
        for j in range(points):
            angle = py5.TWO_PI * j / points
            
            # Star point
            inner_r = radius - 50 * bloom
            outer_r = radius + 50 * bloom
            
            x1 = inner_r * np.cos(angle - 0.1)
            y1 = inner_r * np.sin(angle - 0.1)
            py5.vertex(x1, y1, 0)
            
            x2 = outer_r * np.cos(angle)
            y2 = outer_r * np.sin(angle)
            py5.vertex(x2, y2, 0)
            
            x3 = inner_r * np.cos(angle + 0.1)
            y3 = inner_r * np.sin(angle + 0.1)
            py5.vertex(x3, y3, 0)
        py5.end_shape(py5.CLOSE)
        
        # Cross connecting lines for depth
        py5.stroke(hue, 50, 100, 40)
        py5.stroke_weight(1)
        for j in range(0, points, 2):
            angle1 = py5.TWO_PI * j / points
            angle2 = py5.TWO_PI * (j + points//3) / points
            
            x1 = radius * np.cos(angle1)
            y1 = radius * np.sin(angle1)
            x2 = radius * np.cos(angle2)
            y2 = radius * np.sin(angle2)
            
            py5.line(x1, y1, 0, x2, y2, 50)
            py5.line(x1, y1, 0, x2, y2, -50)
            
        py5.pop_matrix()

    # Core Wireframe Sphere
    py5.push_matrix()
    py5.rotate_x(py5.frame_count * 0.02)
    py5.rotate_y(py5.frame_count * 0.03)
    py5.stroke(320, 80, 100, 90)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.sphere_detail(8 + int(bloom * 4))
    py5.sphere(100 + bloom * 50)
    py5.pop_matrix()

    # Reset blend mode
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
