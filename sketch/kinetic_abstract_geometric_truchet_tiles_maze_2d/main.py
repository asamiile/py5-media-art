from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid
TILE_SIZE = 60
COLS = SIZE[0] // TILE_SIZE + 2
ROWS = SIZE[1] // TILE_SIZE + 2

# State: 0 or 1 for the two tile orientations
state = np.random.randint(0, 2, (COLS, ROWS)).astype(np.float32)
target_state = state.copy()
# Delay offsets to make rotation look like a wave
offsets = np.zeros((COLS, ROWS))
for i in range(COLS):
    for j in range(ROWS):
        offsets[i, j] = np.random.uniform(0, 2 * np.pi)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(TILE_SIZE * 0.15)
    py5.stroke_cap(py5.SQUARE)
    py5.no_fill()

def draw():
    global state, target_state
    
    # Trails / motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    time_val = py5.frame_count * 0.05
    
    # Periodically assign new target states based on a wave
    for i in range(COLS):
        for j in range(ROWS):
            noise_val = np.sin(time_val * 0.5 + i * 0.1) * np.cos(time_val * 0.4 + j * 0.1)
            if noise_val > 0.8:
                target_state[i, j] = 1.0
            elif noise_val < -0.8:
                target_state[i, j] = 0.0
                
            # Smooth interpolation
            diff = target_state[i, j] - state[i, j]
            state[i, j] += diff * 0.1
    
    # Draw tiles
    for i in range(COLS):
        for j in range(ROWS):
            x = i * TILE_SIZE
            y = j * TILE_SIZE
            
            s = state[i, j]
            # Rotation angle from 0 to PI/2
            angle = s * (np.pi / 2.0)
            
            py5.push_matrix()
            py5.translate(x + TILE_SIZE/2, y + TILE_SIZE/2)
            py5.rotate(angle)
            
            # Color shifts across the grid
            hue = (time_val * 20.0 + i * 5.0 + j * 5.0) % 360.0
            py5.stroke(hue, 80, 100, 80)
            
            # Draw Truchet arcs
            r = TILE_SIZE / 2.0
            
            py5.arc(-r, -r, TILE_SIZE, TILE_SIZE, 0, np.pi/2)
            py5.arc(r, r, TILE_SIZE, TILE_SIZE, np.pi, np.pi*1.5)
            
            py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

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
