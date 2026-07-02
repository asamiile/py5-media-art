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

streams = []
num_streams = 200

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(num_streams):
        # random radius and angle
        radius = py5.random(100, 800)
        angle = py5.random(py5.TWO_PI)
        z = py5.random(-py5.height, py5.height)
        speed = py5.random(5, 20)
        length = py5.random(50, 300)
        hue = py5.random(150, 190) # Cyan to deep green/blue
        streams.append({'r': radius, 'a': angle, 'z': z, 's': speed, 'l': length, 'h': hue})

def draw():
    py5.background(5, 10, 15)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    py5.rotate_x(py5.PI / 6)
    py5.rotate_y(t * 0.2)
    
    py5.stroke_weight(3)
    
    for s in streams:
        s['z'] += s['s']
        if s['z'] > py5.height:
            s['z'] = -py5.height
            s['a'] = py5.random(py5.TWO_PI)
            s['r'] = py5.random(100, 800)
            s['h'] = py5.random(150, 190)
            
        x = py5.cos(s['a']) * s['r']
        y = s['z']
        z = py5.sin(s['a']) * s['r']
        
        # The head of the stream
        py5.stroke(s['h'], 90, 100, 100)
        py5.point(x, y, z)
        
        # The tail of the stream
        py5.stroke(s['h'], 80, 50, 30)
        py5.line(x, y, z, x, y - s['l'], z)
        
        # Random data bursts (branches)
        if py5.random_int(100) < 2:
            py5.stroke(0, 0, 100, 80)
            burst_len = py5.random(20, 100)
            angle_burst = s['a'] + py5.random(-0.5, 0.5)
            x2 = py5.cos(angle_burst) * (s['r'] + py5.random(-50, 50))
            y2 = y - py5.random(50)
            z2 = py5.sin(angle_burst) * (s['r'] + py5.random(-50, 50))
            py5.line(x, y, z, x2, y2, z2)


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
