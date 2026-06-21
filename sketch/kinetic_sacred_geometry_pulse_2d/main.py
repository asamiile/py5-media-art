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
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_seed_of_life(x, y, radius, time):
    py5.push_matrix()
    py5.translate(x, y)
    py5.rotate(time * 0.1)
    
    # Center circle
    py5.circle(0, 0, radius * 2)
    
    # 6 surrounding circles
    for i in range(6):
        angle = (i / 6) * py5.TWO_PI
        cx = radius * py5.cos(angle)
        cy = radius * py5.sin(angle)
        py5.circle(cx, cy, radius * 2)
        
    py5.pop_matrix()

def draw():
    py5.background(5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2)
    py5.no_fill()
    
    # Grid of sacred geometry
    rings = 6
    spacing = 400
    
    for ring in range(rings):
        # Base radius pulses
        pulse = py5.sin(t * 0.5 - ring * 0.5)
        radius = 150 + pulse * 50
        
        hue = (t * 20 + ring * 30) % 360
        py5.stroke(hue, 80, 90, 80)
        py5.stroke_weight(2 + py5.sin(t - ring) * 1.5)
        
        if ring == 0:
            draw_seed_of_life(0, 0, radius, t)
        else:
            num_points = ring * 6
            for i in range(num_points):
                angle = (i / num_points) * py5.TWO_PI
                # Hexagonal grid logic roughly
                x = ring * spacing * py5.cos(angle)
                y = ring * spacing * py5.sin(angle)
                
                # Modulate the distance slightly
                wave = py5.sin(t + i * 0.5) * 50
                x += wave * py5.cos(angle)
                y += wave * py5.sin(angle)
                
                draw_seed_of_life(x, y, radius * 0.8, -t)

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
