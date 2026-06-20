from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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

NUM_RIBBONS = 50
TRAIL_LENGTH = 80

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
    global ribbons
    # Initialize ribbon start positions
    ribbons = []
    for i in range(NUM_RIBBONS):
        x = py5.random(-800, 800)
        y = py5.random(-800, 800)
        z = py5.random(-800, 800)
        hue = (200 + py5.random(-40, 40)) % 360
        ribbons.append({
            'pos': np.array([x, y, z]),
            'hue': hue,
            'trail': []
        })

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2, -500)
    
    # Rotate the whole camera view slowly
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.2)
    
    noise_scale = 0.003
    
    for r in ribbons:
        p = r['pos']
        
        # Calculate vector field force based on 3D noise
        angle_x = py5.os_noise(p[0] * noise_scale, p[1] * noise_scale, t * 0.5) * py5.TWO_PI * 4
        angle_y = py5.os_noise(p[1] * noise_scale, p[2] * noise_scale, t * 0.5) * py5.TWO_PI * 4
        angle_z = py5.os_noise(p[2] * noise_scale, p[0] * noise_scale, t * 0.5) * py5.TWO_PI * 4
        
        v_x = py5.cos(angle_x) * 15
        v_y = py5.sin(angle_y) * 15
        v_z = py5.sin(angle_z) * 15
        
        # Add a slight pull towards center to keep them visible
        pull_x = -p[0] * 0.005
        pull_y = -p[1] * 0.005
        pull_z = -p[2] * 0.005
        
        r['pos'] += np.array([v_x + pull_x, v_y + pull_y, v_z + pull_z])
        
        # Add to trail
        r['trail'].append(r['pos'].copy())
        if len(r['trail']) > TRAIL_LENGTH:
            r['trail'].pop(0)
            
        # Draw ribbon
        if len(r['trail']) > 1:
            py5.no_fill()
            py5.stroke_weight(4)
            py5.begin_shape(py5.LINE_STRIP)
            for i, tp in enumerate(r['trail']):
                alpha = (i / TRAIL_LENGTH) * 100
                py5.stroke(r['hue'], 80, 90, alpha)
                py5.vertex(tp[0], tp[1], tp[2])
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
