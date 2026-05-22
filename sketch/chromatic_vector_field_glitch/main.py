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

BG_COLOR = (2, 2, 8)
NUM_PARTICLES = 10000

# Arrays for particles
px = np.random.uniform(0, SIZE[0], NUM_PARTICLES)
py = np.random.uniform(0, SIZE[1], NUM_PARTICLES)
phues = np.random.uniform(0, 360, NUM_PARTICLES)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(*BG_COLOR)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    
def draw():
    global px, py, phues
    
    # Slight fade for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(240, 100, 5, 20)  # Very dark blue/black fade
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    progress = py5.frame_count / TOTAL_FRAMES
    glitch_intensity = progress ** 2
    
    noise_scale = 0.005
    
    # Generate vector field angles
    angles = py5.os_noise(px * noise_scale, py * noise_scale, np.full_like(px, t)) * py5.TWO_PI * 4
    
    # Random glitch in vector field
    if np.random.random() < glitch_intensity * 0.3:
        angles += np.random.uniform(-py5.PI, py5.PI, NUM_PARTICLES)
        
    speed = 4.0
    vx = np.cos(angles) * speed
    vy = np.sin(angles) * speed
    
    px += vx
    py += vy
    
    # Wrap edges
    px = np.where(px < 0, py5.width, px)
    px = np.where(px > py5.width, 0, px)
    py = np.where(py < 0, py5.height, py)
    py = np.where(py > py5.height, 0, py)
    
    # Shift colors over time
    phues = (phues + 1) % 360
    
    # Draw particles (use point arrays or small rects)
    # Since py5 points in a loop can be slow, we draw a fraction of them or use numpy to pack points?
    # Actually, drawing 10000 small rects is doable in python if we optimize
    # Let's just use point() in a loop but with py5.begin_shape(py5.POINTS)
    
    py5.stroke_weight(2)
    for i in range(0, NUM_PARTICLES, 2):  # Draw half to save time
        py5.stroke(phues[i], 90, 100, 150)
        py5.point(px[i], py[i])
        
    py5.no_stroke()

    # NumPy array glitching
    if np.random.random() < glitch_intensity * 0.6:
        py5.load_np_pixels()
        arr = py5.np_pixels
        h, w = arr.shape[:2]
        
        # Horizontal shift blocks
        for _ in range(np.random.randint(1, 5)):
            y1 = np.random.randint(0, h - 20)
            y2 = y1 + np.random.randint(5, 50)
            shift = np.random.randint(-150, 150)
            
            if shift > 0:
                arr[y1:y2, shift:] = arr[y1:y2, :-shift]
                arr[y1:y2, :shift] = 0
            elif shift < 0:
                arr[y1:y2, :shift] = arr[y1:y2, -shift:]
                arr[y1:y2, shift:] = 0
                
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
