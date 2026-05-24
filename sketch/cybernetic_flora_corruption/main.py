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

# Colors
BG_COLOR = "#05050A"  # Dark obsidian/navy
CYAN = "#00FFFF"
MAGENTA = "#FF00FF"
YELLOW = "#FFFF00"

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(py5.color(5, 5, 10))
    py5.color_mode(py5.RGB, 255)
    py5.blend_mode(py5.ADD)

def draw():
    # We do NOT call background() each frame so trails accumulate and we can "datamosh" them
    
    # Random glitch background clearing (very faint fade)
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 10, 5)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / 100.0
    progress = py5.frame_count / TOTAL_FRAMES
    
    # Center
    cx, cy = py5.width / 2, py5.height / 2
    
    # Draw blooming cyber flora
    num_petals = 7
    base_radius = py5.width * 0.2 * (1.0 + progress)
    
    # Introduce glitch: random stutter in time
    glitch_t = t
    if np.random.random() < progress * 0.3:  # Glitches increase over time
        glitch_t += np.random.uniform(-0.5, 0.5)
        
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(glitch_t * 0.2)
    
    # Draw geometric structure
    for i in range(num_petals):
        angle = py5.TWO_PI / num_petals * i
        
        # Chromatic splitting
        for c_idx, hex_col in enumerate([CYAN, MAGENTA, YELLOW]):
            offset_x = 0
            offset_y = 0
            if np.random.random() < progress * 0.5:
                # RGB split shear glitch
                offset_x = np.random.uniform(-50, 50) * progress
                offset_y = np.random.uniform(-10, 10) * progress
                
            col = py5.color(int(hex_col[1:3], 16), int(hex_col[3:5], 16), int(hex_col[5:7], 16), 150)
            py5.stroke(col)
            py5.stroke_weight(2)
            py5.no_fill()
            
            py5.push_matrix()
            py5.rotate(angle)
            
            # Flora curves (Maurer rose inspired)
            py5.begin_shape()
            for theta in np.linspace(0, py5.PI, 60):
                r = base_radius * np.sin(num_petals * theta + glitch_t)
                x = r * np.cos(theta) + offset_x
                y = r * np.sin(theta) + offset_y
                
                # High-frequency noise glitch
                if np.random.random() < 0.05:
                    x += np.random.uniform(-20, 20)
                    y += np.random.uniform(-20, 20)
                    
                py5.vertex(x, y)
            py5.end_shape()
            py5.pop_matrix()

    py5.pop_matrix()
    
    # Pixel manipulation: datamoshing / horizontal tearing
    if np.random.random() < 0.1 + progress * 0.4:
        py5.load_np_pixels()
        px = py5.np_pixels
        h, w = px.shape[:2]
        
        # Horizontal shift block
        y1 = np.random.randint(0, h - 50)
        y2 = y1 + np.random.randint(10, 50)
        shift = np.random.randint(-100, 100)
        
        if shift > 0:
            px[y1:y2, shift:] = px[y1:y2, :-shift]
            px[y1:y2, :shift] = 0
        elif shift < 0:
            px[y1:y2, :shift] = px[y1:y2, -shift:]
            px[y1:y2, shift:] = 0
            
        py5.update_np_pixels()
        
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
