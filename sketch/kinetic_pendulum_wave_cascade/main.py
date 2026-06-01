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

# Pendulum parameters
NUM_PENDULUMS = 250
base_oscillations = 20
oscillations = np.linspace(base_oscillations, base_oscillations + 30, NUM_PENDULUMS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur / fade
    py5.fill(0, 0, 0, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES # normalized time 0.0 to 1.0
    
    py5.blend_mode(py5.ADD)
    
    y_step = (py5.height * 0.8) / NUM_PENDULUMS
    start_y = py5.height * 0.1
    
    max_amplitude = py5.width * 0.4
    
    py5.stroke_weight(5)
    
    for i in range(NUM_PENDULUMS):
        osc = oscillations[i]
        # phase offset so they start at maximum amplitude
        angle = t * osc * py5.TWO_PI
        
        x_offset = np.cos(angle) * max_amplitude
        
        x = py5.width / 2 + x_offset
        y = start_y + i * y_step
        
        # Color mapping (Amber to Crimson to Cyan gradient)
        h = (45 + (i / NUM_PENDULUMS) * 300) % 360
        
        # calculate velocity to modulate brightness (brighter when moving faster at the center)
        v = np.abs(np.sin(angle))
        
        py5.stroke(h, 80, 50 + v * 50, 200)
        py5.point(x, y)
        
        # Draw a faint line to the center
        py5.stroke_weight(1)
        py5.stroke(h, 80, 50, 15)
        py5.line(py5.width/2, y, x, y)
        py5.stroke_weight(5)
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.", flush=True)
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.", flush=True)
            
        import os
        os._exit(0)

py5.run_sketch()
