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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 4000
positions = None
angles = None
colors = None

def setup():
    global positions, angles, colors
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.random.rand(NUM_PARTICLES, 2)
    positions[:, 0] *= py5.width
    positions[:, 1] *= py5.height
    
    # Store previous positions for drawing lines
    global prev_positions
    prev_positions = positions.copy()
    
def get_angle(x, y, z):
    # Scale coordinates for noise
    scl = 0.002
    n = py5.os_noise(x * scl, y * scl, z)
    return py5.remap(n, 0, 1, 0, py5.TWO_PI * 4)

def draw():
    global positions, prev_positions
    
    # Fade background
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 5)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.005
    
    lines = []
    stroke_colors = []
    
    # Evolve positions
    for i in range(NUM_PARTICLES):
        x, y = positions[i]
        
        angle = get_angle(x, y, time)
        
        # Velocity
        vx = np.cos(angle) * 4
        vy = np.sin(angle) * 4
        
        # New position
        nx = x + vx
        ny = y + vy
        
        # Wrap around screen but don't draw line across
        wrapped = False
        if nx < 0: nx = py5.width; wrapped = True
        if nx > py5.width: nx = 0; wrapped = True
        if ny < 0: ny = py5.height; wrapped = True
        if ny > py5.height: ny = 0; wrapped = True
        
        if not wrapped:
            lines.append([x, y, nx, ny])
            
            # Map angle to hue (0-360)
            hue = ((angle / py5.TWO_PI) * 360) % 360
            stroke_colors.append((hue, 80, 100, 15))
            
        positions[i] = [nx, ny]
        
    # Batch draw lines (py5 doesn't have a color-per-line in a single batch easily without begin_shape, 
    # so we'll just group them roughly or use points. Actually we can just draw them in a loop if it's fast enough, 
    # but 4000 lines might be a bit slow. Let's try grouping by hue bin)
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    if lines:
        lines_arr = np.array(lines)
        colors_arr = np.array(stroke_colors)
        
        # 12 hue bins
        for b in range(12):
            bin_min = b * 30
            bin_max = (b + 1) * 30
            
            mask = (colors_arr[:, 0] >= bin_min) & (colors_arr[:, 0] < bin_max)
            bin_lines = lines_arr[mask]
            
            if len(bin_lines) > 0:
                py5.stroke(bin_min + 15, 80, 100, 15)
                py5.lines(bin_lines)

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
