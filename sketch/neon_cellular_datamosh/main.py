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
DURATION_SEC = 15  # 15 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# High saturation glitch palette
BG_COLOR = (5, 5, 12)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 128)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(*BG_COLOR)
    py5.color_mode(py5.RGB, 255)

def draw():
    # Don't clear the background entirely, let the "datamosh" accumulate
    # Draw cellular-like random glowing rects
    t = py5.frame_count / TOTAL_FRAMES
    
    # Glitch injection probability increases over time
    glitch_prob = 0.05 + t * 0.4
    
    py5.blend_mode(py5.ADD)
    
    # Draw vertical/horizontal cellular lines
    for _ in range(5):
        x = np.random.randint(0, py5.width)
        y = np.random.randint(0, py5.height)
        w = np.random.choice([2, 5, 10, 20])
        h = np.random.choice([2, 10, 50, 200])
        
        colors = [CYAN, MAGENTA, YELLOW, GREEN]
        c_choice = colors[np.random.randint(len(colors))]
        
        py5.fill(*c_choice, 150)
        py5.no_stroke()
        py5.rect(x, y, w, h)

    # Perform NumPy datamoshing and channel shifting
    if np.random.random() < glitch_prob:
        py5.load_np_pixels()
        px = py5.np_pixels
        height, width = px.shape[:2]
        
        # Horizontal tear
        y1 = np.random.randint(0, height - 100)
        y2 = y1 + np.random.randint(5, 40)
        shift = np.random.randint(-150, 150)
        
        if shift > 0:
            px[y1:y2, shift:] = px[y1:y2, :-shift]
        elif shift < 0:
            px[y1:y2, :shift] = px[y1:y2, -shift:]
            
        # RGB channel swap for a small block
        x1 = np.random.randint(0, width - 200)
        x2 = x1 + np.random.randint(50, 200)
        y3 = np.random.randint(0, height - 100)
        y4 = y3 + np.random.randint(50, 100)
        
        # Shuffle R G B channels in that block
        block = px[y3:y4, x1:x2, :3]
        px[y3:y4, x1:x2, 0] = block[:, :, 1]
        px[y3:y4, x1:x2, 1] = block[:, :, 2]
        px[y3:y4, x1:x2, 2] = block[:, :, 0]
            
        py5.update_np_pixels()
        
    py5.blend_mode(py5.BLEND)
    # Slow fade to dark to prevent pure whiteout
    py5.fill(*BG_COLOR, 10)
    py5.rect(0, 0, py5.width, py5.height)
        
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

py5.run_sketch()
