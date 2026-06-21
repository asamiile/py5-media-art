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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.background(0, 0, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Gently sway the whole creature
    py5.rotate_x(py5.PI/6 + py5.sin(t * 0.2) * 0.1)
    py5.rotate_y(t * 0.3)
    py5.rotate_z(py5.sin(t * 0.15) * 0.1)
    
    # Upward swimming motion
    py5.translate(0, py5.sin(t * 0.5) * 100, 0)
    
    # Jellyfish bell
    py5.no_stroke()
    rings = 30
    pts = 60
    
    for r in range(rings - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for i in range(pts + 1):
            angle = (i % pts) * py5.TWO_PI / pts
            
            # Current ring
            rad1 = py5.sin((r / rings) * py5.PI) * 400
            y1 = -300 + (r / rings) * 600
            # Next ring
            rad2 = py5.sin(((r+1) / rings) * py5.PI) * 400
            y2 = -300 + ((r+1) / rings) * 600
            
            # Undulation
            wave1 = py5.sin(angle * 5 + t + r * 0.2) * 30
            wave2 = py5.sin(angle * 5 + t + (r+1) * 0.2) * 30
            
            hue = (200 + py5.sin(t * 0.1 + r * 0.1) * 40) % 360
            
            py5.fill(hue, 80, 100, 30)
            py5.vertex((rad1 + wave1) * py5.cos(angle), y1, (rad1 + wave1) * py5.sin(angle))
            py5.vertex((rad2 + wave2) * py5.cos(angle), y2, (rad2 + wave2) * py5.sin(angle))
            
        py5.end_shape()
        
    # Jellyfish tentacles
    num_tentacles = 12
    py5.stroke_weight(2)
    py5.no_fill()
    for i in range(num_tentacles):
        angle = (i / num_tentacles) * py5.TWO_PI
        
        hue = (180 + i * 10 + t * 20) % 360
        py5.stroke(hue, 90, 100, 60)
        
        py5.begin_shape()
        
        # Tentacle start point
        start_rad = 300
        start_y = 100
        py5.vertex(start_rad * py5.cos(angle), start_y, start_rad * py5.sin(angle))
        
        # Tentacle segments
        segments = 50
        cx = start_rad * py5.cos(angle)
        cz = start_rad * py5.sin(angle)
        cy = start_y
        
        for s in range(segments):
            cy += 15
            
            # Complex flowing noise
            nx = py5.os_noise(i, s * 0.05, t * 0.5) * 200 - 100
            nz = py5.os_noise(i + 100, s * 0.05, t * 0.5) * 200 - 100
            
            # Overall drift
            cx += py5.sin(t * 0.2 + s * 0.1) * 5 + nx * 0.1
            cz += py5.cos(t * 0.2 + s * 0.1) * 5 + nz * 0.1
            
            py5.vertex(cx, cy, cz)
            
        py5.end_shape()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
            
        import os
        os._exit(0)

py5.run_sketch()
