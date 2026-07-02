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

NUM_STREAMS = 250
MAX_LENGTH = 40

# Each stream has an x position, a y position (head), speed, and a length
stream_x = np.random.uniform(0, SIZE[0], NUM_STREAMS)
stream_y = np.random.uniform(-SIZE[1], SIZE[1], NUM_STREAMS)
stream_speed = np.random.uniform(5.0, 20.0, NUM_STREAMS)
stream_length = np.random.randint(10, MAX_LENGTH, NUM_STREAMS)
stream_hue = np.random.uniform(120, 180, NUM_STREAMS) # Cyan to green

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    # Fade background slightly to create trails for the glitches
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    global stream_y, stream_x, stream_hue
    
    # Update positions
    stream_y += stream_speed
    
    # Glitch logic
    glitch_prob = 0.01
    glitch_mask = np.random.random(NUM_STREAMS) < glitch_prob
    if np.any(glitch_mask):
        # Sudden horizontal shift
        stream_x[glitch_mask] += np.random.uniform(-50, 50, np.sum(glitch_mask))
        # Hue shift
        stream_hue[glitch_mask] = (stream_hue[glitch_mask] + 180) % 360
    
    # Reset streams that fall off screen
    reset_mask = stream_y - stream_length * 15 > SIZE[1]
    if np.any(reset_mask):
        stream_y[reset_mask] = np.random.uniform(-500, -100, np.sum(reset_mask))
        stream_x[reset_mask] = np.random.uniform(0, SIZE[0], np.sum(reset_mask))
        stream_speed[reset_mask] = np.random.uniform(5.0, 20.0, np.sum(reset_mask))
        stream_hue[reset_mask] = np.random.uniform(120, 180, np.sum(reset_mask))
        
    t = py5.frame_count * 0.05
        
    # Draw streams
    # We'll use quads or small rects for the stream parts
    for i in range(NUM_STREAMS):
        x = stream_x[i]
        y_head = stream_y[i]
        length = stream_length[i]
        hue = stream_hue[i]
        
        # Draw tail
        for j in range(length):
            y = y_head - j * 15
            if y > 0 and y < SIZE[1]:
                # Fade alpha towards tail
                alpha = 100 * (1.0 - (j / length))
                
                # Head is white
                if j == 0:
                    py5.fill(0, 0, 100, 100)
                else:
                    # Flicker effect based on noise/time
                    flicker = np.sin(y * 0.1 + t + i) * 20
                    py5.fill(hue, 80, 70 + flicker, alpha)
                
                # Wiggle slightly for glitchy feel
                glitch_x_offset = 0
                if np.random.random() < 0.005:
                    glitch_x_offset = np.random.uniform(-10, 10)
                    
                w = 8
                h = 10
                py5.rect(x + glitch_x_offset, y, w, h)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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
