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

bubbles = []
NUM_BUBBLES = 3000

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    py5.background(0)

    for i in range(NUM_BUBBLES):
        bubbles.append({
            "x": random.uniform(0, py5.width),
            "y": random.uniform(0, py5.height),
            "hue": random.uniform(180, 320), # blue to pink
            "seed": random.uniform(0, 1000)
        })

def draw():
    py5.background(0) # Clear each frame for this one
    
    t = py5.frame_count * 0.015
    
    for b in bubbles:
        # Use 3D noise: x, y, and time
        noise_val = py5.os_noise(b["x"] * 0.002, b["y"] * 0.002, t + b["seed"])
        
        # radius pulses based on noise
        r = py5.remap(noise_val, -1, 1, 0, 150)
        
        # small drift
        drift_x = py5.remap(py5.os_noise(b["x"] * 0.01, t, b["seed"]), -1, 1, -2, 2)
        drift_y = py5.remap(py5.os_noise(t, b["y"] * 0.01, b["seed"]+100), -1, 1, -2, 2)
        
        b["x"] += drift_x
        b["y"] += drift_y
        
        # wrap around
        b["x"] = b["x"] % py5.width
        b["y"] = b["y"] % py5.height
        
        # alpha based on size
        alpha = py5.remap(r, 0, 150, 60, 0)
        if alpha < 0: alpha = 0
        
        if r > 2:
            py5.fill(b["hue"], 80, 100, alpha)
            py5.circle(b["x"], b["y"], r)

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
