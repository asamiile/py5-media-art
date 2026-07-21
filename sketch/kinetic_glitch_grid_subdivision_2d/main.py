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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_cell(x, y, w, h, depth, max_depth, t):
    # Base condition to stop subdividing
    if depth >= max_depth:
        # Draw the cell
        noise_val = py5.noise(x * 0.002, y * 0.002, t * 2.0)
        
        py5.stroke(0, 0, 80, 80)
        py5.stroke_weight(2)
        
        if noise_val > 0.7:
            # Solid glitch block
            hue = (t * 360 + noise_val * 720) % 360
            py5.fill(hue, 90, 100, 90)
            py5.rect(x, y, w, h)
            
            # Inner glitch pattern
            py5.fill(0, 0, 100, 50)
            py5.no_stroke()
            py5.rect(x + py5.random(w*0.1), y + py5.random(h*0.1), py5.random(w*0.8), py5.random(h*0.1))
            
        elif noise_val > 0.4:
            # Wireframe block with cross
            py5.no_fill()
            py5.rect(x, y, w, h)
            py5.line(x, y, x + w, y + h)
            py5.line(x + w, y, x, y + h)
        else:
            # Empty
            py5.no_fill()
            py5.rect(x, y, w, h)
        return

    # Subdivide condition based on noise
    noise_subdiv = py5.noise(x * 0.005 + t, y * 0.005 - t)
    
    # Threshold for subdivision depends on depth (higher depth = harder to subdivide)
    threshold = 0.3 + (depth / max_depth) * 0.4
    
    if noise_subdiv > threshold:
        hw = w / 2
        hh = h / 2
        draw_cell(x, y, hw, hh, depth + 1, max_depth, t)
        draw_cell(x + hw, y, hw, hh, depth + 1, max_depth, t)
        draw_cell(x, y + hh, hw, hh, depth + 1, max_depth, t)
        draw_cell(x + hw, y + hh, hw, hh, depth + 1, max_depth, t)
    else:
        # Draw this cell without further subdivision
        draw_cell(x, y, w, h, max_depth, max_depth, t)

def draw():
    py5.background(10)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Grid properties
    grid_size = 400
    max_depth = 4
    
    py5.push_matrix()
    # Add a slight 2D pan based on time to keep it moving
    pan_x = (t * py5.width * 0.5) % grid_size
    pan_y = (t * py5.height * 0.3) % grid_size
    
    py5.translate(-pan_x, -pan_y)
    
    # Draw a larger grid that covers the screen + padding
    for x in range(0, py5.width + grid_size, grid_size):
        for y in range(0, py5.height + grid_size, grid_size):
            draw_cell(x, y, grid_size, grid_size, 0, max_depth, t)
            
    py5.pop_matrix()

    # Add a CRT scanline overlay
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    py5.fill(0, 0, 50, 10)
    for y in range(0, py5.height, 4):
        py5.rect(0, y, py5.width, 2)
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
        import os
        os._exit(0)

py5.run_sketch()
