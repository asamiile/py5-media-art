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
from lib.safety import apply_anti_flicker_filter

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Colors
BG_COLOR = (5, 5, 10)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(*BG_COLOR)
    py5.color_mode(py5.RGB, 255)
    py5.no_stroke()

def draw():
    # Clear background with a trail fade effect
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / 30.0
    progress = py5.frame_count / TOTAL_FRAMES
    glitch_intensity = progress ** 2  # Increases over time
    
    cx, cy = py5.width / 2, py5.height / 2
    
    # Draw interference pattern
    colors = [CYAN, MAGENTA, YELLOW]
    num_sources = 3
    
    for i in range(num_sources):
        py5.fill(*colors[i], 15)
        
        # Moving sources
        sx = cx + np.sin(t * 0.5 + i * py5.TWO_PI / num_sources) * 300
        sy = cy + np.cos(t * 0.7 + i * py5.TWO_PI / num_sources) * 300
        
        # Glitch source position
        if np.random.random() < glitch_intensity * 0.5:
            sx += np.random.uniform(-100, 100)
            sy += np.random.uniform(-100, 100)
            
        # Draw concentric rings
        num_rings = 40
        for r in range(1, num_rings + 1):
            radius = (r * 20 + t * 50) % (py5.width * 1.5)
            thickness = max(2, 10 - r * 0.2)
            
            py5.stroke(*colors[i], 100 - r * 2)
            py5.stroke_weight(thickness)
            py5.no_fill()
            
            # Sub-segment drawing to allow tearing
            py5.begin_shape()
            segments = 100
            for s in range(segments + 1):
                angle = s * py5.TWO_PI / segments
                x = sx + np.cos(angle) * radius
                y = sy + np.sin(angle) * radius
                
                # Introduce noise/tearing
                if np.random.random() < glitch_intensity * 0.1:
                    x += np.random.uniform(-50, 50)
                
                py5.vertex(x, y)
            py5.end_shape()
            py5.no_stroke()

    # Datamoshing / Channel manipulation via NumPy
    if np.random.random() < glitch_intensity * 0.8:
        py5.load_np_pixels()
        px = py5.np_pixels
        h, w = px.shape[:2]
        
        # Horizontal shift block
        y1 = np.random.randint(0, h - 50)
        y2 = y1 + np.random.randint(10, 150)
        shift = np.random.randint(-200, 200)
        
        if shift > 0:
            px[y1:y2, shift:] = px[y1:y2, :-shift]
            px[y1:y2, :shift] = 0
        elif shift < 0:
            px[y1:y2, :shift] = px[y1:y2, -shift:]
            px[y1:y2, shift:] = 0
            
        # RGB channel inversion
        if np.random.random() < 0.3:
            x1 = np.random.randint(0, w - 100)
            x2 = x1 + np.random.randint(50, 300)
            y3 = np.random.randint(0, h - 50)
            y4 = y3 + np.random.randint(50, 200)
            
            block = px[y3:y4, x1:x2, :3]
            px[y3:y4, x1:x2, :3] = 255 - block
            
        py5.update_np_pixels()
        
    apply_anti_flicker_filter(0.5)
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
